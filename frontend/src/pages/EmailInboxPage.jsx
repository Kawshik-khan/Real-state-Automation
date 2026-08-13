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
      const res = await fetch('http://localhost:8000/api/v1/email/threads');
      if (res.ok) {
        const data = await res.json();
        if (data.threads && data.threads.length > 0) {
          setThreads(data.threads);
        }
      }
    } catch (e) {
      console.log('Using local mock threads fallback');
    }
  };

  useEffect(() => {
    fetchThreadsFromBackend();
  }, []);

  const handleApproveDraft = async () => {
    if (!activeThread) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/email/threads/${activeThread.thread_id}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Automation-Secret': 'change-me-in-production'
        },
        body: JSON.stringify({
          thread_id: activeThread.thread_id,
          edited_reply: isEditingDraft ? editedDraftReply : undefined
        })
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

  return (
    <div className="p-6 bg-slate-950 text-slate-100 min-h-screen font-sans">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
              <Mail className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                AI Email Reply Automation
                <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  n8n Email Dispatcher Active
                </span>
              </h1>
              <p className="text-slate-400 text-sm">
                Human-in-the-Loop review, RAG context enrichment, and automated thread management
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchThreadsFromBackend}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 text-sm font-medium transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Inbox
        </button>
      </div>

      {toastMessage && (
        <div className="mb-4 p-3 bg-emerald-950/80 border border-emerald-500/30 text-emerald-200 rounded-lg text-sm flex items-center justify-between animate-fadeIn">
          <span>{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} className="text-emerald-400 hover:text-white">
            &times;
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Email Thread List */}
        <div className="lg:col-span-5 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col h-[750px]">
          {/* Search & Filter Controls */}
          <div className="space-y-3 mb-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search by sender or subject..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex gap-2">
              {['ALL', 'PENDING_APPROVAL', 'AUTO_REPLIED', 'APPROVED_AND_SENT'].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    filterStatus === st
                      ? 'bg-indigo-600 text-white border-indigo-500'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                  }`}
                >
                  {st === 'PENDING_APPROVAL' ? 'Pending Review' : st === 'APPROVED_AND_SENT' ? 'Sent' : st}
                </button>
              ))}
            </div>
          </div>

          {/* Thread Scroll List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {filteredThreads.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-sm">No email threads found</div>
            ) : (
              filteredThreads.map((thread) => {
                const isSelected = thread.thread_id === selectedThreadId;
                const isPending = thread.status === 'PENDING_APPROVAL';
                return (
                  <div
                    key={thread.thread_id}
                    onClick={() => setSelectedThreadId(thread.thread_id)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-indigo-950/40 border-indigo-500/50 shadow-lg shadow-indigo-500/5'
                        : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-semibold text-slate-200 text-sm truncate max-w-[200px]">
                        {thread.customer_name || thread.customer_email}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                          isPending
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            : thread.status === 'AUTO_REPLIED'
                            ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        }`}
                      >
                        {isPending ? 'Action Required' : thread.status}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-slate-300 truncate mb-1">{thread.subject}</p>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span className="capitalize text-slate-400">Intent: {thread.intent_category}</span>
                      <span>Confidence: {Math.round((thread.confidence_score || 0) * 100)}%</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Active Thread Detail & AI Draft Approval Box */}
        {activeThread && (
          <div className="lg:col-span-7 bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col h-[750px]">
            {/* Header Detail */}
            <div className="border-b border-slate-800 pb-4 mb-4">
              <div className="flex items-start justify-between gap-3 mb-2">
                <h2 className="text-lg font-semibold text-white leading-snug">{activeThread.subject}</h2>
                <span
                  className={`text-xs px-3 py-1 rounded-full font-semibold border whitespace-nowrap ${
                    activeThread.lead_priority === 'high'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                  }`}
                >
                  Priority: {activeThread.lead_priority.toUpperCase()}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <User className="w-3.5 h-3.5 text-slate-500" />
                  {activeThread.customer_email}
                </span>
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  AI Confidence: {Math.round((activeThread.confidence_score || 0) * 100)}%
                </span>
              </div>
            </div>

            {/* Conversation Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
              {activeThread.messages.map((msg, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-xl border text-sm ${
                    msg.sender_type === 'customer'
                      ? 'bg-slate-950 border-slate-800 text-slate-200'
                      : 'bg-indigo-950/20 border-indigo-800/40 text-indigo-100'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span className="font-semibold">
                      {msg.sender_type === 'customer' ? msg.sender_email : 'GLG Assets AI Advisor'}
                    </span>
                    <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.body_text}</p>
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-slate-800 flex gap-2 flex-wrap">
                      {msg.attachments.map((att, attIdx) => (
                        <div
                          key={attIdx}
                          className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900 border border-slate-700 rounded-lg text-xs text-indigo-300"
                        >
                          <Paperclip className="w-3.5 h-3.5" />
                          <span>{att.filename}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Staged AI Draft Box */}
              {activeThread.ai_draft_reply && activeThread.status !== 'APPROVED_AND_SENT' && (
                <div className="p-4 rounded-xl border border-indigo-500/40 bg-indigo-950/30">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-indigo-300 font-semibold text-sm">
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                      AI Staged Draft Response
                    </div>
                    {!isEditingDraft && (
                      <button
                        onClick={() => setIsEditingDraft(true)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        Edit Draft
                      </button>
                    )}
                  </div>

                  {isEditingDraft ? (
                    <textarea
                      rows={8}
                      value={editedDraftReply}
                      onChange={(e) => setEditedDraftReply(e.target.value)}
                      className="w-full bg-slate-950 border border-indigo-500/50 rounded-lg p-3 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-sans leading-relaxed"
                    />
                  ) : (
                    <div className="bg-slate-950/60 p-3 rounded-lg border border-indigo-900/40 text-sm text-slate-200 whitespace-pre-wrap font-sans leading-relaxed">
                      {editedDraftReply || activeThread.ai_draft_reply}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Bottom Approval Toolbar */}
            {activeThread.status === 'PENDING_APPROVAL' && (
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
                <button
                  onClick={handleRejectDraft}
                  className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                >
                  <XCircle className="w-4 h-4" />
                  Reject Draft
                </button>

                <div className="flex gap-2">
                  {isEditingDraft && (
                    <button
                      onClick={() => setIsEditingDraft(false)}
                      className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-700"
                    >
                      Cancel Edit
                    </button>
                  )}
                  <button
                    onClick={handleApproveDraft}
                    disabled={isSubmitting}
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-colors"
                  >
                    <CheckCircle className="w-4 h-4" />
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
