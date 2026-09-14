import React, { useState, useEffect } from 'react';
import {
  Split,
  Plus,
  Play,
  Pause,
  Award,
  TrendingUp,
  CheckCircle2,
  Clock,
  Sliders,
  RefreshCw,
  Users,
  Activity,
  ArrowRight
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import {
  getAiExperiments,
  createAiExperiment,
  actOnAiExperiment
} from '../../services/aiControlPlaneApi';

export default function AbTestingView({ agentSlug }) {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [statusNotice, setStatusNotice] = useState(null);

  // New Experiment Form State
  const [newExp, setNewExp] = useState({
    name: 'Concierge Tone Optimization 2026',
    description: 'Testing high-luxury consultative tone vs direct pricing presentation',
    splitA: 50,
    splitB: 50,
    variant_a_prompt: 'v3.8.0',
    variant_a_temp: 0.2,
    variant_b_prompt: 'v3.9.0-candidate',
    variant_b_temp: 0.3
  });

  const loadExperiments = async () => {
    try {
      setLoading(true);
      const res = await getAiExperiments(agentSlug);
      setExperiments(res.experiments || []);
    } catch (err) {
      console.error('Failed to load experiments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExperiments();
  }, [agentSlug]);

  const handleAction = async (expId, action, winner = null) => {
    try {
      await actOnAiExperiment(expId, action, winner);
      setStatusNotice({ type: 'success', text: `Experiment updated: action "${action}" executed.` });
      loadExperiments();
    } catch (err) {
      setStatusNotice({ type: 'error', text: err.message || 'Action failed' });
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      setCreating(true);
      const payload = {
        name: newExp.name,
        description: newExp.description,
        agent_id: agentSlug || 'property_agent',
        test_type: 'PROMPT',
        traffic_split_a_pct: Number(newExp.splitA),
        traffic_split_b_pct: Number(newExp.splitB),
        variant_a_config: {
          prompt_version: newExp.variant_a_prompt,
          temperature: Number(newExp.variant_a_temp)
        },
        variant_b_config: {
          prompt_version: newExp.variant_b_prompt,
          temperature: Number(newExp.variant_b_temp)
        }
      };

      await createAiExperiment(payload);
      setStatusNotice({ type: 'success', text: 'Experiment created and queued!' });
      setShowCreateModal(false);
      loadExperiments();
    } catch (err) {
      setStatusNotice({ type: 'error', text: err.message || 'Failed to create experiment' });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-card, #FFFFFF)',
        padding: '16px 20px',
        borderRadius: '20px',
        border: '1px solid var(--border-glass)',
        boxShadow: '0 2px 6px rgba(0,0,0,0.02)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '14px',
            background: 'rgba(232, 101, 74, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--primary-coral, #E8654A)'
          }}>
            <Split size={22} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main, #0F172A)' }}>
              Live A/B Testing & Prompt Experiment Studio
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted, #64748B)' }}>
              Run live split traffic experiments evaluating conversion rate, customer sentiment, and grounding accuracy.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={loadExperiments}
            disabled={loading}
            style={{ borderRadius: '14px' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowCreateModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--primary-coral, #E8654A)',
              color: '#FFFFFF',
              borderRadius: '14px'
            }}
          >
            <Plus size={15} />
            <span>Create Experiment</span>
          </Button>
        </div>
      </div>

      {statusNotice && (
        <div style={{
          padding: '10px 16px',
          borderRadius: '14px',
          background: statusNotice.type === 'success' ? '#ECFDF5' : '#FEF2F2',
          border: statusNotice.type === 'success' ? '1px solid #A7F3D0' : '1px solid #FECACA',
          color: statusNotice.type === 'success' ? '#065F46' : '#991B1B',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span>{statusNotice.text}</span>
          <button
            onClick={() => setStatusNotice(null)}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontWeight: 700 }}
          >
            ×
          </button>
        </div>
      )}

      {/* Experiments List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted, #94A3B8)' }}>Loading experiments...</div>
        ) : experiments.length === 0 ? (
          <Card style={{ padding: '40px 20px', textAlign: 'center', borderRadius: '20px' }}>
            <Split size={36} style={{ color: '#94A3B8', marginBottom: '8px' }} />
            <h4 style={{ margin: 0, fontSize: '0.92rem', color: 'var(--text-main, #0F172A)' }}>No Active Experiments</h4>
            <p style={{ margin: '4px 0 16px 0', fontSize: '0.78rem', color: 'var(--text-muted, #64748B)' }}>
              Create an A/B test to scientifically compare two prompt or temperature variants.
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowCreateModal(true)}
              style={{ background: 'var(--primary-coral, #E8654A)', color: '#FFFFFF', borderRadius: '14px' }}
            >
              Create First A/B Test
            </Button>
          </Card>
        ) : (
          experiments.map((exp) => {
            const isRunning = exp.status === 'RUNNING';
            const isPaused = exp.status === 'PAUSED';
            const isCompleted = exp.status === 'COMPLETED';

            const splitA = exp.traffic_split_a_pct || 50;
            const splitB = exp.traffic_split_b_pct || 50;

            return (
              <Card key={exp.id} style={{ padding: '20px', borderRadius: '20px' }}>
                {/* Header Row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-main, #0F172A)' }}>
                        {exp.name}
                      </h3>
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '20px',
                        background: isRunning ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.08)',
                        color: isRunning ? '#10B981' : 'var(--text-muted, #64748B)'
                      }}>
                        {exp.status}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748B)' }}>
                        Agent: <b>{exp.agent_id}</b>
                      </span>
                    </div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.78rem', color: 'var(--text-muted, #64748B)' }}>
                      {exp.description}
                    </p>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isRunning && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleAction(exp.id, 'PAUSE')}
                        style={{ fontSize: '0.75rem', borderRadius: '14px' }}
                      >
                        <Pause size={13} style={{ marginRight: '4px' }} /> Pause
                      </Button>
                    )}
                    {isPaused && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleAction(exp.id, 'RESUME')}
                        style={{ fontSize: '0.75rem', borderRadius: '14px' }}
                      >
                        <Play size={13} style={{ marginRight: '4px' }} /> Resume
                      </Button>
                    )}
                    {!isCompleted && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleAction(exp.id, 'SELECT_WINNER', 'VARIANT_B')}
                        style={{
                          fontSize: '0.75rem',
                          background: 'var(--primary-coral, #E8654A)',
                          color: '#FFFFFF',
                          borderRadius: '14px'
                        }}
                      >
                        <Award size={13} style={{ marginRight: '4px' }} /> Promote Variant B
                      </Button>
                    )}
                  </div>
                </div>

                {/* Split Traffic Comparison Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  {/* Variant A (Baseline) */}
                  <div style={{
                    background: 'var(--bg-elevated, #1E293B)',
                    padding: '14px 16px',
                    borderRadius: '16px',
                    border: '1px solid var(--border-glass)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--text-main, #334155)' }}>
                        VARIANT A (Control Baseline)
                      </span>
                      <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#38BDF8' }}>
                        {splitA}% Traffic
                      </span>
                    </div>

                    <div style={{ fontSize: '0.76rem', color: 'var(--text-muted, #64748B)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div>Prompt: <b>{exp.variant_a_config?.prompt_version || 'v3.8.0'}</b></div>
                      <div>Temperature: <b>{exp.variant_a_config?.temperature ?? 0.2}</b></div>
                      <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '6px', marginTop: '4px' }}>
                        Conversion: <b style={{ color: 'var(--text-main, #0F172A)' }}>{exp.results?.variant_a?.conversion_pct || '18.4'}%</b> · P50: <b>310ms</b>
                      </div>
                    </div>
                  </div>

                  {/* Variant B (Challenger) */}
                  <div style={{
                    background: 'rgba(232, 101, 74, 0.08)',
                    padding: '14px 16px',
                    borderRadius: '16px',
                    border: '1px solid rgba(232, 101, 74, 0.25)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--primary-coral, #E8654A)' }}>
                        VARIANT B (Candidate)
                      </span>
                      <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--primary-coral, #E8654A)' }}>
                        {splitB}% Traffic
                      </span>
                    </div>

                    <div style={{ fontSize: '0.76rem', color: 'var(--text-muted, #64748B)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div>Prompt: <b>{exp.variant_b_config?.prompt_version || 'v3.9.0'}</b></div>
                      <div>Temperature: <b>{exp.variant_b_config?.temperature ?? 0.35}</b></div>
                      <div style={{ borderTop: '1px solid rgba(232, 101, 74, 0.2)', paddingTop: '6px', marginTop: '4px' }}>
                        Conversion: <b style={{ color: '#10B981' }}>{exp.results?.variant_b?.conversion_pct || '24.1'}%</b> · P50: <b>285ms</b>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>

      {/* Create Experiment Modal */}
      {showCreateModal && (
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create Live A/B Experiment"
        >
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main, #334155)', marginBottom: '4px' }}>
                Experiment Name *
              </label>
              <input
                type="text"
                required
                value={newExp.name}
                onChange={(e) => setNewExp({ ...newExp, name: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
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
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main, #334155)', marginBottom: '4px' }}>
                Hypothesis / Description
              </label>
              <textarea
                rows={2}
                value={newExp.description}
                onChange={(e) => setNewExp({ ...newExp, description: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div style={{ background: 'var(--bg-elevated, #1E293B)', padding: '12px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--text-main, #334155)', marginBottom: '6px' }}>
                  Variant A (Control)
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>Prompt Version</label>
                  <input
                    type="text"
                    value={newExp.variant_a_prompt}
                    onChange={(e) => setNewExp({ ...newExp, variant_a_prompt: e.target.value })}
                    style={{ width: '100%', padding: '6px 10px', fontSize: '0.8rem', borderRadius: '12px', border: '1px solid var(--border-glass)', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>Temperature</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={newExp.variant_a_temp}
                    onChange={(e) => setNewExp({ ...newExp, variant_a_temp: e.target.value })}
                    style={{ width: '100%', padding: '6px 10px', fontSize: '0.8rem', borderRadius: '12px', border: '1px solid var(--border-glass)', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ background: 'rgba(232, 101, 74, 0.08)', padding: '12px', borderRadius: '16px', border: '1px solid rgba(232, 101, 74, 0.25)' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--primary-coral, #E8654A)', marginBottom: '6px' }}>
                  Variant B (Candidate)
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>Prompt Version</label>
                  <input
                    type="text"
                    value={newExp.variant_b_prompt}
                    onChange={(e) => setNewExp({ ...newExp, variant_b_prompt: e.target.value })}
                    style={{ width: '100%', padding: '6px 10px', fontSize: '0.8rem', borderRadius: '12px', border: '1px solid var(--border-glass)', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>Temperature</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={newExp.variant_b_temp}
                    onChange={(e) => setNewExp({ ...newExp, variant_b_temp: e.target.value })}
                    style={{ width: '100%', padding: '6px 10px', fontSize: '0.8rem', borderRadius: '12px', border: '1px solid var(--border-glass)', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)', boxSizing: 'border-box' }}
                  />
                </div>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main, #334155)', marginBottom: '4px' }}>
                Traffic Split: {newExp.splitA}% / {newExp.splitB}%
              </label>
              <input
                type="range"
                min="10"
                max="90"
                step="10"
                value={newExp.splitA}
                onChange={(e) => {
                  const a = Number(e.target.value);
                  setNewExp({ ...newExp, splitA: a, splitB: 100 - a });
                }}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <Button
                variant="outline"
                size="sm"
                type="button"
                onClick={() => setShowCreateModal(false)}
                style={{ borderRadius: '14px' }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                type="submit"
                disabled={creating}
                style={{ background: 'var(--primary-coral, #E8654A)', color: '#FFFFFF', borderRadius: '14px' }}
              >
                {creating ? 'Starting...' : 'Start A/B Test'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
