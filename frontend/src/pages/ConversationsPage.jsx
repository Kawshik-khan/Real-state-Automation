import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  UserCheck, 
  Bot, 
  Send, 
  FileText, 
  Calendar, 
  ShieldAlert, 
  Search, 
  Filter, 
  Radio, 
  Bell, 
  X, 
  Plus, 
  Trash2, 
  Sparkles, 
  RefreshCw, 
  User, 
  PhoneCall, 
  CheckCircle2, 
  AlertTriangle 
} from 'lucide-react';
import { 
  getConversations, 
  toggleTakeover, 
  sendAgentReply, 
  sendCustomerMessage, 
  createConversation, 
  deleteConversation, 
  getConversationsStreamUrl,
  getWebSocketUrl 
} from '../services/api';

const INITIAL_CONVERSATIONS = [
  {
    id: 'wa_8801711122233',
    name: 'Tanvir Hossain',
    phone: '+880 1711-122233',
    channel: 'whatsapp',
    lastMessage: 'I want 3 BHK in Gulshan under 1 crore',
    time: '2 mins ago',
    status: 'active',
    aiPaused: false,
    confidence: 0.92,
    intent: 'property_search',
    messages: [
      { sender: 'user', text: 'Hi, looking for apartments in Gulshan', time: '10:14 AM' },
      { sender: 'ai', text: 'Hello Tanvir! Welcome to GLG Assets. What is your preferred budget?', time: '10:14 AM' },
      { sender: 'user', text: 'I want 3 BHK in Gulshan under 1 crore', time: '10:16 AM' },
      { sender: 'ai', text: 'Great choice! GLG Gulshan Heights features 3 BHK units priced from ৳95 Lakhs.', time: '10:16 AM' }
    ]
  },
  {
    id: 'tg_88018998877',
    name: 'Mahmudur Rahman',
    phone: '+880 1899-887766',
    channel: 'telegram',
    lastMessage: 'Send me the brochure and price list for Uttara project',
    time: '5 mins ago',
    status: 'active',
    aiPaused: false,
    confidence: 0.95,
    intent: 'brochure',
    messages: [
      { sender: 'user', text: 'Send me the brochure and price list for Uttara project', time: '10:11 AM' },
      { sender: 'ai', text: 'Brochure for GLG Uttara Paradise has been generated. Sent via Telegram PDF attachment.', time: '10:11 AM' }
    ]
  },
  {
    id: 'fb_1029384756',
    name: 'Sarah Khan',
    phone: '+880 1822-334455',
    channel: 'facebook',
    lastMessage: 'Can I visit the site tomorrow at 3 PM?',
    time: '15 mins ago',
    status: 'escalated',
    aiPaused: true,
    confidence: 0.68,
    intent: 'booking',
    messages: [
      { sender: 'user', text: 'Is Banani Crest project open for site visit?', time: '09:45 AM' },
      { sender: 'ai', text: 'Yes Sarah! Site visits are available daily from 10 AM to 5 PM.', time: '09:45 AM' },
      { sender: 'user', text: 'Can I visit the site tomorrow at 3 PM?', time: '10:01 AM' }
    ]
  },
  {
    id: 'ig_99887766',
    name: 'Anisur Rahman',
    phone: '+880 1911-556677',
    channel: 'instagram',
    lastMessage: 'Is payment schedule flexible over 3 years?',
    time: '1 hour ago',
    status: 'active',
    aiPaused: false,
    confidence: 0.88,
    intent: 'faq',
    messages: [
      { sender: 'user', text: 'Is payment schedule flexible over 3 years?', time: '09:12 AM' }
    ]
  }
];

