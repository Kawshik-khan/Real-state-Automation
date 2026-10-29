import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, ShieldCheck, Sparkles } from 'lucide-react';
import Button from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { useAuth } from '../context/AuthContext';
import { salesApi, formatBdt, formatWhen, canManage } from '../services/salesApi';
import '../styles/sales.css';

const KIND_LABEL = { UNIT_HOLD: 'Hold a unit', PRICE_EXCEPTION: 'Price / plan request', CONTENT_POST: 'Marketing post' };
const STATUS_BADGE = { PENDING: 'badge-amber', APPROVED: 'badge-emerald', REJECTED: 'badge-rose', STALE: 'badge-neutral' };

export default function SalesApprovalsPage() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const manager = canManage(user?.role);
  const [status, setStatus] = useState('PENDING');
  const [items, setItems] = useState([]);
  const [reasons, setReasons] = useState({});
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      setItems((await salesApi.approvals(status)).approvals);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [status]);

  useEffect(() => { load(); }, [load]);

  const decide = async (approval, decision) => {
    setBusy(approval.approval_id);
    try {
      await salesApi.decide(approval.approval_id, decision, reasons[approval.approval_id]);
      showToast(decision === 'APPROVED' ? 'Approved' : 'Rejected', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setBusy(null);
      load();
    }
  };

  const draftPosts = async () => {
    setBusy('content');
    try {
      const result = await salesApi.runContentDrafts();
      const made = result.created.length;
      showToast(made ? `${made} post draft${made === 1 ? '' : 's'} ready for review` : 'No projects with new units this week', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setBusy(null);
      load();
    }
  };

  return (
    <div className="sales-page">
      <div className="sales-toolbar">
        <div>
          <h2>Approvals</h2>
          <p>Requests the AI raised that only a manager can grant. A hold is refused if the unit changed since the request. Marketing posts are drafted from new inventory every Sunday; approving one marks it ready to publish, nothing is posted automatically.</p>
        </div>
        <div className="sales-toolbar-actions">
          {['PENDING', 'APPROVED', 'REJECTED', 'STALE'].map((s) => (
            <button key={s} type="button" className={`sales-chip ${status === s ? 'on' : ''}`} onClick={() => setStatus(s)}>{s.toLowerCase()}</button>
          ))}
          {manager && <Button icon={<Sparkles size={14} />} disabled={busy === 'content'} onClick={draftPosts}>Draft posts now</Button>}
          <Button icon={<RefreshCw size={14} />} onClick={load}>Refresh</Button>
        </div>
      </div>
      {error && <p className="sales-error">{error}</p>}
      {items.length === 0 && <div className="glass-card sales-empty"><ShieldCheck size={18} /> Nothing {status.toLowerCase()}.</div>}
      {items.map((a) => (
        <div key={a.approval_id} className="glass-card sales-section">
          <div className="sales-toolbar">
            <div>
              <h3 style={{ margin: 0 }}>{KIND_LABEL[a.kind] || a.kind}{a.unit_code ? ` · ${a.unit_code}` : ''}</h3>
              <p>{a.kind === 'CONTENT_POST' ? a.payload.project_name : `For ${a.lead_name || a.lead_id}`} · requested by {a.requested_by} · {formatWhen(a.created_at)}</p>
            </div>
            <span className={`badge ${STATUS_BADGE[a.status]}`}>{a.status}</span>
          </div>
          <div className="sales-lead-meta" style={{ fontSize: '0.86rem', marginTop: 8 }}>
            {a.payload.list_price_bdt && <div>List price: {formatBdt(a.payload.list_price_bdt)}{a.unit_status_now ? ` · unit is ${a.unit_status_now} now` : ''}</div>}
            {a.payload.requested_price_bdt && <div>Customer asks: {formatBdt(a.payload.requested_price_bdt)}</div>}
            {a.payload.request && <div>“{a.payload.request}”</div>}
            {a.payload.note && <div>Note: {a.payload.note}</div>}
            {a.kind === 'CONTENT_POST' && (
              <>
                <div className="sales-post-text">{a.payload.text}</div>
                <div>Based on: {a.payload.facts?.available_units} new unit(s) {a.payload.facts?.unit_codes?.join(', ')} · from {formatBdt(a.payload.facts?.price_from_bdt)}</div>
              </>
            )}
            {a.decided_by && <div>Decided by {a.decided_by} · {formatWhen(a.decided_at)}{a.decision_reason ? ` — ${a.decision_reason}` : ''}</div>}
          </div>
          {a.status === 'PENDING' && manager && (
            <div className="sales-reply" style={{ marginTop: 'var(--space-3)' }}>
              <input type="text" aria-label="Reason" placeholder="Reason (shared with the team)" value={reasons[a.approval_id] || ''} onChange={(e) => setReasons({ ...reasons, [a.approval_id]: e.target.value })} style={{ flex: 1 }} />
              <Button variant="emerald" disabled={busy === a.approval_id} onClick={() => decide(a, 'APPROVED')}>Approve</Button>
              <Button variant="rose" disabled={busy === a.approval_id} onClick={() => decide(a, 'REJECTED')}>Reject</Button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
