import React, { useState, useEffect, useMemo } from 'react';
import {
  KeyRound,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  ExternalLink,
  Eye,
  EyeOff,
  Zap,
  RotateCcw,
  Trash2,
  Lock,
  RefreshCw,
  Check,
  Cpu,
  Database,
  Send,
  Mail,
  Activity,
  Sparkles,
  Megaphone,
  Info
} from 'lucide-react';
import {
  getServiceIntegrations,
  saveServiceIntegration,
  testServiceIntegration,
  deleteServiceIntegration
} from '../../services/api';

const SERVICE_ICONS = {
  groq: Cpu,
  pinecone: Database,
  telegram: Send,
  gmail: Mail,
  langsmith: Activity,
  whatsapp: Sparkles,
  meta_ads: Megaphone,
  google_ads: Megaphone,
  tiktok_ads: Megaphone,
};

export default function ServiceIntegrationsTab() {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [showSecrets, setShowSecrets] = useState({});
  const [formValues, setFormValues] = useState({});
  const [testResults, setTestResults] = useState({});
  const [testingService, setTestingService] = useState({});
  const [savingService, setSavingService] = useState({});
  const [globalMessage, setGlobalMessage] = useState(null);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const res = await getServiceIntegrations();
      if (res && res.integrations) {
        setIntegrations(res.integrations);
        // Pre-fill editable forms with existing masked values or active fields
        const initialFormValues = {};
        res.integrations.forEach((item) => {
          initialFormValues[item.service_key] = {};
          if (item.active_credentials) {
            Object.entries(item.active_credentials).forEach(([k, v]) => {
              initialFormValues[item.service_key][k] = v || '';
            });
          }
        });
        setFormValues(initialFormValues);
      }
    } catch (err) {
      setGlobalMessage({
        type: 'error',
        text: `Failed to load integrations: ${err.message || 'Unknown network error'}`
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleInputChange = (serviceKey, fieldKey, value) => {
    setFormValues((prev) => ({
      ...prev,
      [serviceKey]: {
        ...(prev[serviceKey] || {}),
        [fieldKey]: value,
      },
    }));
    // Clear test result on edit so developer is encouraged to re-test
    if (testResults[serviceKey]) {
      setTestResults((prev) => {
        const next = { ...prev };
        delete next[serviceKey];
        return next;
      });
    }
  };

  const toggleSecretVisibility = (serviceKey, fieldKey) => {
    const key = `${serviceKey}_${fieldKey}`;
    setShowSecrets((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleTestConnection = async (serviceKey) => {
    setTestingService((prev) => ({ ...prev, [serviceKey]: true }));
    setTestResults((prev) => {
      const next = { ...prev };
      delete next[serviceKey];
      return next;
    });

    try {
      const draftCreds = formValues[serviceKey] || {};
      const res = await testServiceIntegration(serviceKey, draftCreds);
      setTestResults((prev) => ({
        ...prev,
        [serviceKey]: res,
      }));
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [serviceKey]: {
          success: false,
          message: err.message || 'Network handshake failed',
          tested_at: new Date().toISOString(),
        },
      }));
    } finally {
      setTestingService((prev) => ({ ...prev, [serviceKey]: false }));
    }
  };

  const handleSaveIntegration = async (serviceKey) => {
    setSavingService((prev) => ({ ...prev, [serviceKey]: true }));
    try {
      const credentials = formValues[serviceKey] || {};
      const res = await saveServiceIntegration(serviceKey, credentials, true);
      if (res && res.success) {
        setGlobalMessage({
          type: 'success',
          text: `Encrypted credentials saved for ${serviceKey.toUpperCase()} successfully.`,
        });
        setTimeout(() => setGlobalMessage(null), 4000);
        await fetchIntegrations(true);
      } else {
        throw new Error(res?.detail || 'Save rejected by server');
      }
    } catch (err) {
      setGlobalMessage({
        type: 'error',
        text: `Error saving ${serviceKey}: ${err.message}`,
      });
    } finally {
      setSavingService((prev) => ({ ...prev, [serviceKey]: false }));
    }
  };

  const handleDeleteIntegration = async (serviceKey) => {
    if (!window.confirm(`Disconnect and purge database credentials for ${serviceKey.toUpperCase()}? The system will revert to .env fallback if available.`)) {
      return;
    }
    try {
      const res = await deleteServiceIntegration(serviceKey);
      if (res && res.success) {
        setGlobalMessage({
          type: 'success',
          text: `Credentials cleared for ${serviceKey}. Reverted to environment default.`,
        });
        setTimeout(() => setGlobalMessage(null), 4000);
        await fetchIntegrations(true);
      }
    } catch (err) {
      setGlobalMessage({
        type: 'error',
        text: `Failed to disconnect ${serviceKey}: ${err.message}`,
      });
    }
  };

  // Stats calculation
  const stats = useMemo(() => {
    const total = integrations.length;
    const inDb = integrations.filter((i) => i.source === 'database').length;
    const inEnv = integrations.filter((i) => i.source === 'env_fallback').length;
    const unconfigured = integrations.filter((i) => i.source === 'none' || !i.is_configured).length;
    return { total, inDb, inEnv, unconfigured };
  }, [integrations]);

  const filteredIntegrations = useMemo(() => {
    if (categoryFilter === 'ALL') return integrations;
    if (categoryFilter === 'AI') return integrations.filter((i) => i.category === 'ai' || i.category === 'vector_db');
    if (categoryFilter === 'COMM') return integrations.filter((i) => i.category === 'communication');
    if (categoryFilter === 'OBS') return integrations.filter((i) => i.category === 'observability' || i.category === 'notifications');
    if (categoryFilter === 'ADS') return integrations.filter((i) => i.category === 'advertising');
    return integrations;
  }, [integrations, categoryFilter]);

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
        <p style={{ fontWeight: 600 }}>Loading Service Integrations & Encryption Status...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ── Security Architecture Banner ── */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.08) 0%, rgba(20, 20, 25, 0.4) 100%)',
        border: '1px solid var(--border-glass)',
        borderRadius: '16px',
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', gap: '14px', maxWidth: '780px' }}>
          <div style={{
            background: 'rgba(232, 101, 74, 0.15)',
            border: '1px solid rgba(232, 101, 74, 0.3)',
            borderRadius: '12px',
            padding: '10px',
            height: 'fit-content',
            color: 'var(--accent-coral)'
          }}>
            <Lock size={22} />
          </div>
          <div>
            <h3 style={{ margin: '0 0 6px 0', fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Dynamic Secrets Management Vault
              <span style={{
                fontSize: '0.7rem',
                padding: '2px 8px',
                borderRadius: '12px',
                background: 'rgba(52, 211, 153, 0.15)',
                color: '#34d399',
                border: '1px solid rgba(52, 211, 153, 0.3)',
                fontWeight: 700
              }}>
                AES-256 Authenticated
              </span>
            </h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.45' }}>
              Connect, test, and rotate third-party API keys dynamically without modifying Render environment variables or restarting server containers.
              Only <strong>DATABASE_URL</strong>, <strong>JWT_SECRET</strong>, and <strong>AUTOMATION_SHARED_SECRET</strong> remain in Render; all services below are encrypted at rest in PostgreSQL and hot-reloaded into memory.
            </p>
          </div>
        </div>

        <button
          onClick={() => fetchIntegrations(true)}
          disabled={refreshing}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-glass)',
            color: 'var(--text-main)',
            padding: '9px 16px',
            borderRadius: '10px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: refreshing ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      {/* Global alert feedback */}
      {globalMessage && (
        <div style={{
          padding: '12px 18px',
          borderRadius: '10px',
          background: globalMessage.type === 'success' ? 'rgba(52, 211, 153, 0.12)' : 'rgba(239, 68, 68, 0.12)',
          border: `1px solid ${globalMessage.type === 'success' ? 'rgba(52, 211, 153, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          color: globalMessage.type === 'success' ? '#34d399' : '#ef4444',
          fontSize: '0.85rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {globalMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{globalMessage.text}</span>
        </div>
      )}

      {/* ── Key Metrics Cards ── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '14px'
      }}>
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-glass)',
          borderRadius: '12px',
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'rgba(232, 101, 74, 0.1)', color: 'var(--accent-coral)' }}>
            <KeyRound size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Total Services</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)' }}>{stats.total}</div>
          </div>
        </div>

        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-glass)',
          borderRadius: '12px',
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'rgba(52, 211, 153, 0.1)', color: '#34d399' }}>
            <ShieldCheck size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Encrypted in DB</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#34d399' }}>{stats.inDb}</div>
          </div>
        </div>

        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-glass)',
          borderRadius: '12px',
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
            <Info size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Environment Fallback (.env)</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#3b82f6' }}>{stats.inEnv}</div>
          </div>
        </div>

        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-glass)',
          borderRadius: '12px',
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'rgba(234, 179, 8, 0.1)', color: '#eab308' }}>
            <AlertTriangle size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Unconfigured</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: stats.unconfigured > 0 ? '#eab308' : 'var(--text-muted)' }}>{stats.unconfigured}</div>
          </div>
        </div>
      </div>

      {/* ── Category Filter Pills ── */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px' }}>
        {[
          { key: 'ALL', label: `All Services (${integrations.length})` },
          { key: 'AI', label: 'AI & Vector Index' },
          { key: 'COMM', label: 'Communication (Gmail & WhatsApp)' },
          { key: 'OBS', label: 'Alerts & Telemetry (Telegram & LangSmith)' },
          { key: 'ADS', label: 'Ad Platforms (Meta, Google, TikTok)' },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setCategoryFilter(f.key)}
            style={{
              background: categoryFilter === f.key ? 'var(--accent-coral)' : 'var(--bg-card)',
              color: categoryFilter === f.key ? '#fff' : 'var(--text-muted)',
              border: '1px solid var(--border-glass)',
              borderRadius: '20px',
              padding: '6px 14px',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* ── Integrations Grid ── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))',
        gap: '20px'
      }}>
        {filteredIntegrations.map((item) => {
          const Icon = SERVICE_ICONS[item.service_key] || KeyRound;
          const isDbSource = item.source === 'database';
          const isEnvSource = item.source === 'env_fallback';
          const isTesting = !!testingService[item.service_key];
          const isSaving = !!savingService[item.service_key];
          const currentTest = testResults[item.service_key];

          return (
            <div
              key={item.service_key}
              style={{
                background: 'var(--bg-card)',
                border: isDbSource ? '1px solid rgba(52, 211, 153, 0.3)' : '1px solid var(--border-glass)',
                borderRadius: '16px',
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '18px',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
              }}
            >
              {/* Card Header */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      padding: '10px',
                      borderRadius: '12px',
                      background: 'rgba(232, 101, 74, 0.1)',
                      color: 'var(--accent-coral)'
                    }}>
                      <Icon size={22} />
                    </div>
                    <div>
                      <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                        {item.display_name}
                      </h4>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {item.category}
                      </span>
                    </div>
                  </div>

                  {/* Status Badges */}
                  <div>
                    {isDbSource ? (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '4px 10px',
                        borderRadius: '20px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'rgba(52, 211, 153, 0.15)',
                        color: '#34d399',
                        border: '1px solid rgba(52, 211, 153, 0.3)'
                      }}>
                        <ShieldCheck size={12} /> Encrypted in DB
                      </span>
                    ) : isEnvSource ? (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '4px 10px',
                        borderRadius: '20px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'rgba(59, 130, 246, 0.15)',
                        color: '#3b82f6',
                        border: '1px solid rgba(59, 130, 246, 0.3)'
                      }}>
                        <Info size={12} /> Active via .env
                      </span>
                    ) : (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '4px 10px',
                        borderRadius: '20px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'rgba(239, 68, 68, 0.12)',
                        color: '#ef4444',
                        border: '1px solid rgba(239, 68, 68, 0.3)'
                      }}>
                        <AlertCircle size={12} /> Not Configured
                      </span>
                    )}
                  </div>
                </div>

                <p style={{ margin: '0 0 16px 0', fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  {item.description}
                </p>

                {/* Form Fields */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {item.fields && item.fields.map((f) => {
                    const secretKey = `${item.service_key}_${f.key}`;
                    const isPassword = f.type === 'password';
                    const isVisible = showSecrets[secretKey];
                    const val = formValues[item.service_key]?.[f.key] ?? '';

                    return (
                      <div key={f.key}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                            {f.label} {f.required && <span style={{ color: 'var(--accent-coral)' }}>*</span>}
                          </label>
                          {f.key === 'api_key' && item.docs_url && (
                            <a
                              href={item.docs_url}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                fontSize: '0.72rem',
                                color: 'var(--accent-coral)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '3px',
                                textDecoration: 'none'
                              }}
                            >
                              Get Key <ExternalLink size={10} />
                            </a>
                          )}
                        </div>

                        <div style={{ position: 'relative' }}>
                          <input
                            type={isPassword && !isVisible ? 'password' : 'text'}
                            value={val}
                            placeholder={f.placeholder}
                            onChange={(e) => handleInputChange(item.service_key, f.key, e.target.value)}
                            style={{
                              width: '100%',
                              padding: isPassword ? '9px 40px 9px 12px' : '9px 12px',
                              borderRadius: '8px',
                              border: '1px solid var(--border-glass)',
                              background: 'var(--bg-main)',
                              color: 'var(--text-main)',
                              fontSize: '0.85rem',
                              fontFamily: isPassword && !isVisible ? 'inherit' : 'monospace',
                              boxSizing: 'border-box',
                              outline: 'none',
                              transition: 'border-color 0.2s',
                            }}
                          />
                          {isPassword && (
                            <button
                              type="button"
                              onClick={() => toggleSecretVisibility(item.service_key, f.key)}
                              style={{
                                position: 'absolute',
                                right: '10px',
                                top: '50%',
                                transform: 'translateY(-50%)',
                                background: 'transparent',
                                border: 'none',
                                color: 'var(--text-muted)',
                                cursor: 'pointer',
                                padding: '4px',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                              title={isVisible ? 'Hide value' : 'Show value'}
                            >
                              {isVisible ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Live Test Results Feedback Box */}
              {currentTest && (
                <div style={{
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: currentTest.success ? 'rgba(52, 211, 153, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                  border: `1px solid ${currentTest.success ? 'rgba(52, 211, 153, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '8px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                    {currentTest.success ? <CheckCircle2 size={16} color="#34d399" /> : <AlertCircle size={16} color="#ef4444" />}
                    <span style={{ color: currentTest.success ? '#34d399' : '#ef4444', fontWeight: 600 }}>
                      {currentTest.message}
                    </span>
                  </div>
                  {currentTest.latency_ms !== undefined && (
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', fontFamily: 'monospace' }}>
                      {currentTest.latency_ms} ms
                    </span>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'space-between', paddingTop: '10px', borderTop: '1px solid var(--border-glass)' }}>
                <button
                  type="button"
                  onClick={() => handleTestConnection(item.service_key)}
                  disabled={isTesting}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-glass)',
                    background: 'var(--bg-main)',
                    color: 'var(--text-main)',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: isTesting ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <Zap size={14} className={isTesting ? 'animate-spin' : ''} color={isTesting ? 'var(--accent-coral)' : '#eab308'} />
                  {isTesting ? 'Testing Ping...' : 'Test Connection'}
                </button>

                <div style={{ display: 'flex', gap: '8px' }}>
                  {isDbSource && (
                    <button
                      type="button"
                      onClick={() => handleDeleteIntegration(item.service_key)}
                      title="Clear DB credentials and fall back to environment variables"
                      style={{
                        padding: '8px 12px',
                        borderRadius: '8px',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        background: 'rgba(239, 68, 68, 0.08)',
                        color: '#ef4444',
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => handleSaveIntegration(item.service_key)}
                    disabled={isSaving}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      borderRadius: '8px',
                      border: 'none',
                      background: 'var(--accent-coral)',
                      color: '#ffffff',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      cursor: isSaving ? 'not-allowed' : 'pointer',
                      boxShadow: '0 2px 8px rgba(232, 101, 74, 0.3)',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {isSaving ? <RefreshCw size={14} className="animate-spin" /> : <Check size={14} />}
                    {isSaving ? 'Encrypting...' : 'Save & Connect'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
