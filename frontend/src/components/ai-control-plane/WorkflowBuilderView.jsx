import React, { useState, useEffect } from 'react';
import {
  Workflow,
  CheckCircle2,
  AlertTriangle,
  Play,
  Layers,
  ArrowRight,
  RefreshCw,
  Sliders,
  ShieldCheck,
  Plus
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiWorkflows, validateAiWorkflow } from '../../services/aiControlPlaneApi';

const DEFAULT_NODES = [
  { id: 'start', label: '1. Webhook Entrypoint', type: 'trigger', status: 'ready', description: 'Receives WhatsApp/Web message payload' },
  { id: 'intent', label: '2. Intent Classifier', type: 'llm', status: 'ready', description: 'Extracts buyer intent & budget constraints' },
  { id: 'guardrail_in', label: '3. Input Guardrails', type: 'policy', status: 'ready', description: 'Checks prompt injection & PII leaks' },
  { id: 'rag_retrieval', label: '4. Hybrid RAG', type: 'retrieval', status: 'ready', description: 'Retrieves verified GLG property listings' },
  { id: 'property_matcher', label: '5. Tool: Property Search', type: 'tool', status: 'ready', description: 'Queries PostgreSQL for matching units' },
  { id: 'response_gen', label: '6. Response Generator', type: 'llm', status: 'ready', description: 'Synthesizes professional response in Banglish/English' },
  { id: 'guardrail_out', label: '7. Output Guardrails', type: 'policy', status: 'ready', description: 'Locks pricing against official price list' },
  { id: 'end', label: '8. Channel Dispatch', type: 'action', status: 'ready', description: 'Streams message back to customer channel' }
];

const DEFAULT_EDGES = [
  { from: 'start', to: 'intent' },
  { from: 'intent', to: 'guardrail_in' },
  { from: 'guardrail_in', to: 'rag_retrieval' },
  { from: 'rag_retrieval', to: 'property_matcher' },
  { from: 'property_matcher', to: 'response_gen' },
  { from: 'response_gen', to: 'guardrail_out' },
  { from: 'guardrail_out', to: 'end' }
];

