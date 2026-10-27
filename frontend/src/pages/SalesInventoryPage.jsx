import React, { useCallback, useEffect, useState } from 'react';
import { Plus, RefreshCw, Save, X } from 'lucide-react';
import Button from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { useAuth } from '../context/AuthContext';
import { salesApi, formatBdt, formatWhen, canManage } from '../services/salesApi';
import '../styles/sales.css';

const UNIT_STATUSES = ['AVAILABLE', 'HELD', 'BOOKED', 'SOLD'];
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const STATUS_BADGE = { AVAILABLE: 'badge-emerald', HELD: 'badge-amber', BOOKED: 'badge-blue', SOLD: 'badge-neutral' };

function UnitRow({ unit, editable, onSaved }) {
  const { showToast } = useToast();
  const [price, setPrice] = useState(unit.list_price_bdt);
  const [status, setStatus] = useState(unit.status);
  const [busy, setBusy] = useState(false);
  const dirty = Number(price) !== unit.list_price_bdt || status !== unit.status;

  useEffect(() => {
    setPrice(unit.list_price_bdt);
    setStatus(unit.status);
  }, [unit.list_price_bdt, unit.status]);

  const save = async (fields) => {
    setBusy(true);
    try {
      const res = await salesApi.updateUnit(unit.unit_id, { version: unit.version, ...fields });
      showToast(res.unit_match_alert_queued ? 'Saved — matching leads will be told it is available' : 'Saved', 'success');
      onSaved();
    } catch (err) {
      showToast(err.message, 'error');
      if (err.status === 409) onSaved();
    } finally {
      setBusy(false);
    }
  };

  return (
    <tr>
      <td><strong>{unit.unit_code}</strong><div className="sales-lead-meta">{unit.project_name}</div></td>
      <td>{unit.floor ?? '—'}</td>
      <td>{unit.bedrooms ?? '—'}</td>
      <td>{unit.size_sqft ? `${unit.size_sqft.toLocaleString()} sqft` : '—'}</td>
      <td>
        {editable ? (
          <input aria-label={`Price for ${unit.unit_code}`} type="number" min="1" value={price} onChange={(e) => setPrice(e.target.value)} style={{ width: 130 }} />
        ) : formatBdt(unit.list_price_bdt)}
      </td>
      <td>
        {editable ? (
          <select aria-label={`Status for ${unit.unit_code}`} value={status} onChange={(e) => setStatus(e.target.value)}>
            {UNIT_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        ) : <span className={`badge ${STATUS_BADGE[unit.status]}`}>{unit.status}</span>}
        {unit.status === 'HELD' && unit.held_until && <div className="sales-lead-meta">until {formatWhen(unit.held_until)}</div>}
      </td>
      <td>
        <span className="sales-lead-meta">{formatWhen(unit.updated_at)}</span>
        {unit.needs_confirmation && <div><span className="badge badge-amber" title="Not updated for 14 days: the assistant tells customers it needs confirming">Check status</span></div>}
      </td>
      {editable && (
        <td style={{ whiteSpace: 'nowrap' }}>
          <Button size="sm" variant={dirty ? 'coral' : 'secondary'} icon={<Save size={13} />} disabled={busy || (dirty && !(Number(price) > 0))}
            onClick={() => save(dirty ? { list_price_bdt: Number(price), status } : {})}
            title={dirty ? 'Save changes' : 'Mark as checked today'}>
            {dirty ? 'Save' : 'Checked'}
          </Button>
        </td>
      )}
    </tr>
  );
}

export default function SalesInventoryPage() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const editable = canManage(user?.role);
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [units, setUnits] = useState([]);
  const [slots, setSlots] = useState([]);
  const [plans, setPlans] = useState([]);
  const [error, setError] = useState('');
  const [newUnit, setNewUnit] = useState({ unit_code: '', floor: '', bedrooms: '', size_sqft: '', list_price_bdt: '', facing: '' });
  const [newSlot, setNewSlot] = useState({ weekday: '5', start_time: '11:00', duration_minutes: '60', capacity: '2' });
  const [newPlan, setNewPlan] = useState({ name: '', booking_money_bdt: '', down_payment_pct: '20', installment_months: '36' });

  const load = useCallback(async () => {
    try {
      const [u, s, p] = await Promise.all([
        salesApi.units({ project_id: projectId || undefined, status: statusFilter || undefined }),
        salesApi.slots(projectId || undefined),
        salesApi.plans(projectId || undefined),
      ]);
      setUnits(u.units);
      setSlots(s.slots.filter((x) => x.active));
      setPlans(p.plans);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [projectId, statusFilter]);

  useEffect(() => {
    salesApi.projects().then((r) => setProjects(r.projects)).catch((err) => setError(err.message));
  }, []);
  useEffect(() => { load(); }, [load]);

  const projectName = (id) => projects.find((p) => p.project_id === id)?.name || id;
  const needProject = () => {
    if (!projectId) {
      showToast('Pick a project first', 'warning');
      return true;
    }
    return false;
  };

  const submit = async (fn, success, reset) => {
    try {
      await fn();
      showToast(success, 'success');
      reset?.();
      load();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const num = (v) => (v === '' ? undefined : Number(v));

  return (
    <div className="sales-page">
      <div className="sales-toolbar">
        <div>
          <h2>Unit inventory</h2>
          <p>The assistant quotes only what is here. Changes apply to its very next reply.</p>
        </div>
        <div className="sales-toolbar-actions">
          <select aria-label="Project" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            <option value="">All projects</option>
            {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
          </select>
          <select aria-label="Status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            {UNIT_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <Button icon={<RefreshCw size={14} />} onClick={load}>Refresh</Button>
        </div>
      </div>

      {error && <p className="sales-error">{error}</p>}

      <div className="glass-card sales-section">
        <h3>Units ({units.length})</h3>
        <div className="sales-table-wrap">
          <table className="sales-table">
            <thead>
              <tr><th>Unit</th><th>Floor</th><th>Beds</th><th>Size</th><th>List price (BDT)</th><th>Status</th><th>Last checked</th>{editable && <th />}</tr>
            </thead>
            <tbody>
              {units.map((u) => <UnitRow key={u.unit_id} unit={u} editable={editable} onSaved={load} />)}
            </tbody>
          </table>
          {units.length === 0 && <p className="sales-empty">No units yet. {editable ? 'Add one below or load a CSV with scripts/seed_sales_data.py.' : ''}</p>}
        </div>
        {editable && (
          <form className="sales-form" style={{ marginTop: 'var(--space-4)' }} onSubmit={(e) => {
            e.preventDefault();
            if (needProject()) return;
            submit(() => salesApi.createUnit({
              project_id: projectId, unit_code: newUnit.unit_code.trim(), list_price_bdt: Number(newUnit.list_price_bdt),
              floor: num(newUnit.floor), bedrooms: num(newUnit.bedrooms), size_sqft: num(newUnit.size_sqft), facing: newUnit.facing || undefined,
            }), 'Unit added', () => setNewUnit({ unit_code: '', floor: '', bedrooms: '', size_sqft: '', list_price_bdt: '', facing: '' }));
          }}>
            <label className="sales-field">Unit code<input type="text" required value={newUnit.unit_code} onChange={(e) => setNewUnit({ ...newUnit, unit_code: e.target.value })} placeholder="A-5" /></label>
            <label className="sales-field">Floor<input type="number" value={newUnit.floor} onChange={(e) => setNewUnit({ ...newUnit, floor: e.target.value })} /></label>
            <label className="sales-field">Bedrooms<input type="number" min="0" value={newUnit.bedrooms} onChange={(e) => setNewUnit({ ...newUnit, bedrooms: e.target.value })} /></label>
            <label className="sales-field">Size (sqft)<input type="number" min="1" value={newUnit.size_sqft} onChange={(e) => setNewUnit({ ...newUnit, size_sqft: e.target.value })} /></label>
            <label className="sales-field">Facing<input type="text" value={newUnit.facing} onChange={(e) => setNewUnit({ ...newUnit, facing: e.target.value })} placeholder="South" /></label>
            <label className="sales-field">List price (BDT)<input required type="number" min="1" value={newUnit.list_price_bdt} onChange={(e) => setNewUnit({ ...newUnit, list_price_bdt: e.target.value })} /></label>
            <Button type="submit" variant="coral" icon={<Plus size={14} />}>Add unit</Button>
          </form>
        )}
      </div>

      <div className="sales-grid-2">
        <div className="glass-card sales-section">
          <h3>Site-visit slots</h3>
          <p className="sales-lead-meta">The assistant can only book these times (Asia/Dhaka). Capacity = visits per slot.</p>
          <div className="sales-table-wrap">
            <table className="sales-table">
              <thead><tr><th>Project</th><th>Day</th><th>Time</th><th>Length</th><th>Capacity</th>{editable && <th />}</tr></thead>
              <tbody>
                {slots.map((s) => (
                  <tr key={s.slot_id}>
                    <td>{projectName(s.project_id)}</td><td>{WEEKDAYS[s.weekday]}</td><td>{s.start_time}</td><td>{s.duration_minutes} min</td><td>{s.capacity}</td>
                    {editable && <td><Button size="sm" variant="secondary" icon={<X size={13} />} onClick={() => submit(() => salesApi.deleteSlot(s.slot_id), 'Slot removed')} title="Remove slot" /></td>}
                  </tr>
                ))}
              </tbody>
            </table>
            {slots.length === 0 && <p className="sales-empty">No visit slots: the assistant will hand visit requests to staff.</p>}
          </div>
          {editable && (
            <form className="sales-form" style={{ marginTop: 'var(--space-3)' }} onSubmit={(e) => {
              e.preventDefault();
              if (needProject()) return;
              submit(() => salesApi.createSlot({ project_id: projectId, weekday: Number(newSlot.weekday), start_time: newSlot.start_time, duration_minutes: Number(newSlot.duration_minutes), capacity: Number(newSlot.capacity) }), 'Slot added');
            }}>
              <label className="sales-field">Day
                <select value={newSlot.weekday} onChange={(e) => setNewSlot({ ...newSlot, weekday: e.target.value })}>
                  {WEEKDAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}
                </select>
              </label>
              <label className="sales-field">Start<input className="glass-input" type="time" required value={newSlot.start_time} onChange={(e) => setNewSlot({ ...newSlot, start_time: e.target.value })} /></label>
              <label className="sales-field">Minutes<input type="number" min="15" max="480" value={newSlot.duration_minutes} onChange={(e) => setNewSlot({ ...newSlot, duration_minutes: e.target.value })} /></label>
              <label className="sales-field">Capacity<input type="number" min="1" max="50" value={newSlot.capacity} onChange={(e) => setNewSlot({ ...newSlot, capacity: e.target.value })} /></label>
              <Button type="submit" variant="coral" icon={<Plus size={14} />}>Add slot</Button>
            </form>
          )}
        </div>

        <div className="glass-card sales-section">
          <h3>Payment plans</h3>
          <p className="sales-lead-meta">Only active plans here can be used by the assistant's calculator.</p>
          <div className="sales-table-wrap">
            <table className="sales-table">
              <thead><tr><th>Project</th><th>Plan</th><th>Booking</th><th>Down payment</th><th>Installments</th></tr></thead>
              <tbody>
                {plans.map((p) => (
                  <tr key={p.plan_id}>
                    <td>{projectName(p.project_id)}</td><td>{p.name}{!p.active && ' (inactive)'}</td><td>{formatBdt(p.booking_money_bdt)}</td><td>{p.down_payment_pct}%</td><td>{p.installment_months} months</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {plans.length === 0 && <p className="sales-empty">No published plans: payment questions go to a sales agent.</p>}
          </div>
          {editable && (
            <form className="sales-form" style={{ marginTop: 'var(--space-3)' }} onSubmit={(e) => {
              e.preventDefault();
              if (needProject()) return;
              submit(() => salesApi.createPlan({ project_id: projectId, name: newPlan.name.trim(), booking_money_bdt: Number(newPlan.booking_money_bdt || 0), down_payment_pct: Number(newPlan.down_payment_pct), installment_months: Number(newPlan.installment_months) }), 'Plan added', () => setNewPlan({ ...newPlan, name: '' }));
            }}>
              <label className="sales-field">Name<input type="text" required value={newPlan.name} onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })} placeholder="36-month plan" /></label>
              <label className="sales-field">Booking (BDT)<input type="number" min="0" value={newPlan.booking_money_bdt} onChange={(e) => setNewPlan({ ...newPlan, booking_money_bdt: e.target.value })} /></label>
              <label className="sales-field">Down %<input type="number" min="0" max="100" value={newPlan.down_payment_pct} onChange={(e) => setNewPlan({ ...newPlan, down_payment_pct: e.target.value })} /></label>
              <label className="sales-field">Months<input type="number" min="0" max="240" value={newPlan.installment_months} onChange={(e) => setNewPlan({ ...newPlan, installment_months: e.target.value })} /></label>
              <Button type="submit" variant="coral" icon={<Plus size={14} />}>Add plan</Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
