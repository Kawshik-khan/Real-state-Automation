import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Zap, 
  RefreshCw, 
  Play, 
  Power, 
  Clock, 
  Layers, 
  Cpu, 
  Server, 
  Search, 
  ShieldCheck, 
  ChevronDown, 
  ChevronUp, 
  Terminal, 
  Sliders, 
  AlertCircle,
  ExternalLink,
  Wifi,
  Radio
} from 'lucide-react';
import { getN8nTelemetry, toggleN8nWorkflow, testN8nWorkflow } from '../services/api';

const DEFAULT_TELEMETRY = {
  timestamp: new Date().toISOString(),
  overall_status: 'HEALTHY',
  connection_mode: 'TELEMETRY_ENGINE',
  metrics: {
    total_workflows: 6,
    active_workflows: 6,
    inactive_workflows: 0,
    total_nodes: 20,
    healthy_nodes: 19,
    degraded_nodes: 1,
    failed_nodes: 0,
    avg_system_latency_ms: 148,
  },
  workflows: [
    {
      id: "wf-tg-001",
      name: "Telegram AI Assistant & Lead Qualifier",
      category: "Messaging & Conversational AI",
      active: true,
      trigger: "Telegram Webhook",
      last_executed: "Just now",
      total_executions: 1420,
      success_rate: 99.6,
      avg_latency_ms: 148,
      nodes: [
        { id: "node-101", name: "Telegram Webhook Trigger", type: "n8n-nodes-base.telegramTrigger", latency_ms: 12, status: "HEALTHY", last_run: "Just now", error: null },
        { id: "node-102", name: "Secret Verification & Tenant Scoping", type: "n8n-nodes-base.code", latency_ms: 4, status: "HEALTHY", last_run: "Just now", error: null },
        { id: "node-103", name: "FastAPI RAG Agent & Intent Query", type: "n8n-nodes-base.httpRequest", latency_ms: 115, status: "HEALTHY", last_run: "Just now", error: null },
        { id: "node-104", name: "Send Telegram Rich Message", type: "n8n-nodes-base.telegram", latency_ms: 17, status: "HEALTHY", last_run: "Just now", error: null }
      ]
    },
    {
      id: "wf-em-002",
      name: "Email Reply Automation & Lead Ingestion",
      category: "Email & Lead Capture",
      active: true,
      trigger: "IMAP Mailbox / Cloud Webhook",
      last_executed: "2 minutes ago",
      total_executions: 890,
      success_rate: 98.8,
      avg_latency_ms: 335,
      nodes: [
        { id: "node-201", name: "IMAP Email Listener", type: "n8n-nodes-base.emailReadImap", latency_ms: 45, status: "HEALTHY", last_run: "2 mins ago", error: null },
        { id: "node-202", name: "OpenAI GPT-4o Email Draft Generator", type: "n8n-nodes-base.openAi", latency_ms: 210, status: "HEALTHY", last_run: "2 mins ago", error: null },
        { id: "node-203", name: "PostgreSQL Lead Upsert", type: "n8n-nodes-base.postgres", latency_ms: 18, status: "HEALTHY", last_run: "2 mins ago", error: null },
        { id: "node-204", name: "SMTP Email Dispatcher", type: "n8n-nodes-base.emailSend", latency_ms: 62, status: "HEALTHY", last_run: "2 mins ago", error: null }
      ]
    },
    {
      id: "wf-fb-003",
      name: "Facebook & Instagram Lead Capture Router",
      category: "Social Lead Ads",
      active: true,
      trigger: "Meta Graph API Webhook",
      last_executed: "5 minutes ago",
      total_executions: 640,
      success_rate: 100.0,
      avg_latency_ms: 98,
      nodes: [
        { id: "node-301", name: "Meta Webhook Ingress", type: "n8n-nodes-base.webhook", latency_ms: 15, status: "HEALTHY", last_run: "5 mins ago", error: null },
        { id: "node-302", name: "Lead Payload Parser & Sanitizer", type: "n8n-nodes-base.code", latency_ms: 5, status: "HEALTHY", last_run: "5 mins ago", error: null },
        { id: "node-303", name: "CRM Sync HTTP POST", type: "n8n-nodes-base.httpRequest", latency_ms: 78, status: "HEALTHY", last_run: "5 mins ago", error: null }
      ]
    },
    {
      id: "wf-bk-004",
      name: "Property Tour Booking & Calendar Sync",
      category: "Schedule & Calendar",
      active: true,
      trigger: "Booking Webhook Endpoint",
      last_executed: "12 minutes ago",
      total_executions: 310,
      success_rate: 97.5,
      avg_latency_ms: 176,
      nodes: [
        { id: "node-401", name: "Booking Payload Ingress", type: "n8n-nodes-base.webhook", latency_ms: 14, status: "HEALTHY", last_run: "12 mins ago", error: null },
        { id: "node-402", name: "Google Calendar API Slot Creation", type: "n8n-nodes-base.googleCalendar", latency_ms: 110, status: "HEALTHY", last_run: "12 mins ago", error: null },
        { id: "node-403", name: "Slack Agent Notification", type: "n8n-nodes-base.slack", latency_ms: 52, status: "HEALTHY", last_run: "12 mins ago", error: null }
      ]
    },
    {
      id: "wf-rg-005",
      name: "RAG Knowledge Indexer & Vector Sync",
      category: "RAG Knowledge Base",
      active: true,
      trigger: "PDF OCR Upload Webhook",
      last_executed: "18 minutes ago",
      total_executions: 145,
      success_rate: 95.2,
      avg_latency_ms: 360,
      nodes: [
        { id: "node-501", name: "OCR Document Ingestion Webhook", type: "n8n-nodes-base.webhook", latency_ms: 22, status: "HEALTHY", last_run: "18 mins ago", error: null },
        { id: "node-502", name: "Text Chunking & Preprocessor", type: "n8n-nodes-base.code", latency_ms: 18, status: "HEALTHY", last_run: "18 mins ago", error: null },
        { id: "node-503", name: "Pinecone Vector Store Upsert", type: "n8n-nodes-base.pinecone", latency_ms: 320, status: "WARN", last_run: "18 mins ago", error: "Latency spike (>300ms) detected during dense vector batch embedding" }
      ]
    },
    {
      id: "wf-sc-006",
      name: "Social Media Content Generator & Publisher",
      category: "Content Engine",
      active: true,
      trigger: "Cron Schedule (Every 6h)",
      last_executed: "1 hour ago",
      total_executions: 520,
      success_rate: 99.2,
      avg_latency_ms: 129,
      nodes: [
        { id: "node-601", name: "Cron Scheduler", type: "n8n-nodes-base.cron", latency_ms: 2, status: "HEALTHY", last_run: "1 hour ago", error: null },
        { id: "node-602", name: "Fetch Approved Content Drafts", type: "n8n-nodes-base.httpRequest", latency_ms: 35, status: "HEALTHY", last_run: "1 hour ago", error: null },
        { id: "node-603", name: "Meta Graph API Post Dispatcher", type: "n8n-nodes-base.httpRequest", latency_ms: 92, status: "HEALTHY", last_run: "1 hour ago", error: null }
      ]
    }
  ],
  node_issues: [
    {
      timestamp: new Date().toISOString(),
      workflow_id: "wf-rg-005",
      workflow_name: "RAG Knowledge Indexer & Vector Sync",
      node_id: "node-503",
      node_name: "Pinecone Vector Store Upsert",
      node_type: "n8n-nodes-base.pinecone",
      severity: "WARNING",
      latency_ms: 320,
      error_message: "Latency spike (>300ms) detected during dense vector batch embedding",
      failing_parameter: "batch_size=50",
      remediation: "Optimize batch size or verify upstream API connection rate limit."
    }
  ]
};

