import React, { useState, useEffect, useCallback } from 'react';
import {
  UserCheck,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  FileCode,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  Edit3,
  Check,
  X
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiApprovals, decideAiApproval } from '../../services/aiControlPlaneApi';

export default function HumanApprovalView() {
  const [approvals, setApprovals] = useState([]);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [reviewerNotes, setReviewerNotes] = useState('');

  const loadApprovals = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getAiApprovals(statusFilter === 'ALL' ? null : statusFilter);
      const list = data.approvals || [];
      setApprovals(list);
      if (list.length > 0) {
        setSelectedApproval(list[0]);
        setEditedContent(list[0].generated_content || '');
      } else {
        setSelectedApproval(null);
        setEditedContent('');
      }
    } catch (err) {
      console.error('Failed to load approvals:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const handleSelect = (appr) => {
    setSelectedApproval(appr);
    setEditedContent(appr.generated_content || '');
    setIsEditing(false);
    setReviewerNotes('');
  };

  const handleDecision = async (decision) => {
    if (!selectedApproval) return;
    setActionLoading(true);
    try {
      await decideAiApproval(
        selectedApproval.id,
        decision,
        reviewerNotes || `Action marked as ${decision} by developer`,
        decision === 'EDITED' ? editedContent : null
      );
      setStatusMessage(`Request ${selectedApproval.id} marked as ${decision}!`);
      setIsEditing(false);
      await loadApprovals();
    } catch (err) {
      console.error('Decision error:', err);
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setActionLoading(false);
      setTimeout(() => setStatusMessage(null), 4000);
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
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <UserCheck size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              Human-in-the-Loop Production Approval Gate
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Review, certify, reject, or edit high-risk VIP site bookings, discount proposals, and contract terms.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', background: 'var(--bg-card)', border: '1px solid var(--border-glass)', borderRadius: '20px', padding: '3px' }}>
            <button
              onClick={() => setStatusFilter('PENDING')}
              style={{
                padding: '5px 14px',
                borderRadius: '16px',
                border: 'none',
                background: statusFilter === 'PENDING' ? 'var(--primary-coral, #E8654A)' : 'transparent',
                color: statusFilter === 'PENDING' ? '#FFFFFF' : 'var(--text-muted)',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              Pending ({approvals.filter(a => a.status === 'PENDING').length})
            </button>
            <button
              onClick={() => setStatusFilter('ALL')}
              style={{
                padding: '5px 14px',
                borderRadius: '16px',
                border: 'none',
                background: statusFilter === 'ALL' ? 'var(--primary-coral, #E8654A)' : 'transparent',
                color: statusFilter === 'ALL' ? '#FFFFFF' : 'var(--text-muted)',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              All History
            </button>
          </div>

          <button
            onClick={loadApprovals}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '7px 14px',
              borderRadius: '20px',
              background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
              border: '1px solid var(--border-glass)',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: 'var(--text-main)',
              cursor: 'pointer'
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div style={{ padding: '10px 16px', borderRadius: '14px', background: 'rgba(16, 185, 129, 0.12)', color: '#10B981', fontSize: '0.84rem', fontWeight: 600, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          {statusMessage}
        </div>
      )}

      {/* Main Grid: Approvals List & Certification Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '20px' }}>
        {/* Left: Approvals List */}
        <Card style={{ padding: '16px', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '700px', overflowY: 'auto' }}>
          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)', textTransform: 'uppercase' }}>
            Queue Items ({approvals.length})
          </span>

          {loading && approvals.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Loading approval requests...
            </div>
          ) : approvals.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No pending approval requests. High-risk tool calls will appear here automatically.
            </div>
          ) : (
            approvals.map((appr) => {
              const isSelected = selectedApproval?.id === appr.id;
              const isPending = appr.status === 'PENDING';

              return (
                <div
                  key={appr.id}
                  onClick={() => handleSelect(appr)}
                  style={{
                    padding: '14px',
                    borderRadius: '16px',
                    border: isSelected ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass)',
                    background: isSelected ? 'rgba(232, 101, 74, 0.12)' : 'var(--bg-elevated, rgba(255,255,255,0.05))',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? '0 4px 14px rgba(232, 101, 74, 0.15)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.74rem', fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                      {appr.id}
                    </span>
                    <span style={{
                      fontSize: '0.68rem',
                      fontWeight: 800,
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: appr.risk_level === 'HIGH' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: appr.risk_level === 'HIGH' ? '#F87171' : '#FBBF24'
                    }}>
                      {appr.risk_level || 'HIGH'} RISK
                    </span>
                  </div>

                  <h4 style={{ margin: '0 0 6px', fontSize: '0.88rem', fontWeight: 700, color: '#0F172A' }}>
                    {appr.action_type || 'APPROVAL_REQUEST'}
                  </h4>

                  <p style={{ margin: '0 0 8px', fontSize: '0.8rem', color: '#475569', lineHeight: 1.4 }}>
                    {appr.reason}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94A3B8' }}>
                    <span>Agent: <strong>{appr.agent_id}</strong></span>
                    <span style={{
                      fontWeight: 700,
                      color: isPending ? '#D97706' : '#059669'
                    }}>
                      {appr.status}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </Card>

        {/* Right: Detail & Action Studio */}
        <Card style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {selectedApproval ? (
            <>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #E2E8F0', paddingBottom: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#0F172A' }}>
                      {selectedApproval.action_type}
                    </h3>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: selectedApproval.status === 'PENDING' ? '#FEF3C7' : '#D1FAE5',
                      color: selectedApproval.status === 'PENDING' ? '#92400E' : '#065F46'
                    }}>
                      {selectedApproval.status}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.78rem', color: '#64748B' }}>
                    Triggered by <strong>{selectedApproval.agent_id}</strong> | Timestamp: {selectedApproval.created_at}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '7px 14px',
                      borderRadius: '16px',
                      background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                      border: '1px solid var(--border-glass)',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: 'var(--text-main)',
                      cursor: 'pointer'
                    }}
                  >
                    <Edit3 size={14} />
                    <span>{isEditing ? 'Cancel Edit' : 'Edit Content'}</span>
                  </button>
                </div>
              </div>

              {/* Risk Context Card */}
              <div style={{
                padding: '14px 16px',
                borderRadius: '16px',
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={16} color="#EF4444" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#F87171' }}>
                    Reason for Human Escalation
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.84rem', color: '#FCA5A5', lineHeight: 1.4 }}>
                  {selectedApproval.reason}
                </p>
              </div>

              {/* Context Data */}
              {selectedApproval.context_data && Object.keys(selectedApproval.context_data).length > 0 && (
                <div style={{ padding: '14px 16px', borderRadius: '16px', background: 'var(--bg-elevated, rgba(255,255,255,0.05))', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                    Payload Context Data
                  </span>
                  <pre style={{ margin: 0, fontSize: '0.78rem', fontFamily: 'monospace', color: 'var(--text-main)', whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(selectedApproval.context_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* Generated Content Box */}
              <div>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>
                  Generated Customer Draft & Proposed Action
                </span>

                {isEditing ? (
                  <textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    rows={6}
                    style={{
                      width: '100%',
                      padding: '12px 14px',
                      borderRadius: '16px',
                      border: '1px solid var(--primary-coral, #E8654A)',
                      background: 'var(--bg-input, #151C2C)',
                      color: 'var(--text-main, #F8FAFC)',
                      fontSize: '0.86rem',
                      fontFamily: 'inherit',
                      lineHeight: 1.5,
                      boxSizing: 'border-box',
                      outline: 'none'
                    }}
                  />
                ) : (
                  <div style={{
                    padding: '14px 16px',
                    borderRadius: '16px',
                    background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                    border: '1px solid var(--border-glass)',
                    fontSize: '0.86rem',
                    color: 'var(--text-main)',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap'
                  }}>
                    {selectedApproval.generated_content}
                  </div>
                )}
              </div>

              {/* Reviewer Notes Input */}
              {selectedApproval.status === 'PENDING' && (
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', display: 'block', marginBottom: '6px' }}>
                    Reviewer Notes (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Add audit cert notes (e.g. Certified against payment plan schedule #889)"
                    value={reviewerNotes}
                    onChange={(e) => setReviewerNotes(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '14px',
                      border: '1px solid var(--border-glass)',
                      background: 'var(--bg-input, #151C2C)',
                      color: 'var(--text-main, #F8FAFC)',
                      fontSize: '0.82rem',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              )}

              {/* Action Buttons */}
              {selectedApproval.status === 'PENDING' ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                  <button
                    onClick={() => handleDecision('REJECTED')}
                    disabled={actionLoading}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '10px 20px',
                      borderRadius: '16px',
                      background: 'rgba(239, 68, 68, 0.15)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      color: '#F87171',
                      fontSize: '0.86rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    <X size={16} />
                    <span>Reject Action</span>
                  </button>

                  {isEditing ? (
                    <button
                      onClick={() => handleDecision('EDITED')}
                      disabled={actionLoading}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '10px 24px',
                        borderRadius: '16px',
                        background: 'var(--primary-coral, #E8654A)',
                        border: 'none',
                        color: '#FFFFFF',
                        fontSize: '0.86rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      <Check size={16} />
                      <span>Save & Approve</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleDecision('APPROVED')}
                      disabled={actionLoading}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '10px 24px',
                        borderRadius: '16px',
                        background: '#059669',
                        border: 'none',
                        color: '#FFFFFF',
                        fontSize: '0.86rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      <Check size={16} />
                      <span>Approve & Execute</span>
                    </button>
                  )}
                </div>
              ) : (
                <div style={{
                  padding: '12px',
                  borderRadius: '14px',
                  background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                  border: '1px solid var(--border-glass)',
                  fontSize: '0.82rem',
                  color: 'var(--text-muted)',
                  textAlign: 'center'
                }}>
                  This request has been certified as <strong>{selectedApproval.status}</strong> by {selectedApproval.reviewer || 'developer'}.
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
              Select an item from the approval queue on the left to inspect details.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
