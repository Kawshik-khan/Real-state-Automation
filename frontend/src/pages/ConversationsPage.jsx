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
import { useParams, useNavigate } from 'react-router-dom';
import { 
  getConversations, 
  getConversationMessages,
  toggleTakeover, 
  sendAgentReply, 
  sendCustomerMessage, 
  createConversation, 
  deleteConversation, 
  getConversationsStreamUrl,
  getWebSocketUrl 
} from '../services/api';
import Pagination from '../components/ui/Pagination';


export default function ConversationsPage() {
  const { convId } = useParams();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(convId || null);
  const [isLoadingConvs, setIsLoadingConvs] = useState(true);
  const [convsError, setConvsError] = useState(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [replyText, setReplyText] = useState('');

  // Sync route param convId if present
  useEffect(() => {
    if (convId && convId !== selectedId) {
      setSelectedId(convId);
    }
  }, [convId]);

  const handleSelectConversation = (id) => {
    setSelectedId(id);
    navigate(`/conversations/${id}`, { replace: true });
  };
  
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
  const loadConversations = async () => {
    setIsLoadingConvs(true);
    setConvsError(null);
    try {
      const res = await getConversations();
      if (res && Array.isArray(res.conversations)) {
        setConversations(prev => {
          // Retain loaded message histories across refreshes
          const messagesMap = new Map();
          prev.forEach(c => {
            if (c.messages && c.messages.length > 0) {
              messagesMap.set(c.id, c.messages);
            }
          });
          return res.conversations.map(c => ({
            ...c,
            messages: messagesMap.get(c.id) || c.messages || []
          }));
        });
        if (res.conversations.length > 0 && !selectedId) {
          setSelectedId(res.conversations[0].id);
        }
      } else {
        setConversations([]);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setConvsError('Failed to load live conversations. Check backend connectivity.');
    } finally {
      setIsLoadingConvs(false);
    }
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
                    time: data.message?.time || 'Just now',
                    messages: [...(c.messages || []), data.message]
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
                  time: data.message?.time || 'Just now',
                  status: data.requires_escalation ? 'escalated' : 'active',
                  aiPaused: data.requires_escalation || false,
                  confidence: 0.90,
                  intent: 'inquiry',
                  beliefs: {},
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
              const incomingId = data.message?.id;

              const currentMessages = c.messages || [];
              const lastMsg = currentMessages.length > 0 ? currentMessages[currentMessages.length - 1] : null;

              // Check if incoming message is duplicate of the most recent message (e.g. optimistic user/agent send)
              const isDuplicateOfLast = lastMsg && 
                (lastMsg.text || '').trim() === textToMatch && 
                lastMsg.sender === senderToMatch;

              // Check if message ID matches any existing message
              const isSameId = incomingId && currentMessages.some(m => m.id && m.id === incomingId);

              if (isDuplicateOfLast) {
                // Update the last optimistic message with the server-confirmed timestamp and id
                return {
                  ...c,
                  lastMessage: textToMatch || c.lastMessage,
                  time: data.message?.time || c.time,
                  messages: currentMessages.map((m, idx) => 
                    idx === currentMessages.length - 1 ? { ...m, ...data.message } : m
                  )
                };
              }

              if (isSameId) {
                return {
                  ...c,
                  lastMessage: textToMatch || c.lastMessage,
                  time: data.message?.time || c.time,
                };
              }

              return {
                ...c,
                lastMessage: textToMatch || c.lastMessage,
                time: data.message?.time || 'Just now',
                messages: [...currentMessages, data.message]
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

  const selectedConv = conversations.find(c => c.id === selectedId) || conversations[0] || null;

  // Lazy-load full message history (up to 60 messages) when a conversation is selected
  useEffect(() => {
    if (!selectedConv?.id) return;

    let isMounted = true;
    setLoadingMessages(true);

    getConversationMessages(selectedConv.id, 60)
      .then(res => {
        if (!isMounted) return;
        if (res && res.success && Array.isArray(res.messages)) {
          setConversations(prev => prev.map(c => {
            if (c.id === selectedConv.id) {
              return {
                ...c,
                messages: res.messages
              };
            }
            return c;
          }));
        }
      })
      .catch(err => {
        console.error('Failed to fetch messages for conversation:', err);
      })
      .finally(() => {
        if (isMounted) setLoadingMessages(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedConv?.id]);

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
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (inputMode === 'customer') {
      // 1. Optimistic append user message
      const userMsg = { sender: 'user', text, time: nowTime, createdAt: new Date().toISOString() };
      setConversations(prev => prev.map(c => {
        if (c.id === selectedId) {
          return {
            ...c,
            lastMessage: text,
            time: nowTime,
            messages: [...(c.messages || []), userMsg]
          };
        }
        return c;
      }));

      setIsSending(true);
      try {
        const res = await sendCustomerMessage(selectedId, text, selectedConv?.channel || 'website');
        if (res && res.ai_reply) {
          setConversations(prev => prev.map(c => {
            if (c.id === selectedId) {
              const currentMessages = c.messages || [];
              const lastMsg = currentMessages.length > 0 ? currentMessages[currentMessages.length - 1] : null;
              const hasAiMsg = lastMsg && lastMsg.sender === 'ai' && (lastMsg.text || '').trim() === (res.ai_reply.text || '').trim();
              return {
                ...c,
                confidence: res.conversation?.confidence || c.confidence,
                intent: res.conversation?.intent || c.intent,
                beliefs: res.conversation?.beliefs || c.beliefs,
                messages: hasAiMsg ? currentMessages : [...currentMessages, res.ai_reply]
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
      // Role: HUMAN SALES AGENT
      const agentMsg = { sender: 'human_agent', text, time: nowTime, createdAt: new Date().toISOString() };
      setConversations(prev => prev.map(c => {
        if (c.id === selectedId) {
          return {
            ...c,
            lastMessage: text,
            time: nowTime,
            messages: [...(c.messages || []), agentMsg]
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
      const activeProjectName = selectedConv?.projectName || 'GLG Gulshan Heights';
      const msg = `📄 Here is our official GLG Assets Property Catalog & Brochure for ${activeProjectName}: https://fdjzbtkypedzlkwpzzzt.supabase.co/storage/v1/object/public/brochures/gulshan_heights_brochure.pdf`;
      setReplyText(msg);
    } else if (type === 'visit') {
      const msg = `📅 You can confirm your VIP site visit booking online here: ${window.location.origin}/#book-visit or reply with your preferred date and time to schedule directly.`;
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
        if (selectedId === id) {
          setSelectedId(updated.length > 0 ? updated[0].id : null);
        }
        return updated;
      });
    } catch (err) {
      console.error('Delete conversation error:', err);
    }
  };

  // Search & Filtered Conversations
  const filteredConversations = conversations.filter(c => {
    if (channelFilter !== 'all' && c.channel !== channelFilter) return false;
    if (statusFilter === 'active' && c.aiPaused) return false;
    if (statusFilter === 'takeover' && !c.aiPaused) return false;
    if (statusFilter === 'escalated' && c.status !== 'escalated') return false;
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchName = c.name?.toLowerCase().includes(query);
      const matchPhone = c.phone?.toLowerCase().includes(query);
      const matchMsg = c.lastMessage?.toLowerCase().includes(query);
      if (!matchName && !matchPhone && !matchMsg) return false;
    }
    return true;
  });

  const [convPage, setConvPage] = useState(1);
  const convPageSize = 8;

  useEffect(() => {
    setConvPage(1);
  }, [searchQuery, channelFilter, statusFilter]);

  const paginatedConversations = filteredConversations.slice(
    (convPage - 1) * convPageSize,
    convPage * convPageSize
  );

  return (
    <div className="chat-page-container">
      
      {/* Toast Notification Alert Overlay */}
      {activeToast && (
        <div style={{
          position: 'absolute',
          top: '20px',
          right: '28px',
          zIndex: 1000,
          background: activeToast.type === 'escalation' ? '#DC2626' : '#059669',
          color: '#FFFFFF',
          padding: '12px 18px',
          borderRadius: '16px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
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

      {/* Left Floating Card: Inquiries List & Filters */}
      <div className="chat-floating-card" style={{ width: '380px', flexShrink: 0 }}>
        {/* Search, Actions & Status Header */}
        <div style={{ padding: '16px 16px 12px 16px', borderBottom: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)', margin: 0 }}>
              <div style={{
                width: '30px',
                height: '30px',
                borderRadius: '10px',
                background: 'rgba(232, 101, 74, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <MessageSquare size={16} color="var(--primary-coral)" />
              </div>
              <span>Live Inquiries</span>
              <span className="badge badge-coral" style={{ borderRadius: '999px', fontSize: '0.68rem', padding: '1px 8px' }}>
                {filteredConversations.length}
              </span>
            </h2>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={() => setShowNewLeadModal(true)}
                title="Simulate New Incoming Lead"
                className="btn-gradient"
                style={{
                  padding: '5px 12px',
                  fontSize: '0.75rem',
                  borderRadius: '12px',
                  gap: '4px'
                }}
              >
                <Plus size={14} /> New Lead
              </button>
            </div>
          </div>

          {/* SSE Live Connection Badge */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.72rem',
            background: 'var(--bg-main)',
            border: '1px solid var(--border-glass)',
            padding: '6px 12px',
            borderRadius: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Radio size={12} color={sseConnected ? '#10B981' : '#F59E0B'} />
              <span className={sseConnected ? 'text-emerald-themed' : 'text-amber-themed'} style={{ fontWeight: 600 }}>
                {sseConnected ? 'SSE Stream Live' : 'Connecting SSE...'}
              </span>
            </div>
            <button 
              onClick={loadConversations}
              title="Refresh list"
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
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
              className="glass-input"
              style={{
                width: '100%',
                padding: '8px 12px 8px 34px',
                fontSize: '0.82rem',
                borderRadius: '12px',
                background: 'var(--bg-input)'
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

          {/* Channel Filters (Smooth Rounded Pills) */}
          <div style={{ display: 'flex', gap: '5px', overflowX: 'auto', paddingBottom: '2px', scrollbarWidth: 'none' }}>
            {['all', 'email', 'whatsapp', 'telegram', 'facebook', 'instagram', 'website'].map(ch => (
              <button
                key={ch}
                onClick={() => setChannelFilter(ch)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '999px',
                  border: channelFilter === ch ? '1px solid var(--primary-coral)' : '1px solid var(--border-glass)',
                  fontSize: '0.68rem',
                  textTransform: 'capitalize',
                  cursor: 'pointer',
                  background: channelFilter === ch ? 'var(--primary-coral)' : 'var(--bg-main)',
                  color: channelFilter === ch ? '#FFFFFF' : 'var(--text-muted)',
                  whiteSpace: 'nowrap',
                  fontWeight: 600,
                  transition: 'all 0.15s ease'
                }}
              >
                {ch === 'email' ? '✉️ Email' : ch}
              </button>
            ))}
          </div>

          {/* Status Filters (Segmented Pill Buttons) */}
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-main)', padding: '3px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
            {[
              { id: 'all', label: 'All' },
              { id: 'active', label: '🤖 AI Live' },
              { id: 'takeover', label: '👨‍💼 Takeover' },
              { id: 'escalated', label: '⚠️ Escalated' }
            ].map(st => (
              <button
                key={st.id}
                onClick={() => setStatusFilter(st.id)}
                style={{
                  flex: 1,
                  padding: '5px 4px',
                  borderRadius: '9px',
                  border: 'none',
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: statusFilter === st.id ? 'var(--primary-coral)' : 'transparent',
                  color: statusFilter === st.id ? '#FFFFFF' : 'var(--text-muted)',
                  boxShadow: statusFilter === st.id ? '0 2px 6px rgba(232, 101, 74, 0.25)' : 'none',
                  transition: 'all 0.15s ease'
                }}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>

        {/* List of Conversations (Individual Rounded Cards) */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {isLoadingConvs ? (
            <div style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
              <RefreshCw size={22} className="spin-anim" style={{ color: 'var(--primary-coral)' }} />
              <span>Loading conversations...</span>
            </div>
          ) : convsError ? (
            <div style={{ padding: '20px 16px', textAlign: 'center', background: 'rgba(239, 68, 68, 0.08)', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.25)', margin: '8px 0' }}>
              <AlertTriangle size={20} color="#EF4444" style={{ marginBottom: '6px' }} />
              <div style={{ color: '#EF4444', fontWeight: 600, fontSize: '0.82rem', marginBottom: '4px' }}>Sync Notice</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', lineHeight: '1.4' }}>{convsError}</div>
              <button
                onClick={loadConversations}
                style={{
                  marginTop: '10px',
                  padding: '5px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  background: 'var(--primary-coral)',
                  color: '#FFFFFF',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Retry
              </button>
            </div>
          ) : filteredConversations.length === 0 ? (
            <div style={{ padding: '36px 16px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              {conversations.length === 0 ? (
                <div>
                  <p style={{ margin: '0 0 8px 0', fontWeight: 700, color: 'var(--text-main)' }}>No conversations yet</p>
                  <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                    Incoming leads from WhatsApp, Telegram, or Web will appear here in real time.
                  </p>
                  <button
                    onClick={() => setShowNewLeadModal(true)}
                    style={{
                      marginTop: '14px',
                      padding: '6px 14px',
                      borderRadius: '999px',
                      border: 'none',
                      background: 'var(--grad-coral)',
                      color: '#FFFFFF',
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    + Create Test Lead
                  </button>
                </div>
              ) : (
                'No matching live conversations found.'
              )}
            </div>
          ) : (
            paginatedConversations.map(conv => {
              const isSelected = conv.id === selectedId;
              const initials = conv.name
                ? conv.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
                : 'U';
              return (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                  className={`chat-inquiry-card ${isSelected ? 'selected' : ''}`}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                      <div style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        background: isSelected ? 'var(--grad-coral)' : 'rgba(232, 101, 74, 0.15)',
                        color: isSelected ? '#FFFFFF' : 'var(--primary-coral)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.68rem',
                        fontWeight: 800,
                        flexShrink: 0
                      }}>
                        {initials}
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {conv.name}
                      </span>
                    </div>
                    <span style={{
                      fontSize: '0.66rem',
                      color: 'var(--text-dim)',
                      background: 'rgba(255, 255, 255, 0.05)',
                      padding: '2px 7px',
                      borderRadius: '8px',
                      flexShrink: 0
                    }}>
                      {conv.time}
                    </span>
                  </div>

                  <div style={{
                    fontSize: '0.78rem',
                    color: 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    lineHeight: 1.3
                  }}>
                    {conv.lastMessage}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2px' }}>
                    <span className={`badge badge-${conv.channel === 'whatsapp' ? 'emerald' : conv.channel === 'telegram' ? 'cyan' : conv.channel === 'facebook' ? 'blue' : 'violet'}`} style={{ fontSize: '0.62rem', borderRadius: '999px', padding: '2px 8px' }}>
                      {conv.channel}
                    </span>

                    {conv.aiPaused ? (
                      <span className="badge badge-amber" style={{ fontSize: '0.62rem', borderRadius: '999px', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <UserCheck size={10} /> Human Takeover
                      </span>
                    ) : conv.status === 'escalated' ? (
                      <span className="badge badge-rose" style={{ fontSize: '0.62rem', borderRadius: '999px', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <ShieldAlert size={10} /> Escalated
                      </span>
                    ) : (
                      <span className="badge badge-cyan" style={{ fontSize: '0.62rem', borderRadius: '999px', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <Bot size={10} /> AI Agent ({Math.round((conv.confidence || 0.9) * 100)}%)
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {filteredConversations.length > convPageSize && (
          <Pagination
            compact={true}
            currentPage={convPage}
            totalItems={filteredConversations.length}
            pageSize={convPageSize}
            onPageChange={setConvPage}
            itemLabel="chats"
          />
        )}
      </div>

      {/* Right Floating Card: Chat Window & Controls */}
      <div className="chat-floating-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {!selectedConv ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(232, 101, 74, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px', color: 'var(--primary-coral)' }}>
              <MessageSquare size={30} />
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', margin: '0 0 8px 0' }}>
              {conversations.length === 0 ? 'No Conversations Available' : 'Select a Conversation'}
            </h3>
            <p style={{ maxWidth: '380px', fontSize: '0.85rem', lineHeight: '1.5', margin: '0 0 20px 0' }}>
              {conversations.length === 0 
                ? 'Incoming messages from WhatsApp, Telegram, or the Website bot will appear here automatically.' 
                : 'Choose a contact from the left sidebar to view message history, test AI responses, or take over as human agent.'}
            </p>
            <button
              onClick={() => setShowNewLeadModal(true)}
              className="btn-gradient"
              style={{ padding: '10px 20px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
            >
              <Plus size={16} /> Simulate New Lead
            </button>
          </div>
        ) : (
          <>
        {/* Chat Window Header */}
        <div style={{
          padding: '14px 24px',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(255, 255, 255, 0.02)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              background: 'var(--grad-coral)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '0.92rem',
              boxShadow: '0 4px 14px rgba(232, 101, 74, 0.3)'
            }}>
              {selectedConv.name ? selectedConv.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'U'}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontSize: '1.08rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>{selectedConv.name}</h3>
                <span className={`badge badge-${selectedConv.channel === 'whatsapp' ? 'emerald' : selectedConv.channel === 'telegram' ? 'cyan' : selectedConv.channel === 'facebook' ? 'blue' : 'violet'}`} style={{ fontSize: '0.65rem', borderRadius: '999px', padding: '2px 8px' }}>
                  {selectedConv.channel}
                </span>
              </div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                {selectedConv.phone} • Intent: <strong style={{ color: 'var(--primary-coral)' }}>{selectedConv.intent || 'property_inquiry'}</strong>
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {/* AI Summary Button */}
            <button
              onClick={() => setShowAiSummaryModal(true)}
              className="glass-card"
              style={{
                padding: '7px 14px',
                borderRadius: '12px',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                color: 'var(--text-main)',
                border: '1px solid var(--border-glass)'
              }}
            >
              <Sparkles size={14} className="text-amber-themed" /> AI Lead Summary
            </button>

            {/* Toggle Takeover Button */}
            <button
              onClick={() => handleToggleTakeover(selectedConv.id)}
              className={selectedConv.aiPaused ? 'btn-gradient' : 'badge badge-amber'}
              style={{
                padding: '7px 14px',
                borderRadius: '12px',
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
              className="text-rose-themed"
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                padding: '7px 10px',
                borderRadius: '12px',
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
          background: 'var(--bg-main)',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          gap: '10px',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600 }}>Quick Actions:</span>
          <button
            onClick={() => handleQuickAction('brochure')}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glass)',
              color: 'var(--text-main)',
              padding: '4px 12px',
              borderRadius: '999px',
              cursor: 'pointer',
              fontSize: '0.72rem',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
            }}
          >
            <FileText size={12} color="var(--primary-coral)" /> Insert Brochure Link
          </button>
          <button
            onClick={() => handleQuickAction('visit')}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glass)',
              color: 'var(--text-main)',
              padding: '4px 12px',
              borderRadius: '999px',
              cursor: 'pointer',
              fontSize: '0.72rem',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
            }}
          >
            <Calendar size={12} className="text-emerald-themed" /> Insert Booking Link
          </button>
        </div>

        {/* Messages Stream Area */}
        <div style={{ flex: 1, padding: '24px 28px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {loadingMessages ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '220px', gap: '12px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <RefreshCw size={22} className="spin-anim" style={{ color: 'var(--primary-coral)' }} />
              <span>Loading message history...</span>
            </div>
          ) : (!selectedConv.messages || selectedConv.messages.length === 0) ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '220px', gap: '8px', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              <MessageSquare size={24} style={{ opacity: 0.4, color: 'var(--text-muted)' }} />
              <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>No messages in this conversation yet</span>
              <span style={{ fontSize: '0.78rem' }}>Type below to test the AI agent or chat as human agent.</span>
            </div>
          ) : (
            selectedConv.messages.map((msg, idx) => {
              const isUser = msg.sender === 'user';
              const isHumanAgent = msg.sender === 'human_agent';
              return (
                <div 
                  key={idx}
                  style={{
                    alignSelf: isUser ? 'flex-start' : 'flex-end',
                    maxWidth: '68%',
                    background: isUser 
                      ? 'var(--bg-main)' 
                      : isHumanAgent 
                        ? 'linear-gradient(135deg, #F59E0B, #D97706)' 
                        : 'var(--grad-coral)',
                    padding: '12px 18px',
                    borderRadius: isUser ? '18px 18px 18px 6px' : '18px 18px 6px 18px',
                    color: isUser ? 'var(--text-main)' : '#FFFFFF',
                    border: isUser ? '1px solid var(--border-glass)' : 'none',
                    boxShadow: isUser ? '0 2px 8px rgba(0,0,0,0.04)' : '0 4px 16px rgba(232, 101, 74, 0.25)'
                  }}
                >
                  <div style={{ fontSize: '0.68rem', opacity: isUser ? 0.75 : 0.9, marginBottom: '4px', display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
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
            })
          )}

          {/* Typing indicator when AI is generating response */}
          {isSending && (
            <div style={{
              alignSelf: 'flex-end',
              background: 'rgba(232, 101, 74, 0.1)',
              border: '1px solid rgba(232, 101, 74, 0.25)',
              padding: '10px 18px',
              borderRadius: '18px 18px 6px 18px',
              color: 'var(--primary-coral)',
              fontSize: '0.8rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <RefreshCw size={14} className="spin-anim" /> GLG AI Agent is thinking &amp; generating reply...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar with Role Switcher */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border-glass)',
          background: 'rgba(255, 255, 255, 0.02)',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          {/* Mode Switcher Banner */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600 }}>Message Mode:</span>
              <button
                type="button"
                onClick={() => setInputMode('customer')}
                style={{
                  padding: '5px 12px',
                  borderRadius: '999px',
                  border: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: inputMode === 'customer' ? 'var(--primary-coral)' : 'var(--bg-main)',
                  color: inputMode === 'customer' ? '#FFFFFF' : 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  boxShadow: inputMode === 'customer' ? '0 2px 8px rgba(232, 101, 74, 0.3)' : 'none',
                  transition: 'all 0.15s ease'
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
                  padding: '5px 12px',
                  borderRadius: '999px',
                  border: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: inputMode === 'agent' ? '#D97706' : 'var(--bg-main)',
                  color: inputMode === 'agent' ? '#FFFFFF' : 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  boxShadow: inputMode === 'agent' ? '0 2px 8px rgba(217, 119, 6, 0.3)' : 'none',
                  transition: 'all 0.15s ease'
                }}
              >
                <UserCheck size={12} /> Human Agent Reply
              </button>
            </div>

            <span 
              className={inputMode === 'agent' ? 'text-amber-themed' : 'text-emerald-themed'} 
              style={{ fontSize: '0.7rem', fontWeight: 600 }}
            >
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
              className="glass-input"
              style={{
                flex: 1,
                padding: '12px 18px',
                fontSize: '0.88rem',
                borderRadius: '14px',
                background: 'var(--bg-input)'
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
                gap: '6px',
                padding: '12px 20px',
                borderRadius: '14px',
                boxShadow: '0 4px 14px rgba(232, 101, 74, 0.25)'
              }}
            >
              <Send size={16} /> {inputMode === 'customer' ? 'Send & Test AI' : 'Send Agent Reply'}
            </button>
          </form>
        </div>

          </>
        )}
      </div>

      {/* Modal: Simulate New Lead */}
      {showNewLeadModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 2000,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '20px'
        }}>
          <div className="glass-card" style={{
            background: 'var(--bg-card)',
            borderRadius: '24px',
            width: '460px',
            padding: '26px',
            boxShadow: '0 25px 60px rgba(0,0,0,0.2)',
            border: '1px solid var(--border-glass)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>Simulate Incoming Customer Lead</h3>
              <button onClick={() => setShowNewLeadModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateLead} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-main)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Customer Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rafiq Islam"
                  value={newLeadForm.name}
                  onChange={e => setNewLeadForm({ ...newLeadForm, name: e.target.value })}
                  className="glass-input"
                  style={{ width: '100%', background: 'var(--bg-input)', borderRadius: '12px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-main)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Phone Number</label>
                <input
                  type="text"
                  placeholder="+880 1711-000000"
                  value={newLeadForm.phone}
                  onChange={e => setNewLeadForm({ ...newLeadForm, phone: e.target.value })}
                  className="glass-input"
                  style={{ width: '100%', background: 'var(--bg-input)', borderRadius: '12px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-main)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Lead Source Channel</label>
                <select
                  value={newLeadForm.channel}
                  onChange={e => setNewLeadForm({ ...newLeadForm, channel: e.target.value })}
                  className="glass-input"
                  style={{ width: '100%', background: 'var(--bg-input)', borderRadius: '12px' }}
                >
                  <option value="whatsapp">WhatsApp Business</option>
                  <option value="telegram">Telegram Bot / Channel</option>
                  <option value="facebook">Facebook Messenger</option>
                  <option value="instagram">Instagram Direct</option>
                  <option value="website">Website Live Widget</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-main)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Initial Customer Message</label>
                <textarea
                  rows={3}
                  placeholder="e.g. I need a 3 BHK luxury flat in Dhanmondi."
                  value={newLeadForm.message}
                  onChange={e => setNewLeadForm({ ...newLeadForm, message: e.target.value })}
                  className="glass-input"
                  style={{ width: '100%', background: 'var(--bg-input)', borderRadius: '12px' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowNewLeadModal(false)}
                  className="glass-card"
                  style={{ padding: '8px 16px', cursor: 'pointer', fontSize: '0.85rem', borderRadius: '12px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-gradient"
                  style={{ padding: '8px 18px', cursor: 'pointer', fontSize: '0.85rem', borderRadius: '12px' }}
                >
                  Create &amp; Simulate Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: AI Lead Requirement Summary */}
      {showAiSummaryModal && selectedConv && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 2000,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '20px'
        }}>
          <div className="glass-card" style={{
            background: 'var(--bg-card)',
            borderRadius: '24px',
            width: '500px',
            padding: '26px',
            boxShadow: '0 25px 60px rgba(0,0,0,0.2)',
            border: '1px solid var(--border-glass)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)' }}>
                <Sparkles size={18} color="#D97706" /> AI Lead Requirement Intelligence
              </h3>
              <button onClick={() => setShowAiSummaryModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            {(() => {
              const b = selectedConv.beliefs || {};
              const locations = Array.isArray(b.preferred_locations) && b.preferred_locations.length > 0 ? b.preferred_locations.join(', ') : 'Not specified yet';
              const bedrooms = b.bedrooms ? `${b.bedrooms} BHK` : 'Not specified';
              const budget = b.budget_raw || (b.budget_max ? `৳${Number(b.budget_max).toLocaleString()} BDT` : (b.budget_min ? `৳${Number(b.budget_min).toLocaleString()} BDT+` : 'Not specified'));
              const facing = b.facing || 'Any / Flexible';
              const handover = b.handover_status || 'Any';
              const buyerProfile = b.buyer_profile && typeof b.buyer_profile === 'object' ? b.buyer_profile : {};
              const urgency = buyerProfile.urgency || 'Active Inquiry';

              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem' }}>
                  <div style={{ background: 'var(--bg-main)', padding: '12px 14px', borderRadius: '14px', border: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong style={{ color: 'var(--text-muted)' }}>Buyer: </strong>
                      <span style={{ color: 'var(--text-main)', fontWeight: 700 }}>{selectedConv.name}</span>
                      <span style={{ marginLeft: '8px', color: 'var(--text-dim)', fontSize: '0.78rem' }}>({selectedConv.phone})</span>
                    </div>
                    <span className={`badge badge-${selectedConv.channel === 'whatsapp' ? 'emerald' : selectedConv.channel === 'telegram' ? 'cyan' : selectedConv.channel === 'facebook' ? 'blue' : 'violet'}`} style={{ fontSize: '0.65rem', borderRadius: '999px', padding: '2px 8px' }}>
                      {selectedConv.channel}
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div style={{ background: 'var(--bg-main)', padding: '10px 12px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'block' }}>Detected Intent</span>
                      <span className="badge badge-cyan" style={{ borderRadius: '999px', marginTop: '4px', display: 'inline-block' }}>{selectedConv.intent || 'property_inquiry'}</span>
                    </div>
                    <div style={{ background: 'var(--bg-main)', padding: '10px 12px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'block' }}>AI Confidence Score</span>
                      <span className="text-emerald-themed" style={{ fontWeight: 800, fontSize: '1rem', display: 'block', marginTop: '2px' }}>
                        {Math.round((selectedConv.confidence || 0.9) * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* AI Dynamic Memory Reflection Attributes */}
                  <div style={{ background: 'var(--bg-main)', padding: '12px 14px', borderRadius: '14px', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '0.3px', textTransform: 'uppercase' }}>
                      Extracted Constraints &amp; Preferences
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.78rem' }}>
                      <div><strong style={{ color: 'var(--text-dim)' }}>Location:</strong> <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{locations}</span></div>
                      <div><strong style={{ color: 'var(--text-dim)' }}>Bedrooms:</strong> <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{bedrooms}</span></div>
                      <div><strong style={{ color: 'var(--text-dim)' }}>Budget:</strong> <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{budget}</span></div>
                      <div><strong style={{ color: 'var(--text-dim)' }}>Facing:</strong> <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{facing}</span></div>
                      <div><strong style={{ color: 'var(--text-dim)' }}>Handover:</strong> <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{handover}</span></div>
                      <div><strong style={{ color: 'var(--text-dim)' }}>Priority:</strong> <span style={{ color: 'var(--primary-coral)', fontWeight: 600 }}>{urgency}</span></div>
                    </div>
                  </div>

                  <div style={{ background: 'rgba(232, 101, 74, 0.08)', border: '1px solid rgba(232, 101, 74, 0.25)', padding: '14px 16px', borderRadius: '14px' }}>
                    <strong style={{ color: 'var(--primary-coral)', display: 'block', marginBottom: '6px' }}>Latest Requirement Context:</strong>
                    <span style={{ color: 'var(--text-main)', fontSize: '0.82rem', lineHeight: '1.45' }}>
                      {selectedConv.lastMessage ? `"${selectedConv.lastMessage}"` : 'Initial inquiry recorded. Ready for personalized project recommendations.'}
                    </span>
                  </div>
                </div>
              );
            })()}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button
                onClick={() => setShowAiSummaryModal(false)}
                className="btn-gradient"
                style={{ padding: '8px 20px', cursor: 'pointer', fontSize: '0.85rem', borderRadius: '12px' }}
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
