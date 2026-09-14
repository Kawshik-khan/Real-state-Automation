import React, { useState, useEffect } from 'react';
import {
  FileCode,
  Save,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Copy,
  Check,
  RotateCcw,
  Hash,
  Eye,
  Rocket
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { validateAiPrompt } from '../../services/aiControlPlaneApi';

const PROMPT_VARIABLES = [
  { tag: '{{project_name}}', desc: 'Active real-estate development name (e.g. GLG Sky Tower)' },
  { tag: '{{location}}', desc: 'Dhaka micro-market neighborhood (Gulshan, Banani, Baridhara)' },
  { tag: '{{price_bdt}}', desc: 'Verified price in BDT (e.g. ৳1.85 Crore BDT)' },
  { tag: '{{handover_date}}', desc: 'Approved handover date (e.g. December 2026)' },
  { tag: '{{customer_name}}', desc: 'Customer full name or detected greeting' },
  { tag: '{{approved_payment_plan}}', desc: 'Approved company installment schedule policy' },
  { tag: '{{verified_amenities}}', desc: 'List of canonical verified amenities' },
  { tag: '{{customer_budget}}', desc: 'Detected buyer budget range in BDT' },
];

export default function PromptStudioView({
  agent,
  systemPrompt,
  onChangePrompt,
  onSavePromptVersion,
  saving = false
}) {
  const [localPrompt, setLocalPrompt] = useState(systemPrompt || '');
  const [validation, setValidation] = useState({ valid: true, variables_found: [], undefined_variables: [] });
  const [copied, setCopied] = useState(false);
  const [changelog, setChangelog] = useState('Refined luxury tone and verified Dhaka landmarks');

  useEffect(() => {
    setLocalPrompt(systemPrompt || '');
  }, [systemPrompt]);

  // Live syntax and variable check
  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const res = await validateAiPrompt(localPrompt);
        setValidation(res);
      } catch (err) {
        console.debug('Validation error:', err);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [localPrompt]);

  const handleTextChange = (newVal) => {
    setLocalPrompt(newVal);
    onChangePrompt(newVal);
  };

  const insertVariable = (tag) => {
    const next = localPrompt + ` ${tag} `;
    handleTextChange(next);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(localPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const charCount = localPrompt.length;
  const estTokens = validation.estimated_tokens || Math.max(10, Math.round(charCount / 4.2));

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
      {/* Left: Editor & Syntax Validation */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <Card
          title={`System Prompt Studio — ${agent.name || agent.slug}`}
          subtitle={`Active Version: ${agent.current_prompt_version || 'v1.0'} | Immutable Production Release`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Action Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted, #64748B)' }}>
                  Characters: <strong>{charCount}</strong> | Est. Tokens: <strong>{estTokens}</strong>
                </span>
                {validation.valid ? (
                  <span style={{ fontSize: '0.74rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                    <CheckCircle2 size={13} />
                    Variables Validated
                  </span>
                ) : (
                  <span style={{ fontSize: '0.74rem', color: '#EF4444', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                    <AlertTriangle size={13} />
                    Undefined Variable Found
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  onClick={copyToClipboard}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-glass, rgba(0,0,0,0.1))',
                    background: 'transparent',
                    fontSize: '0.76rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  {copied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            {/* Prompt Editor */}
            <textarea
              rows={16}
              value={localPrompt}
              onChange={(e) => handleTextChange(e.target.value)}
              style={{
                width: '100%',
                padding: '16px',
                borderRadius: '16px',
                border: validation.valid ? '1px solid var(--border-glass, rgba(255,255,255,0.12))' : '1px solid #EF4444',
                background: 'var(--bg-input, #151C2C)',
                fontFamily: 'monospace',
                fontSize: '0.86rem',
                lineHeight: 1.55,
                color: 'var(--text-main, #F8FAFC)',
                resize: 'vertical'
              }}
            />

            {validation.warning && (
              <div style={{
                padding: '12px 16px',
                borderRadius: '14px',
                background: '#FEF2F2',
                border: '1px solid #FCA5A5',
                color: '#991B1B',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <AlertTriangle size={16} />
                <span>{validation.warning}</span>
              </div>
            )}

            {/* Version Publishing Controls */}
            <div style={{
              marginTop: '12px',
              padding: '16px',
              borderRadius: '16px',
              background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
              border: '1px solid var(--border-glass, rgba(255,255,255,0.08))',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
              <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-main, #F1F5F9)' }}>
                Publish New Immutable Version
              </span>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  placeholder="Changelog notes for this version (e.g. Updated Banani luxury pricing)"
                  value={changelog}
                  onChange={e => setChangelog(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '10px 14px',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)',
                    fontSize: '0.82rem'
                  }}
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onSavePromptVersion && onSavePromptVersion(changelog)}
                  loading={saving}
                  icon={Save}
                  style={{ borderRadius: '14px', padding: '8px 16px', fontWeight: 700 }}
                >
                  Save Version
                </Button>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted, #94A3B8)' }}>
                Every published version is recorded immutably in the audit log and can be rolled back at any time.
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Right: Dynamic Context Variables Browser */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <Card title="Dynamic Variable Browser" subtitle="Click tag to insert into prompt at cursor">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {PROMPT_VARIABLES.map(v => (
              <div
                key={v.tag}
                onClick={() => insertVariable(v.tag)}
                style={{
                  padding: '10px 14px',
                  borderRadius: '14px',
                  background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                  border: '1px solid var(--border-glass, rgba(0,0,0,0.06))',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--primary-coral, #E8654A)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-glass, rgba(0,0,0,0.06))'}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <code style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-coral, #E8654A)' }}>
                    {v.tag}
                  </code>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted, #64748B)', fontWeight: 600 }}>INSERT</span>
                </div>
                <p style={{ margin: 0, fontSize: '0.74rem', color: 'var(--text-muted, #64748B)', lineHeight: 1.3 }}>
                  {v.desc}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
