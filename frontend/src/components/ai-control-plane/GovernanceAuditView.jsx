import React, { useState, useEffect } from 'react';
import {
  ScrollText,
  ShieldCheck,
  Search,
  Filter,
  Download,
  CheckCircle2,
  AlertCircle,
  Clock,
  User
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiAuditLogs } from '../../services/aiControlPlaneApi';

export default function GovernanceAuditView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterAction, setFilterAction] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const data = await getAiAuditLogs(100);
      if (data.logs) {
        setLogs(data.logs);
      }
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchAction = filterAction === 'all' || log.action === filterAction;
    const matchSearch = !searchQuery || 
      (log.entity && log.entity.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (log.actor && log.actor.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (log.action && log.action.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchAction && matchSearch;
  });

  const exportLogsAsJson = () => {
    const blob = new Blob([JSON.stringify(filteredLogs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai_audit_logs_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.08) 0%, rgba(243, 144, 114, 0.04) 100%)',
        border: '1px solid rgba(232, 101, 74, 0.2)',
        borderRadius: '20px',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <ScrollText size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              Governance, Compliance & Immutable Audit Trails
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Every agent prompt modification, model parameter change, rollback, and deployment is cryptographically logged.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={exportLogsAsJson}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '16px',
              background: 'var(--bg-card, #FFFFFF)',
              border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
              color: 'var(--text-main, #1E293B)',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Download size={14} />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Filter Controls */}
      <Card style={{ padding: '16px', borderRadius: '20px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted, #94A3B8)' }} />
            <input
              type="text"
              placeholder="Search by actor, entity, or action..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px 10px 38px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)',
                fontSize: '0.84rem'
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} color="var(--text-muted, #64748B)" />
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              style={{
                padding: '10px 14px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)',
                fontSize: '0.84rem'
              }}
            >
              <option value="all">All Action Types</option>
              <option value="publish_agent">Publish Agent</option>
              <option value="save_agent">Save Agent</option>
              <option value="deploy_release">Deploy Release</option>
              <option value="rollback_release">Rollback Release</option>
              <option value="test_tool">Test Tool</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Audit Log Table */}
      <Card style={{ padding: '20px', borderRadius: '20px' }}>
        <div style={{ border: '1px solid var(--border-glass, rgba(255, 255, 255, 0.08))', borderRadius: '16px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-elevated, #1E293B)', borderBottom: '1px solid var(--border-glass, rgba(255, 255, 255, 0.08))', textAlign: 'left', color: 'var(--text-muted, #94A3B8)' }}>
                <th style={{ padding: '10px 14px' }}>Timestamp</th>
                <th style={{ padding: '10px 14px' }}>Actor</th>
                <th style={{ padding: '10px 14px' }}>Action</th>
                <th style={{ padding: '10px 14px' }}>Entity Target</th>
                <th style={{ padding: '10px 14px' }}>Status</th>
                <th style={{ padding: '10px 14px' }}>Diff / Changes</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-glass, rgba(255, 255, 255, 0.06))' }}>
                    <td style={{ padding: '10px 14px', color: 'var(--text-muted, #64748B)', whiteSpace: 'nowrap' }}>
                      {log.created_at || '2026-09-14 14:00:00'}
                    </td>
                    <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-main, #1E293B)' }}>
                      {log.actor || 'developer@glg.com'}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <code style={{ fontSize: '0.78rem', background: 'var(--bg-elevated, #1E293B)', padding: '3px 8px', borderRadius: '20px', color: 'var(--primary-coral, #E8654A)', fontWeight: 600, border: '1px solid var(--border-glass, rgba(255,255,255,0.06))' }}>
                        {log.action}
                      </code>
                    </td>
                    <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-main, #1E293B)' }}>
                      {log.entity}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '3px 10px',
                        borderRadius: '20px',
                        background: log.status === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                        color: log.status === 'success' ? '#10B981' : '#EF4444',
                        border: log.status === 'success' ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid rgba(239, 68, 68, 0.25)'
                      }}>
                        {log.status?.toUpperCase() || 'SUCCESS'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <button
                        onClick={() => setSelectedLog(log)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--primary-coral, #E8654A)',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          textDecoration: 'underline'
                        }}
                      >
                        Inspect Payload
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted, #94A3B8)' }}>
                    No audit records matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Diff / Payload Inspector Modal */}
      {selectedLog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--bg-card, #1E293B)',
            borderRadius: '22px',
            border: '1px solid var(--border-glass, rgba(255, 255, 255, 0.12))',
            width: '600px',
            maxHeight: '80vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.4)'
          }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-glass, rgba(255, 255, 255, 0.08))', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-main, #F8FAFC)' }}>
                Audit Log Payload: {selectedLog.action}
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: 'var(--text-muted, #94A3B8)' }}
              >
                ✕
              </button>
            </div>
            <div style={{ padding: '20px', overflowY: 'auto', background: 'var(--bg-input, #0F172A)', color: '#F8FAFC', fontFamily: 'monospace', fontSize: '0.82rem', borderRadius: '0 0 22px 22px' }}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {JSON.stringify(selectedLog, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
