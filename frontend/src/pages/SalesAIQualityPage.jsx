import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, CircleDashed, Gauge, RefreshCw, XCircle } from 'lucide-react';
import Button from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { useAuth } from '../context/AuthContext';
import { salesApi, formatWhen } from '../services/salesApi';
import '../styles/sales.css';

const ROUTE_TEXT = {
  legacy: 'The old pipeline answers every chat. Nothing is compared yet.',
  shadow: 'The old pipeline answers; the sales assistant drafts a reply to the same message for you to compare.',
  sales: 'The sales assistant answers wherever it is live. Where it isn’t live yet, the old pipeline answers and a draft is stored for comparison.',
};

const GATE_TEXT = {
  enough_ratings: (t) => `At least ${t.min_rated_pairs} comparisons rated`,
  enough_turns: (t) => `At least ${t.min_turns.toLocaleString()} assistant turns measured`,
  worse_under_limit: (t) => `Sales reply worse in under ${t.max_worse_pct}% of them`,
  better_or_same: (t) => `Better or the same in at least ${t.min_better_or_same_pct}%`,
  median_model_calls: (t) => `Median of ${t.max_median_model_calls} AI calls per message or fewer`,
  p95_model_calls: (t) => `No more than ${t.max_p95_model_calls} AI calls for 95% of messages`,
  p95_latency: (t) => `Reply within ${t.max_p95_latency_ms / 1000} s for 95% of messages`,
  grounding_blocks: (t) => `Grounding gate blocks under ${t.max_grounding_blocks_per_100} replies per 100`,
};

const RATING_LABEL = { better: 'Sales reply better', same: 'About the same', worse: 'Sales reply worse' };

function GateIcon({ value }) {
  if (value === true) return <CheckCircle2 size={16} color="var(--accent-emerald)" aria-label="met" />;
  if (value === false) return <XCircle size={16} color="var(--accent-rose)" aria-label="not met" />;
  return <CircleDashed size={16} color="var(--text-dim)" aria-label="no data yet" />;
}

const show = (value, suffix = '') => (value === null || value === undefined ? '—' : `${value}${suffix}`);

