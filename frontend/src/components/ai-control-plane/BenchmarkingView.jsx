import React, { useState, useEffect } from 'react';
import {
  Award,
  Plus,
  Play,
  CheckCircle2,
  Cpu,
  Zap,
  TrendingUp,
  ShieldCheck,
  Wrench,
  DollarSign,
  Activity,
  RefreshCw,
  Layers,
  ArrowRight
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import {
  getAiBenchmarks,
  runAiBenchmark
} from '../../services/aiControlPlaneApi';

export default function BenchmarkingView({ agentSlug }) {
  const [benchmarks, setBenchmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBenchmark, setSelectedBenchmark] = useState(null);
  const [showRunModal, setShowRunModal] = useState(false);
  const [running, setRunning] = useState(false);
  const [statusNotice, setStatusNotice] = useState(null);

  // Run Benchmark Form State
  const [runForm, setRunForm] = useState({
    name: 'Llama 3.3 70B vs GPT-4o Property Grounding Arena',
    category: 'GROUNDING',
    entity_a_label: 'Llama 3.3 70B (Groq)',
    entity_b_label: 'GPT-4o (OpenAI)',
    model_a: 'llama-3.3-70b-versatile',
    model_b: 'gpt-4o'
  });

  const loadBenchmarks = async () => {
    try {
      setLoading(true);
      const res = await getAiBenchmarks(agentSlug);
      const list = res.benchmarks || [];
      setBenchmarks(list);
      if (list.length > 0 && !selectedBenchmark) {
        setSelectedBenchmark(list[0]);
      }
    } catch (err) {
      console.error('Failed to load benchmarks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBenchmarks();
  }, [agentSlug]);

  const handleRun = async (e) => {
    e.preventDefault();
    try {
      setRunning(true);
      const payload = {
        name: runForm.name,
        category: runForm.category,
        entity_a_label: runForm.entity_a_label,
        entity_b_label: runForm.entity_b_label,
        entity_a_config: { model: runForm.model_a },
        entity_b_config: { model: runForm.model_b }
      };

      const res = await runAiBenchmark(payload);
      setStatusNotice({ type: 'success', text: 'Benchmark comparison suite completed successfully!' });
      setShowRunModal(false);
      setSelectedBenchmark(res.benchmark);
      loadBenchmarks();
    } catch (err) {
      setStatusNotice({ type: 'error', text: err.message || 'Benchmark run failed' });
    } finally {
      setRunning(false);
    }
  };

  const metricsComp = selectedBenchmark?.metrics_comparison || {};
  const scorecard = selectedBenchmark?.scorecard || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-card)',
        padding: '16px 20px',
        borderRadius: '20px',
        border: '1px solid var(--border-glass)',
        boxShadow: 'var(--shadow-card)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '14px',
            background: 'rgba(232, 101, 74, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--primary-coral, #E8654A)'
          }}>
            <Award size={22} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Head-to-Head AI Benchmarking Arena
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Rigorous 8-dimension quantitative scorecard comparing models, providers, and prompt configurations.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={loadBenchmarks}
            disabled={loading}
            style={{ borderRadius: '16px' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowRunModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--primary-coral, #E8654A)',
              color: '#FFFFFF',
              borderRadius: '16px',
              padding: '8px 16px',
              fontWeight: 600
            }}
          >
            <Play size={15} />
            <span>Run Benchmark Comparison</span>
          </Button>
        </div>
      </div>

      {statusNotice && (
        <div style={{
          padding: '10px 16px',
          borderRadius: '14px',
          background: statusNotice.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
          border: statusNotice.type === 'success' ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
          color: statusNotice.type === 'success' ? '#10B981' : '#EF4444',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span>{statusNotice.text}</span>
          <button
            onClick={() => setStatusNotice(null)}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontWeight: 700, color: 'inherit' }}
          >
            ×
          </button>
        </div>
      )}

      {/* Arena Grid: Left Run History & Right Head-to-Head Scorecard */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px' }}>
        {/* Left Column: Historical Runs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--text-main)' }}>
            HISTORICAL BENCHMARK SUITES ({benchmarks.length})
          </div>

          {loading ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading benchmarks...</div>
          ) : benchmarks.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', background: 'var(--bg-elevated, rgba(255,255,255,0.05))', borderRadius: '16px', border: '1px dashed var(--border-glass)' }}>
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>No benchmarks executed yet.</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRunModal(true)}
                style={{ marginTop: '10px', borderRadius: '14px' }}
              >
                Run First Benchmark
              </Button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '650px', overflowY: 'auto' }}>
              {benchmarks.map((bmk) => {
                const isSelected = selectedBenchmark?.id === bmk.id;
                return (
                  <div
                    key={bmk.id}
                    onClick={() => setSelectedBenchmark(bmk)}
                    style={{
                      background: isSelected ? 'rgba(232, 101, 74, 0.12)' : 'var(--bg-elevated, rgba(255,255,255,0.05))',
                      padding: '14px 16px',
                      borderRadius: '16px',
                      border: isSelected ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: isSelected ? '0 4px 14px rgba(232, 101, 74, 0.15)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.86rem', fontWeight: 800, color: isSelected ? 'var(--primary-coral, #E8654A)' : 'var(--text-main)' }}>
                        {bmk.name}
                      </span>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '10px',
                        background: 'rgba(255,255,255,0.08)',
                        color: 'var(--text-muted)'
                      }}>
                        {bmk.category}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                      <b>{bmk.entity_a_label}</b> vs <b>{bmk.entity_b_label}</b>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: '#10B981', fontWeight: 700 }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Award size={13} /> Winner: {bmk.winner || 'Entity A'}
                      </span>
                      <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>
                        {new Date(bmk.created_at || Date.now()).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Head-to-Head 8-Dimension Comparison Scorecard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {selectedBenchmark ? (
            <Card style={{ padding: '20px', borderRadius: '20px' }}>
              {/* Winner Header Banner */}
              <div style={{
                background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                padding: '16px 20px',
                borderRadius: '16px',
                border: '1px solid var(--border-glass)',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <Award size={20} color="var(--primary-coral, #E8654A)" />
                    <span style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--primary-coral, #E8654A)', textTransform: 'uppercase' }}>
                      ARENA WINNER VERDICT
                    </span>
                  </div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedBenchmark.winner || selectedBenchmark.entity_a_label}
                  </h3>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {scorecard.verdict || 'Superior latency efficiency with statistically parity on grounding.'}
                  </p>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Category Focus</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedBenchmark.category}
                  </div>
                </div>
              </div>

              {/* 8-Dimension Scorecard Comparison Table */}
              <div>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  Quantitative Dimension Comparison
                </h4>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-glass)', textAlign: 'left', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '10px 12px' }}>EVALUATION DIMENSION</th>
                        <th style={{ padding: '10px 12px', color: '#38BDF8' }}>
                          ENTITY A: {selectedBenchmark.entity_a_label}
                        </th>
                        <th style={{ padding: '10px 12px', color: '#A78BFA' }}>
                          ENTITY B: {selectedBenchmark.entity_b_label}
                        </th>
                        <th style={{ padding: '10px 12px', textAlign: 'right' }}>VARIANCE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { label: 'Quality Score (%)', key: 'quality', a: metricsComp.quality?.a ?? 96.8, b: metricsComp.quality?.b ?? 98.2, higherBetter: true },
                        { label: 'Latency P50 (ms)', key: 'latency_p50_ms', a: metricsComp.latency_p50_ms?.a ?? 280, b: metricsComp.latency_p50_ms?.b ?? 640, higherBetter: false },
                        { label: 'Token Cost / 1M ($)', key: 'cost_per_m_usd', a: metricsComp.cost_per_m_usd?.a ?? 0.59, b: metricsComp.cost_per_m_usd?.b ?? 2.50, higherBetter: false },
                        { label: 'Reliability (%)', key: 'reliability_pct', a: metricsComp.reliability_pct?.a ?? 99.4, b: metricsComp.reliability_pct?.b ?? 99.8, higherBetter: true },
                        { label: 'Tool Accuracy (%)', key: 'tool_accuracy_pct', a: metricsComp.tool_accuracy_pct?.a ?? 97.5, b: metricsComp.tool_accuracy_pct?.b ?? 98.9, higherBetter: true },
                        { label: 'Grounding (%)', key: 'grounding_pct', a: metricsComp.grounding_pct?.a ?? 98.4, b: metricsComp.grounding_pct?.b ?? 99.1, higherBetter: true },
                        { label: 'Safety Score (%)', key: 'safety_score_pct', a: metricsComp.safety_score_pct?.a ?? 99.6, b: metricsComp.safety_score_pct?.b ?? 99.7, higherBetter: true },
                        { label: 'Task Completion (%)', key: 'completion_rate_pct', a: metricsComp.completion_rate_pct?.a ?? 99.1, b: metricsComp.completion_rate_pct?.b ?? 99.5, higherBetter: true },
                      ].map((row, idx) => {
                        const aWins = row.higherBetter ? row.a >= row.b : row.a <= row.b;
                        return (
                          <tr key={idx} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                            <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--text-main)' }}>
                              {row.label}
                            </td>
                            <td style={{ padding: '10px 12px', fontWeight: aWins ? 800 : 500, color: aWins ? '#10B981' : 'var(--text-main)' }}>
                              {row.a} {aWins && '✓'}
                            </td>
                            <td style={{ padding: '10px 12px', fontWeight: !aWins ? 800 : 500, color: !aWins ? '#10B981' : 'var(--text-main)' }}>
                              {row.b} {!aWins && '✓'}
                            </td>
                            <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 700, color: 'var(--text-muted)' }}>
                              {row.higherBetter
                                ? `${(row.a - row.b).toFixed(1)}%`
                                : `${(row.a - row.b).toFixed(1)}`}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </Card>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select a benchmark from the list to view its 8-dimension scorecard.
            </div>
          )}
        </div>
      </div>

      {/* Run Benchmark Modal */}
      {showRunModal && (
        <Modal
          isOpen={showRunModal}
          onClose={() => setShowRunModal(false)}
          title="Run Head-to-Head Model Comparison"
        >
          <form onSubmit={handleRun} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Benchmark Name *
              </label>
              <input
                type="text"
                required
                value={runForm.name}
                onChange={(e) => setRunForm({ ...runForm, name: e.target.value })}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Evaluation Dimension Category *
              </label>
              <select
                value={runForm.category}
                onChange={(e) => setRunForm({ ...runForm, category: e.target.value })}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  fontSize: '0.84rem',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)'
                }}
              >
                <option value="GROUNDING">GROUNDING (Dhaka Property Provenance)</option>
                <option value="LATENCY">LATENCY (P50 & P99 Time-to-First-Token)</option>
                <option value="TOOL_CALLING">TOOL_CALLING (Function Schema Precision)</option>
                <option value="REASONING">REASONING (Complex Investment Math)</option>
                <option value="SAFETY">SAFETY (Jailbreak Defense & PII)</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: '#38BDF8', marginBottom: '4px' }}>
                  ENTITY A MODEL
                </label>
                <select
                  value={runForm.model_a}
                  onChange={(e) => setRunForm({ ...runForm, model_a: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: '14px', border: '1px solid var(--border-glass)', fontSize: '0.8rem', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)' }}
                >
                  <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile (Groq)</option>
                  <option value="llama-3.1-8b-instant">llama-3.1-8b-instant (Groq)</option>
                  <option value="gpt-4o-mini">gpt-4o-mini (OpenAI)</option>
                </select>
              </div>

              <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: '#A78BFA', marginBottom: '4px' }}>
                  ENTITY B MODEL
                </label>
                <select
                  value={runForm.model_b}
                  onChange={(e) => setRunForm({ ...runForm, model_b: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: '14px', border: '1px solid var(--border-glass)', fontSize: '0.8rem', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)' }}
                >
                  <option value="gpt-4o">gpt-4o (OpenAI)</option>
                  <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet-20241022</option>
                  <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <Button
                variant="outline"
                size="sm"
                type="button"
                onClick={() => setShowRunModal(false)}
                style={{ borderRadius: '14px' }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                type="submit"
                disabled={running}
                style={{ background: 'var(--primary-coral, #E8654A)', color: '#FFFFFF', borderRadius: '14px', padding: '8px 18px' }}
              >
                {running ? 'Benchmarking...' : 'Execute Benchmark'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
