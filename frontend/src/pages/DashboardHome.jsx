import React, { useState, useEffect, useRef } from 'react';
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
  Inbox,
  RefreshCw,
  Zap,
  Activity
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { sendChatMessage, getAnalyticsReport, getConversations } from '../services/api';

export default function DashboardHome({ setActiveTab }) {
  const { user } = useAuth();
  const userRole = String(user?.role || 'viewer').toLowerCase();

  const [testMessage, setTestMessage] = useState('');
  const [chatResponse, setChatResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastSynced, setLastSynced] = useState('Just now');
  const [pingStats, setPingStats] = useState({
    whatsapp: 24,
    messenger: 31,
    instagram: 28,
    website: 12,
    pinecone: 18,
    pgvector: 14
  });

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

  // Dynamic live customer message stream for Agent role
  const [liveMessagesQueue, setLiveMessagesQueue] = useState([
    { id: 'msg-1', customer: 'Tanvir Ahmed', channel: 'WhatsApp', text: 'Hi, what is the booking amount for 3 BHK in GLG Sky Tower?', time: 'Just now', priority: 'High', intent: 'property_search' },
    { id: 'msg-2', customer: 'Nusrat Jahan', channel: 'Website', text: 'Can I schedule a site tour tomorrow at 11:00 AM?', time: '2 mins ago', priority: 'High', intent: 'booking' },
    { id: 'msg-3', customer: 'Rahim Chowdhury', channel: 'Facebook', text: 'Is bank loan financing available for Palm Beach Villa?', time: '5 mins ago', priority: 'Medium', intent: 'faq' },
    { id: 'msg-4', customer: 'Sabrina Karim', channel: 'Instagram', text: 'Please send floor plan PDF for Bandra project.', time: '12 mins ago', priority: 'Medium', intent: 'knowledge' },
  ]);

  // Real-time background polling interval (every 4 seconds)
  useEffect(() => {
    fetchLiveStats();
    const timer = setInterval(() => {
      fetchLiveStats(true);
      // Random subtle jitter for real-time latency pings
      setPingStats({
        whatsapp: Math.floor(20 + Math.random() * 10),
        messenger: Math.floor(25 + Math.random() * 12),
        instagram: Math.floor(22 + Math.random() * 10),
        website: Math.floor(10 + Math.random() * 6),
        pinecone: Math.floor(15 + Math.random() * 8),
        pgvector: Math.floor(12 + Math.random() * 6)
      });
    }, 4000);

    return () => clearInterval(timer);
  }, []);

  const fetchLiveStats = async (isBackground = false) => {
    if (!isBackground) setIsRefreshing(true);
    try {
      const [analyticsRes, convsRes] = await Promise.allSettled([
        getAnalyticsReport(),
        getConversations()
      ]);

      setMetrics((prev) => {
        let newMetrics = { ...prev };
        if (analyticsRes.status === 'fulfilled' && analyticsRes.value?.metrics) {
          const m = analyticsRes.value.metrics;
          newMetrics.totalLeads = m.total_incoming_leads || prev.totalLeads;
          newMetrics.aiRate = `${m.ai_resolution_rate_percent || 94.2}%`;
          newMetrics.hotLeads = m.hot_leads_scored_above_80 || prev.hotLeads;
          newMetrics.avgResponse = `${m.avg_response_time_seconds || 1.2}s`;
        }
        if (convsRes.status === 'fulfilled' && convsRes.value?.conversations) {
          newMetrics.activeChats = convsRes.value.conversations.length;
        }
        return newMetrics;
      });

      const now = new Date();
      setLastSynced(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } catch (err) {
      console.warn('Dashboard live stats poll fallback:', err);
    } finally {
      if (!isBackground) setIsRefreshing(false);
    }
  };

  const handleTestChat = async (e) => {
    e.preventDefault();
    if (!testMessage.trim()) return;
    
    const userMsgText = testMessage;
    setLoading(true);
    setChatResponse(null);

    // Immediately push to real-time message stream
    const newLiveMsg = {
      id: `msg-${Date.now()}`,
      customer: user?.full_name || 'Live Web User',
      channel: 'Website Test',
      text: userMsgText,
      time: 'Just now',
      priority: 'High',
      intent: 'live_test'
    };

    setLiveMessagesQueue((prev) => [newLiveMsg, ...prev.slice(0, 5)]);
    setMetrics((prev) => ({
      ...prev,
      incomingMessagesToday: prev.incomingMessagesToday + 1,
      activeChats: prev.activeChats + 1
    }));

    try {
      const res = await sendChatMessage({
        message: userMsgText,
        conversation_id: `live_demo_${Date.now()}`,
        channel: 'website',
        user_id: user?.id || 'usr_live'
      });
      setChatResponse(res);
    } catch (err) {
      setChatResponse({ reply: `Error: ${err.message}`, actions: [] });
    } finally {
      setLoading(false);
      setTestMessage('');
    }
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* ── Realtime Ticker & Sync Status Bar (Admin Only) ── */}
      {userRole === 'admin' && (
        <div style={{
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(139, 92, 246, 0.2)',
          borderRadius: '14px',
          padding: '10px 20px',
          fontSize: '0.8rem',
          color: '#D1D5DB'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: '#10B981',
              boxShadow: '0 0 10px #10B981',
              display: 'inline-block'
            }} />
            <span style={{ fontWeight: 700, color: '#34D399', letterSpacing: '0.5px' }}>REALTIME ENGINE ACTIVE</span>
            <span style={{ color: '#6B7280' }}>|</span>
            <span>Last Poll: <strong style={{ color: '#FFFFFF' }}>{lastSynced}</strong></span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '0.75rem', color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Activity size={14} color="#8B5CF6" /> Pinecone Vector: {pingStats.pinecone}ms
            </span>
            <span style={{ fontSize: '0.75rem', color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Zap size={14} color="#34D399" /> Supabase DB: {pingStats.pgvector}ms
            </span>
            <button 
              onClick={() => fetchLiveStats(false)} 
              disabled={isRefreshing}
              style={{
                background: 'rgba(139, 92, 246, 0.2)',
                border: '1px solid rgba(139, 92, 246, 0.4)',
                color: '#C084FC',
                borderRadius: '8px',
                padding: '4px 10px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <RefreshCw size={12} className={isRefreshing ? 'spin-anim' : ''} />
              {isRefreshing ? 'Syncing...' : 'Sync Now'}
            </button>
          </div>
        </div>
      )}

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
            <Sparkles size={12} /> {userRole.toUpperCase()} REAL-TIME CONSOLE
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>
            Welcome back, {user?.full_name || 'Team Member'} 👋
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            {userRole === 'agent' && `🎧 Customer Support & Sales Desk • ${metrics.incomingMessagesToday} Live Messages Received Today`}
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
            {/* KPI 1: Total Ad Spend */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Total Ad Spend (Monthly)</span>
                <DollarSign size={20} color="#10B981" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                ৳1,25,000
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <ArrowUpRight size={14} /> +12% vs last month
              </span>
            </div>

            {/* KPI 2: Campaign Reach & Impressions */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Campaign Reach &amp; Views</span>
                <TrendingUp size={20} color="#60A5FA" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                185,000 Reach
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#60A5FA', fontWeight: 600 }}>
                340,000 Total Impressions
              </span>
            </div>

            {/* KPI 3: Messages Received from Ads */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Messages Received from Ads</span>
                <Inbox size={20} color="#34D399" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                1,420 Messages
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600 }}>
                Cost Per Message: ৳88
              </span>
            </div>

            {/* KPI 4: Response Rate & AI Speed */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>AI Response Rate &amp; Speed</span>
                <Clock size={20} color="#8B5CF6" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                96.8% Answered
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600 }}>
                Avg 1.2s AI Response Time
              </span>
            </div>

            {/* KPI 5: Qualified Hot Leads */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Qualified Leads &amp; Tours</span>
                <UserCheck size={20} color="#FBBF24" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.totalLeads} Qualified
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FBBF24', fontWeight: 600 }}>
                32 Confirmed Site Tours
              </span>
            </div>

            {/* KPI 6: Pending Social Approvals */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Pending Social Approvals</span>
                <Share2 size={20} color="#F43F5E" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.pendingApprovals} Posts
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FB7185', fontWeight: 600 }}>
                Requires Manager Sign-off
              </span>
            </div>
          </>
        )}

        {/* ADMIN ROLE KPIS */}
        {userRole === 'admin' && (
          <>
            {/* KPI 1: Active Pipeline Value */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Active Pipeline Value (GDV)</span>
                <DollarSign size={20} color="#10B981" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                ৳14.8 Crore
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <ArrowUpRight size={14} /> +18.4% this week
              </span>
            </div>

            {/* KPI 2: AI-Attributed Deal Value */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>AI-Attributed Deal Value</span>
                <Sparkles size={20} color="#8B5CF6" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                ৳8.2 Crore
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600 }}>
                55.4% AI-Driven Pipeline
              </span>
            </div>

            {/* KPI 3: Autonomous Resolution % */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Autonomous AI Self-Resolution</span>
                <TrendingUp size={20} color="#34D399" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.aiRate}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600 }}>
                5.8% Human Escalation Rate
              </span>
            </div>

            {/* KPI 4: VIP Hot Leads Scored */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Hot Leads (Score &ge; 80)</span>
                <AlertCircle size={20} color="#F43F5E" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.hotLeads} VIP Leads
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FB7185', fontWeight: 600 }}>
                Requires Phone Call Follow-up
              </span>
            </div>

            {/* KPI 5: Avg Lead Qualification Speed */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Avg Qualification Speed</span>
                <Clock size={20} color="#06B6D4" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                45 Seconds
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#22D3EE', fontWeight: 600 }}>
                Real-Time AI Scoring
              </span>
            </div>

            {/* KPI 6: Site Tour Booking Rate */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Site Tour Booking Rate</span>
                <UserCheck size={20} color="#FBBF24" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                32.4%
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#FBBF24', fontWeight: 600 }}>
                Confirmed Property Visits
              </span>
            </div>

            {/* KPI 7: Knowledge Vector Precision */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Vector RAG Precision</span>
                <ShieldCheck size={20} color="#A78BFA" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                98.4%
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#A78BFA', fontWeight: 600 }}>
                Pinecone + pgvector Accuracy
              </span>
            </div>

            {/* KPI 8: System SLA Response Latency */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>System SLA &amp; Response Speed</span>
                <Zap size={20} color="#34D399" />
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
                {metrics.avgResponse}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600 }}>
                End-to-End API SLA
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
                Live Customer Message Stream (Real-Time Ingest)
              </h3>
              <span className="badge badge-emerald">● Auto-Syncing</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {liveMessagesQueue.map((msg) => (
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

      {/* MANAGER ROLE MAIN FEATURE: Active Ad Campaigns Performance & CPL Table */}
      {userRole === 'manager' && (
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Active Ad Campaigns &amp; Marketing Performance</h3>
              <p style={{ fontSize: '0.8rem', color: '#9CA3AF', marginTop: '2px' }}>
                Real-time advertising spend, reach, incoming message inquiries, and cost per lead (CPL).
              </p>
            </div>
            <button className="btn-gradient" onClick={() => setActiveTab('content')}>
              <Share2 size={16} /> Content &amp; Campaign Manager
            </button>
          </div>

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#9CA3AF' }}>
                  <th style={{ padding: '12px 16px' }}>Campaign Name &amp; Platform</th>
                  <th style={{ padding: '12px 16px' }}>Ad Budget Spent</th>
                  <th style={{ padding: '12px 16px' }}>Reach</th>
                  <th style={{ padding: '12px 16px' }}>Messages Recv</th>
                  <th style={{ padding: '12px 16px' }}>Qualified Leads</th>
                  <th style={{ padding: '12px 16px' }}>Cost Per Lead (CPL)</th>
                  <th style={{ padding: '12px 16px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#FFFFFF' }}>
                    GLG Sky Tower - Gulshan 3BHK
                    <div style={{ fontSize: '0.7rem', color: '#8B5CF6' }}>Meta Click-to-WhatsApp</div>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#34D399' }}>৳45,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>65,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>520</td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#60A5FA' }}>58 Leads</td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#C084FC' }}>৳775 / lead</td>
                  <td style={{ padding: '12px 16px' }}><span className="badge badge-emerald">🟢 Active</span></td>
                </tr>

                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#FFFFFF' }}>
                    Palm Beach Villa - Coastal Luxury
                    <div style={{ fontSize: '0.7rem', color: '#8B5CF6' }}>Instagram Reels Video Ad</div>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#34D399' }}>৳38,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>52,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>410</td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#60A5FA' }}>42 Leads</td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#C084FC' }}>৳904 / lead</td>
                  <td style={{ padding: '12px 16px' }}><span className="badge badge-emerald">🟢 Active</span></td>
                </tr>

                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#FFFFFF' }}>
                    Dhanmondi Heights - Residential
                    <div style={{ fontSize: '0.7rem', color: '#38BDF8' }}>Google Search Text Ads</div>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#34D399' }}>৳24,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>38,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>310</td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#60A5FA' }}>28 Leads</td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#C084FC' }}>৳857 / lead</td>
                  <td style={{ padding: '12px 16px' }}><span className="badge badge-emerald">🟢 Active</span></td>
                </tr>

                <tr>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#FFFFFF' }}>
                    Bandra Skyline - Investment Units
                    <div style={{ fontSize: '0.7rem', color: '#F43F5E' }}>FB Instant Lead Form</div>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#34D399' }}>৳18,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>30,000</td>
                  <td style={{ padding: '12px 16px', color: '#D1D5DB' }}>180</td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#60A5FA' }}>14 Leads</td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#C084FC' }}>৳1,285 / lead</td>
                  <td style={{ padding: '12px 16px' }}><span className="badge badge-amber">🟡 Paused</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MANAGER & ADMIN ROLE MAIN FEATURE: Gateway Webhooks & Channel Status */}
      {(userRole === 'admin' || userRole === 'manager') && (
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Active Webhook Gateways &amp; Channel Status</h3>
            <span className="badge badge-emerald">4 Channels Connected</span>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#FFFFFF' }}>WhatsApp Business</span>
                <span className="pulse-online" />
              </div>
              <span className="badge badge-emerald">{pingStats.whatsapp}ms latency</span>
            </div>

            <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#FFFFFF' }}>Facebook Messenger</span>
                <span className="pulse-online" />
              </div>
              <span className="badge badge-emerald">{pingStats.messenger}ms latency</span>
            </div>

            <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#FFFFFF' }}>Instagram DM</span>
                <span className="pulse-online" />
              </div>
              <span className="badge badge-emerald">{pingStats.instagram}ms latency</span>
            </div>

            <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#FFFFFF' }}>Website Live Widget</span>
                <span className="pulse-online" />
              </div>
              <span className="badge badge-emerald">{pingStats.website}ms latency</span>
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
