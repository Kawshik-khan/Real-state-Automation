import React, { useState, useEffect } from 'react';
import {
  Scale,
  Plus,
  Play,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Code,
  Zap,
  RefreshCw,
  Terminal,
  FileCode,
  Lock,
  ArrowRight
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import {
  getAiPolicies,
  createAiPolicy,
  simulateAiPolicy
} from '../../services/aiControlPlaneApi';

export default function PolicyEngineView() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [statusNotice, setStatusNotice] = useState(null);

  // New Policy Form State
  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    condition_expression: 'price_bdt > 50000000 and location == "Banani"',
    action: 'HUMAN_APPROVAL',
    priority: 10
  });

  // Simulator State
  const [simExpression, setSimExpression] = useState("price_bdt > 50000000 and location == 'Banani'");
  const [simContextStr, setSimContextStr] = useState(JSON.stringify({ price_bdt: 60000000, location: 'Banani' }, null, 2));
  const [simResult, setSimResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const res = await getAiPolicies();
      setPolicies(res.policies || []);
    } catch (err) {
      console.error('Failed to load policies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      setCreating(true);
      const payload = {
        name: newPolicy.name,
        description: newPolicy.description,
        condition_expression: newPolicy.condition_expression,
        action: newPolicy.action,
        priority: Number(newPolicy.priority)
      };

      await createAiPolicy(payload);
      setStatusNotice({ type: 'success', text: `Policy "${newPolicy.name}" added successfully!` });
      setShowCreateModal(false);
      setNewPolicy({
        name: '',
        description: '',
        condition_expression: 'price_bdt > 50000000 and location == "Banani"',
        action: 'HUMAN_APPROVAL',
        priority: 10
      });
      loadPolicies();
    } catch (err) {
      setStatusNotice({ type: 'error', text: err.message || 'Failed to create policy' });
    } finally {
      setCreating(false);
    }
  };

  const handleSimulate = async () => {
    try {
      setSimulating(true);
      let parsedContext = {};
      try {
        parsedContext = JSON.parse(simContextStr);
      } catch {
        throw new Error('Invalid JSON format in test context');
      }

      const res = await simulateAiPolicy({
        condition_expression: simExpression,
        context: parsedContext
      });
      setSimResult(res);
    } catch (err) {
      setSimResult({ error: err.message });
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
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
            <Scale size={22} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Governance Policy Engine & Condition Rules
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Condition-action logic enforcing company discounts, legal boundaries, and supervisory escalations.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={loadPolicies}
            disabled={loading}
            style={{ borderRadius: '16px' }}
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
              borderRadius: '16px',
              padding: '8px 16px',
              fontWeight: 600
            }}
          >
            <Plus size={15} />
            <span>Create Rule</span>
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

      {/* Main Grid: Policy Rules Table & Policy Simulation Sandbox */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* Left Column: Active Rules */}
        <Card style={{ padding: '20px', borderRadius: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Enforced Policy Rules ({policies.length})
            </h3>
            <span style={{ fontSize: '0.74rem', color: '#10B981', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldCheck size={14} /> Real-Time Interception Active
            </span>
          </div>

          {loading ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading policy rules...</div>
          ) : policies.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>No policies defined.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {policies.map((p) => {
                const isBlock = p.action === 'BLOCK';
                const isApproval = p.action === 'HUMAN_APPROVAL';
                const actionBg = isBlock ? 'rgba(239, 68, 68, 0.15)' : isApproval ? 'rgba(245, 158, 11, 0.15)' : 'rgba(59, 130, 246, 0.15)';
                const actionColor = isBlock ? '#F87171' : isApproval ? '#FBBF24' : '#60A5FA';

                return (
                  <div
                    key={p.id}
                    style={{
                      background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                      padding: '14px 16px',
                      borderRadius: '16px',
                      border: '1px solid var(--border-glass)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-main)' }}>
                        {p.name}
                      </span>
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '3px 10px',
                        borderRadius: '12px',
                        background: actionBg,
                        color: actionColor
                      }}>
                        {p.action}
                      </span>
                    </div>

                    <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                      {p.description}
                    </p>

                    <div style={{
                      background: 'rgba(0, 0, 0, 0.35)',
                      color: '#38BDF8',
                      padding: '8px 12px',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      border: '1px solid var(--border-glass)'
                    }}>
                      <code>{p.condition_expression}</code>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        {/* Right Column: Real-Time Policy Simulation Sandbox */}
        <Card style={{ padding: '20px', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={18} color="var(--primary-coral, #E8654A)" />
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Policy Evaluation Sandbox
            </h3>
          </div>

          <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--text-muted)' }}>
            Simulate arbitrary payloads against conditional rules before publishing to production agents.
          </p>

          <div>
            <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              Condition Expression
            </label>
            <input
              type="text"
              value={simExpression}
              onChange={(e) => setSimExpression(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)',
                fontSize: '0.82rem',
                fontFamily: 'monospace',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              Test Evaluation Context (JSON)
            </label>
            <textarea
              rows={4}
              value={simContextStr}
              onChange={(e) => setSimContextStr(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)',
                fontSize: '0.8rem',
                fontFamily: 'monospace',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={handleSimulate}
            disabled={simulating}
            style={{
              background: 'var(--primary-coral, #E8654A)',
              color: '#FFFFFF',
              fontWeight: 700,
              borderRadius: '14px',
              padding: '9px 16px'
            }}
          >
            {simulating ? 'Evaluating...' : 'Run Simulation Test'}
          </Button>

          {/* Simulation Output Result */}
          {simResult && (
            <div style={{
              background: simResult.error ? 'rgba(239, 68, 68, 0.1)' : simResult.triggered ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-elevated)',
              border: `1px solid ${simResult.error ? 'rgba(239, 68, 68, 0.3)' : simResult.triggered ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-glass)'}`,
              borderRadius: '14px',
              padding: '14px'
            }}>
              {simResult.error ? (
                <div style={{ color: '#EF4444', fontSize: '0.78rem', fontWeight: 600 }}>
                  Error: {simResult.error}
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 800, color: simResult.triggered ? '#10B981' : 'var(--text-muted)' }}>
                      {simResult.triggered ? 'POLICY TRIGGERED: TRUE' : 'NO POLICY TRIGGERED'}
                    </span>
                    {simResult.action_recommended && (
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '10px',
                        background: 'rgba(245, 158, 11, 0.15)',
                        color: '#FBBF24'
                      }}>
                        ACTION: {simResult.action_recommended}
                      </span>
                    )}
                  </div>
                  <pre style={{ margin: '4px 0 0 0', fontSize: '0.72rem', color: 'var(--text-main)', opacity: 0.85 }}>
                    {JSON.stringify(simResult.evaluated_context, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Create Policy Modal */}
      {showCreateModal && (
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create Governance Policy Rule"
        >
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Rule Name *
              </label>
              <input
                type="text"
                required
                value={newPolicy.name}
                onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
                placeholder="e.g. High Value Banani Offer Interception"
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
                Condition Expression (Python Syntax) *
              </label>
              <input
                type="text"
                required
                value={newPolicy.condition_expression}
                onChange={(e) => setNewPolicy({ ...newPolicy, condition_expression: e.target.value })}
                placeholder="e.g. discount_pct > 10.0 or offer_bdt > 50000000"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.82rem',
                  fontFamily: 'monospace',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                  Enforcement Action *
                </label>
                <select
                  value={newPolicy.action}
                  onChange={(e) => setNewPolicy({ ...newPolicy, action: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass)',
                    fontSize: '0.84rem',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)',
                    boxSizing: 'border-box'
                  }}
                >
                  <option value="HUMAN_APPROVAL">HUMAN_APPROVAL (Queue in Approvals)</option>
                  <option value="BLOCK">BLOCK (Immediate Safe Fallback)</option>
                  <option value="ALERT_ENGINEER">ALERT_ENGINEER (Incident Log)</option>
                  <option value="REWRITE_SAFE">REWRITE_SAFE (Mask PII / Sanitize)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                  Rule Priority (1 = Highest)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={newPolicy.priority}
                  onChange={(e) => setNewPolicy({ ...newPolicy, priority: e.target.value })}
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
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Description / Rationale
              </label>
              <textarea
                rows={2}
                value={newPolicy.description}
                onChange={(e) => setNewPolicy({ ...newPolicy, description: e.target.value })}
                placeholder="Reason for policy rule."
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
                style={{ background: 'var(--primary-coral, #E8654A)', color: '#FFFFFF', borderRadius: '14px', padding: '8px 18px' }}
              >
                {creating ? 'Saving...' : 'Save Rule'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
