import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw, UserPlus } from 'lucide-react';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import { useToast } from '../components/ui/Toast';
import LeadDrawer from '../components/sales/LeadDrawer';
import { useAuth } from '../context/AuthContext';
import { salesApi, STAGES, formatBdt, formatWhen, canWork } from '../services/salesApi';
import '../styles/sales.css';

function NewLeadModal({ onClose, onCreated }) {
  const { showToast } = useToast();
  const [form, setForm] = useState({ name: '', phone: '', source: 'walk_in', budget_max_bdt: '', preferred_areas: '', bedrooms: '' });
  const [busy, setBusy] = useState(false);
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const body = {
        name: form.name.trim(),
        phone: form.phone.trim(),
        source: form.source,
        budget_max_bdt: form.budget_max_bdt ? Number(form.budget_max_bdt) : undefined,
        preferred_areas: form.preferred_areas ? form.preferred_areas.split(',').map((a) => a.trim()).filter(Boolean) : undefined,
        bedrooms: form.bedrooms ? Number(form.bedrooms) : undefined,
      };
      const res = await salesApi.createLead(body);
      showToast(res.created ? 'Lead added' : 'This phone number already has a lead; opened it', 'success');
      onCreated(res.lead.lead_id);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Add a lead" subtitle="Walk-ins, phone calls and referrals" maxWidth="560px">
      <form onSubmit={submit} className="sales-form">
        <label className="sales-field">Name<input type="text" required value={form.name} onChange={set('name')} /></label>
        <label className="sales-field">Phone (WhatsApp)<input type="text" required value={form.phone} onChange={set('phone')} placeholder="01711 000000" /></label>
        <label className="sales-field">Source
          <select value={form.source} onChange={set('source')}>
            <option value="walk_in">Walk-in</option>
            <option value="phone_call">Phone call</option>
            <option value="referral">Referral</option>
            <option value="event">Event / fair</option>
          </select>
        </label>
        <label className="sales-field">Budget up to (BDT)<input type="number" min="0" value={form.budget_max_bdt} onChange={set('budget_max_bdt')} placeholder="10000000" /></label>
        <label className="sales-field">Areas (comma separated)<input type="text" value={form.preferred_areas} onChange={set('preferred_areas')} placeholder="Gulshan, Banani" /></label>
        <label className="sales-field">Bedrooms<input type="number" min="1" max="10" value={form.bedrooms} onChange={set('bedrooms')} /></label>
        <Button type="submit" variant="coral" disabled={busy}>Add lead</Button>
      </form>
    </Modal>
  );
}

export default function SalesPipelinePage() {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [leads, setLeads] = useState([]);
  const [search, setSearch] = useState('');
  const [mine, setMine] = useState(false);
  const [openLead, setOpenLead] = useState(null);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [ov, ls] = await Promise.all([salesApi.overview(), salesApi.leads({ search, mine: mine || undefined })]);
      setOverview(ov);
      setLeads(ls.leads);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [search, mine]);

  useEffect(() => {
    const t = setTimeout(load, search ? 300 : 0);
    return () => clearTimeout(t);
  }, [load, search]);

  const byStage = useMemo(() => {
    const groups = Object.fromEntries(STAGES.map((s) => [s.id, []]));
    leads.forEach((l) => (groups[l.stage] || (groups[l.stage] = [])).push(l));
    return groups;
  }, [leads]);

  const openCount = overview ? STAGES.filter((s) => !['WON', 'LOST'].includes(s.id)).reduce((n, s) => n + (overview.pipeline[s.id] || 0), 0) : 0;

  return (
    <div className="sales-page">
      <div className="sales-toolbar">
        <div>
          <h2>Sales pipeline</h2>
          <p>Every inquiry from every channel, from first message to booking money.</p>
        </div>
        <div className="sales-toolbar-actions">
          <input type="text" aria-label="Search leads" placeholder="Search name or phone" value={search} onChange={(e) => setSearch(e.target.value)} style={{ minWidth: 200 }} />
          <button type="button" className={`sales-chip ${mine ? 'on' : ''}`} onClick={() => setMine(!mine)}>My leads</button>
          <Button icon={<RefreshCw size={14} />} onClick={load}>Refresh</Button>
          {canWork(user?.role) && <Button variant="coral" icon={<UserPlus size={14} />} onClick={() => setAdding(true)}>Add lead</Button>}
        </div>
      </div>

      {error && <p className="sales-error">{error}</p>}

      {overview && (
        <div className="sales-kpis">
          <div className="glass-card sales-kpi">
            <div className="sales-kpi-label">Open leads</div>
            <div className="sales-kpi-value">{openCount}</div>
            <div className="sales-kpi-hint">{overview.pipeline.WON} won · {overview.pipeline.LOST} lost</div>
          </div>
          <div className="glass-card sales-kpi">
            <div className="sales-kpi-label">Visits today</div>
            <div className="sales-kpi-value">{overview.visits_today.length}</div>
            <div className="sales-kpi-hint">{overview.visits_today[0] ? `Next: ${overview.visits_today[0].slot_label}` : 'None booked'}</div>
          </div>
          <div className="glass-card sales-kpi">
            <div className="sales-kpi-label">Approvals waiting</div>
            <div className="sales-kpi-value">{overview.pending_approvals}</div>
            <div className="sales-kpi-hint">Unit holds and price requests</div>
          </div>
          <div className="glass-card sales-kpi">
            <div className="sales-kpi-label">AI assistant</div>
            <div className="sales-kpi-value" style={{ textTransform: 'capitalize' }}>{overview.assistant.kill_switch ? 'Stopped' : overview.assistant.mode}</div>
            <div className="sales-kpi-hint">
              {overview.drafts.rated ? `${overview.drafts.usable_pct}% of ${overview.drafts.rated} rated drafts usable` : 'No drafts rated yet'}
            </div>
          </div>
        </div>
      )}

      <div className="sales-board" role="list" aria-label="Pipeline stages">
        {STAGES.map((stage) => (
          <section key={stage.id} className="sales-column" role="listitem" aria-label={stage.label}>
            <div className="sales-column-head">
              <span>{stage.label}</span>
              <span className="badge badge-neutral">{byStage[stage.id]?.length || 0}</span>
            </div>
            {(byStage[stage.id] || []).map((lead) => (
              <button type="button" key={lead.lead_id} className="sales-lead-card" onClick={() => setOpenLead(lead.lead_id)}>
                <div className="sales-lead-name">
                  <span>{lead.name || lead.phone || 'Unknown'}</span>
                  <span className="sales-score">{lead.score}</span>
                </div>
                <div className="sales-lead-meta">
                  {lead.budget_max_bdt ? `Up to ${formatBdt(lead.budget_max_bdt)}` : 'Budget unknown'}
                  {lead.bedrooms ? ` · ${lead.bedrooms} bed` : ''}
                  {lead.preferred_areas?.length ? ` · ${lead.preferred_areas.join(', ')}` : ''}
                  <br />
                  {lead.channel} · {lead.next_followup_at ? `follow-up ${formatWhen(lead.next_followup_at)}` : 'no follow-up scheduled'}
                </div>
              </button>
            ))}
            {(byStage[stage.id] || []).length === 0 && <div className="sales-empty" style={{ padding: 8 }}>—</div>}
          </section>
        ))}
      </div>

      {openLead && <LeadDrawer leadId={openLead} role={user?.role} onClose={() => setOpenLead(null)} onChanged={load} />}
      {adding && <NewLeadModal onClose={() => setAdding(false)} onCreated={(id) => { setAdding(false); load(); setOpenLead(id); }} />}
    </div>
  );
}
