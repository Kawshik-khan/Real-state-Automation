import React, { useCallback, useEffect, useState } from 'react';
import { CalendarClock, Phone, Send } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import { useToast } from '../ui/Toast';
import { salesApi, STAGES, stageLabel, formatBdt, formatWhen, canWork } from '../../services/salesApi';

const EVENT_LABELS = {
  created: 'Lead created',
  profile_updated: 'Profile updated',
  stage_change: 'Stage changed',
  owner_assigned: 'Owner assigned',
  note: 'Note',
  visit_booked: 'Visit booked',
  visit_done: 'Visit done',
  visit_no_show: 'No-show',
  visit_cancelled: 'Visit cancelled',
  visit_confirmed: 'Visit confirmed',
  visit_rescheduled: 'Visit rescheduled',
  handoff: 'Handed to staff',
  handback: 'Handed back to AI',
  followup_sent: 'Follow-up',
  followup_enrolled: 'Follow-up sequence started',
  approval_requested: 'Approval requested',
  approval_decided: 'Approval decided',
  approval_stale: 'Approval refused (unit changed)',
  unit_alert: 'Unit match alert',
  reminder_24h: 'Visit reminder (24 h)',
  reminder_2h: 'Visit reminder (2 h)',
};

function describe(event) {
  const p = event.payload || {};
  if (event.type === 'stage_change') return `${stageLabel(p.from)} → ${stageLabel(p.to)}${p.lost_reason ? ` (${p.lost_reason})` : ''}`;
  if (event.type === 'note') return p.text;
  if (event.type === 'profile_updated') return Object.keys(p).join(', ');
  if (p.status) return `${p.status}${p.error ? ` — ${p.error}` : ''}`;
  if (p.reason) return p.reason;
  return '';
}