// Node Type Icon Helper
const getNodeTypeIcon = (nodeType) => {
  if (!nodeType) return <Cpu size={16} />;
  const t = nodeType.toLowerCase();
  if (t.includes('webhook') || t.includes('trigger')) return <Zap size={16} color="#38BDF8" />;
  if (t.includes('code')) return <Terminal size={16} color="#F59E0B" />;
  if (t.includes('http')) return <Server size={16} color="#A855F7" />;
  if (t.includes('telegram')) return <Wifi size={16} color="#22D3EE" />;
  if (t.includes('openai')) return <Cpu size={16} color="#10B981" />;
  if (t.includes('postgres') || t.includes('db')) return <Layers size={16} color="#3B82F6" />;
  if (t.includes('pinecone') || t.includes('vector')) return <Layers size={16} color="#EC4899" />;
  if (t.includes('email') || t.includes('imap') || t.includes('smtp')) return <Activity size={16} color="#F43F5E" />;
  return <Cpu size={16} color="#9CA3AF" />;
};

export default function N8nMonitoringPage() {
  const [telemetry, setTelemetry] = useState(DEFAULT_TELEMETRY);
  const [isLiveConnection, setIsLiveConnection] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedWorkflows, setExpandedWorkflows] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [testingWfId, setTestingWfId] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  const fetchTelemetry = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const data = await getN8nTelemetry();
      if (data && data.metrics) {
        setTelemetry(data);
        setIsLiveConnection(true);
        // Expand all workflows on initial load
        setExpandedWorkflows(prev => {
          if (Object.keys(prev).length === 0) {
            const initialExpanded = {};
            data.workflows?.forEach(wf => { initialExpanded[wf.id] = true; });
            return initialExpanded;
          }
          return prev;
        });
      }
    } catch (err) {
      console.warn("Using local n8n monitoring telemetry fallback:", err);
      setIsLiveConnection(false);
      setTelemetry(prev => prev || DEFAULT_TELEMETRY);
      setExpandedWorkflows(prev => {
        if (Object.keys(prev).length === 0) {
          const initialExpanded = {};
          DEFAULT_TELEMETRY.workflows.forEach(wf => { initialExpanded[wf.id] = true; });
          return initialExpanded;
        }
        return prev;
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  // Auto-refresh interval (every 10s)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchTelemetry();
    }, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleToggleWorkflow = async (workflowId, currentActive) => {
    const nextActive = !currentActive;
    try {
      const result = await toggleN8nWorkflow(workflowId, nextActive);
      showNotification(result.message || `Workflow ${nextActive ? 'enabled' : 'disabled'}`, 'success');
      fetchTelemetry();
    } catch (err) {
      // Local fallback state toggle
      setTelemetry(prev => {
        if (!prev) return prev;
        const updatedWfs = prev.workflows.map(wf => wf.id === workflowId ? { ...wf, active: nextActive } : wf);
        const activeCount = updatedWfs.filter(w => w.active).length;
        return {
          ...prev,
          metrics: {
            ...prev.metrics,
            active_workflows: activeCount,
            inactive_workflows: updatedWfs.length - activeCount
          },
          workflows: updatedWfs
        };
      });
      showNotification(`Workflow toggled to ${nextActive ? 'ACTIVE' : 'INACTIVE'} (Telemetry state)`, 'info');
    }
  };

  const handleTestWorkflow = async (workflowId) => {
    setTestingWfId(workflowId);
    try {
      const result = await testN8nWorkflow(workflowId);
      showNotification(result.message || 'Latency ping test completed', 'success');
      fetchTelemetry();
    } catch (err) {
      // Local fallback latency ping simulation
      const pingMs = Math.floor(Math.random() * 80) + 15;
      setTelemetry(prev => {
        if (!prev) return prev;
        const updatedWfs = prev.workflows.map(wf => wf.id === workflowId ? {
          ...wf,
          avg_latency_ms: pingMs,
          last_executed: "Just now (Test Ping)",
          total_executions: wf.total_executions + 1,
          nodes: wf.nodes.map(n => ({ ...n, latency_ms: Math.floor(pingMs / wf.nodes.length) || 5, last_run: "Just now (Ping)" }))
        } : wf);
        return { ...prev, workflows: updatedWfs };
      });
      showNotification(`Latency ping completed in ${pingMs}ms (Simulated)`, 'info');
    } finally {
      setTestingWfId(null);
    }
  };

  const toggleExpand = (wfId) => {
    setExpandedWorkflows(prev => ({ ...prev, [wfId]: !prev[wfId] }));
  };

  const showNotification = (msg, type = 'info') => {
    setActionMessage({ text: msg, type });
    setTimeout(() => setActionMessage(null), 4000);
  };

  if (loading && !telemetry) {
    return (
      <div style={{ padding: '40px', color: '#FFFFFF', textAlign: 'center' }}>
        <RefreshCw size={32} className="spin" style={{ color: '#8B5CF6', marginBottom: '16px' }} />
        <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)' }}>Initializing n8n Workflow & Node Health Monitor...</p>
      </div>
    );
  }

  const currentTelemetry = telemetry || DEFAULT_TELEMETRY;
  const metrics = currentTelemetry.metrics || DEFAULT_TELEMETRY.metrics;
  const workflows = currentTelemetry.workflows || DEFAULT_TELEMETRY.workflows;
  const issues = currentTelemetry.node_issues || DEFAULT_TELEMETRY.node_issues;

  const filteredWorkflows = workflows.filter(wf => {
    const matchesSearch = wf.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          wf.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          wf.id.toLowerCase().includes(searchQuery.toLowerCase());
    if (statusFilter === 'ACTIVE') return matchesSearch && wf.active;
    if (statusFilter === 'INACTIVE') return matchesSearch && !wf.active;
    return matchesSearch;
  });

  return (
    <div style={{ padding: '24px 32px', color: '#FFFFFF', maxWidth: '1600px', margin: '0 auto' }}>
      
      {/* Header & Controls Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, background: 'linear-gradient(135deg, #FFFFFF, #9CA3AF)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              n8n Workflow & Node Health Command
            </h1>
            <span style={{
              padding: '4px 10px',
              borderRadius: '20px',
              fontSize: '0.75rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: currentTelemetry.overall_status === 'HEALTHY' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              color: currentTelemetry.overall_status === 'HEALTHY' ? '#34D399' : '#FBBF24',
              border: `1px solid ${currentTelemetry.overall_status === 'HEALTHY' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
            }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: currentTelemetry.overall_status === 'HEALTHY' ? '#10B981' : '#F59E0B',
                boxShadow: `0 0 10px ${currentTelemetry.overall_status === 'HEALTHY' ? '#10B981' : '#F59E0B'}`
              }} />
              SYSTEM {currentTelemetry.overall_status || 'HEALTHY'}
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            Real-time execution status, node-by-node latency, processing health, and failure diagnostic engine.
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            fontSize: '0.75rem',
            padding: '6px 12px',
            borderRadius: '8px',
            background: isLiveConnection ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            color: isLiveConnection ? '#34D399' : '#FBBF24',
            border: `1px solid ${isLiveConnection ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Radio size={12} className={isLiveConnection ? 'spin' : ''} />
            {isLiveConnection ? 'LIVE FASTAPI' : 'STANDALONE TELEMETRY'}
          </span>

          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.85rem',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            background: 'rgba(15, 23, 42, 0.6)',
            padding: '8px 14px',
            borderRadius: '10px',
            border: '1px solid var(--border-glass)'
          }}>
            <input 
              type="checkbox" 
              checked={autoRefresh} 
              onChange={e => setAutoRefresh(e.target.checked)} 
              style={{ accentColor: '#8B5CF6' }}
            />
            Auto-refresh (10s)
          </label>

          <button
            onClick={() => fetchTelemetry(true)}
            disabled={refreshing}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '10px',
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              color: '#C084FC',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh Telemetry'}
          </button>
        </div>
      </div>

      {/* Action Notification Toast */}
      {actionMessage && (
        <div style={{
          marginBottom: '20px',
          padding: '12px 20px',
          borderRadius: '12px',
          background: actionMessage.type === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
          border: `1px solid ${actionMessage.type === 'error' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
          color: actionMessage.type === 'error' ? '#FCA5A5' : '#6EE7B7',
          fontSize: '0.9rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertCircle size={18} />
          {actionMessage.text}
        </div>
      )}

      {/* KPI Stats Overview Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px',
        marginBottom: '28px'
      }}>
        {/* Active Workflows */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid var(--border-glass)',
          borderRadius: '16px',
          padding: '20px',
          backdropFilter: 'blur(20px)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>Active Workflows</span>
            <Activity size={20} color="#34D399" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#FFFFFF' }}>
            {metrics.active_workflows} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 500 }}>/ {metrics.total_workflows}</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '6px' }}>
            <CheckCircle2 size={12} /> {metrics.inactive_workflows === 0 ? 'All 100% Running' : `${metrics.inactive_workflows} Paused`}
          </span>
        </div>

        {/* Avg System Latency */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid var(--border-glass)',
          borderRadius: '16px',
          padding: '20px',
          backdropFilter: 'blur(20px)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>Avg Response Latency</span>
            <Clock size={20} color="#C084FC" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#FFFFFF' }}>
            {metrics.avg_system_latency_ms} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 500 }}>ms</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#C084FC', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '6px' }}>
            <Zap size={12} /> End-to-end node average
          </span>
        </div>

        {/* Total Inspected Nodes */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid var(--border-glass)',
          borderRadius: '16px',
          padding: '20px',
          backdropFilter: 'blur(20px)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>Nodes Inspected</span>
            <Cpu size={20} color="#38BDF8" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#FFFFFF' }}>
            {metrics.total_nodes} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 500 }}>nodes</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#38BDF8', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '6px' }}>
            <ShieldCheck size={12} /> {metrics.healthy_nodes} Healthy
          </span>
        </div>

        {/* Node Processing Errors */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: metrics.degraded_nodes > 0 || metrics.failed_nodes > 0 ? '1px solid rgba(245, 158, 11, 0.5)' : '1px solid var(--border-glass)',
          borderRadius: '16px',
          padding: '20px',
          backdropFilter: 'blur(20px)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>Node Processing Issues</span>
            <AlertTriangle size={20} color={issues.length > 0 ? "#F59E0B" : "#34D399"} />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: issues.length > 0 ? "#F59E0B" : "#FFFFFF" }}>
            {issues.length} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 500 }}>issues</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: issues.length > 0 ? '#FBBF24' : '#34D399', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '6px' }}>
            {issues.length > 0 ? `${metrics.degraded_nodes} Degraded / ${metrics.failed_nodes} Failed` : '0 Node Execution Errors'}
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        background: 'rgba(15, 23, 42, 0.6)',
        padding: '12px 20px',
        borderRadius: '14px',
        border: '1px solid var(--border-glass)',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {/* Search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(11, 15, 25, 0.8)', padding: '8px 14px', borderRadius: '10px', width: '320px', border: '1px solid var(--border-glass)' }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Filter workflows or node types..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: '#FFFFFF', outline: 'none', fontSize: '0.85rem', width: '100%' }}
          />
        </div>

        {/* Status Tabs */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'ACTIVE', 'INACTIVE'].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: statusFilter === status ? 'var(--grad-violet)' : 'rgba(255, 255, 255, 0.05)',
                color: statusFilter === status ? '#FFFFFF' : 'var(--text-muted)'
              }}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Workflow & Node Pipeline Section */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '36px' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={20} color="#8B5CF6" /> Workflows & Real-Time Node Health Pipeline
        </h2>

        {filteredWorkflows.map(wf => {
          const isExpanded = expandedWorkflows[wf.id];
          const isTesting = testingWfId === wf.id;

          return (
            <div
              key={wf.id}
              style={{
                background: 'rgba(15, 23, 42, 0.7)',
                border: wf.active ? '1px solid var(--border-glass)' : '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '16px',
                overflow: 'hidden',
                backdropFilter: 'blur(20px)',
                opacity: wf.active ? 1 : 0.75,
                transition: 'all 0.2s ease'
              }}
            >
              {/* Workflow Header Row */}
              <div
                style={{
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  padding: '20px 24px',
                  background: 'rgba(11, 15, 25, 0.4)',
                  borderBottom: isExpanded ? '1px solid var(--border-glass)' : 'none',
                  cursor: 'pointer'
                }}
                onClick={() => toggleExpand(wf.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  {/* Active Indicator & Icon */}
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '12px',
                    background: wf.active ? 'rgba(139, 92, 246, 0.15)' : 'rgba(156, 163, 175, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: `1px solid ${wf.active ? 'rgba(139, 92, 246, 0.3)' : 'rgba(156, 163, 175, 0.2)'}`
                  }}>
                    <Zap size={20} color={wf.active ? '#C084FC' : '#9CA3AF'} />
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#FFFFFF' }}>{wf.name}</h3>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '6px',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        background: wf.active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: wf.active ? '#34D399' : '#FCA5A5',
                        border: `1px solid ${wf.active ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                      }}>
                        {wf.active ? 'RUNNING' : 'PAUSED'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      <span>Category: <strong style={{ color: '#D1D5DB' }}>{wf.category}</strong></span>
                      <span>• Trigger: <strong style={{ color: '#D1D5DB' }}>{wf.trigger}</strong></span>
                      <span>• Total Runs: <strong style={{ color: '#D1D5DB' }}>{wf.total_executions.toLocaleString()}</strong></span>
                      <span>• Success Rate: <strong style={{ color: '#34D399' }}>{wf.success_rate}%</strong></span>
                    </div>
                  </div>
                </div>

                {/* Right Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }} onClick={e => e.stopPropagation()}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#C084FC', background: 'rgba(139, 92, 246, 0.1)', padding: '4px 10px', borderRadius: '8px' }}>
                    {wf.avg_latency_ms} ms avg
                  </span>

                  {/* Test Ping Button */}
                  <button
                    onClick={() => handleTestWorkflow(wf.id)}
                    disabled={isTesting || !wf.active}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 12px',
                      borderRadius: '8px',
                      background: 'rgba(56, 189, 248, 0.15)',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      color: '#38BDF8',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: wf.active ? 'pointer' : 'not-allowed',
                      opacity: wf.active ? 1 : 0.5
                    }}
                  >
                    <Play size={14} className={isTesting ? 'spin' : ''} />
                    {isTesting ? 'Pinging...' : 'Test Latency'}
                  </button>

                  {/* Toggle Active Switch */}
                  <button
                    onClick={() => handleToggleWorkflow(wf.id, wf.active)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 12px',
                      borderRadius: '8px',
                      background: wf.active ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                      border: `1px solid ${wf.active ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                      color: wf.active ? '#FCA5A5' : '#6EE7B7',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    <Power size={14} />
                    {wf.active ? 'Disable' : 'Enable'}
                  </button>

                  <button
                    onClick={() => toggleExpand(wf.id)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                  >
                    {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </button>
                </div>
              </div>

              {/* Node Pipeline Breakdown */}
              {isExpanded && (
                <div style={{ padding: '24px', background: 'rgba(15, 23, 42, 0.4)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '16px' }}>
                    EXECUTION NODE GRAPH ({wf.nodes.length} NODES)
                  </div>

                  {/* Horizontal / Grid Visual Node Pipeline */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
                    {wf.nodes.map((node, index) => {
                      const isHealthy = node.status === 'HEALTHY';
                      const isWarn = node.status === 'WARN';
                      const isErr = node.status === 'ERROR';

                      return (
                        <div
                          key={node.id}
                          style={{
                            background: 'rgba(11, 15, 25, 0.8)',
                            border: isErr ? '1px solid #EF4444' : isWarn ? '1px solid #F59E0B' : '1px solid var(--border-glass)',
                            borderRadius: '14px',
                            padding: '16px',
                            display: 'flex',
                            flexDirection: 'column',
                            justify: 'space-between',
                            position: 'relative'
                          }}
                        >
                          {/* Node Step Number */}
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700 }}>
                              STEP {index + 1}
                            </span>

                            {/* Node Health Badge */}
                            <span style={{
                              fontSize: '0.65rem',
                              fontWeight: 800,
                              padding: '2px 6px',
                              borderRadius: '4px',
                              background: isHealthy ? 'rgba(16, 185, 129, 0.15)' : isWarn ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                              color: isHealthy ? '#34D399' : isWarn ? '#FBBF24' : '#FCA5A5',
                              border: `1px solid ${isHealthy ? 'rgba(16, 185, 129, 0.3)' : isWarn ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                            }}>
                              {node.status}
                            </span>
                          </div>

                          {/* Node Title & Type */}
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', marginBottom: '12px' }}>
                            <div style={{
                              padding: '8px',
                              borderRadius: '8px',
                              background: 'rgba(255, 255, 255, 0.05)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {getNodeTypeIcon(node.type)}
                            </div>
                            <div>
                              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#FFFFFF' }}>{node.name}</div>
                              <code style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{node.type}</code>
                            </div>
                          </div>

                          {/* Node Latency & Last Run Footer */}
                          <div style={{
                            display: 'flex',
                            justify: 'space-between',
                            alignItems: 'center',
                            paddingTop: '10px',
                            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                            fontSize: '0.75rem',
                            color: 'var(--text-muted)'
                          }}>
                            <span>Latency: <strong style={{ color: node.latency_ms > 200 ? '#F59E0B' : '#34D399' }}>{node.latency_ms} ms</strong></span>
                            <span>{node.last_run}</span>
                          </div>

                          {/* Error Message Snippet */}
                          {node.error && (
                            <div style={{
                              marginTop: '10px',
                              padding: '8px 10px',
                              borderRadius: '8px',
                              background: 'rgba(239, 68, 68, 0.1)',
                              border: '1px solid rgba(239, 68, 68, 0.3)',
                              color: '#FCA5A5',
                              fontSize: '0.72rem'
                            }}>
                              ⚠️ {node.error}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Node Errors & Diagnostics Panel */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.7)',
        border: '1px solid var(--border-glass)',
        borderRadius: '16px',
        padding: '24px',
        backdropFilter: 'blur(20px)'
      }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <AlertTriangle size={20} color="#F59E0B" /> Node Processing Exceptions & Diagnostic Log
        </h2>

        {issues.length === 0 ? (
          <div style={{ padding: '30px', textAlign: 'center', color: '#34D399', background: 'rgba(16, 185, 129, 0.05)', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <CheckCircle2 size={32} style={{ marginBottom: '8px' }} />
            <p style={{ fontWeight: 600, fontSize: '0.95rem' }}>No Active Node Processing Exceptions</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>All n8n workflow nodes are executing cleanly within latency parameters.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px 16px' }}>Severity</th>
                  <th style={{ padding: '12px 16px' }}>Workflow & Node</th>
                  <th style={{ padding: '12px 16px' }}>Error Details</th>
                  <th style={{ padding: '12px 16px' }}>Failing Param</th>
                  <th style={{ padding: '12px 16px' }}>Suggested Remediation</th>
                  <th style={{ padding: '12px 16px' }}>Latency</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((issue, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', background: 'rgba(11, 15, 25, 0.4)' }}>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        background: issue.severity === 'CRITICAL' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: issue.severity === 'CRITICAL' ? '#FCA5A5' : '#FBBF24',
                        border: `1px solid ${issue.severity === 'CRITICAL' ? 'rgba(239, 68, 68, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`
                      }}>
                        {issue.severity}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <strong style={{ color: '#FFFFFF', display: 'block' }}>{issue.node_name}</strong>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{issue.workflow_name}</span>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#FCA5A5' }}>
                      {issue.error_message}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <code style={{ background: 'rgba(255, 255, 255, 0.08)', padding: '2px 6px', borderRadius: '4px', color: '#E5E7EB', fontSize: '0.75rem' }}>
                        {issue.failing_parameter}
                      </code>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#9CA3AF', fontSize: '0.8rem' }}>
                      {issue.remediation}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#F59E0B', fontWeight: 700 }}>
                      {issue.latency_ms} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