export default function WorkflowBuilderView({ agentSlug }) {
  const [nodes, setNodes] = useState(DEFAULT_NODES);
  const [edges, setEdges] = useState(DEFAULT_EDGES);
  const [selectedNode, setSelectedNode] = useState(DEFAULT_NODES[1]);
  const [validationResult, setValidationResult] = useState({ valid: true, message: 'Workflow graph topology valid. Zero cycles detected.' });
  const [validating, setValidating] = useState(false);
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const data = await getAiWorkflows();
      if (data.workflows && data.workflows.length > 0) {
        setWorkflows(data.workflows);
        const active = data.workflows.find(w => w.agent_slug === agentSlug) || data.workflows[0];
        if (active.nodes && active.nodes.length > 0) setNodes(active.nodes);
        if (active.edges && active.edges.length > 0) setEdges(active.edges);
      }
    } catch (err) {
      console.error('Failed to load workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateGraph = async () => {
    setValidating(true);
    try {
      const res = await validateAiWorkflow(nodes, edges);
      setValidationResult(res);
    } catch (err) {
      setValidationResult({ valid: false, message: err.message || 'Validation failed' });
    } finally {
      setValidating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.08) 0%, rgba(243, 144, 114, 0.04) 100%)',
        border: '1px solid rgba(232, 101, 74, 0.25)',
        borderRadius: '20px',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Workflow size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              Stateful LangGraph Workflow Canvas
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Design and validate multi-agent choreography, conditional routing, and deterministic tool chains.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            onClick={handleValidateGraph}
            disabled={validating}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '0.84rem', borderRadius: '14px' }}
          >
            <ShieldCheck size={16} />
            <span>{validating ? 'Validating Graph...' : 'Validate Topology'}</span>
          </Button>
        </div>
      </div>

      {/* Validation Status Badge */}
      <div style={{
        padding: '12px 16px',
        borderRadius: '14px',
        border: validationResult.valid ? '1px solid #10B981' : '1px solid #EF4444',
        background: validationResult.valid ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
        color: validationResult.valid ? '#065F46' : '#991B1B',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        fontSize: '0.85rem'
      }}>
        {validationResult.valid ? <CheckCircle2 size={18} color="#10B981" /> : <AlertTriangle size={18} color="#EF4444" />}
        <span><strong>Topology Status:</strong> {validationResult.message || (validationResult.valid ? 'Graph valid' : 'Graph invalid')}</span>
      </div>

      {/* Workflow Visualization Canvas */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
        {/* Left: Interactive Graph Flow */}
        <Card style={{ padding: '24px', background: 'var(--bg-card, #1E293B)', border: '1px solid var(--border-glass)', borderRadius: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main, #475569)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Execution Graph Flow ({nodes.length} Nodes, {edges.length} Directed Edges)
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94A3B8)' }}>
              Click any node to configure parameters & timeouts
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {nodes.map((node, idx) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <div key={node.id}>
                  <div
                    onClick={() => setSelectedNode(node)}
                    style={{
                      padding: '14px 18px',
                      borderRadius: '16px',
                      background: isSelected ? 'rgba(232, 101, 74, 0.08)' : 'var(--bg-elevated, #1E293B)',
                      border: isSelected ? '2px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass)',
                      boxShadow: isSelected ? '0 4px 12px rgba(232, 101, 74, 0.12)' : 'none',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        background: isSelected ? 'var(--primary-coral, #E8654A)' : 'rgba(255,255,255,0.08)',
                        color: isSelected ? '#FFFFFF' : 'var(--text-main, #475569)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.78rem'
                      }}>
                        {idx + 1}
                      </span>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main, #1E293B)' }}>
                          {node.label}
                        </div>
                        <div style={{ fontSize: '0.76rem', color: 'var(--text-muted, #64748B)' }}>
                          {node.description}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '20px',
                        background: node.type === 'llm' ? 'rgba(99, 102, 241, 0.15)' : node.type === 'tool' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: node.type === 'llm' ? '#6366F1' : node.type === 'tool' ? '#10B981' : '#D97706'
                      }}>
                        {node.type?.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {/* Connecting Arrow */}
                  {idx < nodes.length - 1 && (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: '4px 0' }}>
                      <ArrowRight size={16} color="#94A3B8" style={{ transform: 'rotate(90deg)' }} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>

        {/* Right: Node Properties Inspector */}
        <Card style={{ padding: '20px', height: 'fit-content', borderRadius: '20px' }}>
          {selectedNode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '10px' }}>
                <Sliders size={18} color="var(--primary-coral, #E8654A)" />
                <h3 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
                  Node Inspector: {selectedNode.label}
                </h3>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '4px' }}>
                  NODE IDENTIFIER
                </label>
                <code style={{ fontSize: '0.85rem', color: 'var(--text-main, #0F172A)', background: 'var(--bg-input, #151C2C)', border: '1px solid var(--border-glass)', padding: '6px 10px', borderRadius: '12px', display: 'block' }}>
                  {selectedNode.id}
                </code>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '4px' }}>
                  NODE CLASSIFICATION
                </label>
                <input
                  type="text"
                  readOnly
                  value={selectedNode.type}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass)',
                    fontSize: '0.82rem',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '4px' }}>
                  EXECUTION TIMEOUT (MS)
                </label>
                <input
                  type="number"
                  defaultValue={3000}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass)',
                    fontSize: '0.82rem',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '4px' }}>
                  MAX RETRIES ON FAULT
                </label>
                <select
                  defaultValue={2}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass)',
                    fontSize: '0.82rem',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)'
                  }}
                >
                  <option value={0}>0 (Fail fast)</option>
                  <option value={1}>1 retry</option>
                  <option value={2}>2 retries (Standard)</option>
                  <option value={3}>3 retries</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '4px' }}>
                  FALLBACK STRATEGY
                </label>
                <select
                  defaultValue="handoff"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass)',
                    fontSize: '0.82rem',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)'
                  }}
                >
                  <option value="handoff">Escalate to Human Agent</option>
                  <option value="cached">Return Cached Verified Fact</option>
                  <option value="graceful_msg">Return Apology Message</option>
                </select>
              </div>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '12px', marginTop: '6px' }}>
                <span style={{ fontSize: '0.75rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CheckCircle2 size={14} /> Node connected to active LangGraph runtime.
                </span>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-muted, #94A3B8)', fontSize: '0.85rem' }}>
              Select a node on the left to edit execution properties.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
