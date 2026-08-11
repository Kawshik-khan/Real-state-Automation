import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  MessageSquare, 
  Sparkles, 
  AlertCircle, 
  DollarSign, 
  ArrowUpRight, 
  Clock, 
  UserCheck,
  Send,
  Building2,
  CheckCircle2,
  FileText,
  Share2,
  ShieldCheck,
  Inbox
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { sendChatMessage, getAnalyticsReport, getConversations } from '../services/api';

export default function DashboardHome({ setActiveTab }) {
  const { user } = useAuth();
  const userRole = user?.role || 'viewer';

  const [testMessage, setTestMessage] = useState('');
  const [chatResponse, setChatResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({
    totalLeads: 142,
    aiRate: '94.2%',
    hotLeads: 12,
    activeChats: 4,
    avgResponse: '1.2s',
    incomingMessagesToday: 58,
    pendingApprovals: 5,
    conversionRate: '18.4%'
  });

  // Recent incoming messages queue for Agent role
  const recentAgentMessages = [
    { id: 'msg-1', customer: 'Tanvir Ahmed', channel: 'WhatsApp', text: 'Hi, what is the booking amount for 3 BHK in GLG Sky Tower?', time: '2 mins ago', priority: 'High', intent: 'property_search' },
    { id: 'msg-2', customer: 'Nusrat Jahan', channel: 'Website', text: 'Can I schedule a site tour tomorrow at 11:00 AM?', time: '8 mins ago', priority: 'High', intent: 'booking' },
    { id: 'msg-3', customer: 'Rahim Chowdhury', channel: 'Facebook', text: 'Is bank loan financing available for Palm Beach Villa?', time: '15 mins ago', priority: 'Medium', intent: 'faq' },
    { id: 'msg-4', customer: 'Sabrina Karim', channel: 'Instagram', text: 'Please send floor plan PDF for Bandra project.', time: '32 mins ago', priority: 'Medium', intent: 'knowledge' },
  ];

  useEffect(() => {
    fetchLiveStats();
  }, []);

  const fetchLiveStats = async () => {
    try {
      const [analyticsRes, convsRes] = await Promise.allSettled([
        getAnalyticsReport(),
        getConversations()
      ]);

      let newMetrics = { ...metrics };
      if (analyticsRes.status === 'fulfilled' && analyticsRes.value?.metrics) {
        const m = analyticsRes.value.metrics;
        newMetrics.totalLeads = m.total_incoming_leads || 142;
        newMetrics.aiRate = `${m.ai_resolution_rate_percent || 94.2}%`;
        newMetrics.hotLeads = m.hot_leads_scored_above_80 || 12;
        newMetrics.avgResponse = `${m.avg_response_time_seconds || 1.2}s`;
      }
      if (convsRes.status === 'fulfilled' && convsRes.value?.conversations) {
        newMetrics.activeChats = convsRes.value.conversations.length;
      }
      setMetrics(newMetrics);
    } catch (err) {
      console.warn('Dashboard stats fallback:', err);
    }
  };

  const handleTestChat = async (e) => {
    e.preventDefault();
    if (!testMessage.trim()) return;
    
    setLoading(true);
    setChatResponse(null);
    try {
      const res = await sendChatMessage({
        message: testMessage,
        conversation_id: `demo_${Date.now()}`,
        channel: 'website',
        user_id: 'usr_demo'
      });
      setChatResponse(res);
    } catch (err) {
      setChatResponse({ reply: `Error: ${err.message}`, actions: [] });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* ── Dynamic Hero Banner ── */}
      <div className="glass-card" style={{
        padding: '24px 32px',
        background: userRole === 'agent'
          ? 'linear-gradient(135deg, rgba(6, 78, 59, 0.7), rgba(17, 24, 39, 0.9))'
          : userRole === 'manager'
          ? 'linear-gradient(135deg, rgba(30, 58, 138, 0.7), rgba(17, 24, 39, 0.9))'
          : userRole === 'admin'
          ? 'linear-gradient(135deg, rgba(88, 28, 135, 0.7), rgba(17, 24, 39, 0.9))'
          : 'linear-gradient(135deg, rgba(31, 41, 55, 0.7), rgba(17, 24, 39, 0.9))',
        border: '1px solid rgba(139, 92, 246, 0.3)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div className="badge badge-violet" style={{ marginBottom: '8px' }}>
            <Sparkles size={12} /> {userRole.toUpperCase()} CONSOLE ACTIVE
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>
            Welcome back, {user?.full_name || 'Team Member'}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            {userRole === 'agent' && `🎧 Customer Support & Sales Desk • ${metrics.incomingMessagesToday} Messages Received Today`}
            {userRole === 'manager' && `👔 Operations & Team Performance Hub • ${metrics.pendingApprovals} Social Posts Pending Review`}
            {userRole === 'admin' && `👑 Executive AI Command Center • 4 Channels Active • 94.2% AI Self-Resolution`}
            {userRole === 'viewer' && `👁️ Real Estate Project Catalog & Knowledge Repository`}
          </p>
        </div>

        {/* Dynamic Action Button */}
        {userRole === 'agent' && (
          <button className="btn-gradient" onClick={() => setActiveTab('conversations')}>
            <MessageSquare size={16} /> Takeover Live Chats
          </button>
        )}
        {userRole === 'manager' && (
          <button className="btn-gradient" onClick={() => setActiveTab('content')}>
            <Share2 size={16} /> Review Pending Content
          </button>
        )}
        {userRole === 'admin' && (
          <button className="btn-gradient" onClick={() => setActiveTab('conversations')}>
            <MessageSquare size={16} /> Open Live Command Center
          </button>
        )}
        {userRole === 'viewer' && (
          <button className="btn-gradient" onClick={() => setActiveTab('properties')}>
            <Building2 size={16} /> View Property Catalog
          </button>
        )}
      </div>

      {/* ── Dynamic KPI Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        
        {/* AGENT ROLE KPIS */}
        {userRole === 'agent' && (
          <>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Incoming Messages Today</span>
                <Inbox size={20} color="#34D399" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.incomingMessagesToday} Messages
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <ArrowUpRight size={14} /> +24% vs yesterday
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Assigned Live Chats</span>
                <MessageSquare size={20} color="#60A5FA" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.activeChats} Active
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#60A5FA', fontWeight: 600 }}>
                4 Channels Monitored
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>VIP Escalated Leads</span>
                <AlertCircle size={20} color="#F43F5E" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.hotLeads} Hot Leads
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FB7185', fontWeight: 600 }}>
                Requires Phone Call
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Avg Response Speed</span>
                <Clock size={20} color="#C084FC" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.avgResponse}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600 }}>
                Real-Time Fast Resolution
              </span>
            </div>
          </>
        )}

        {/* MANAGER ROLE KPIS */}
        {userRole === 'manager' && (
          <>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Team Lead Volume</span>
                <UserCheck size={20} color="#60A5FA" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.totalLeads} Total
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#60A5FA', fontWeight: 600 }}>
                Across All Channels
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>AI Self-Resolution %</span>
                <TrendingUp size={20} color="#8B5CF6" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.aiRate}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600 }}>
                Automated Bot Resolution
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Pending Social Approvals</span>
                <Share2 size={20} color="#FBBF24" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.pendingApprovals} Posts
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FBBF24', fontWeight: 600 }}>
                Requires Manager Sign-off
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Lead Conversion Rate</span>
                <DollarSign size={20} color="#10B981" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.conversionRate}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600 }}>
                +3.2% vs last month
              </span>
            </div>
          </>
        )}

        {/* ADMIN ROLE KPIS */}
        {userRole === 'admin' && (
          <>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Active Pipeline Value</span>
                <DollarSign size={20} color="#10B981" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                ৳14.8 Crore
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <ArrowUpRight size={14} /> +18.4% this week
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>AI Resolution %</span>
                <TrendingUp size={20} color="#8B5CF6" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.aiRate}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600 }}>
                Avg {metrics.avgResponse} response speed
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Active Conversations</span>
                <MessageSquare size={20} color="#06B6D4" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.activeChats} Active
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#22D3EE', fontWeight: 600 }}>
                Across 4 Social Channels
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Hot Leads (&ge; 80)</span>
                <AlertCircle size={20} color="#F43F5E" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.hotLeads} VIP Leads
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FB7185', fontWeight: 600 }}>
                Sales Follow-up Priority
              </span>
            </div>
          </>
        )}

        {/* VIEWER ROLE KPIS */}
        {userRole === 'viewer' && (
          <>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Total Projects</span>
                <Building2 size={20} color="#60A5FA" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                6 Projects
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#60A5FA', fontWeight: 600 }}>
                Luxury Developments
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Locations Covered</span>
                <Building2 size={20} color="#34D399" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                3 Prime Cities
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600 }}>
                Mumbai, Bangalore, Goa
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Available Housing Units</span>
                <FileText size={20} color="#C084FC" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                124 Units
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600 }}>
                Ready to Move &amp; Upcoming
              </span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Starting Price</span>
                <DollarSign size={20} color="#FBBF24" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                ৳85 Lakhs
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FBBF24', fontWeight: 600 }}>
                Financing Options Available
              </span>
            </div>
          </>
        )}

      </div>

      {/* ── Main Grid Content by Role ── */}

      {/* AGENT ROLE MAIN FEATURE: Live Incoming Customer Message Queue Stream */}
      {userRole === 'agent' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Inbox size={18} color="#34D399" />
                Live Customer Message Queue (Real-Time Ingest)
              </h3>
              <span className="badge badge-emerald">4 Channels Active</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recentAgentMessages.map((msg) => (
                <div key={msg.id} style={{
                  padding: '14px 16px',
                  borderRadius: '12px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#FFFFFF' }}>{msg.customer}</span>
                      <span className="badge badge-violet" style={{ fontSize: '0.65rem' }}>{msg.channel}</span>
                      <span style={{ fontSize: '0.7rem', color: '#9CA3AF' }}>{msg.time}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: '#D1D5DB', margin: 0 }}>"{msg.text}"</p>
                  </div>
                  <button
                    className="btn-gradient"
                    onClick={() => setActiveTab('conversations')}
                    style={{ padding: '8px 14px', fontSize: '0.75rem' }}
                  >
                    Reply Now
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Quick Agent Shortcuts</h3>
            <button className="btn-gradient" onClick={() => setActiveTab('conversations')} style={{ padding: '12px' }}>
              <MessageSquare size={16} /> Open Customer Chat Desk
            </button>
            <button className="glass-card" onClick={() => setActiveTab('properties')} style={{ padding: '12px', color: '#FFFFFF', cursor: 'pointer', textAlign: 'center', fontWeight: 600 }}>
              🏢 Search Properties &amp; Pricing
            </button>
          </div>
        </div>
      )}

      {/* MANAGER & ADMIN ROLE MAIN FEATURE: API Sandbox & Channel Status */}
      {(userRole === 'admin' || userRole === 'manager') && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          
          {/* Interactive Chat Sandbox */}
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Test AI Agent Engine (`POST /api/chat`)</h3>
              <span className="badge badge-emerald">Connected to FastAPI</span>
            </div>

            <form onSubmit={handleTestChat} style={{ display: 'flex', gap: '12px' }}>
              <input
                type="text"
                className="glass-input"
                style={{ flex: 1 }}
                placeholder="e.g. Apartment in Gulshan under 1 crore"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
              />
              <button type="submit" className="btn-gradient" disabled={loading}>
                <Send size={16} /> {loading ? 'Thinking...' : 'Test Send'}
              </button>
            </form>

            {/* Response Container */}
            {chatResponse && (
              <div style={{
                background: 'rgba(15, 23, 42, 0.7)',
                padding: '16px',
                borderRadius: '12px',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}>
                <div style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600 }}>
                  AI Assistant Response:
                </div>
                <p style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>
                  {chatResponse.reply}
                </p>

                {chatResponse.actions && chatResponse.actions.length > 0 && (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    {chatResponse.actions.map((act, i) => (
                      <span key={i} className="badge badge-amber">⚡ Trigger Action: {act}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Channel Health Status */}
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Gateway Webhooks</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="pulse-online" /> WhatsApp Business API
                </span>
                <span className="badge badge-emerald">Online</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="pulse-online" /> Facebook Messenger
                </span>
                <span className="badge badge-emerald">Online</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="pulse-online" /> Instagram DM
                </span>
                <span className="badge badge-emerald">Online</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="pulse-online" /> Website Live Widget
                </span>
                <span className="badge badge-emerald">Online</span>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* VIEWER ROLE MAIN FEATURE: Property Catalog Shortcut Banner */}
      {userRole === 'viewer' && (
        <div className="glass-card" style={{ padding: '24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <Building2 size={42} color="#C084FC" />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Explore GLG Assets Luxury Developments</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '600px' }}>
            Browse available residential apartments, villas, floor plans, brochures, and amenities across Mumbai, Bangalore, and Goa.
          </p>
          <button className="btn-gradient" onClick={() => setActiveTab('properties')}>
            Open Property Catalog &amp; Media Store
          </button>
        </div>
      )}

    </div>
  );
}