export default function SalesAIQualityPage() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const canRate = ['admin', 'manager', 'agent'].includes(user?.role);
  const [days, setDays] = useState(14);
  const [report, setReport] = useState(null);
  const [pairs, setPairs] = useState([]);
  const [showRated, setShowRated] = useState(false);
  const [notes, setNotes] = useState({});
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [quality, list] = await Promise.all([salesApi.aiQuality(days), salesApi.shadowPairs(showRated ? undefined : false)]);
      setReport(quality);
      setPairs(list.pairs);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [days, showRated]);

  useEffect(() => { load(); }, [load]);

  const rate = async (pair, rating) => {
    setBusy(pair.pair_id);
    try {
      await salesApi.rateShadowPair(pair.pair_id, rating, notes[pair.pair_id]);
      showToast('Rating saved', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setBusy(null);
      load();
    }
  };

  const c = report?.comparison;
  const p = report?.performance;

  return (
    <div className="sales-page">
      <div className="sales-toolbar">
        <div>
          <h2>AI quality</h2>
          <p>Compare the old chatbot with the sales assistant on real messages. The old pipeline is retired only when every check below is met.</p>
        </div>
        <div className="sales-toolbar-actions">
          {[7, 14, 30].map((d) => (
            <button key={d} type="button" className={`sales-chip ${days === d ? 'on' : ''}`} onClick={() => setDays(d)}>{d} days</button>
          ))}
          <Button icon={<RefreshCw size={14} />} onClick={load}>Refresh</Button>
        </div>
      </div>
      {error && <p className="sales-error">{error}</p>}

      {report && (
        <>
          <div className="sales-grid-2">
            <div className="glass-card sales-section">
              <h3>Who answers customers</h3>
              <div className="sales-route">
                <span className="badge badge-amber">{report.routing.ai_route_via_sales}</span>
                <span>{ROUTE_TEXT[report.routing.ai_route_via_sales]}</span>
              </div>
              <div className="sales-lead-meta" style={{ fontSize: '0.84rem', marginTop: 'var(--space-3)' }}>
                <div>Email into the sales pipeline: {report.routing.email_via_sales ? 'on (drafts for staff)' : 'off'}</div>
                <div>Social comments into the sales pipeline: {report.routing.social_via_sales ? 'on' : 'off'}</div>
                <div>Extra AI safety calls in the old pipeline: {report.routing.legacy_llm_safety_checks ? 'on (fail closed)' : 'off (rules only)'}</div>
                <div className="sales-kpi-hint">Set on the server: AI_ROUTE_VIA_SALES, EMAIL_VIA_SALES, SOCIAL_VIA_SALES.</div>
              </div>
            </div>
            <div className="glass-card sales-section">
              <div className="sales-toolbar" style={{ marginBottom: 'var(--space-3)' }}>
                <h3 style={{ margin: 0 }}>Retirement checks</h3>
                <span className={`badge ${report.ready_to_retire_legacy ? 'badge-emerald' : 'badge-neutral'}`}>
                  {report.ready_to_retire_legacy ? 'Ready to retire the old pipeline' : 'Not ready yet'}
                </span>
              </div>
              {Object.entries(report.gates).map(([key, value]) => (
                <div key={key} className="sales-gate-row">
                  <GateIcon value={value} />
                  <span>{GATE_TEXT[key] ? GATE_TEXT[key](report.thresholds) : key}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="sales-kpis">
            <div className="glass-card sales-kpi">
              <div className="sales-kpi-label">Comparisons rated</div>
              <div className="sales-kpi-value">{c.rated}<span className="sales-kpi-of"> / {c.pairs}</span></div>
              <div className="sales-kpi-hint">{c.better} better · {c.same} same · {c.worse} worse</div>
            </div>
            <div className="glass-card sales-kpi">
              <div className="sales-kpi-label">Better or same</div>
              <div className="sales-kpi-value">{show(c.better_or_same_pct, '%')}</div>
              <div className="sales-kpi-hint">Worse: {show(c.worse_pct, '%')}</div>
            </div>
            <div className="glass-card sales-kpi">
              <div className="sales-kpi-label">AI calls per message</div>
              <div className="sales-kpi-value">{show(p.median_model_calls)}</div>
              <div className="sales-kpi-hint">95% within {show(p.p95_model_calls)} · {p.turns} turn{p.turns === 1 ? '' : 's'}</div>
            </div>
            <div className="glass-card sales-kpi">
              <div className="sales-kpi-label">Reply time (95%)</div>
              <div className="sales-kpi-value">{p.p95_latency_ms ? `${(p.p95_latency_ms / 1000).toFixed(1)} s` : '—'}</div>
              <div className="sales-kpi-hint">Typical: {p.p50_latency_ms ? `${(p.p50_latency_ms / 1000).toFixed(1)} s` : '—'}</div>
            </div>
            <div className="glass-card sales-kpi">
              <div className="sales-kpi-label">Grounding blocks</div>
              <div className="sales-kpi-value">{show(p.grounding_blocks_per_100)}</div>
              <div className="sales-kpi-hint">per 100 replies · handoffs {show(p.handoff_pct, '%')}</div>
            </div>
            <div className="glass-card sales-kpi">
              <div className="sales-kpi-label">Tokens per chat</div>
              <div className="sales-kpi-value">{p.tokens_per_conversation ? p.tokens_per_conversation.toLocaleString() : '—'}</div>
              <div className="sales-kpi-hint">sales assistant only</div>
            </div>
          </div>
        </>
      )}

      <div className="glass-card sales-section">
        <div className="sales-toolbar" style={{ marginBottom: 'var(--space-3)' }}>
          <div>
            <h3 style={{ margin: 0 }}>Side-by-side replies</h3>
            <p>Same customer message, two answers. The customer saw the old one.</p>
          </div>
          <div className="sales-toolbar-actions">
            <button type="button" className={`sales-chip ${!showRated ? 'on' : ''}`} onClick={() => setShowRated(false)}>to rate</button>
            <button type="button" className={`sales-chip ${showRated ? 'on' : ''}`} onClick={() => setShowRated(true)}>all</button>
          </div>
        </div>
        {pairs.length === 0 && (
          <div className="sales-empty"><Gauge size={18} /> {showRated ? 'No comparisons yet.' : 'Nothing waiting to be rated.'} Comparisons appear while AI_ROUTE_VIA_SALES is shadow or sales.</div>
        )}
        {pairs.map((pair) => (
          <div key={pair.pair_id} className="sales-compare-card">
            <div className="sales-compare-question">
              <span className="sales-kpi-label">{pair.channel} · {formatWhen(pair.created_at)}</span>
              <div>“{pair.customer_text}”</div>
            </div>
            <div className="sales-compare">
              <div className="sales-compare-col">
                <div className="sales-kpi-label">Old pipeline{pair.legacy_agent ? ` · ${pair.legacy_agent}` : ''}{pair.legacy_escalated ? ' · escalated' : ''}</div>
                <div className="sales-compare-text">{pair.legacy_reply || <em>No reply</em>}</div>
              </div>
              <div className="sales-compare-col sales-compare-new">
                <div className="sales-kpi-label">Sales assistant · {pair.sales_outcome || 'no draft'}{pair.sales_reply && pair.sales_reason ? ` · ${pair.sales_reason}` : ''}</div>
                <div className="sales-compare-text">{pair.sales_reply || <em>No draft{pair.sales_reason ? ` (${pair.sales_reason})` : ''}</em>}</div>
              </div>
            </div>
            {pair.rating ? (
              <div className="sales-kpi-hint">{RATING_LABEL[pair.rating]} · {pair.rated_by}{pair.rating_note ? ` — ${pair.rating_note}` : ''}</div>
            ) : canRate && pair.sales_reply && (
              <div className="sales-reply">
                <input type="text" aria-label="Note" placeholder="Why? (optional)" value={notes[pair.pair_id] || ''} onChange={(e) => setNotes({ ...notes, [pair.pair_id]: e.target.value })} style={{ flex: 1 }} />
                <Button variant="emerald" disabled={busy === pair.pair_id} onClick={() => rate(pair, 'better')}>Better</Button>
                <Button disabled={busy === pair.pair_id} onClick={() => rate(pair, 'same')}>Same</Button>
                <Button variant="rose" disabled={busy === pair.pair_id} onClick={() => rate(pair, 'worse')}>Worse</Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
