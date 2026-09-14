import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Play,
  CheckCircle2,
  Lock,
  EyeOff,
  Scale,
  Sparkles,
  FileCheck
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiGuardrails, testAiGuardrail } from '../../services/aiControlPlaneApi';

export default function GuardrailsView({ agentSlug }) {
  const [guardrails, setGuardrails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRule, setSelectedRule] = useState('rule_hallucination_price');
  const [testText, setTestText] = useState('I will give you a special 50% discount on GLG Sky Tower penthouse for only 15,000,000 BDT!');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testError, setTestError] = useState(null);

  useEffect(() => {
    loadGuardrails();
  }, []);

  const loadGuardrails = async () => {
    try {
      setLoading(true);
      const data = await getAiGuardrails();
      if (data.guardrails) setGuardrails(data.guardrails);
    } catch (err) {
      console.error('Failed to load guardrails:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunTest = async () => {
    if (!testText.trim()) return;
    setTesting(true);
    setTestError(null);
    setTestResult(null);
    try {
      const res = await testAiGuardrail(selectedRule, testText);
      setTestResult(res);
    } catch (err) {
      setTestError(err.message || 'Guardrail test failed');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.08) 0%, rgba(243, 144, 114, 0.04) 100%)',
        border: '1px solid rgba(232, 101, 74, 0.2)',
        borderRadius: '12px',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <ShieldCheck size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              AI Guardrails & Deterministic Policy Enforcement
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Enforce real-estate pricing bounds, PII redaction, prompt injection defense, and brand safety rules.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{
            fontSize: '0.78rem',
            fontWeight: 700,
            padding: '4px 10px',
            borderRadius: '20px',
            background: 'rgba(16, 185, 129, 0.12)',
            color: '#10B981',
            border: '1px solid rgba(16, 185, 129, 0.25)'
          }}>
            Zero-Hallucination Pricing Gate ACTIVE
          </span>
        </div>
      </div>

      {/* Grid: Policies List + Live Tester */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Guardrail Policies */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card style={{ padding: '20px', borderRadius: '20px' }}>
            <h3 style={{ margin: '0 0 14px 0', fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Active Guardrail Rulesets
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{
                padding: '14px 16px',
                borderRadius: '16px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-elevated, rgba(255,255,255,0.05))'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Lock size={16} color="var(--primary-coral, #E8654A)" />
                    <span style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-main)' }}>
                      Pricing Accuracy Lock
                    </span>
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '3px 8px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                    ENFORCING
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  Validates any stated price or discount against the authoritative GLG pricing matrix. Unapproved discounts trigger an immediate fallback response.
                </p>
              </div>

              <div style={{
                padding: '14px 16px',
                borderRadius: '16px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-elevated, rgba(255,255,255,0.05))'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <EyeOff size={16} color="#818CF8" />
                    <span style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-main)' }}>
                      Customer PII Redaction
                    </span>
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '3px 8px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                    ENFORCING
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  Automatically masks Bangladeshi phone numbers (+880...), National ID (NID) numbers, and bank account credentials before dispatching to LLMs.
                </p>
              </div>

              <div style={{
                padding: '14px 16px',
                borderRadius: '16px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-elevated, rgba(255,255,255,0.05))'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldAlert size={16} color="#FBBF24" />
                    <span style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-main)' }}>
                      Prompt Injection & Jailbreak Defense
                    </span>
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '3px 8px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                    ENFORCING
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  Evaluates incoming customer inputs against pattern classifiers detecting attempts to override system prompts, extract developer instructions, or emulate illegal roles.
                </p>
              </div>

              <div style={{
                padding: '14px 16px',
                borderRadius: '16px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-elevated, rgba(255,255,255,0.05))'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Scale size={16} color="#34D399" />
                    <span style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-main)' }}>
                      Scope & Topic Boundary
                    </span>
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '3px 8px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                    ENFORCING
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  Prevents agents from answering out-of-domain questions (cryptocurrency, political opinions, unrelated real estate) and steers users back to GLG projects.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Live Guardrail Test Console */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card style={{ padding: '20px', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={18} color="var(--primary-coral, #E8654A)" />
                <h3 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  Live Policy Enforcement Tester
                </h3>
              </div>
              <Button
                onClick={handleRunTest}
                disabled={testing}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '0.82rem', borderRadius: '14px' }}
              >
                <Play size={14} />
                <span>{testing ? 'Evaluating...' : 'Test Policy'}</span>
              </Button>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px' }}>
                TARGET POLICY RULE
              </label>
              <select
                value={selectedRule}
                onChange={(e) => setSelectedRule(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem'
                }}
              >
                <option value="rule_hallucination_price">Pricing Accuracy Lock (Anti-Hallucination)</option>
                <option value="rule_pii_masking">PII Masking (Phone, NID, Bank Details)</option>
                <option value="rule_prompt_injection">Prompt Injection & Jailbreak Defense</option>
                <option value="rule_topic_boundary">Real-Estate Topic Boundary</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px' }}>
                CANDIDATE PROMPT / LLM OUTPUT TEXT
              </label>
              <textarea
                rows={5}
                value={testText}
                onChange={(e) => setTestText(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '16px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.85rem',
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>

            {testError && (
              <div style={{ padding: '10px 14px', borderRadius: '14px', background: 'rgba(239, 68, 68, 0.12)', color: '#EF4444', fontSize: '0.8rem', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                {testError}
              </div>
            )}

            {testResult && (
              <div style={{
                padding: '14px 16px',
                borderRadius: '16px',
                border: testResult.passed ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
                background: testResult.passed ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  {testResult.passed ? (
                    <>
                      <CheckCircle2 size={18} color="#10B981" />
                      <strong style={{ color: '#10B981', fontSize: '0.88rem' }}>
                        VERDICT: SAFE / PASSED POLICY GATE
                      </strong>
                    </>
                  ) : (
                    <>
                      <AlertTriangle size={18} color="#EF4444" />
                      <strong style={{ color: '#EF4444', fontSize: '0.88rem' }}>
                        VERDICT: VIOLATION DETECTED & BLOCKED
                      </strong>
                    </>
                  )}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', marginBottom: '6px' }}>
                  {testResult.message || (testResult.passed ? 'No policy infractions detected.' : 'Content violates safety policy.')}
                </div>
                {testResult.remediation && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'var(--bg-card)', padding: '10px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
                    <strong style={{ color: 'var(--text-main)' }}>Action Taken:</strong> {testResult.remediation}
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
