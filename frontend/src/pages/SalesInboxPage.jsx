import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Bot, Hand, Power, RefreshCw, RotateCcw, Send, ThumbsDown, ThumbsUp } from 'lucide-react';
import Button from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { useAuth } from '../context/AuthContext';
import { salesApi, formatWhen, canManage, canWork, stageLabel } from '../services/salesApi';
import '../styles/sales.css';

const CHANNELS = ['whatsapp', 'messenger', 'instagram', 'telegram', 'website', 'email'];
const TRIGGER_LABEL = { new_lead: 'New inquiry', post_visit: 'After a visit', no_show: 'Missed visit', reengage: 'Quiet leads' };

function AssistantSettings() {
  const { showToast } = useToast();
  const [settings, setSettings] = useState(null);
  const [tokens, setTokens] = useState(0);
  const [sequences, setSequences] = useState([]);
  const [editing, setEditing] = useState({});
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const [s, q] = await Promise.all([salesApi.settings(), salesApi.sequences()]);
      setSettings(s.settings);
      setTokens(s.tokens_used_today);
      setSequences(q.sequences);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }, [showToast]);

  useEffect(() => { load(); }, [load]);

  const update = async (fields, message) => {
    try {
      const res = await salesApi.updateSettings(fields);
      setSettings(res.settings);
      showToast(message, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  if (!settings) return null;
  const toggleChannel = (c) => {
    const next = settings.enabled_channels.includes(c) ? settings.enabled_channels.filter((x) => x !== c) : [...settings.enabled_channels, c];
    update({ enabled_channels: next }, 'Channels updated');
  };

  const summary = settings.kill_switch
    ? 'Stopped by emergency stop'
    : `${settings.mode === 'live' ? 'Live — sends replies' : settings.mode === 'shadow' ? 'Shadow — drafts only' : 'Off'} · ${settings.enabled_channels.length} channels · ${tokens.toLocaleString()} tokens today`;

  return (
    <div className="glass-card sales-section">
      <div className="sales-toolbar">
        <h3 style={{ margin: 0 }}><Bot size={16} /> AI assistant <span className="sales-lead-meta" style={{ fontWeight: 500 }}>· {summary}</span></h3>
        <Button size="sm" onClick={() => setOpen(!open)} title={open ? 'Hide assistant settings' : 'Show assistant settings'}>{open ? 'Hide settings' : 'Settings & follow-ups'}</Button>
      </div>
      {open && (<>
      <div className="sales-switch-row" style={{ marginTop: 'var(--space-3)' }}>
        {['off', 'shadow', 'live'].map((m) => (
          <button key={m} type="button" className={`sales-chip ${settings.mode === m ? 'on' : ''}`} onClick={() => update({ mode: m }, `Assistant is ${m}`)}>
            {m === 'shadow' ? 'Shadow (drafts only)' : m === 'live' ? 'Live (sends replies)' : 'Off'}
          </button>
        ))}
        <Button size="sm" variant={settings.kill_switch ? 'emerald' : 'rose'} icon={<Power size={13} />}
          onClick={() => update({ kill_switch: !settings.kill_switch }, settings.kill_switch ? 'Assistant restarted' : 'Assistant stopped everywhere')}>
          {settings.kill_switch ? 'Restart assistant' : 'Emergency stop'}
        </Button>
      </div>
      <div className="sales-switch-row" style={{ marginTop: 'var(--space-3)' }}>
        <span className="sales-kpi-label">Channels</span>
        {CHANNELS.map((c) => (
          <button key={c} type="button" className={`sales-chip ${settings.enabled_channels.includes(c) ? 'on' : ''}`} onClick={() => toggleChannel(c)}>{c}</button>
        ))}
      </div>
      <div className="sales-switch-row" style={{ marginTop: 'var(--space-3)' }}>
        <span className="sales-kpi-label" title="When the assistant is live, a draft-only channel still stores replies for staff to send">Draft only</span>
        {CHANNELS.filter((c) => settings.enabled_channels.includes(c)).map((c) => {
          const draftOnly = settings.channel_modes?.[c] === 'draft_only';
          return (
            <button key={c} type="button" className={`sales-chip ${draftOnly ? 'on' : ''}`}
              onClick={() => update({ channel_modes: { [c]: draftOnly ? 'live' : 'draft_only' } }, draftOnly ? `${c} replies are sent when live` : `${c} replies stay drafts`)}>
              {c}
            </button>
          );
        })}
      </div>
      <div className="sales-form" style={{ marginTop: 'var(--space-3)' }}>
        <label className="sales-field">Daily token budget
          <input type="number" min="0" defaultValue={settings.daily_token_budget} onBlur={(e) => Number(e.target.value) !== settings.daily_token_budget && update({ daily_token_budget: Number(e.target.value) }, 'Budget saved')} />
        </label>
        <label className="sales-field">Unit hold (hours)
          <input type="number" min="1" max="168" defaultValue={settings.hold_hours} onBlur={(e) => Number(e.target.value) !== settings.hold_hours && update({ hold_hours: Number(e.target.value) }, 'Hold time saved')} />
        </label>
        <label className="sales-field">Staff Telegram chat id
          <input type="text" defaultValue={settings.digest_chat_id || ''} onBlur={(e) => (e.target.value || null) !== settings.digest_chat_id && update({ digest_chat_id: e.target.value }, 'Staff chat saved')} />
        </label>
        <div className="sales-lead-meta">Used today: {tokens.toLocaleString()} tokens</div>
      </div>

      <h3 style={{ marginTop: 'var(--space-5)' }}>Follow-up sequences</h3>
      {sequences.length === 0 && (
        <Button size="sm" variant="coral" onClick={async () => { try { await salesApi.installDefaultSequences(); showToast('Default sequences added', 'success'); load(); } catch (err) { showToast(err.message, 'error'); } }}>
          Add the default sequences
        </Button>
      )}
      {sequences.map((seq) => {
        const draft = editing[seq.trigger];
        return (
          <div key={seq.sequence_id} style={{ borderTop: '1px solid var(--border-glass)', paddingTop: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
            <div className="sales-toolbar">
              <strong>{TRIGGER_LABEL[seq.trigger] || seq.trigger} · {seq.name}</strong>
              <div className="sales-toolbar-actions">
                <button type="button" className={`sales-chip ${seq.active ? 'on' : ''}`}
                  onClick={async () => { try { await salesApi.saveSequence(seq.trigger, { name: seq.name, active: !seq.active, steps: seq.steps.map(({ delay_minutes, message_template, whatsapp_template }) => ({ delay_minutes, message_template, whatsapp_template })) }); load(); } catch (err) { showToast(err.message, 'error'); } }}>
                  {seq.active ? 'Active' : 'Paused'}
                </button>
                {!draft && <Button size="sm" onClick={() => setEditing({ ...editing, [seq.trigger]: seq.steps.map((s) => ({ ...s })) })}>Edit</Button>}
              </div>
            </div>
            {(draft || seq.steps).map((step, i) => (
              <div key={step.step_id || i} className="sales-form" style={{ marginTop: 6 }}>
                <label className="sales-field">Wait (hours)
                  <input type="number" min="0" disabled={!draft} value={Math.round((step.delay_minutes / 60) * 10) / 10}
                    onChange={(e) => { const next = [...draft]; next[i] = { ...step, delay_minutes: Math.round(Number(e.target.value) * 60) }; setEditing({ ...editing, [seq.trigger]: next }); }} />
                </label>
                <label className="sales-field" style={{ gridColumn: 'span 3' }}>Message ({'{name}'}, {'{project}'} are filled in)
                  <textarea rows={2} disabled={!draft} value={step.message_template}
                    onChange={(e) => { const next = [...draft]; next[i] = { ...step, message_template: e.target.value }; setEditing({ ...editing, [seq.trigger]: next }); }} />
                </label>
              </div>
            ))}
            {draft && (
              <div className="sales-toolbar-actions" style={{ marginTop: 6 }}>
                <Button size="sm" variant="coral" onClick={async () => {
                  try {
                    await salesApi.saveSequence(seq.trigger, { name: seq.name, active: seq.active, steps: draft.map(({ delay_minutes, message_template, whatsapp_template }) => ({ delay_minutes, message_template, whatsapp_template })) });
                    setEditing({ ...editing, [seq.trigger]: undefined });
                    showToast('Sequence saved', 'success');
                    load();
                  } catch (err) { showToast(err.message, 'error'); }
                }}>Save</Button>
                <Button size="sm" onClick={() => setEditing({ ...editing, [seq.trigger]: undefined })}>Cancel</Button>
              </div>
            )}
          </div>
        );
      })}
      </>)}
    </div>
  );
}

export default function SalesInboxPage() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [filter, setFilter] = useState('');
  const [conversations, setConversations] = useState([]);
  const [active, setActive] = useState(null);
  const [thread, setThread] = useState(null);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);
  const worker = canWork(user?.role);

  const loadList = useCallback(async () => {
    try {
      setConversations((await salesApi.conversations(filter || undefined)).conversations);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }, [filter, showToast]);

  const loadThread = useCallback(async (id) => {
    if (!id) return;
    try {
      setThread(await salesApi.messages(id));
    } catch (err) {
      showToast(err.message, 'error');
    }
  }, [showToast]);

  useEffect(() => { loadList(); }, [loadList]);
  useEffect(() => { loadThread(active); }, [active, loadThread]);
  useEffect(() => {
    const timer = setInterval(() => { loadList(); if (active) loadThread(active); }, 10000);
    return () => clearInterval(timer);
  }, [active, loadList, loadThread]);
  useEffect(() => { endRef.current?.scrollIntoView({ block: 'end' }); }, [thread]);

  const act = async (fn, message) => {
    setBusy(true);
    try {
      await fn();
      if (message) showToast(message, 'success');
      await Promise.all([loadThread(active), loadList()]);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setBusy(false);
    }
  };

  const conv = thread?.conversation;

  return (
    <div className="sales-page">
      <div className="sales-toolbar">
        <div>
          <h2>Sales inbox</h2>
          <p>Customer chats handled by the AI assistant. Reply to take a chat over; hand it back when you're done.</p>
        </div>
        <div className="sales-toolbar-actions">
          {[['', 'All'], ['AI', 'With AI'], ['HUMAN', 'With staff']].map(([v, label]) => (
            <button key={label} type="button" className={`sales-chip ${filter === v ? 'on' : ''}`} onClick={() => setFilter(v)}>{label}</button>
          ))}
          <Button icon={<RefreshCw size={14} />} onClick={loadList}>Refresh</Button>
        </div>
      </div>

      {canManage(user?.role) && <AssistantSettings />}

      <div className="sales-inbox">
        <div className="glass-card sales-chat-list" role="list">
          {conversations.length === 0 && <p className="sales-empty">No conversations yet.</p>}
          {conversations.map((c) => (
            <button key={c.conversation_id} type="button" role="listitem" className={`sales-chat-item ${active === c.conversation_id ? 'active' : ''}`} onClick={() => setActive(c.conversation_id)}>
              <span>
                <strong>{c.lead_name || c.external_id}</strong>
                <span className="sales-lead-meta" style={{ display: 'block' }}>{c.channel} · {stageLabel(c.lead_stage)} · {formatWhen(c.last_customer_message_at)}</span>
              </span>
              <span className={`badge ${c.mode === 'AI' ? 'badge-emerald' : 'badge-amber'}`}>{c.mode === 'AI' ? 'AI' : 'Staff'}</span>
            </button>
          ))}
        </div>

        <div className="glass-card sales-thread">
          {!conv && <p className="sales-empty">Pick a conversation.</p>}
          {conv && (
            <>
              <div className="sales-toolbar">
                <div>
                  <strong>{conv.external_id}</strong> <span className="sales-lead-meta">· {conv.channel}</span>
                  {conv.handoff_reason && <div className="sales-lead-meta">With staff: {conv.handoff_reason}</div>}
                </div>
                {worker && (
                  conv.mode === 'AI'
                    ? <Button size="sm" icon={<Hand size={13} />} disabled={busy} onClick={() => act(() => salesApi.setChatMode(conv.conversation_id, 'HUMAN', 'taken over'), 'You have this chat')}>Take over</Button>
                    : <Button size="sm" icon={<RotateCcw size={13} />} disabled={busy} onClick={() => act(() => salesApi.setChatMode(conv.conversation_id, 'AI'), 'Handed back to the assistant')}>Hand back to AI</Button>
                )}
              </div>
              <div className="sales-messages">
                {thread.messages.map((m) => (
                  <div key={m.message_id} className={`sales-bubble ${m.direction} ${m.status === 'draft' ? 'draft' : ''}`}>
                    {m.text}
                    <div className="sales-bubble-meta">
                      <span>{m.sender}{m.status === 'draft' ? ' · draft (not sent)' : ''}{['not_sent', 'skipped'].includes(m.status) ? ` · NOT SENT: ${m.error}` : ''}</span>
                      <span>{formatWhen(m.created_at)}</span>
                      {m.status === 'draft' && worker && (
                        m.draft_rating ? <span>rated {m.draft_rating.replace('_', ' ')}</span> : (
                          <>
                            <Button size="sm" variant="secondary" icon={<ThumbsUp size={12} />} title="Usable" onClick={() => act(() => salesApi.rateDraft(m.message_id, 'usable'), 'Rated usable')} />
                            <Button size="sm" variant="secondary" icon={<ThumbsDown size={12} />} title="Not usable" onClick={() => act(() => salesApi.rateDraft(m.message_id, 'not_usable'), 'Rated not usable')} />
                          </>
                        )
                      )}
                    </div>
                  </div>
                ))}
                <div ref={endRef} />
              </div>
              {worker && (
                <form className="sales-reply" onSubmit={(e) => { e.preventDefault(); if (!text.trim()) return; act(async () => { await salesApi.reply(conv.conversation_id, text); setText(''); }, 'Sent'); }}>
                  <textarea aria-label="Reply" placeholder="Reply as staff (takes the chat over)" value={text} onChange={(e) => setText(e.target.value)} />
                  <Button type="submit" variant="coral" icon={<Send size={14} />} disabled={busy || !text.trim()}>Send</Button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