export default function ConversationsPage() {
  const [conversations, setConversations] = useState(INITIAL_CONVERSATIONS);
  const [selectedId, setSelectedId] = useState(INITIAL_CONVERSATIONS[0].id);
  const [replyText, setReplyText] = useState('');
  
  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [channelFilter, setChannelFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  // Input Mode: 'customer' (Test AI) vs 'agent' (Human Takeover Reply)
  const [inputMode, setInputMode] = useState('customer');
  const [isSending, setIsSending] = useState(false);

  // SSE / WS & Modals
  const [sseConnected, setSseConnected] = useState(false);
  const [activeToast, setActiveToast] = useState(null);

  const [showNewLeadModal, setShowNewLeadModal] = useState(false);
  const [showAiSummaryModal, setShowAiSummaryModal] = useState(false);

  // New Lead Form State
  const [newLeadForm, setNewLeadForm] = useState({
    name: '',
    phone: '',
    channel: 'whatsapp',
    message: ''
  });

  const messagesEndRef = useRef(null);

  // Fetch initial conversations from API
  const loadConversations = () => {
    getConversations()
      .then(res => {
        if (res.conversations && res.conversations.length > 0) {
          setConversations(res.conversations);
        }
      })
      .catch(err => console.error('Failed to load conversations:', err));
  };

  useEffect(() => {
    loadConversations();
  }, []);

  // WebSocket Live Stream Listener
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(getWebSocketUrl());
      ws.onopen = () => setSseConnected(true);
      ws.onclose = () => setSseConnected(false);
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'new_message') {
            setActiveToast({
              type: 'lead',
              title: `🔔 Real-Time Message Received!`,
              message: `Conv: ${payload.conversation_id} • ${payload.user_message || 'New activity'}`,
            });
            loadConversations();
          }
        } catch (err) {
          console.error("WS message parse error:", err);
        }
      };
    } catch (e) {
      console.warn("WebSocket fallback:", e);
    }
    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Real-time SSE Stream Listener
  useEffect(() => {
    const streamUrl = getConversationsStreamUrl();
    const eventSource = new EventSource(streamUrl);

    eventSource.onopen = () => setSseConnected(true);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const { event: evtType, data } = payload;

        if (evtType === 'new_lead') {
          setActiveToast({
            type: 'lead',
            title: `🔔 New ${data.channel?.toUpperCase() || 'Web'} Lead Received!`,
            message: `Lead ID: ${data.conversation_id} • ${data.message?.text || 'New message arrived'}`,
          });

          setConversations(prev => {
            const exists = prev.some(c => c.id === data.conversation_id);
            if (exists) {
              return prev.map(c => {
                if (c.id === data.conversation_id) {
                  return {
                    ...c,
                    lastMessage: data.message?.text || c.lastMessage,
                    time: 'Just now',
                    messages: [...c.messages, data.message]
                  };
                }
                return c;
              });
            } else {
              return [
                {
                  id: data.conversation_id,
                  name: data.name || `Lead ${data.conversation_id.slice(-6)}`,
                  phone: '+880 1700-000000',
                  channel: data.channel || 'website',
                  lastMessage: data.message?.text || 'New conversation',
                  time: 'Just now',
                  status: data.requires_escalation ? 'escalated' : 'active',
                  aiPaused: data.requires_escalation || false,
                  confidence: 0.90,
                  intent: 'inquiry',
                  messages: [data.message]
                },
                ...prev
              ];
            }
          });
        } else if (evtType === 'escalation_required') {
          setActiveToast({
            type: 'escalation',
            title: `⚠️ AI Escalation Alert!`,
            message: `Conversation ${data.conversation_id} requested Human Agent takeover!`,
          });
        } else if (evtType === 'message_received' || evtType === 'ai_reply') {
          setConversations(prev => prev.map(c => {
            if (c.id === data.conversation_id) {
              const textToMatch = (data.message?.text || '').trim();
              const senderToMatch = data.message?.sender;
              const exists = c.messages.some(
                m => (m.text || '').trim() === textToMatch && m.sender === senderToMatch
              );
              if (exists) {
                return {
                  ...c,
                  lastMessage: textToMatch || c.lastMessage,
                  time: 'Just now'
                };
              }
              return {
                ...c,
                lastMessage: textToMatch || c.lastMessage,
                time: 'Just now',
                messages: [...c.messages, data.message]
              };
            }
            return c;
          }));
        } else if (evtType === 'agent_takeover') {
          setConversations(prev => prev.map(c => {
            if (c.id === data.conversation_id) {
              return {
                ...c,
                aiPaused: data.aiPaused,
                status: data.status
              };
            }
            return c;
          }));
        } else if (evtType === 'conversation_deleted') {
          setConversations(prev => prev.filter(c => c.id !== data.conversation_id));
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    eventSource.onerror = () => setSseConnected(false);

    return () => eventSource.close();
  }, []);

  const selectedConv = conversations.find(c => c.id === selectedId) || conversations[0] || INITIAL_CONVERSATIONS[0];

  // Auto-scroll chat window when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [selectedConv?.messages?.length, isSending]);

  // Keep input mode in sync with selected conversation's takeover status
  useEffect(() => {
    if (selectedConv) {
      setInputMode(selectedConv.aiPaused ? 'agent' : 'customer');
    }
  }, [selectedConv?.id, selectedConv?.aiPaused]);

  // Toggle Human Takeover vs AI Automation
  const handleToggleTakeover = (id) => {
    const targetConv = conversations.find(c => c.id === id);
    if (!targetConv) return;

    const nextAiPaused = !targetConv.aiPaused;
    
    setConversations(prev => prev.map(c => {
      if (c.id === id) {
        return { 
          ...c, 
          aiPaused: nextAiPaused,
          status: nextAiPaused ? 'human_takeover' : 'active'
        };
      }
      return c;
    }));

    setInputMode(nextAiPaused ? 'agent' : 'customer');
    toggleTakeover(id).catch(err => console.error('Takeover API error:', err));
  };

  // Send Message Handler
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!replyText.trim() || isSending) return;

    const text = replyText.trim();
    setReplyText('');

    if (inputMode === 'customer') {
      // ----------------------------------------------------
      // Role: CUSTOMER (Simulate incoming message & run AI)
      // ----------------------------------------------------
      // 1. Optimistic append user message
      const userMsg = { sender: 'user', text, time: 'Just now' };
      setConversations(prev => prev.map(c => {
        if (c.id === selectedId) {
          return {
            ...c,
            lastMessage: text,
            time: 'Just now',
            messages: [...c.messages, userMsg]
          };
        }
        return c;
      }));

      setIsSending(true);
      try {
        const res = await sendCustomerMessage(selectedId, text, selectedConv.channel);
        if (res.ai_reply) {
          setConversations(prev => prev.map(c => {
            if (c.id === selectedId) {
              const hasAiMsg = c.messages.some(
                m => (m.text || '').trim() === (res.ai_reply.text || '').trim() && m.sender === 'ai'
              );
              return {
                ...c,
                confidence: res.conversation?.confidence || c.confidence,
                intent: res.conversation?.intent || c.intent,
                messages: hasAiMsg ? c.messages : [...c.messages, res.ai_reply]
              };
            }
            return c;
          }));
        }
      } catch (err) {
        console.error('Send customer message failed:', err);
      } finally {
        setIsSending(false);
      }

    } else {
      // ----------------------------------------------------
      // Role: HUMAN SALES AGENT (Manual Takeover Reply)
      // ----------------------------------------------------
      const agentMsg = { sender: 'human_agent', text, time: 'Just now' };
      setConversations(prev => prev.map(c => {
        if (c.id === selectedId) {
          return {
            ...c,
            lastMessage: text,
            time: 'Just now',
            messages: [...c.messages, agentMsg]
          };
        }
        return c;
      }));

      sendAgentReply(selectedId, text).catch(err => console.error('Reply API error:', err));
    }
  };

  // Quick Action Buttons
  const handleQuickAction = (type) => {
    if (type === 'brochure') {
      const msg = "📄 Here is our official GLG Assets Property Catalog & Brochure: https://glgassets.bd/brochure.pdf";
      setReplyText(msg);
    } else if (type === 'visit') {
      const msg = "📅 You can confirm your VIP site visit booking online here: https://glgassets.bd/book-visit";
      setReplyText(msg);
    }
  };

  // Create New Simulation Lead
  const handleCreateLead = async (e) => {
    e.preventDefault();
    if (!newLeadForm.name.trim()) return;

    try {
      const payload = {
        name: newLeadForm.name.trim(),
        phone: newLeadForm.phone.trim() || '+880 1711-998877',
        channel: newLeadForm.channel,
        message: newLeadForm.message.trim() || 'Hi! Looking for 3 BHK apartments.'
      };
      const res = await createConversation(payload);
      if (res.conversation) {
        setConversations(prev => [res.conversation, ...prev]);
        setSelectedId(res.conversation.id);
      }
      setShowNewLeadModal(false);
      setNewLeadForm({ name: '', phone: '', channel: 'whatsapp', message: '' });
    } catch (err) {
      console.error('Failed to create lead:', err);
    }
  };

  // Delete Conversation
  const handleDeleteConversation = async (id) => {
    if (!window.confirm('Are you sure you want to delete this live chat record?')) return;
    try {
      await deleteConversation(id);
      setConversations(prev => {
        const updated = prev.filter(c => c.id !== id);
        if (selectedId === id && updated.length > 0) {
          setSelectedId(updated[0].id);
        }
        return updated;
      });
    } catch (err) {
      console.error('Delete conversation error:', err);
    }
  };

  // Search & Filtered Conversations
  const filteredConversations = conversations.filter(c => {
    // Channel filter
    if (channelFilter !== 'all' && c.channel !== channelFilter) return false;
    // Status filter
    if (statusFilter === 'active' && c.aiPaused) return false;
    if (statusFilter === 'takeover' && !c.aiPaused) return false;
    if (statusFilter === 'escalated' && c.status !== 'escalated') return false;
    // Search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchName = c.name?.toLowerCase().includes(query);
      const matchPhone = c.phone?.toLowerCase().includes(query);
      const matchMsg = c.lastMessage?.toLowerCase().includes(query);
      if (!matchName && !matchPhone && !matchMsg) return false;
    }
    return true;
  });

  return (
    <div style={{ height: 'calc(100vh - 70px)', display: 'flex', position: 'relative' }}>
      
      {/* Toast Notification Alert Overlay */}
      {activeToast && (
        <div style={{
          position: 'absolute',
          top: '16px',
          right: '24px',
          zIndex: 1000,
          background: activeToast.type === 'escalation' ? 'rgba(239, 68, 68, 0.95)' : 'rgba(16, 185, 129, 0.95)',
          color: '#FFFFFF',
          padding: '12px 18px',
          borderRadius: '12px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          backdropFilter: 'blur(8px)',
          maxWidth: '420px'
        }}>
          <Bell size={20} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 800, fontSize: '0.85rem' }}>{activeToast.title}</div>
            <div style={{ fontSize: '0.78rem', opacity: 0.9, marginTop: '2px' }}>{activeToast.message}</div>
          </div>
          <button onClick={() => setActiveToast(null)} style={{ background: 'none', border: 'none', color: '#FFF', cursor: 'pointer' }}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Sidebar: Conversation List */}
      <div style={{
        width: '360px',
        borderRight: '1px solid var(--border-glass)',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-card)'
      }}>
        {/* Search, Actions & Status */}
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <MessageSquare size={18} color="var(--primary)" /> Live Inquiries
            </h2>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={() => setShowNewLeadModal(true)}
                title="Simulate New Incoming Lead"
                style={{
                  background: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
                  border: 'none',
                  color: '#FFF',
                  padding: '5px 10px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Plus size={14} /> New Lead
              </button>
            </div>
          </div>

          {/* SSE Live Connection Badge */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem', background: 'rgba(0,0,0,0.2)', padding: '6px 10px', borderRadius: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Radio size={12} color={sseConnected ? '#10B981' : '#F59E0B'} />
              <span style={{ color: sseConnected ? '#34D399' : '#FBBF24', fontWeight: 600 }}>
                {sseConnected ? 'SSE Stream Live' : 'Connecting SSE...'}
              </span>
            </div>
            <button 
              onClick={loadConversations}
              title="Refresh list"
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <RefreshCw size={12} />
            </button>
          </div>

          {/* Search Input */}
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--text-dim)' }} />
            <input 
              type="text" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search buyer name, phone, text..." 
              style={{
                width: '100%',
                padding: '8px 12px 8px 34px',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-glass)',
                borderRadius: '8px',
                color: 'var(--text-light)',
                fontSize: '0.82rem',
                outline: 'none'
              }}
            />
            {searchQuery && (
              <X 
                size={14} 
                onClick={() => setSearchQuery('')}
                style={{ position: 'absolute', right: '10px', top: '10px', color: 'var(--text-dim)', cursor: 'pointer' }} 
              />
            )}
          </div>

          {/* Channel Filters */}
          <div style={{ display: 'flex', gap: '4px', overflowX: 'auto', paddingBottom: '2px' }}>
            {['all', 'whatsapp', 'telegram', 'facebook', 'instagram', 'website'].map(ch => (
              <button
                key={ch}
                onClick={() => setChannelFilter(ch)}
                style={{
                  padding: '3px 7px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.68rem',
                  textTransform: 'capitalize',
                  cursor: 'pointer',
                  background: channelFilter === ch ? 'var(--primary)' : 'rgba(255, 255, 255, 0.05)',
                  color: channelFilter === ch ? '#FFF' : 'var(--text-muted)',
                  whiteSpace: 'nowrap'
                }}
              >
                {ch}
              </button>
            ))}
          </div>

          {/* Status Filters */}
          <div style={{ display: 'flex', gap: '4px' }}>
            {[
              { id: 'all', label: 'All Status' },
              { id: 'active', label: '🤖 AI Live' },
              { id: 'takeover', label: '👨‍💼 Takeover' },
              { id: 'escalated', label: '⚠️ Escalated' }
            ].map(st => (
              <button
                key={st.id}
                onClick={() => setStatusFilter(st.id)}
                style={{
                  flex: 1,
                  padding: '3px 4px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.65rem',
                  cursor: 'pointer',
                  background: statusFilter === st.id ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.2)',
                  color: statusFilter === st.id ? '#FFF' : 'var(--text-muted)'
                }}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>

        {/* List of Conversations */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {filteredConversations.length === 0 ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              No matching live conversations found.
            </div>
          ) : (
            filteredConversations.map(conv => {
              const isSelected = conv.id === selectedId;
              return (
                <div
                  key={conv.id}
                  onClick={() => setSelectedId(conv.id)}
                  style={{
                    padding: '14px 16px',
                    borderBottom: '1px solid var(--border-glass)',
                    background: isSelected ? 'rgba(139, 92, 246, 0.14)' : 'transparent',
                    borderLeft: isSelected ? '3px solid var(--primary)' : '3px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>{conv.name}</span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>{conv.time}</span>
                  </div>

                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '8px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {conv.lastMessage}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className={`badge badge-${conv.channel === 'whatsapp' ? 'emerald' : conv.channel === 'telegram' ? 'cyan' : conv.channel === 'facebook' ? 'blue' : 'violet'}`} style={{ fontSize: '0.62rem' }}>
                      {conv.channel}
                    </span>

                    {conv.aiPaused ? (
                      <span className="badge badge-amber" style={{ fontSize: '0.62rem', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <UserCheck size={10} /> Human Takeover
                      </span>
                    ) : conv.status === 'escalated' ? (
                      <span className="badge badge-rose" style={{ fontSize: '0.62rem', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <ShieldAlert size={10} /> Escalated
                      </span>
                    ) : (
                      <span className="badge badge-cyan" style={{ fontSize: '0.62rem', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <Bot size={10} /> AI Agent ({Math.round((conv.confidence || 0.9) * 100)}%)
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Content: Chat Window & Controls */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-dark)' }}>
        
        {/* Chat Window Header */}
        <div style={{
          padding: '14px 24px',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'var(--bg-card)'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>{selectedConv.name}</h3>
              <span className={`badge badge-${selectedConv.channel === 'whatsapp' ? 'emerald' : selectedConv.channel === 'telegram' ? 'cyan' : selectedConv.channel === 'facebook' ? 'blue' : 'violet'}`} style={{ fontSize: '0.65rem' }}>
                {selectedConv.channel}
              </span>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {selectedConv.phone} • Intent: <strong style={{ color: 'var(--primary-light)' }}>{selectedConv.intent || 'property_inquiry'}</strong>
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {/* AI Summary Button */}
            <button
              onClick={() => setShowAiSummaryModal(true)}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border-glass)',
                color: 'var(--text-light)',
                padding: '7px 12px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Sparkles size={14} color="#F59E0B" /> AI Lead Summary
            </button>

            {/* Toggle Takeover Button */}
            <button
              onClick={() => handleToggleTakeover(selectedConv.id)}
              className={selectedConv.aiPaused ? 'btn-gradient' : 'badge badge-amber'}
              style={{
                padding: '7px 14px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              {selectedConv.aiPaused ? (
                <> <Bot size={15} /> Resume AI Automation </>
              ) : (
                <> <UserCheck size={15} /> Human Takeover </>
              )}
            </button>

            {/* Delete Chat */}
            <button
              onClick={() => handleDeleteConversation(selectedConv.id)}
              title="Delete conversation"
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#EF4444',
                padding: '7px 10px',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              <Trash2 size={15} />
            </button>
          </div>
        </div>

        {/* Quick Sales Action Shortcuts Bar */}
        <div style={{
          padding: '8px 24px',
          background: 'rgba(0, 0, 0, 0.25)',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          gap: '10px',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600 }}>Quick Actions:</span>
          <button
            onClick={() => handleQuickAction('brochure')}
            style={{
              background: 'rgba(139, 92, 246, 0.15)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              color: 'var(--text-light)',
              padding: '4px 10px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.72rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <FileText size={12} color="#A78BFA" /> Insert Brochure Link
          </button>
          <button
            onClick={() => handleQuickAction('visit')}
            style={{
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: 'var(--text-light)',
              padding: '4px 10px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.72rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Calendar size={12} color="#34D399" /> Insert Booking Link
          </button>
        </div>

        {/* Messages Stream Area */}
        <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {selectedConv.messages?.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            const isHumanAgent = msg.sender === 'human_agent';
            return (
              <div 
                key={idx}
                style={{
                  alignSelf: isUser ? 'flex-start' : 'flex-end',
                  maxWidth: '68%',
                  background: isUser 
                    ? 'rgba(255, 255, 255, 0.08)' 
                    : isHumanAgent 
                      ? 'linear-gradient(135deg, #F59E0B, #D97706)' 
                      : 'linear-gradient(135deg, #8B5CF6, #6366F1)',
                  padding: '12px 16px',
                  borderRadius: isUser ? '16px 16px 16px 4px' : '16px 16px 4px 16px',
                  color: '#FFFFFF',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                }}
              >
                <div style={{ fontSize: '0.68rem', opacity: 0.8, marginBottom: '4px', display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
                  <span style={{ fontWeight: 700 }}>
                    {isUser ? selectedConv.name : isHumanAgent ? '👨‍💼 You (Sales Agent)' : '🤖 GLG AI Assistant'}
                  </span>
                  <span>{msg.time}</span>
                </div>
                <div style={{ fontSize: '0.88rem', lineHeight: '1.45', whiteSpace: 'pre-wrap' }}>
                  {msg.text}
                </div>
              </div>
            );
          })}

          {/* Typing indicator when AI is generating response */}
          {isSending && (
            <div style={{
              alignSelf: 'flex-end',
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              padding: '10px 16px',
              borderRadius: '16px 16px 4px 16px',
              color: '#A78BFA',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <RefreshCw size={14} className="spin" /> GLG AI Agent is thinking & generating reply...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar with Role Switcher */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border-glass)',
          background: 'var(--bg-card)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          {/* Mode Switcher Banner */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600 }}>Message Mode:</span>
              <button
                type="button"
                onClick={() => setInputMode('customer')}
                style={{
                  padding: '3px 8px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: inputMode === 'customer' ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                  color: inputMode === 'customer' ? '#FFF' : 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <User size={12} /> Test Customer Message (Triggers AI)
              </button>
              <button
                type="button"
                onClick={() => {
                  if (!selectedConv.aiPaused) handleToggleTakeover(selectedConv.id);
                  setInputMode('agent');
                }}
                style={{
                  padding: '3px 8px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: inputMode === 'agent' ? '#F59E0B' : 'rgba(255,255,255,0.05)',
                  color: inputMode === 'agent' ? '#FFF' : 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <UserCheck size={12} /> Human Agent Reply
              </button>
            </div>

            <span style={{ fontSize: '0.7rem', color: inputMode === 'agent' ? '#F59E0B' : '#34D399' }}>
              {inputMode === 'customer' 
                ? '⚡ Sends message as customer & triggers AI graph pipeline' 
                : '👨‍💼 Manual Human Sales Agent Takeover active'}
            </span>
          </div>

          <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder={
                inputMode === 'customer'
                  ? "Type customer inquiry to test live AI response..."
                  : "Type manual message as Human Sales Agent..."
              }
              disabled={isSending}
              style={{
                flex: 1,
                padding: '12px 16px',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border-glass)',
                borderRadius: '10px',
                color: 'var(--text-light)',
                fontSize: '0.88rem',
                outline: 'none'
              }}
            />
            <button 
              type="submit" 
              disabled={!replyText.trim() || isSending}
              className="btn-gradient"
              style={{
                opacity: (!replyText.trim() || isSending) ? 0.5 : 1,
                cursor: (!replyText.trim() || isSending) ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Send size={16} /> {inputMode === 'customer' ? 'Send & Test AI' : 'Send Agent Reply'}
            </button>
          </form>
        </div>

      </div>

      {/* Modal: Simulate New Lead */}
      {showNewLeadModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(6px)',
          zIndex: 2000,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-glass)',
            borderRadius: '16px',
            width: '450px',
            padding: '24px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>Simulate Incoming Customer Lead</h3>
              <button onClick={() => setShowNewLeadModal(false)} style={{ background: 'none', border: 'none', color: '#FFF', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateLead} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Customer Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rafiq Islam"
                  value={newLeadForm.name}
                  onChange={e => setNewLeadForm({ ...newLeadForm, name: e.target.value })}
                  style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-glass)', borderRadius: '8px', color: '#FFF', fontSize: '0.85rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Phone Number</label>
                <input
                  type="text"
                  placeholder="+880 1711-000000"
                  value={newLeadForm.phone}
                  onChange={e => setNewLeadForm({ ...newLeadForm, phone: e.target.value })}
                  style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-glass)', borderRadius: '8px', color: '#FFF', fontSize: '0.85rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Lead Source Channel</label>
                <select
                  value={newLeadForm.channel}
                  onChange={e => setNewLeadForm({ ...newLeadForm, channel: e.target.value })}
                  style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-glass)', borderRadius: '8px', color: '#FFF', fontSize: '0.85rem' }}
                >
                  <option value="whatsapp">WhatsApp Business</option>
                  <option value="telegram">Telegram Bot / Channel</option>
                  <option value="facebook">Facebook Messenger</option>
                  <option value="instagram">Instagram Direct</option>
                  <option value="website">Website Live Widget</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Initial Customer Message</label>
                <textarea
                  rows={3}
                  placeholder="e.g. I need a 3 BHK luxury flat in Dhanmondi."
                  value={newLeadForm.message}
                  onChange={e => setNewLeadForm({ ...newLeadForm, message: e.target.value })}
                  style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-glass)', borderRadius: '8px', color: '#FFF', fontSize: '0.85rem' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowNewLeadModal(false)}
                  style={{ padding: '8px 16px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', color: '#FFF', cursor: 'pointer', fontSize: '0.85rem' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-gradient"
                  style={{ padding: '8px 18px', cursor: 'pointer', fontSize: '0.85rem' }}
                >
                  Create & Simulate Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: AI Lead Requirement Summary */}
      {showAiSummaryModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(6px)',
          zIndex: 2000,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-glass)',
            borderRadius: '16px',
            width: '500px',
            padding: '24px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="#F59E0B" /> AI Lead Requirement Intelligence
              </h3>
              <button onClick={() => setShowAiSummaryModal(false)} style={{ background: 'none', border: 'none', color: '#FFF', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '10px' }}>
                <strong style={{ color: 'var(--text-muted)' }}>Buyer Name:</strong> {selectedConv.name}
              </div>
              <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '10px' }}>
                <strong style={{ color: 'var(--text-muted)' }}>Detected Intent:</strong> <span className="badge badge-cyan">{selectedConv.intent || 'property_search'}</span>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '10px' }}>
                <strong style={{ color: 'var(--text-muted)' }}>AI Confidence Score:</strong> {Math.round((selectedConv.confidence || 0.9) * 100)}%
              </div>
              <div style={{ background: 'rgba(139, 92, 246, 0.15)', border: '1px solid rgba(139, 92, 246, 0.3)', padding: '14px', borderRadius: '10px' }}>
                <strong style={{ color: '#A78BFA', display: 'block', marginBottom: '6px' }}>Requirements Summary:</strong>
                {selectedConv.lastMessage ? `Customer expressed: "${selectedConv.lastMessage}". System recommends offering GLG Gulshan Heights or Banani Crest units with customized 3-year installment plans.` : 'No key requirements recorded yet.'}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button
                onClick={() => setShowAiSummaryModal(false)}
                className="btn-gradient"
                style={{ padding: '8px 20px', cursor: 'pointer', fontSize: '0.85rem' }}
              >
                Close Summary
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
