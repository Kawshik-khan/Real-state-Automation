import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  Layers,
  Cpu,
  Search,
  ChevronRight,
  ShieldCheck,
  Terminal,
  Filter,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiTraces } from '../../services/aiControlPlaneApi';

export default function AiTracesView({ agentSlug }) {
  const [traces, setTraces] = useState([]);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [filterAgent, setFilterAgent] = useState(agentSlug || 'all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTraces = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAiTraces(50, filterAgent === 'all' ? null : filterAgent);
      const list = data.traces || [];
      setTraces(list);
      if (list.length > 0) {
        setSelectedTrace(list[0]);
      } else {
        setSelectedTrace(null);
      }
    } catch (err) {
      console.error('Failed to load traces:', err);
      setError(err.message || 'Failed to retrieve traces');
    } finally {
      setLoading(false);
    }
  }, [filterAgent]);

  useEffect(() => {
    fetchTraces();
  }, [fetchTraces]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.08) 0%, rgba(243, 144, 114, 0.04) 100%)',
        border: '1px solid rgba(232, 101, 74, 0.25)',
        borderRadius: '20px',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Activity size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              Distributed AI Execution Traces & Span Trees
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Inspect full lifecycle spans: guardrail latency, pgvector search, tool invocation, and token consumption.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={filterAgent}
            onChange={(e) => setFilterAgent(e.target.value)}
            style={{
              padding: '8px 14px',
              borderRadius: '14px',
              border: '1px solid var(--border-glass)',
              background: 'var(--bg-input, #151C2C)',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: 'var(--text-main, #F8FAFC)',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Agents</option>
            <option value="property_agent">Property Consultant</option>
            <option value="faq_agent">FAQ Advisor</option>
            <option value="supervisor">Supervisor Orchestrator</option>
            <option value="email_agent">Lead Concierge</option>
            <option value="social_bridge">Social Bridge</option>
          </select>

          <button
            onClick={fetchTraces}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '14px',
              background: 'var(--bg-card, #1E293B)',
              border: '1px solid var(--border-glass)',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: 'var(--text-main, #F8FAFC)',
              cursor: 'pointer'
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', borderRadius: '14px', background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Traces List & Span Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: '20px' }}>
        {/* Left: Traces List */}
        <Card style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '720px', overflowY: 'auto', borderRadius: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main, #1E293B)', textTransform: 'uppercase' }}>
              Execution Logs ({traces.length})
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748B)' }}>
              Last 50 Runs
            </span>
          </div>

          {loading && traces.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted, #94A3B8)', fontSize: '0.85rem' }}>
              Loading persisted traces...
            </div>
          ) : traces.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted, #94A3B8)', fontSize: '0.85rem' }}>
              No execution traces recorded yet. Run prompts in Playground to generate live traces.
            </div>
          ) : (
            traces.map((tr) => {
              const isSelected = selectedTrace?.trace_id === tr.trace_id || selectedTrace?.id === tr.id;
              const isSuccess = tr.status === 'SUCCESS';
              const isBlocked = tr.status === 'BLOCKED';

              return (
                <div
                  key={tr.trace_id || tr.id}
                  onClick={() => setSelectedTrace(tr)}
                  style={{
                    padding: '12px',
                    borderRadius: '14px',
                    border: isSelected ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass)',
                    background: isSelected ? 'rgba(232, 101, 74, 0.08)' : 'var(--bg-elevated, #1E293B)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      color: isSelected ? 'var(--primary-coral, #E8654A)' : 'var(--text-main, #0F172A)'
                    }}>
                      {tr.trace_id}
                    </span>
                    <span style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '20px',
                      background: isSuccess ? 'rgba(16, 185, 129, 0.15)' : isBlocked ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: isSuccess ? '#10B981' : isBlocked ? '#EF4444' : '#F59E0B'
                    }}>
                      {tr.status}
                    </span>
                  </div>

                  <p style={{
                    margin: '0 0 8px',
                    fontSize: '0.82rem',
                    color: 'var(--text-main, #CBD5E1)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {tr.user_query || 'Inquiry processed'}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>
                    <span>{tr.agent_id || 'property_agent'}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>{Math.round(tr.latency_ms || 0)}ms</span>
                      <span>•</span>
                      <span>৳{Number(tr.cost_bdt || 0).toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </Card>

        {/* Right: Span Inspector & Waterfall */}
        <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', borderRadius: '20px' }}>
          {selectedTrace ? (
            <>
              {/* Trace Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: '14px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'monospace', color: 'var(--text-main, #0F172A)' }}>
                      {selectedTrace.trace_id}
                    </span>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '20px',
                      background: selectedTrace.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: selectedTrace.status === 'SUCCESS' ? '#10B981' : '#EF4444'
                    }}>
                      {selectedTrace.status}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.76rem', color: 'var(--text-muted, #64748B)' }}>
                    Agent: <strong>{selectedTrace.agent_id}</strong> | Model: <strong>{selectedTrace.model_used}</strong> | Channel: {selectedTrace.channel || 'Playground'}
                  </span>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--primary-coral, #E8654A)' }}>
                    {Math.round(selectedTrace.latency_ms || 0)}ms
                  </div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted, #64748B)' }}>
                    {selectedTrace.total_tokens || 0} tokens | ৳{Number(selectedTrace.cost_bdt || 0).toFixed(4)} BDT
                  </div>
                </div>
              </div>

              {/* User Query & Response Box */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ padding: '14px', borderRadius: '16px', background: 'var(--bg-elevated, #1E293B)', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', textTransform: 'uppercase' }}>
                    User Query
                  </span>
                  <p style={{ margin: '6px 0 0', fontSize: '0.84rem', color: 'var(--text-main, #1E293B)' }}>
                    {selectedTrace.user_query}
                  </p>
                </div>
                <div style={{ padding: '14px', borderRadius: '16px', background: 'var(--bg-elevated, #1E293B)', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', textTransform: 'uppercase' }}>
                    Agent Response
                  </span>
                  <p style={{ margin: '6px 0 0', fontSize: '0.84rem', color: 'var(--text-main, #1E293B)', maxHeight: '120px', overflowY: 'auto' }}>
                    {selectedTrace.agent_response}
                  </p>
                </div>
              </div>

              {/* Spans Waterfall Tree */}
              <div>
                <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-main, #1E293B)', textTransform: 'uppercase', marginBottom: '10px', display: 'block' }}>
                  Execution Spans Waterfall ({selectedTrace.spans?.length || 0} Spans)
                </span>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(selectedTrace.spans || []).map((sp, idx) => {
                    const totalDuration = Math.max(1, selectedTrace.latency_ms || 1);
                    const spanDuration = sp.latency_ms || 10;
                    const widthPct = Math.min(100, Math.max(5, (spanDuration / totalDuration) * 100));

                    return (
                      <div
                        key={sp.span_id || idx}
                        style={{
                          padding: '12px 14px',
                          borderRadius: '14px',
                          background: 'var(--bg-elevated, #1E293B)',
                          border: '1px solid var(--border-glass)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-main, #1E293B)' }}>
                            {sp.name}
                          </span>
                          <span style={{ fontWeight: 700, color: 'var(--text-muted, #64748B)', fontSize: '0.78rem' }}>
                            {Math.round(spanDuration)}ms
                          </span>
                        </div>

                        {/* Waterfall Duration Bar */}
                        <div style={{ height: '6px', width: '100%', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{
                            height: '100%',
                            width: `${widthPct}%`,
                            background: sp.status === 'BLOCKED' ? '#EF4444' : 'var(--primary-coral, #E8654A)',
                            borderRadius: '3px'
                          }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted, #94A3B8)' }}>
              Select a trace from the left panel to inspect detailed execution spans.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
