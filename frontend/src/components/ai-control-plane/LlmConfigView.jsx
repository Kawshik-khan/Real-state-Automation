import React, { useState } from 'react';
import {
  Cpu,
  CheckCircle2,
  AlertCircle,
  Zap,
  Activity,
  Server,
  DollarSign,
  ShieldCheck,
  RefreshCw,
  Clock
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { testAiModelConnection } from '../../services/aiControlPlaneApi';

export default function LlmConfigView({
  providers = [],
  models = [],
  onRefreshProviders
}) {
  const [testingKey, setTestingKey] = useState(null);
  const [testResults, setTestResults] = useState({});

  const handleTestConnection = async (providerKey, modelId) => {
    setTestingKey(providerKey);
    try {
      const res = await testAiModelConnection(providerKey, modelId);
      setTestResults(prev => ({ ...prev, [providerKey]: res }));
      if (onRefreshProviders) onRefreshProviders();
    } catch (err) {
      setTestResults(prev => ({
        ...prev,
        [providerKey]: { success: false, status: 'DOWN', error: err.message, latency_ms: 0 }
      }));
    } finally {
      setTestingKey(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div>
        <h2 style={{ margin: '0 0 4px', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
          LLM Providers & Multi-Model Gateway
        </h2>
        <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-muted, #64748B)' }}>
          Live inference provider connections, real latency pings, capability matrix, and token pricing schedules.
        </p>
      </div>

      {/* Provider Connectivity Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {providers.map(p => {
          const testRes = testResults[p.provider_key];
          const isTesting = testingKey === p.provider_key;
          const status = testRes ? testRes.status : p.health_status;
          const pingMs = testRes?.latency_ms || p.last_ping_ms;

          return (
            <div
              key={p.provider_key}
              style={{
                background: 'var(--bg-card, #FFFFFF)',
                border: '1px solid var(--border-glass, rgba(255,255,255,0.08))',
                borderRadius: '20px',
                padding: '18px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '14px'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Server size={18} color="var(--primary-coral, #E8654A)" />
                    <span style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
                      {p.display_name}
                    </span>
                  </div>
                  <span style={{
                    fontSize: '0.72rem',
                    padding: '3px 10px',
                    borderRadius: '20px',
                    background: status === 'HEALTHY' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                    color: status === 'HEALTHY' ? '#10B981' : '#EF4444',
                    border: status === 'HEALTHY' ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid rgba(239, 68, 68, 0.25)',
                    fontWeight: 700
                  }}>
                    {status}
                  </span>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted, #64748B)', marginBottom: '8px' }}>
                  Endpoint: <code style={{ fontSize: '0.74rem', background: 'var(--bg-elevated, #1E293B)', padding: '2px 6px', borderRadius: '12px' }}>{p.base_url || 'Default SDK Route'}</code>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '10px' }}>
                  {(p.capabilities || ['chat', 'streaming', 'tools']).map(cap => (
                    <span
                      key={cap}
                      style={{
                        fontSize: '0.68rem',
                        padding: '3px 8px',
                        borderRadius: '20px',
                        background: 'var(--bg-elevated, #1E293B)',
                        color: 'var(--text-muted, #94A3B8)',
                        border: '1px solid var(--border-glass, rgba(255,255,255,0.06))',
                        fontWeight: 600
                      }}
                    >
                      {cap}
                    </span>
                  ))}
                </div>

                {pingMs && (
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted, #64748B)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    <span>Last Response Latency: <strong>{pingMs}ms</strong></span>
                  </div>
                )}

                {testRes?.error && (
                  <div style={{ fontSize: '0.72rem', color: '#EF4444', marginTop: '6px' }}>
                    Error: {testRes.error}
                  </div>
                )}
              </div>

              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleTestConnection(p.provider_key)}
                loading={isTesting}
                icon={RefreshCw}
                style={{ borderRadius: '14px' }}
              >
                Test Connection
              </Button>
            </div>
          );
        })}
      </div>

      {/* Model Registry & Capability Matrix */}
      <Card title="Model Catalog & Pricing Matrix" subtitle="Per-million token rates in USD ($) and converted BDT (৳)" style={{ borderRadius: '20px' }}>
        <div style={{ overflowX: 'auto', border: '1px solid var(--border-glass, rgba(255, 255, 255, 0.08))', borderRadius: '16px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-elevated, #1E293B)', borderBottom: '1px solid var(--border-glass, rgba(255, 255, 255, 0.08))', color: 'var(--text-muted, #94A3B8)', textAlign: 'left' }}>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>MODEL IDENTIFIER</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>PROVIDER</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>TYPE</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>CONTEXT WINDOW</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>INPUT / 1M</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>OUTPUT / 1M</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>TOOLS & SCHEMAS</th>
              </tr>
            </thead>
            <tbody>
              {models.map(m => (
                <tr key={m.model_id} style={{ borderBottom: '1px solid var(--border-glass, rgba(255, 255, 255, 0.06))' }}>
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
                    {m.display_name}
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted, #64748B)', fontFamily: 'monospace' }}>
                      {m.model_id}
                    </div>
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted, #64748B)' }}>
                    {m.provider_id.replace('prov-', '').toUpperCase()}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      fontSize: '0.7rem',
                      padding: '3px 10px',
                      borderRadius: '20px',
                      background: m.model_type === 'FINE_TUNED' ? 'rgba(232, 101, 74, 0.15)' : 'rgba(59, 130, 246, 0.12)',
                      color: m.model_type === 'FINE_TUNED' ? 'var(--primary-coral, #E8654A)' : '#3B82F6',
                      border: m.model_type === 'FINE_TUNED' ? '1px solid rgba(232, 101, 74, 0.25)' : '1px solid rgba(59, 130, 246, 0.25)',
                      fontWeight: 700
                    }}>
                      {m.model_type}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    {(m.context_window / 1000).toFixed(0)}k tokens
                  </td>
                  <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                    ${m.input_cost_per_m} <span style={{ fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>(৳{(m.input_cost_per_m * 122.5).toFixed(1)})</span>
                  </td>
                  <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                    ${m.output_cost_per_m} <span style={{ fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>(৳{(m.output_cost_per_m * 122.5).toFixed(1)})</span>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ color: '#10B981', fontWeight: 600 }}>✓ Supported</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