export default function LeadDrawer({ leadId, role, onClose, onChanged }) {
  const { showToast } = useToast();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [note, setNote] = useState('');
  const [lostReason, setLostReason] = useState('');
  const [projects, setProjects] = useState([]);
  const [visitProject, setVisitProject] = useState('');
  const [freeSlots, setFreeSlots] = useState([]);
  const [busy, setBusy] = useState(false);
  const editable = canWork(role);

  const load = useCallback(async () => {
    try {
      setData(await salesApi.lead(leadId));
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [leadId]);

  useEffect(() => {
    load();
    salesApi.projects().then((r) => setProjects(r.projects)).catch(() => setProjects([]));
  }, [load]);

  useEffect(() => {
    if (!visitProject) {
      setFreeSlots([]);
      return;
    }
    salesApi.freeSlots(visitProject).then((r) => setFreeSlots(r.slots)).catch((err) => showToast(err.message, 'error'));
  }, [visitProject, showToast]);

  const run = async (fn, success) => {
    setBusy(true);
    try {
      await fn();
      showToast(success, 'success');
      await load();
      onChanged?.();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setBusy(false);
    }
  };

  const lead = data?.lead;

  return (
    <Modal isOpen onClose={onClose} title={lead?.name || 'Lead'} subtitle={lead ? `${lead.channel} · ${stageLabel(lead.stage)} · score ${lead.score}` : ''} maxWidth="860px">
      {error && <p className="sales-error">{error}</p>}
      {!lead && !error && <p className="sales-empty">Loading…</p>}
      {lead && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div className="sales-grid-2">
            <div>
              <div className="sales-kpi-label">Needs</div>
              <div className="sales-lead-meta" style={{ fontSize: '0.86rem' }}>
                <div><Phone size={12} /> {lead.phone || 'No phone yet'}</div>
                <div>Budget: {lead.budget_max_bdt ? `${lead.budget_min_bdt ? `${formatBdt(lead.budget_min_bdt)}–` : 'up to '}${formatBdt(lead.budget_max_bdt)}` : 'unknown'}</div>
                <div>Areas: {lead.preferred_areas?.length ? lead.preferred_areas.join(', ') : 'unknown'}</div>
                <div>Bedrooms: {lead.bedrooms || 'unknown'} · Timeline: {lead.timeline || 'unknown'}</div>
                <div>Next follow-up: {formatWhen(lead.next_followup_at)}</div>
              </div>
            </div>
            {editable && (
              <div>
                <div className="sales-kpi-label">Stage</div>
                <div className="sales-switch-row" style={{ marginTop: 6 }}>
                  <select
                    aria-label="Lead stage"
                    value={lead.stage}
                    disabled={busy}
                    onChange={(e) => {
                      const stage = e.target.value;
                      if (stage === 'LOST' && !lostReason.trim()) {
                        showToast('Type a lost reason first', 'warning');
                        return;
                      }
                      run(() => salesApi.setStage(leadId, stage, lostReason), `Moved to ${stageLabel(stage)}`);
                    }}
                  >
                    {STAGES.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                  </select>
                  <input type="text" placeholder="Lost reason (needed for Lost)" value={lostReason} onChange={(e) => setLostReason(e.target.value)} style={{ flex: 1, minWidth: 160 }} />
                </div>
              </div>
            )}
          </div>

          <div className="sales-grid-2">
            <div>
              <div className="sales-kpi-label">Visits</div>
              {data.visits.length === 0 && <p className="sales-lead-meta">No visits yet.</p>}
              {data.visits.map((v) => (
                <div key={v.visit_id} className="sales-lead-meta" style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                  <span><CalendarClock size={12} /> {v.project_name} · {v.slot_label} · <strong>{v.status}</strong></span>
                  {editable && ['BOOKED', 'CONFIRMED'].includes(v.status) && (
                    <span style={{ display: 'flex', gap: 4 }}>
                      <Button size="sm" variant="emerald" disabled={busy} onClick={() => run(() => salesApi.updateVisit(v.visit_id, { status: 'DONE' }), 'Visit marked done')}>Done</Button>
                      <Button size="sm" disabled={busy} onClick={() => run(() => salesApi.updateVisit(v.visit_id, { status: 'NO_SHOW' }), 'Marked no-show')}>No-show</Button>
                    </span>
                  )}
                </div>
              ))}
              {editable && (
                <div className="sales-form" style={{ marginTop: 8 }}>
                  <label className="sales-field">Project
                    <select value={visitProject} onChange={(e) => setVisitProject(e.target.value)}>
                      <option value="">Book a visit…</option>
                      {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
                    </select>
                  </label>
                  {visitProject && freeSlots.length === 0 && <span className="sales-lead-meta">No free slots set up for this project.</span>}
                  {freeSlots.slice(0, 6).map((slot) => (
                    <Button key={slot.slot_start} size="sm" disabled={busy} onClick={() => run(() => salesApi.bookVisit(leadId, visitProject, slot.slot_start), `Visit booked: ${slot.label}`)}>
                      {slot.label}
                    </Button>
                  ))}
                </div>
              )}
            </div>
            <div>
              <div className="sales-kpi-label">Active follow-ups</div>
              {data.followups.length === 0 && <p className="sales-lead-meta">None scheduled.</p>}
              {data.followups.map((f) => (
                <div key={f.enrollment_id} className="sales-lead-meta">{f.sequence} · next {formatWhen(f.next_run_at)}</div>
              ))}
            </div>
          </div>

          <div className="sales-grid-2">
            <div>
              <div className="sales-kpi-label">History</div>
              <ul className="sales-timeline">
                {data.events.map((e) => (
                  <li key={e.event_id}>
                    <time>{formatWhen(e.created_at)} · {e.actor}</time>
                    <strong>{EVENT_LABELS[e.type] || e.type}</strong> {describe(e)}
                  </li>
                ))}
              </ul>
              {editable && (
                <div className="sales-reply" style={{ marginTop: 8 }}>
                  <textarea placeholder="Add a note for the team" value={note} onChange={(e) => setNote(e.target.value)} />
                  <Button variant="coral" icon={<Send size={14} />} disabled={busy || !note.trim()} onClick={() => run(async () => { await salesApi.addNote(leadId, note); setNote(''); }, 'Note added')}>Add</Button>
                </div>
              )}
            </div>
            <div>
              <div className="sales-kpi-label">Recent messages</div>
              <div className="sales-messages" style={{ maxHeight: 300 }}>
                {data.messages.length === 0 && <p className="sales-lead-meta">No messages.</p>}
                {data.messages.map((m) => (
                  <div key={m.message_id} className={`sales-bubble ${m.direction} ${m.status === 'draft' ? 'draft' : ''}`}>
                    {m.text}
                    <div className="sales-bubble-meta">{m.sender} · {m.status} · {formatWhen(m.created_at)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
