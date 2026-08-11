import React, { useState } from 'react';
import { 
  TrendingUp, 
  MessageSquare, 
  Sparkles, 
  AlertCircle, 
  DollarSign, 
  ArrowUpRight, 
  Clock, 
  UserCheck,
  Send
} from 'lucide-react';
import { sendChatMessage } from '../services/api';

export default function DashboardHome({ setActiveTab }) {
  const [testMessage, setTestMessage] = useState('');
  const [chatResponse, setChatResponse] = useState(null);
  const [loading, setLoading] = useState(false);

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
      
      {/* Hero Welcome Banner */}
      <div className="glass-card" style={{
        padding: '24px 32px',
        background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.8), rgba(17, 24, 39, 0.9))',
        border: '1px solid rgba(139, 92, 246, 0.3)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div className="badge badge-violet" style={{ marginBottom: '8px' }}>
            <Sparkles size={12} /> AI Command Center Live
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Welcome back, GLG Real Estate Director</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            4 Channels Active (WhatsApp, FB, IG, Website) • 94.2% AI Self-Resolution Rate
          </p>
        </div>
        <button className="btn-gradient" onClick={() => setActiveTab('conversations')}>
          <MessageSquare size={16} /> Open Live Chat Viewer
        </button>
      </div>

      {/* Overview KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        
        {/* KPI 1 */}
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

        {/* KPI 2 */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>AI Resolution %</span>
            <TrendingUp size={20} color="#8B5CF6" />
          </div>
          <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
            94.2%
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={14} /> Avg 1.2s response time
          </span>
        </div>

        {/* KPI 3 */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Labor Cost Saved</span>
            <DollarSign size={20} color="#06B6D4" />
          </div>
          <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
            ৳5,20,000
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#22D3EE', fontWeight: 600 }}>
            184 Hours Saved This Month
          </span>
        </div>

        {/* KPI 4 */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Hot Leads (Propensity &gt; 85)</span>
            <AlertCircle size={20} color="#F43F5E" />
          </div>
          <h3 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '8px 0', color: '#FFFFFF' }}>
            12 VIP Leads
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#FB7185', fontWeight: 600 }}>
            Requires Sales Call Follow-up
          </span>
        </div>

      </div>

      {/* Main Grid: Interactive Test & Channel Status */}
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

    </div>
  );
}
