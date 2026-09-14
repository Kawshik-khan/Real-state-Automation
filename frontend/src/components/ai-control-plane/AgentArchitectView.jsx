import React, { useState } from 'react';
import {
  Sliders,
  Cpu,
  ShieldCheck,
  Layers,
  Wrench,
  Save,
  CheckCircle2,
  Copy,
  Sparkles,
  RotateCcw,
  Rocket
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';

const PERSONA_PRESETS = [
  { 
    id: 'luxury', 
    name: 'Consultative Luxury', 
    icon: '💎',
    desc: 'High-end prestigious tone for Gulshan, Banani, and Baridhara luxury residences.',
    temp: 0.2, 
    topP: 0.9, 
    maxTokens: 1024 
  },
  { 
    id: 'closer', 
    name: 'High-Urgency Closer', 
    icon: '⚡',
    desc: 'Action-oriented tone emphasizing limited-unit scarcity and priority booking slots.',
    temp: 0.35, 
    topP: 0.92, 
    maxTokens: 850 
  },
  { 
    id: 'advisor', 
    name: 'Analytical Advisor', 
    icon: '📊',
    desc: 'Strictly factual, numbers-driven tone for square-foot ROI and payment milestones.',
    temp: 0.15, 
    topP: 0.85, 
    maxTokens: 1024 
  },
  { 
    id: 'conversational', 
    name: 'Warm Conversational', 
    icon: '🤝',
    desc: 'Welcoming Bengali/Banglish hospitality ideal for social messaging and initial greetings.',
    temp: 0.3, 
    topP: 0.95, 
    maxTokens: 900 
  },
];

export default function AgentArchitectView({
  agent,
  onSaveAgent,
  onPublishAgent,
  models = [],
  tools = [],
  saving = false
}) {
  const safeAgent = agent || {};
  const [formData, setFormData] = useState({ ...safeAgent });
  const [activeSubTab, setActiveSubTab] = useState('identity'); // identity, model, tools, memory, guardrails

  // Sync if agent changes
  React.useEffect(() => {
    if (agent) {
      setFormData({ ...agent });
    }
  }, [agent?.slug]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const applyPreset = (preset) => {
    setFormData(prev => ({
      ...prev,
      temperature: preset.temp,
      top_p: preset.topP,
      max_tokens: preset.maxTokens,
      persona_preset: preset.name
    }));
  };

  const toggleTool = (toolKey) => {
    const current = formData.enabled_tools || [];
    const next = current.includes(toolKey)
      ? current.filter(k => k !== toolKey)
      : [...current, toolKey];
    handleChange('enabled_tools', next);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <h2 style={{ margin: '0 0 4px', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
            Agent Architect — {safeAgent.name || safeAgent.slug || 'Agent'}
          </h2>
          <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-muted, #64748B)' }}>
            Configure agent identity, primary & fallback model tiers, persona parameters, and tool assignments.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPublishAgent && onPublishAgent(safeAgent.slug, 'Promoted to Production')}
            icon={Rocket}
          >
            Publish Version
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onSaveAgent(formData)}
            loading={saving}
            icon={Save}
          >
            Save Configuration
          </Button>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        borderBottom: '1px solid var(--border-glass, rgba(0,0,0,0.08))',
        paddingBottom: '8px'
      }}>
        {[
          { id: 'identity', label: 'Identity & Presets' },
          { id: 'model', label: 'Model Engine & Hyperparameters' },
          { id: 'tools', label: 'Enabled Tools & Permissions' },
          { id: 'memory', label: 'Memory Scopes & Guardrails' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveSubTab(t.id)}
            style={{
              padding: '7px 16px',
              borderRadius: '20px',
              background: activeSubTab === t.id ? 'rgba(232, 101, 74, 0.16)' : 'transparent',
              color: activeSubTab === t.id ? 'var(--primary-coral, #E8654A)' : 'var(--text-muted, #94A3B8)',
              border: activeSubTab === t.id ? '1px solid rgba(232, 101, 74, 0.3)' : '1px solid transparent',
              fontSize: '0.84rem',
              fontWeight: activeSubTab === t.id ? 700 : 500,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* SUB-TAB 1: IDENTITY & PRESETS */}
      {activeSubTab === 'identity' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
          <Card title="Agent Specification" subtitle="Core metadata, description, and operational lifecycle state">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #F1F5F9)' }}>Agent Name</label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={e => handleChange('name', e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '14px', border: '1px solid var(--border-glass, rgba(255,255,255,0.12))', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #F1F5F9)' }}>Role / Headline</label>
                <input
                  type="text"
                  value={formData.role || ''}
                  onChange={e => handleChange('role', e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '14px', border: '1px solid var(--border-glass, rgba(255,255,255,0.12))', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #F1F5F9)' }}>Objective & Instructions</label>
                <textarea
                  rows={3}
                  value={formData.objective || ''}
                  onChange={e => handleChange('objective', e.target.value)}
                  style={{ width: '100%', padding: '12px 14px', borderRadius: '14px', border: '1px solid var(--border-glass, rgba(255,255,255,0.12))', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)', resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #F1F5F9)' }}>Lifecycle Status</label>
                  <select
                    value={formData.status || 'PRODUCTION'}
                    onChange={e => handleChange('status', e.target.value)}
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '14px', border: '1px solid var(--border-glass, rgba(255,255,255,0.12))', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)' }}
                  >
                    <option value="DRAFT">DRAFT</option>
                    <option value="TESTING">TESTING</option>
                    <option value="STAGING">STAGING</option>
                    <option value="CANARY">CANARY</option>
                    <option value="PRODUCTION">PRODUCTION</option>
                    <option value="DISABLED">DISABLED</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px', color: 'var(--text-main, #F1F5F9)' }}>Approval Policy</label>
                  <select
                    value={formData.human_approval_policy || 'NONE'}
                    onChange={e => handleChange('human_approval_policy', e.target.value)}
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '14px', border: '1px solid var(--border-glass, rgba(255,255,255,0.12))', background: 'var(--bg-input, #151C2C)', color: 'var(--text-main, #F8FAFC)' }}
                  >
                    <option value="NONE">No Human Approval</option>
                    <option value="HIGH_RISK_ONLY">High Risk / Pricing Only</option>
                    <option value="ALWAYS">Always Require Approval</option>
                  </select>
                </div>
              </div>
            </div>
          </Card>

          {/* Persona Tone Presets */}
          <Card title="Persona & Tone Presets" subtitle="Click preset to inject calibrated temperature & token parameters">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {PERSONA_PRESETS.map(p => {
                const isSelected = formData.persona_preset === p.name;
                return (
                  <div
                    key={p.id}
                    onClick={() => applyPreset(p)}
                    style={{
                      padding: '14px 16px',
                      borderRadius: '16px',
                      background: isSelected ? 'rgba(232, 101, 74, 0.12)' : 'var(--bg-elevated, rgba(255,255,255,0.05))',
                      border: isSelected ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass, rgba(255,255,255,0.08))',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--text-main, #F1F5F9)' }}>
                        {p.icon} {p.name}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: isSelected ? 'var(--primary-coral, #E8654A)' : 'var(--text-muted, #94A3B8)', fontWeight: 600 }}>
                        T: {p.temp} | TopP: {p.topP}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--text-muted, #94A3B8)', lineHeight: 1.4 }}>
                      {p.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}

      {/* SUB-TAB 2: MODEL ENGINE */}
      {activeSubTab === 'model' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <Card title="Primary & Fallback Inference Models" subtitle="Configure primary provider and graceful fallback recovery">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Primary Model</label>
                <select
                  value={formData.primary_model || 'llama-3.3-70b-versatile'}
                  onChange={e => handleChange('primary_model', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-glass, rgba(0,0,0,0.1))', background: 'var(--bg-elevated, #F8FAFC)' }}
                >
                  <option value="llama-3.3-70b-versatile">Groq LLaMA 3.3 70B Versatile (Fast)</option>
                  <option value="gpt-4o">OpenAI GPT-4o (Flagship Multimodal)</option>
                  <option value="claude-3-5-sonnet-20241022">Anthropic Claude 3.5 Sonnet</option>
                  <option value="gemini-1.5-pro">Google Gemini 1.5 Pro</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Fallback Model (Recovery Tier)</label>
                <select
                  value={formData.fallback_model || 'llama-3.1-8b-instant'}
                  onChange={e => handleChange('fallback_model', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-glass, rgba(0,0,0,0.1))', background: 'var(--bg-elevated, #F8FAFC)' }}
                >
                  <option value="llama-3.1-8b-instant">Groq LLaMA 3.1 8B Instant (Ultra-low Latency)</option>
                  <option value="gpt-4o-mini">OpenAI GPT-4o Mini</option>
                  <option value="claude-3-5-haiku-20241022">Anthropic Claude 3.5 Haiku</option>
                </select>
              </div>

              <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '0.78rem', color: '#1E40AF' }}>
                ℹ️ Automated fallback engages on provider timeout (&gt;30s), rate-limit 429 errors, or temporary API outages with zero user disruption.
              </div>
            </div>
          </Card>

          <Card title="Hyperparameter Tuning" subtitle="Precision controls for sampling, creativity, and token limits">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Temperature</label>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-coral, #E8654A)' }}>{formData.temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1.5"
                  step="0.05"
                  value={formData.temperature || 0.2}
                  onChange={e => handleChange('temperature', parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary-coral, #E8654A)' }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Top-P (Nucleus Sampling)</label>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-coral, #E8654A)' }}>{formData.top_p}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={formData.top_p || 0.9}
                  onChange={e => handleChange('top_p', parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary-coral, #E8654A)' }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Max Output Tokens</label>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-coral, #E8654A)' }}>{formData.max_tokens}</span>
                </div>
                <input
                  type="range"
                  min="256"
                  max="4096"
                  step="64"
                  value={formData.max_tokens || 1024}
                  onChange={e => handleChange('max_tokens', parseInt(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary-coral, #E8654A)' }}
                />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* SUB-TAB 3: TOOLS & PERMISSIONS */}
      {activeSubTab === 'tools' && (
        <Card title="Agent Tool Bindings" subtitle="Enable or restrict tools authorized for this agent's runtime execution">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {[
              { key: 'property_search', name: 'Property Inventory Search', desc: 'Query verified listings, floor plans, and BDT pricing' },
              { key: 'availability_check', name: 'Unit Availability & Status', desc: 'Check real-time tower inventory and booked status' },
              { key: 'crm_lead_sync', name: 'CRM Lead Sync & Scoring', desc: 'Upsert client interest into CRM pipeline' },
              { key: 'schedule_tour', name: 'VIP Site Tour Booking', desc: 'Reserve private visit slot with luxury relationship manager' },
              { key: 'whatsapp_send', name: 'WhatsApp Direct Dispatch', desc: 'Deliver verified brochures and payment plans via WhatsApp' },
              { key: 'knowledge_search', name: 'Legal & Policy Vault', desc: 'Retrieve NID, TIN, and legal disclosure documentation' },
            ].map(t => {
              const isEnabled = (formData.enabled_tools || []).includes(t.key);
              return (
                <div
                  key={t.key}
                  onClick={() => toggleTool(t.key)}
                  style={{
                    padding: '14px',
                    borderRadius: '10px',
                    background: isEnabled ? 'rgba(232, 101, 74, 0.06)' : 'var(--bg-elevated, #F8FAFC)',
                    border: isEnabled ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass, rgba(0,0,0,0.06))',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>{t.name}</span>
                    <input
                      type="checkbox"
                      checked={isEnabled}
                      onChange={() => {}}
                      style={{ accentColor: 'var(--primary-coral, #E8654A)', cursor: 'pointer' }}
                    />
                  </div>
                  <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted, #64748B)' }}>{t.desc}</p>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* SUB-TAB 4: MEMORY & GUARDRAILS */}
      {activeSubTab === 'memory' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <Card title="Memory Retention Policy" subtitle="Configure memory duration and scope for multi-turn conversations">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Memory Scope</label>
                <select
                  value={formData.memory_config?.scope || 'CONVERSATION'}
                  onChange={e => handleChange('memory_config', { ...(formData.memory_config || {}), scope: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: '1px solid var(--border-glass, rgba(0,0,0,0.1))', background: 'var(--bg-elevated, #F8FAFC)' }}
                >
                  <option value="SHORT_TERM">Short-Term (Last 6 turns)</option>
                  <option value="CONVERSATION">Full Conversation (Session Duration)</option>
                  <option value="CUSTOMER">Customer Profile (Persistent Across Channels)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Retention TTL (Hours)</label>
                <input
                  type="number"
                  value={formData.memory_config?.retention_ttl_hours || 168}
                  onChange={e => handleChange('memory_config', { ...(formData.memory_config || {}), retention_ttl_hours: parseInt(e.target.value) })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: '1px solid var(--border-glass, rgba(0,0,0,0.1))', background: 'var(--bg-elevated, #F8FAFC)' }}
                />
              </div>
            </div>
          </Card>

          <Card title="Active Guardrail Policies" subtitle="Security and business fact validation assigned to this agent">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', fontSize: '0.8rem' }}>
                🛡️ <strong>Verified Property Price Shield:</strong> Active (Blocks unverified price claims)
              </div>
              <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', fontSize: '0.8rem' }}>
                🛡️ <strong>Bangladesh NID & Card Masking:</strong> Active (Automatic PII redaction)
              </div>
              <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', fontSize: '0.8rem' }}>
                🛡️ <strong>Prompt Injection Defense:</strong> Active (Bangla & English overrides blocked)
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
