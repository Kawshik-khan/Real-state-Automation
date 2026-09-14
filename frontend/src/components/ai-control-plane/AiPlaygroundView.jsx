import React, { useState } from 'react';
import {
  Play,
  Send,
  Sparkles,
  Layers,
  Cpu,
  Clock,
  Zap,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  FileText,
  Copy,
  Check
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { runAiPlayground } from '../../services/aiControlPlaneApi';

export default function AiPlaygroundView({
  agentSlug,
  selectedAgentSlug,
  agents = [],
  models = [],
  onOpenEvalDataset
}) {
  const currentSlug = selectedAgentSlug || agentSlug || 'property_agent';
  const activeAgent = agents.find(a => a.slug === currentSlug) || agents[0] || {};

  const [userQuery, setUserQuery] = useState('What are the available 3 BHK penthouses and handover timeline for GLG Sky Tower in Banani?');
  const [modelOverride, setModelOverride] = useState('');
  const [temperature, setTemperature] = useState(0.2);
  const [ragEnabled, setRagEnabled] = useState(true);
  const [running, setRunning] = useState(false);
  const [traceResult, setTraceResult] = useState(null);
  const [isTraceDrawerOpen, setIsTraceDrawerOpen] = useState(true);
  const [copied, setCopied] = useState(false);

  const handleRun = async () => {
    if (!userQuery.trim()) return;
    setRunning(true);
    try {
      const res = await runAiPlayground({
        agent_slug: currentSlug,
        user_message: userQuery,
        model_override: modelOverride || undefined,
        temperature_override: temperature,
        rag_enabled: ragEnabled
      });
      setTraceResult(res);
      setIsTraceDrawerOpen(true);
    } catch (err) {
      alert(`Playground execution error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const copyReply = () => {
    if (!traceResult?.agent_response) return;
    navigator.clipboard.writeText(traceResult.agent_response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div>
        <h2 style={{ margin: '0 0 4px', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
          Interactive AI Agent Playground
        </h2>
        <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-muted, #64748B)' }}>
          Sandbox testing environment with live span tree introspection, token accounting, and RAG grounding verification.
        </p>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', alignItems: 'start' }}>
        {/* Left Column: Sandbox Controls */}
        <Card title="Runtime Controls" subtitle={`Agent: ${activeAgent.name || activeAgent.slug || currentSlug}`}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #F1F5F9)' }}>Model Override</label>
              <select
                value={modelOverride || activeAgent.primary_model_id || activeAgent.primary_model || 'llama-3.3-70b-versatile'}
                onChange={e => setModelOverride(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.86rem',
                  outline: 'none'
                }}
              >
                <option value="llama-3.3-70b-versatile">Groq LLaMA 3.3 70B (Fast)</option>
                <option value="llama-3.1-8b-instant">Groq LLaMA 3.1 8B (Fallback)</option>
                <option value="gpt-4o">OpenAI GPT-4o (Flagship)</option>
                <option value="claude-3-5-sonnet-20241022">Anthropic Claude 3.5 Sonnet</option>
              </select>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main, #F1F5F9)' }}>Temperature</label>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-coral, #E8654A)' }}>{temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={e => setTemperature(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--primary-coral, #E8654A)' }}
              />
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: '14px',
              background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
              border: '1px solid var(--border-glass, rgba(255,255,255,0.08))'
            }}>
              <div>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', color: 'var(--text-main, #F1F5F9)' }}>Hybrid RAG Retrieval</span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted, #94A3B8)' }}>Inject verified brochure facts</span>
              </div>
              <input
                type="checkbox"
                checked={ragEnabled}
                onChange={e => setRagEnabled(e.target.checked)}
                style={{ accentColor: 'var(--primary-coral, #E8654A)', cursor: 'pointer', width: '16px', height: '16px' }}
              />
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={handleRun}
              loading={running}
              icon={Play}
              style={{ borderRadius: '16px', padding: '11px 18px', fontWeight: 700 }}
            >
              Run Agent Query
            </Button>
          </div>
        </Card>

        {/* Right Column: Interactive Chat & Reply */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card title="Conversation Simulator" subtitle="Live prompt exchange with active agent">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #F1F5F9)' }}>Customer Prompt</label>
                <textarea
                  rows={3}
                  value={userQuery}
                  onChange={e => setUserQuery(e.target.value)}
                  placeholder="Enter message to test agent behavior..."
                  style={{
                    width: '100%',
                    padding: '14px 16px',
                    borderRadius: '16px',
                    border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)',
                    fontSize: '0.86rem',
                    outline: 'none',
                    resize: 'vertical'
                  }}
                />
              </div>

              {traceResult && (
                <div style={{
                  padding: '16px 18px',
                  borderRadius: '16px',
                  background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                  border: '1px solid var(--border-glass, rgba(255,255,255,0.1))'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--primary-coral, #E8654A)' }}>
                        AGENT RESPONSE
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted, #94A3B8)' }}>
                        via {traceResult.model_used}
                      </span>
                    </div>

                    <button
                      onClick={copyReply}
                      style={{
                        padding: '4px 10px',
                        borderRadius: '12px',
                        border: '1px solid var(--border-glass, rgba(255,255,255,0.15))',
                        background: 'transparent',
                        color: 'var(--text-main, #CBD5E1)',
                        fontSize: '0.72rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}
                    >
                      {copied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
                      <span>{copied ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>

                  <p style={{ margin: 0, fontSize: '0.88rem', lineHeight: 1.55, color: 'var(--text-main, #F1F5F9)', whiteSpace: 'pre-wrap' }}>
                    {traceResult.agent_response}
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Bottom Trace Drawer (Span Tree) */}
      {traceResult && (
        <Card
          title={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>Execution Trace — {traceResult.trace_id}</span>
                <span style={{
                  fontSize: '0.74rem',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  background: 'rgba(16, 185, 129, 0.1)',
                  color: '#10B981',
                  fontWeight: 700
                }}>
                  {traceResult.status} ({traceResult.latency_ms}ms)
                </span>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted, #64748B)' }}>
                  Tokens: {traceResult.total_tokens} | Cost: ৳{traceResult.cost_bdt} BDT
                </span>
              </div>
              <button
                onClick={() => setIsTraceDrawerOpen(!isTraceDrawerOpen)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted, #64748B)' }}
              >
                {isTraceDrawerOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
            </div>
          }
        >
          {isTraceDrawerOpen && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', letterSpacing: '0.5px' }}>
                HIERARCHICAL EXECUTION SPANS
              </span>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {(traceResult.spans || []).map((span, idx) => (
                  <div
                    key={span.span_id || idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      borderRadius: '12px',
                      background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                      border: '1px solid var(--border-glass, rgba(255,255,255,0.08))',
                      fontSize: '0.8rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: 'var(--primary-coral, #E8654A)', fontWeight: 700 }}>#{idx + 1}</span>
                      <span style={{ fontWeight: 600, color: 'var(--text-main, #F1F5F9)' }}>{span.name}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ color: 'var(--text-muted, #94A3B8)' }}>{span.latency_ms}ms</span>
                      <span style={{
                        fontSize: '0.68rem',
                        padding: '2px 8px',
                        borderRadius: '10px',
                        background: span.status === 'OK' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: span.status === 'OK' ? '#10B981' : '#EF4444',
                        fontWeight: 700
                      }}>
                        {span.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* RAG Retrieved Chunks Provenance */}
              {traceResult.rag_retrievals && traceResult.rag_retrievals.length > 0 && (
                <div style={{ marginTop: '10px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted, #94A3B8)', display: 'block', marginBottom: '6px' }}>
                    RETRIEVED GROUNDING DOCUMENTS
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {traceResult.rag_retrievals.map((chk, i) => (
                      <div
                        key={chk.chunk_id || i}
                        style={{
                          padding: '12px 14px',
                          borderRadius: '14px',
                          background: 'rgba(59, 130, 246, 0.08)',
                          border: '1px solid rgba(59, 130, 246, 0.2)',
                          fontSize: '0.78rem'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <strong style={{ color: '#60A5FA' }}>{chk.document_name} (Page {chk.page})</strong>
                          <span style={{ color: 'var(--text-muted, #94A3B8)' }}>Similarity Score: {(chk.score * 100).toFixed(0)}%</span>
                        </div>
                        <p style={{ margin: 0, color: 'var(--text-main, #F1F5F9)', lineHeight: 1.4 }}>{chk.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
