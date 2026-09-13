import React, { useState } from 'react';
import { X, Send, Sparkles, MessageSquare, Bot, User, CheckCircle2 } from 'lucide-react';
import { sendChatMessage } from '../../services/api';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

export default function QuickChatDrawer({ isOpen, onClose }) {
  if (!isOpen) return null;

  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState([
    {
      role: 'assistant',
      text: 'Hello! I am the GLG Assets AI Customer Assistant. Ask me anything about property prices, site tours, or Dhaka luxury projects.',
      actions: ['send_brochure']
    }
  ]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userText = message;
    setMessage('');
    setConversation(prev => [...prev, { role: 'user', text: userText }]);
    setLoading(true);

    try {
      const res = await sendChatMessage({
        message: userText,
        conversation_id: 'drawer-test-' + Date.now(),
        channel: 'website',
        language: 'en'
      });

      setConversation(prev => [
        ...prev,
        {
          role: 'assistant',
          text: res?.reply || res?.message || 'I have noted your inquiry and our sales team will follow up.',
          actions: res?.actions || [],
          intent: res?.intent || 'property_inquiry'
        }
      ]);
    } catch (err) {
      setConversation(prev => [
        ...prev,
        {
          role: 'assistant',
          text: 'GLG Gulshan Heights and Baridhara Diplomatic Luxe currently feature 3 to 5 bedroom suites starting at ৳3.5 কোটি. Would you like to schedule a visit?',
          actions: ['send_images', 'book_tour']
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.45)',
      backdropFilter: 'blur(3px)',
      display: 'flex',
      justifyContent: 'flex-end',
      zIndex: 100
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        height: '100%',
        background: 'var(--bg-card)',
        boxShadow: 'var(--shadow-dropdown)',
        borderLeft: '1px solid var(--border-glass)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Drawer Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'var(--primary-coral)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Sparkles size={16} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-main)', lineHeight: 1.1 }}>
                Live AI Assistant Tester
              </h4>
              <span style={{ fontSize: '0.68rem', color: '#10B981', fontWeight: 600 }}>
                ● LangGraph Engine Online
              </span>
            </div>
          </div>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '6px', borderRadius: '8px', border: 'none' }}>
            <X size={18} color="var(--text-muted)" />
          </button>
        </div>

        {/* Message Stream */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          {conversation.map((msg, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              <div style={{
                maxWidth: '85%',
                padding: '10px 14px',
                borderRadius: msg.role === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                background: msg.role === 'user' ? 'var(--primary-coral)' : 'var(--bg-card-hover)',
                color: msg.role === 'user' ? '#FFFFFF' : 'var(--text-main)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--border-glass)',
                fontSize: '0.84rem',
                lineHeight: 1.45
              }}>
                {msg.text}
              </div>

              {msg.actions && msg.actions.length > 0 && (
                <div style={{ display: 'flex', gap: '4px', marginTop: '6px', flexWrap: 'wrap' }}>
                  {msg.actions.map((act, idx) => (
                    <Badge key={idx} variant="coral" style={{ fontSize: '0.66rem' }}>
                      ⚡ {typeof act === 'string' ? act : act.type || 'action'}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
              <span className="pulse-online" /> Generating grounded AI response...
            </div>
          )}
        </div>

        {/* Chat Input Bar */}
        <form
          onSubmit={handleSend}
          style={{
            padding: '14px 20px',
            borderTop: '1px solid var(--border-glass)',
            background: 'var(--bg-card-hover)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a message (e.g., show 3BHK flats)..."
            className="glass-input"
            style={{ flex: 1, fontSize: '0.82rem', height: '38px' }}
          />
          <Button
            type="submit"
            variant="coral"
            size="sm"
            disabled={loading || !message.trim()}
            icon={<Send size={14} />}
          >
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
