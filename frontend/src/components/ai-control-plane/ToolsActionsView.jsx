import React, { useState, useEffect } from 'react';
import {
  Wrench,
  Play,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Terminal,
  Clock,
  Sparkles,
  Search,
  ExternalLink,
  ShieldAlert
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiTools, testAiTool } from '../../services/aiControlPlaneApi';

export default function ToolsActionsView({ agentSlug }) {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTool, setSelectedTool] = useState(null);
  const [testParams, setTestParams] = useState('{}');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      setLoading(true);
      const data = await getAiTools();
      setTools(data.tools || []);
      if (data.tools && data.tools.length > 0) {
        selectTool(data.tools[0]);
      }
    } catch (err) {
      console.error('Failed to load AI tools:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectTool = (tool) => {
    setSelectedTool(tool);
    setTestResult(null);
    setTestError(null);
    // Provide sample default payload based on tool key
    if (tool.tool_key === 'property_search') {
      setTestParams(JSON.stringify({ location: 'Gulshan-2', min_bedrooms: 3, max_budget_bdt: 50000000 }, null, 2));
    } else if (tool.tool_key === 'schedule_site_visit') {
      setTestParams(JSON.stringify({ property_id: 'GLG-SKY-01', client_name: 'Tanvir Ahmed', preferred_date: '2026-09-20', phone: '+8801711000000' }, null, 2));
    } else if (tool.tool_key === 'calculate_roi') {
      setTestParams(JSON.stringify({ purchase_price_bdt: 45000000, projected_annual_rent_bdt: 3600000, holding_period_years: 5 }, null, 2));
    } else {
      setTestParams(JSON.stringify(tool.sample_params || {}, null, 2));
    }
  };

  const handleRunTest = async () => {
    if (!selectedTool) return;
    setTesting(true);
    setTestError(null);
    setTestResult(null);
    try {
      let parsed = {};
      try {
        parsed = JSON.parse(testParams);
      } catch (pe) {
        throw new Error(`Invalid JSON parameters: ${pe.message}`);
      }
      const res = await testAiTool(selectedTool.tool_key, parsed);
      setTestResult(res);
    } catch (err) {
      setTestError(err.message || 'Tool execution failed');
    } finally {
      setTesting(false);
    }
  };

  const filteredTools = tools.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.tool_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
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
            <Wrench size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              Agent Tools & Function Calling Registry
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Inspect parameter schemas, verify sandbox execution latencies, and validate deterministic tool outputs.
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
            {tools.length} Tools Registered
          </span>
        </div>
      </div>

      {/* Main 2-Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '20px' }}>
        {/* Left Column: Tool Catalog */}
        <Card style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', height: 'fit-content', borderRadius: '20px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted, #94A3B8)' }} />
            <input
              type="text"
              placeholder="Search tools or handlers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px 10px 38px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)',
                fontSize: '0.85rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '580px', overflowY: 'auto' }}>
            {filteredTools.map((tool) => {
              const isSelected = selectedTool?.tool_key === tool.tool_key;
              return (
                <div
                  key={tool.tool_key}
                  onClick={() => selectTool(tool)}
                  style={{
                    padding: '14px',
                    borderRadius: '14px',
                    border: isSelected 
                      ? '1px solid var(--primary-coral, #E8654A)' 
                      : '1px solid var(--border-glass)',
                    background: isSelected ? 'rgba(232, 101, 74, 0.08)' : 'var(--bg-elevated, #1E293B)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.88rem', color: isSelected ? 'var(--primary-coral, #E8654A)' : 'var(--text-main, #1E293B)' }}>
                      {tool.name}
                    </span>
                    <span style={{
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: '20px',
                      background: tool.is_enabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                      color: tool.is_enabled ? '#10B981' : 'var(--text-muted, #64748B)'
                    }}>
                      {tool.is_enabled ? 'ENABLED' : 'DISABLED'}
                    </span>
                  </div>
                  <code style={{ fontSize: '0.74rem', color: 'var(--text-muted, #64748B)', display: 'block', marginBottom: '6px' }}>
                    {tool.tool_key}
                  </code>
                  <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted, #64748B)', lineHeight: '1.35' }}>
                    {tool.description}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Right Column: Schema Details & Live Test Sandbox */}
        {selectedTool ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Tool Header Card */}
            <Card style={{ padding: '20px', borderRadius: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <Code2 size={20} color="var(--primary-coral, #E8654A)" />
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
                      {selectedTool.name}
                    </h3>
                  </div>
                  <code style={{ fontSize: '0.8rem', color: 'var(--primary-coral, #E8654A)', fontWeight: 600 }}>
                    Function: {selectedTool.tool_key}()
                  </code>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{
                    fontSize: '0.74rem',
                    padding: '3px 10px',
                    borderRadius: '20px',
                    background: 'var(--bg-elevated, #1E293B)',
                    color: 'var(--text-main, #475569)',
                    border: '1px solid var(--border-glass)',
                    fontWeight: 600
                  }}>
                    Timeout: {selectedTool.timeout_ms || 3000}ms
                  </span>
                  <span style={{
                    fontSize: '0.74rem',
                    padding: '3px 10px',
                    borderRadius: '20px',
                    background: 'var(--bg-elevated, #1E293B)',
                    color: 'var(--text-main, #475569)',
                    border: '1px solid var(--border-glass)',
                    fontWeight: 600
                  }}>
                    Retries: {selectedTool.retry_count ?? 1}
                  </span>
                </div>
              </div>

              <p style={{ margin: '0 0 16px 0', fontSize: '0.88rem', color: 'var(--text-main, #475569)', lineHeight: '1.5' }}>
                {selectedTool.description}
              </p>

              {/* Parameter Schema Table */}
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main, #1E293B)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Expected Parameters
                </h4>
                <div style={{
                  border: '1px solid var(--border-glass)',
                  borderRadius: '14px',
                  overflow: 'hidden'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                    <thead>
                      <tr style={{ background: 'var(--bg-elevated, #1E293B)', borderBottom: '1px solid var(--border-glass)', textAlign: 'left', color: 'var(--text-main, #F8FAFC)' }}>
                        <th style={{ padding: '8px 12px', fontWeight: 700 }}>Parameter</th>
                        <th style={{ padding: '8px 12px', fontWeight: 700 }}>Type</th>
                        <th style={{ padding: '8px 12px', fontWeight: 700 }}>Required</th>
                        <th style={{ padding: '8px 12px', fontWeight: 700 }}>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTool.parameters_schema?.properties && Object.entries(selectedTool.parameters_schema.properties).map(([name, prop]) => {
                        const isReq = selectedTool.parameters_schema?.required?.includes(name);
                        return (
                          <tr key={name} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                            <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-main, #0F172A)' }}>
                              <code>{name}</code>
                            </td>
                            <td style={{ padding: '8px 12px', color: 'var(--text-muted, #64748B)' }}>
                              <code>{prop.type || 'string'}</code>
                            </td>
                            <td style={{ padding: '8px 12px' }}>
                              {isReq ? (
                                <span style={{ color: '#EF4444', fontWeight: 700 }}>Yes</span>
                              ) : (
                                <span style={{ color: 'var(--text-muted, #94A3B8)' }}>Optional</span>
                              )}
                            </td>
                            <td style={{ padding: '8px 12px', color: 'var(--text-main, #475569)' }}>
                              {prop.description || '—'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </Card>

            {/* Sandbox Execution Console */}
            <Card style={{ padding: '20px', borderRadius: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Terminal size={18} color="var(--primary-coral, #E8654A)" />
                  <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
                    Live Sandbox Execution Console
                  </h4>
                </div>
                <Button
                  onClick={handleRunTest}
                  disabled={testing}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    fontSize: '0.84rem',
                    borderRadius: '14px'
                  }}
                >
                  <Play size={14} />
                  <span>{testing ? 'Executing...' : 'Execute Tool in Sandbox'}</span>
                </Button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '6px' }}>
                    INPUT PAYLOAD (JSON)
                  </label>
                  <textarea
                    rows={9}
                    value={testParams}
                    onChange={(e) => setTestParams(e.target.value)}
                    style={{
                      width: '100%',
                      fontFamily: 'monospace',
                      fontSize: '0.82rem',
                      padding: '12px',
                      borderRadius: '14px',
                      border: '1px solid var(--border-glass)',
                      background: 'var(--bg-input, #151C2C)',
                      color: 'var(--text-main, #0F172A)',
                      outline: 'none',
                      resize: 'vertical'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '6px' }}>
                    EXECUTION OUTPUT & TELEMETRY
                  </label>
                  <div style={{
                    minHeight: '190px',
                    maxHeight: '260px',
                    overflowY: 'auto',
                    background: 'var(--bg-input, #0F172A)',
                    color: '#F8FAFC',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass)',
                    padding: '12px',
                    fontFamily: 'monospace',
                    fontSize: '0.8rem'
                  }}>
                    {testing && (
                      <div style={{ color: '#FCD34D' }}>⏳ Invoking deterministic handler...</div>
                    )}
                    {testError && (
                      <div style={{ color: '#F87171' }}>
                        ❌ Execution Error: {testError}
                      </div>
                    )}
                    {testResult && (
                      <div>
                        <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '6px', marginBottom: '8px', color: '#94A3B8', fontSize: '0.75rem' }}>
                          <span>Latency: <strong style={{ color: '#34D399' }}>{testResult.execution_time_ms}ms</strong></span>
                          <span>Status: <strong style={{ color: testResult.status === 'success' ? '#34D399' : '#F87171' }}>{testResult.status?.toUpperCase()}</strong></span>
                        </div>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#E2E8F0' }}>
                          {JSON.stringify(testResult.data, null, 2)}
                        </pre>
                      </div>
                    )}
                    {!testing && !testError && !testResult && (
                      <span style={{ color: 'var(--text-muted, #64748B)' }}>Ready. Click "Execute Tool in Sandbox" to trigger.</span>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        ) : (
          <Card style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted, #64748B)', borderRadius: '20px' }}>
            Select a tool from the catalog to inspect schema and run sandbox tests.
          </Card>
        )}
      </div>
    </div>
  );
}
