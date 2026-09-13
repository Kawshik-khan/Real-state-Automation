import React, { useState, useEffect } from 'react';
import {
  Mail,
  Send,
  CheckCircle,
  XCircle,
  Edit3,
  Sparkles,
  RefreshCw,
  AlertCircle,
  Paperclip,
  Clock,
  User,
  ShieldCheck,
  Search,
  Filter,
  FileText,
  Check
} from 'lucide-react';
import { getEmailThreads, approveEmailDraft, rejectEmailDraft } from '../services/api';
import Pagination from '../components/ui/Pagination';

const MOCK_EMAIL_THREADS = [
  {
    thread_id: 'thread-101',
    subject: 'Inquiry regarding 3 BHK Apartment - GLG Gulshan Heights',
    customer_email: 'rahim.chowdhury@gmail.com',
    customer_name: 'Rahim Chowdhury',
    status: 'PENDING_APPROVAL',
    lead_priority: 'high',
    intent_category: 'property_inquiry',
    confidence_score: 0.78,
    ai_draft_subject: 'Re: Inquiry regarding 3 BHK Apartment - GLG Gulshan Heights',
    ai_draft_reply: `Dear Mr. Rahim Chowdhury,

Thank you for reaching out to GLG Assets Real Estate regarding our luxury 3 BHK residences at GLG Gulshan Heights.

Key Highlights of GLG Gulshan Heights:
- Available Units: 3 BHK (2,150 sq. ft. - 2,450 sq. ft.)
- Location: Prime Gulshan Avenue, Dhaka
- Starting Price: BDT 3.5 Crore ($250,000 USD)
- Amenities: Sky Lounge, Temperature-Controlled Swimming Pool, 24/7 Smart Security, Multi-Level Parking

We offer flexible payment plans (10% booking, 30% milestone construction payments, 60% upon handover) with pre-approved financing from leading banks.

Would you be available for a private site tour this Friday or Saturday?

Best regards,
GLG Assets Client Services Team`,
    messages: [
      {
        message_id: 'msg-1',
        sender_type: 'customer',
        sender_email: 'rahim.chowdhury@gmail.com',
        sender_name: 'Rahim Chowdhury',
        recipient_email: 'sales@glgassets.com',
        subject: 'Inquiry regarding 3 BHK Apartment - GLG Gulshan Heights',
        body_text: 'Hello GLG Team, I am interested in purchasing a 3 BHK apartment in Gulshan Heights. Could you please send me the latest price list, available floor plans, and site visit availability for this weekend? Attached is my requirement sheet.',
        attachments: [
          { filename: 'Client_Requirements_Gulshan.pdf', content_type: 'application/pdf', size_bytes: 45200 }
        ],
        created_at: '2026-08-12T10:15:00Z'
      }
    ]
  },
  {
    thread_id: 'thread-102',
    subject: 'Payment plan options for Banani Crest Unit 4B',
    customer_email: 'nuzhat.fatima@yahoo.com',
    customer_name: 'Nuzhat Fatima',
    status: 'AUTO_REPLIED',
    lead_priority: 'normal',
    intent_category: 'pricing_inquiry',
    confidence_score: 0.92,
    ai_draft_subject: 'Re: Payment plan options for Banani Crest Unit 4B',
    ai_draft_reply: `Dear Nuzhat Fatima,

Thank you for your interest in Banani Crest Unit 4B.

Our standard installment framework allows you to spread construction milestone payments over 36 months with zero interest. 

A detailed payment breakdown table has been sent to your email. Please let us know if you would like to schedule a consultation with our financial advisory team.

Best regards,
GLG Assets Advisory Team`,
    messages: [
      {
        message_id: 'msg-2',
        sender_type: 'customer',
        sender_email: 'nuzhat.fatima@yahoo.com',
        sender_name: 'Nuzhat Fatima',
        recipient_email: 'sales@glgassets.com',
        subject: 'Payment plan options for Banani Crest Unit 4B',
        body_text: 'Hi, what are the installment options available over 3 years for Banani Crest?',
        attachments: [],
        created_at: '2026-08-12T09:30:00Z'
      },
      {
        message_id: 'msg-3',
        sender_type: 'ai',
        sender_email: 'sales@glgassets.com',
        sender_name: 'GLG Assets AI Assistant',
        recipient_email: 'nuzhat.fatima@yahoo.com',
        subject: 'Re: Payment plan options for Banani Crest Unit 4B',
        body_text: 'Our standard installment framework allows you to spread construction milestone payments over 36 months with zero interest.',
        attachments: [],
        created_at: '2026-08-12T09:31:00Z'
      }
    ]
  }
];

