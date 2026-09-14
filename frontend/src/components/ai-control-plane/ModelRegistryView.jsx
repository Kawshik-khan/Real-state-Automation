import React, { useState, useEffect } from 'react';
import {
  Database,
  Cpu,
  Zap,
  Activity,
  CheckCircle2,
  DollarSign,
  Search,
  Sparkles,
  Sliders,
  RefreshCw,
  ShieldAlert,
  ArrowRight,
  ExternalLink
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import {
  getAiProviders,
  getAiModels,
  testAiModelConnection,
  recommendAiModel
} from '../../services/aiControlPlaneApi';

export default function ModelRegistryView() {
  const [providers, setProviders] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [providerFilter, setProviderFilter] = useState('ALL');
  const [pingStatus, setPingStatus] = useState({});
  const [pingingModel, setPingingModel] = useState(null);

  // Model Recommendation Calculator State
  const [recTask, setRecTask] = useState('complex_negotiation');
  const [recMaxLatency, setRecMaxLatency] = useState(1500);
  const [recCostPriority, setRecCostPriority] = useState('BALANCED');
  const [recResult, setRecResult] = useState(null);
  const [recommending, setRecommending] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [provRes, modRes] = await Promise.all([
        getAiProviders(),
        getAiModels()
      ]);
      setProviders(provRes.providers || []);
      setModels(modRes.models || []);
    } catch (err) {
      console.error('Failed to load models & providers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePing = async (providerKey, modelId) => {
    const key = `${providerKey}:${modelId}`;
    try {
      setPingingModel(key);
      const res = await testAiModelConnection(providerKey, modelId);
      setPingStatus((prev) => ({
        ...prev,
        [key]: {
          status: res.status || 'CONNECTED',
          latency: res.latency_ms || 240,
          time: new Date().toLocaleTimeString()
        }
      }));
    } catch (err) {
      setPingStatus((prev) => ({
        ...prev,
        [key]: {
          status: 'ERROR',
          error: err.message,
          time: new Date().toLocaleTimeString()
        }
      }));
    } finally {
      setPingingModel(null);
    }
  };

  const handleRecommend = async () => {
    try {
      setRecommending(true);
      const res = await recommendAiModel({
        task_type: recTask,
        max_latency_ms: Number(recMaxLatency),
        cost_priority: recCostPriority,
        requires_tools: true
      });
      setRecResult(res);
    } catch (err) {
      console.error('Recommendation failed:', err);
    } finally {
      setRecommending(false);
    }
  };

  const filteredModels = models.filter((m) => {
    const matchSearch = m.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.provider?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchProvider = providerFilter === 'ALL' || m.provider?.toLowerCase() === providerFilter.toLowerCase();
    return matchSearch && matchProvider;
  });

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
            <Database size={22} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Enterprise Model Registry & Gateway
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Central inventory, capability metrics, live provider pings, and dual-currency token pricing.
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={loadData}
          disabled={loading}
          style={{ borderRadius: '16px' }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </Button>
      </div>

      {/* Model Recommendation Engine Widget */}
      <Card style={{ padding: '18px 20px', borderRadius: '20px', background: 'var(--bg-card)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Sparkles size={18} color="var(--primary-coral, #E8654A)" />
          <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-main)' }}>
            Automated Model Recommendation Engine
          </h3>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Multi-objective Pareto optimizer balancing latency, token cost in BDT, and reasoning depth
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr auto', gap: '12px', alignItems: 'flex-end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
              TASK WORKLOAD
            </label>
            <select
              value={recTask}
              onChange={(e) => setRecTask(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                fontSize: '0.82rem',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)'
              }}
            >
              <option value="complex_negotiation">Complex Luxury Negotiation (3 BHK Banani)</option>
              <option value="faq_instant">Instant Specifications & Amenities Answering</option>
              <option value="multi_agent_routing">Multi-Agent Intent Classification & Routing</option>
              <option value="formal_proposal">Formal Investment Proposal & Email Composition</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
              LATENCY CEILING
            </label>
            <select
              value={recMaxLatency}
              onChange={(e) => setRecMaxLatency(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                fontSize: '0.82rem',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)'
              }}
            >
              <option value="500">&lt; 500 ms (Ultra Fast)</option>
              <option value="1500">&lt; 1,500 ms (Standard)</option>
              <option value="4000">&lt; 4,000 ms (Deep Reasoning)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
              PRIORITY OBJECTIVE
            </label>
            <select
              value={recCostPriority}
              onChange={(e) => setRecCostPriority(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                fontSize: '0.82rem',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)'
              }}
            >
              <option value="BALANCED">Balanced Pareto Optimal</option>
              <option value="COST_FIRST">Cost Optimization (Lowest BDT)</option>
              <option value="QUALITY_FIRST">Maximum Grounding & Quality</option>
            </select>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={handleRecommend}
            disabled={recommending}
            style={{
              background: 'var(--primary-coral, #E8654A)',
              color: '#FFFFFF',
              height: '38px',
              padding: '0 18px',
              fontWeight: 700,
              borderRadius: '14px'
            }}
          >
            {recommending ? 'Analyzing...' : 'Recommend Model'}
          </Button>
        </div>

        {recResult && (
          <div style={{
            marginTop: '14px',
            padding: '12px 16px',
            borderRadius: '14px',
            background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
            border: '1px solid var(--border-glass)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--primary-coral, #E8654A)', textTransform: 'uppercase' }}>
                  OPTIMAL SELECTION:
                </span>
                <span style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  {recResult.recommended_model}
                </span>
              </div>
              <p style={{ margin: '3px 0 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {recResult.rationale}
              </p>
            </div>

            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cost per Turn</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-main)' }}>
                ${recResult.expected_cost_usd_per_turn?.toFixed(5) || '0.00028'} USD
                <span style={{ color: 'var(--primary-coral, #E8654A)', marginLeft: '4px' }}>
                  (৳{recResult.expected_cost_bdt_per_turn?.toFixed(3) || '0.034'} BDT)
                </span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Model Inventory Table */}
      <Card style={{ padding: '20px', borderRadius: '20px' }}>
        {/* Controls: Search & Provider Filters */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ position: 'relative', width: '280px' }}>
            <Search size={15} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search model name, provider, ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px 9px 34px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)',
                fontSize: '0.82rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {['ALL', 'groq', 'openai', 'anthropic', 'deepseek'].map((prov) => (
              <button
                key={prov}
                onClick={() => setProviderFilter(prov)}
                style={{
                  padding: '5px 12px',
                  borderRadius: '20px',
                  fontSize: '0.75rem',
                  fontWeight: providerFilter === prov ? 700 : 500,
                  border: '1px solid',
                  borderColor: providerFilter === prov ? 'var(--primary-coral, #E8654A)' : 'var(--border-glass)',
                  background: providerFilter === prov ? 'rgba(232, 101, 74, 0.15)' : 'var(--bg-elevated, rgba(255,255,255,0.05))',
                  color: providerFilter === prov ? 'var(--primary-coral, #E8654A)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {prov}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glass)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 12px' }}>MODEL & PROVIDER</th>
                <th style={{ padding: '10px 12px' }}>CONTEXT WINDOW</th>
                <th style={{ padding: '10px 12px' }}>TOOL CALLING</th>
                <th style={{ padding: '10px 12px' }}>INPUT / 1M TOKENS</th>
                <th style={{ padding: '10px 12px' }}>OUTPUT / 1M TOKENS</th>
                <th style={{ padding: '10px 12px' }}>GATEWAY CONNECTIVITY</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Loading model registry...
                  </td>
                </tr>
              ) : filteredModels.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No matching models found in registry.
                  </td>
                </tr>
              ) : (
                filteredModels.map((m) => {
                  const pingKey = `${m.provider}:${m.id}`;
                  const currentPing = pingStatus[pingKey];
                  const isPinging = pingingModel === pingKey;

                  // Price calculations in BDT (৳122.50/USD)
                  const inputBdt = ((m.pricing?.prompt_per_m_usd || 0.5) * 122.50).toFixed(1);
                  const outputBdt = ((m.pricing?.completion_per_m_usd || 1.5) * 122.50).toFixed(1);

                  return (
                    <tr
                      key={m.id}
                      style={{
                        borderBottom: '1px solid var(--border-glass)',
                        transition: 'background 0.15s ease'
                      }}
                    >
                      <td style={{ padding: '12px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{m.name || m.id}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ textTransform: 'uppercase', fontWeight: 600 }}>{m.provider}</span>
                          <span>·</span>
                          <code>{m.id}</code>
                        </div>
                      </td>

                      <td style={{ padding: '12px', color: 'var(--text-main)', fontWeight: 600 }}>
                        {m.context_window?.toLocaleString() || '128,000'} tokens
                      </td>

                      <td style={{ padding: '12px' }}>
                        {m.supports_tools !== false ? (
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle2 size={13} /> Native Function Calling
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Prompt Emulated</span>
                        )}
                      </td>

                      <td style={{ padding: '12px', color: 'var(--text-main)' }}>
                        <div>${m.pricing?.prompt_per_m_usd || '0.50'}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--primary-coral, #E8654A)' }}>
                          ৳{inputBdt} BDT
                        </div>
                      </td>

                      <td style={{ padding: '12px', color: 'var(--text-main)' }}>
                        <div>${m.pricing?.completion_per_m_usd || '1.50'}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--primary-coral, #E8654A)' }}>
                          ৳{outputBdt} BDT
                        </div>
                      </td>

                      <td style={{ padding: '12px' }}>
                        {currentPing ? (
                          currentPing.status === 'ERROR' ? (
                            <span style={{ color: '#EF4444', fontSize: '0.72rem', fontWeight: 600 }}>
                              Offline: {currentPing.error}
                            </span>
                          ) : (
                            <span style={{ color: '#10B981', fontSize: '0.72rem', fontWeight: 700 }}>
                              {currentPing.latency} ms ({currentPing.time})
                            </span>
                          )
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Not pinged</span>
                        )}
                      </td>

                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePing(m.provider, m.id)}
                          disabled={isPinging}
                          style={{ fontSize: '0.72rem', padding: '4px 10px', borderRadius: '12px' }}
                        >
                          {isPinging ? 'Pinging...' : 'Ping Gateway'}
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
