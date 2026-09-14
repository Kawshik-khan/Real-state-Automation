import React, { useState, useEffect } from 'react';
import { Route, Play, Zap, ArrowRight, ShieldCheck, DollarSign, Clock } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiRoutingRules, simulateAiRouting } from '../../services/aiControlPlaneApi';

export default function ModelRoutingView() {
  const [rules, setRules] = useState([]);
  const [task, setTask] = useState('classification');
  const [complexity, setComplexity] = useState('low');
  const [agentSlug, setAgentSlug] = useState('supervisor');
  const [simulation, setSimulation] = useState(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const res = await getAiRoutingRules();
      if (res.rules) setRules(res.rules);
    } catch (err) {
      console.debug('Failed to load routing rules:', err);
    }
  };

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      const res = await simulateAiRouting(task, complexity, agentSlug);
      setSimulation(res);
    } catch (err) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ margin: '0 0 4px', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
          Intelligent Model Routing Engine
        </h2>
        <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-muted, #64748B)' }}>
          Route tasks dynamically based on complexity, task domain, latency thresholds, and cost budgets.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
        {/* Left: Active Routing Rules */}
        <Card title="Active Routing Rules" subtitle="Evaluated in sequential priority order" style={{ borderRadius: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {rules.map(r => (
              <div
                key={r.id}
                style={{
                  padding: '14px 16px',
                  borderRadius: '16px',
                  background: 'var(--bg-elevated, #1E293B)',
                  border: '1px solid var(--border-glass, rgba(255,255,255,0.06))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.74rem', padding: '2px 8px', borderRadius: '20px', background: 'var(--primary-coral, #E8654A)', color: '#FFF', fontWeight: 700 }}>
                      #{r.priority}
                    </span>
                    <strong style={{ fontSize: '0.86rem', color: 'var(--text-main, #1E293B)' }}>{r.name}</strong>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748B)' }}>
                    Condition: <code>{r.condition_task || '*'}</code> | Complexity: <code>{r.condition_complexity || '*'}</code>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ArrowRight size={14} color="var(--text-muted, #94A3B8)" />
                  <span style={{
                    fontSize: '0.74rem',
                    padding: '3px 10px',
                    borderRadius: '20px',
                    background: 'rgba(59, 130, 246, 0.12)',
                    color: '#3B82F6',
                    border: '1px solid rgba(59, 130, 246, 0.25)',
                    fontWeight: 700
                  }}>
                    {r.target_model_id}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Right: Decision Simulator */}
        <Card title="Decision Simulator" subtitle="Test route determination for specific prompt parameters" style={{ borderRadius: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #1E293B)' }}>Task Type</label>
              <select
                value={task}
                onChange={e => setTask(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem'
                }}
              >
                <option value="classification">Intent Classification</option>
                <option value="recommendation">Property Recommendation</option>
                <option value="complex_analysis">Complex Financial / Legal Analysis</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #1E293B)' }}>Complexity Tier</label>
              <select
                value={complexity}
                onChange={e => setComplexity(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem'
                }}
              >
                <option value="low">Low (&lt;200 tokens)</option>
                <option value="medium">Medium (Standard Dialog)</option>
                <option value="high">High (Multi-document Synthesis)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #1E293B)' }}>Target Agent</label>
              <select
                value={agentSlug}
                onChange={e => setAgentSlug(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem'
                }}
              >
                <option value="supervisor">Supervisor Intent Classifier</option>
                <option value="property_agent">Property Consultant Agent</option>
                <option value="email_agent">Lead & Email Concierge</option>
              </select>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={handleSimulate}
              loading={simulating}
              icon={Play}
              style={{ borderRadius: '14px', padding: '10px 16px' }}
            >
              Simulate Route
            </Button>

            {simulation && (
              <div style={{
                marginTop: '8px',
                padding: '14px',
                borderRadius: '16px',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                fontSize: '0.78rem'
              }}>
                <div style={{ fontWeight: 700, color: '#10B981', marginBottom: '4px' }}>
                  Routed to: {simulation.selected_model}
                </div>
                <div style={{ color: 'var(--text-muted, #64748B)', marginBottom: '6px' }}>
                  {simulation.reason}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, color: 'var(--text-main, #1E293B)' }}>
                  <span>Est. Cost: ৳{simulation.expected_cost_bdt} BDT</span>
                  <span>Est. Latency: {simulation.expected_latency_ms}ms</span>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