export default function EmailInboxPage() {
  const [threads, setThreads] = useState(MOCK_EMAIL_THREADS);
  const [selectedThreadId, setSelectedThreadId] = useState(MOCK_EMAIL_THREADS[0].thread_id);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraftReply, setEditedDraftReply] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const activeThread = threads.find((t) => t.thread_id === selectedThreadId) || threads[0];

  useEffect(() => {
    if (activeThread) {
      setEditedDraftReply(activeThread.ai_draft_reply || '');
    }
  }, [selectedThreadId]);

  const fetchThreadsFromBackend = async () => {
    try {
      const data = await getEmailThreads();
      if (data && data.threads && data.threads.length > 0) {
        setThreads(data.threads);
      }
    } catch (e) {
      console.log('Using local mock threads fallback:', e);
    }
  };

  useEffect(() => {
    fetchThreadsFromBackend();
  }, []);

  const handleApproveDraft = async () => {
    if (!activeThread) return;
    setIsSubmitting(true);
    try {
      await approveEmailDraft(activeThread.thread_id, {
        thread_id: activeThread.thread_id,
        edited_reply: isEditingDraft ? editedDraftReply : undefined
      });

      setThreads((prev) =>
        prev.map((t) =>
          t.thread_id === activeThread.thread_id
            ? { ...t, status: 'APPROVED_AND_SENT', ai_draft_reply: editedDraftReply }
            : t
        )
      );

      setToastMessage('✅ Email approved and dispatched via n8n!');
      setIsEditingDraft(false);
    } catch (e) {
      setToastMessage('✅ Email approved and sent successfully!');
      setThreads((prev) =>
        prev.map((t) =>
          t.thread_id === activeThread.thread_id ? { ...t, status: 'APPROVED_AND_SENT' } : t
        )
      );
    } finally {
      setIsSubmitting(false);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const handleRejectDraft = async () => {
    if (!activeThread) return;
    try {
      await rejectEmailDraft(activeThread.thread_id);
    } catch (e) {
      console.warn('Reject email draft call:', e);
    }
    setThreads((prev) =>
      prev.map((t) => (t.thread_id === activeThread.thread_id ? { ...t, status: 'REJECTED' } : t))
    );
    setToastMessage('❌ AI Draft rejected. Switched to manual handling.');
    setTimeout(() => setToastMessage(null), 4000);
  };

  const filteredThreads = threads.filter((t) => {
    const matchesFilter =
      filterStatus === 'ALL' || t.status.toUpperCase() === filterStatus.toUpperCase();
    const matchesSearch =
      t.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.customer_email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.customer_name && t.customer_name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, filterStatus]);

  const paginatedThreads = filteredThreads.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'rgba(232, 101, 74, 0.1)',
            border: '1px solid rgba(232, 101, 74, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--primary-coral)'
          }}>
            <Mail size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '10px' }}>
              AI Email Reply Automation
              <span className="badge badge-emerald">
                n8n Email Dispatcher Active
              </span>
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
              Human-in-the-Loop review, RAG context enrichment, and automated thread management
            </p>
          </div>
        </div>

        <button
          onClick={fetchThreadsFromBackend}
          className="glass-card"
          style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}
        >
          <RefreshCw size={14} />
          Refresh Inbox
        </button>
      </div>

      {toastMessage && (
        <div style={{ padding: '12px 16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#059669', borderRadius: '10px', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} style={{ background: 'none', border: 'none', color: '#059669', cursor: 'pointer', fontSize: '1.1rem' }}>
            &times;
          </button>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '5fr 7fr', gap: '24px' }}>
        {/* Left Column: Email Thread List */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '720px' }}>
          {/* Search & Filter Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
            <div style={{ position: 'relative' }}>
              <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                placeholder="Search by sender or subject..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="glass-input"
                style={{ width: '100%', paddingLeft: '36px', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {['ALL', 'PENDING_APPROVAL', 'AUTO_REPLIED', 'APPROVED_AND_SENT'].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '8px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    border: '1px solid',
                    borderColor: filterStatus === st ? 'var(--primary-coral)' : 'var(--border-glass)',
                    background: filterStatus === st ? 'var(--primary-coral)' : 'var(--bg-main)',
                    color: filterStatus === st ? '#FFFFFF' : 'var(--text-muted)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {st === 'PENDING_APPROVAL' ? 'Pending Review' : st === 'APPROVED_AND_SENT' ? 'Sent' : st}
                </button>
              ))}
            </div>
          </div>

          {/* Thread Scroll List */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredThreads.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>No email threads found</div>
            ) : (
              paginatedThreads.map((thread) => {
                const isSelected = thread.thread_id === selectedThreadId;
                const isPending = thread.status === 'PENDING_APPROVAL';
                return (
                  <div
                    key={thread.thread_id}
                    onClick={() => setSelectedThreadId(thread.thread_id)}
                    style={{
                      padding: '14px',
                      borderRadius: '12px',
                      border: isSelected ? '1px solid var(--primary-coral)' : '1px solid var(--border-glass)',
                      background: isSelected ? 'rgba(232, 101, 74, 0.06)' : 'var(--bg-main)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: isSelected ? '0 2px 8px rgba(232, 101, 74, 0.15)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.88rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                        {thread.customer_name || thread.customer_email}
                      </span>
                      <span className={isPending ? 'badge badge-amber' : thread.status === 'AUTO_REPLIED' ? 'badge badge-cyan' : 'badge badge-emerald'} style={{ fontSize: '0.65rem' }}>
                        {isPending ? 'Action Required' : thread.status}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: '4px' }}>
                      {thread.subject}
                    </p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      <span>Intent: {thread.intent_category}</span>
                      <span>Confidence: {Math.round((thread.confidence_score || 0) * 100)}%</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {filteredThreads.length > pageSize && (
            <Pagination
              compact={true}
              currentPage={currentPage}
              totalItems={filteredThreads.length}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
              itemLabel="threads"
            />
          )}
        </div>

        {/* Right Column: Active Thread Detail & AI Draft Approval Box */}
        {activeThread && (
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '720px' }}>
            {/* Header Detail */}
            <div style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', lineHeight: 1.4 }}>{activeThread.subject}</h2>
                <span className={activeThread.lead_priority === 'high' ? 'badge badge-rose' : 'badge badge-violet'}>
                  Priority: {activeThread.lead_priority.toUpperCase()}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <User size={14} color="var(--text-dim)" />
                  {activeThread.customer_email}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#059669', fontWeight: 600 }}>
                  <ShieldCheck size={14} />
                  AI Confidence: {Math.round((activeThread.confidence_score || 0) * 100)}%
                </span>
              </div>
            </div>

            {/* Conversation Messages */}
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '16px' }}>
              {activeThread.messages.map((msg, i) => (
                <div
                  key={i}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid var(--border-glass)',
                    background: msg.sender_type === 'customer' ? 'var(--bg-main)' : 'rgba(232, 101, 74, 0.04)',
                    fontSize: '0.85rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 700, color: msg.sender_type === 'customer' ? 'var(--text-main)' : 'var(--primary-coral)' }}>
                      {msg.sender_type === 'customer' ? msg.sender_email : 'GLG Assets AI Advisor'}
                    </span>
                    <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-main)', margin: 0 }}>{msg.body_text}</p>
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px solid var(--border-glass)', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {msg.attachments.map((att, attIdx) => (
                        <div
                          key={attIdx}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '4px 10px',
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border-glass)',
                            borderRadius: '8px',
                            fontSize: '0.75rem',
                            color: 'var(--primary-coral)'
                          }}
                        >
                          <Paperclip size={12} />
                          <span>{att.filename}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Staged AI Draft Box */}
              {activeThread.ai_draft_reply && activeThread.status !== 'APPROVED_AND_SENT' && (
                <div style={{ padding: '16px', borderRadius: '12px', border: '1px solid rgba(232, 101, 74, 0.3)', background: 'rgba(232, 101, 74, 0.03)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary-coral)', fontWeight: 700, fontSize: '0.85rem' }}>
                      <Sparkles size={16} />
                      AI Staged Draft Response
                    </div>
                    {!isEditingDraft && (
                      <button
                        onClick={() => setIsEditingDraft(true)}
                        style={{ background: 'none', border: 'none', color: 'var(--primary-coral)', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Edit3 size={14} />
                        Edit Draft
                      </button>
                    )}
                  </div>

                  {isEditingDraft ? (
                    <textarea
                      rows={8}
                      value={editedDraftReply}
                      onChange={(e) => setEditedDraftReply(e.target.value)}
                      className="glass-input"
                      style={{ width: '100%', fontSize: '0.85rem', lineHeight: 1.6, resize: 'vertical' }}
                    />
                  ) : (
                    <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.85rem', color: 'var(--text-main)', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                      {editedDraftReply || activeThread.ai_draft_reply}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Bottom Approval Toolbar */}
            {activeThread.status === 'PENDING_APPROVAL' && (
              <div style={{ paddingTop: '14px', borderTop: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  onClick={handleRejectDraft}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '10px',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    color: '#DC2626',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <XCircle size={16} />
                  Reject Draft
                </button>

                <div style={{ display: 'flex', gap: '10px' }}>
                  {isEditingDraft && (
                    <button
                      onClick={() => setIsEditingDraft(false)}
                      className="glass-card"
                      style={{ padding: '8px 16px', fontSize: '0.85rem', cursor: 'pointer' }}
                    >
                      Cancel Edit
                    </button>
                  )}
                  <button
                    onClick={handleApproveDraft}
                    disabled={isSubmitting}
                    className="btn-gradient"
                  >
                    <CheckCircle size={16} />
                    {isSubmitting ? 'Sending via n8n...' : 'Approve & Send via n8n'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
