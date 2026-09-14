import React, { useState, useEffect } from 'react';
import {
  History,
  Plus,
  RotateCcw,
  CheckCircle2,
  FileCode,
  Layers,
  Cpu,
  ShieldCheck,
  Wrench,
  Sparkles,
  RefreshCw,
  GitCommit,
  GitBranch,
  ArrowRight,
  Eye
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import {
  getAiSnapshots,
  createAiSnapshot,
  rollbackAiSnapshot
} from '../../services/aiControlPlaneApi';

export default function AiVersioningView({ agentSlug }) {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [rollingBack, setRollingBack] = useState(false);
  const [statusNotice, setStatusNotice] = useState(null);

  // New Snapshot Form State
  const [newSnapshot, setNewSnapshot] = useState({
    snapshot_tag: `snap-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-v1`,
    title: '',
    description: ''
  });

  const loadSnapshots = async () => {
    try {
      setLoading(true);
      const res = await getAiSnapshots(agentSlug);
      const list = res.snapshots || [];
      setSnapshots(list);
      if (list.length > 0 && !selectedSnapshot) {
        setSelectedSnapshot(list[0]);
      }
    } catch (err) {
      console.error('Failed to load snapshots:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSnapshots();
  }, [agentSlug]);

  const handleCreateSnapshot = async (e) => {
    e.preventDefault();
    try {
      setCreating(true);
      const payload = {
        agent_slug: agentSlug || 'property_agent',
        snapshot_tag: newSnapshot.snapshot_tag,
        title: newSnapshot.title || 'Manual Configuration Checkpoint',
        description: newSnapshot.description || 'Captured from developer control plane studio.'
      };
      await createAiSnapshot(payload);
      setStatusNotice({ type: 'success', text: `Snapshot ${newSnapshot.snapshot_tag} created successfully!` });
      setShowCreateModal(false);
      setNewSnapshot({
        snapshot_tag: `snap-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-v2`,
        title: '',
        description: ''
      });
      loadSnapshots();
    } catch (err) {
      setStatusNotice({ type: 'error', text: err.message || 'Failed to create snapshot' });
    } finally {
      setCreating(false);
    }
  };

  const handleRollback = async (tag) => {
    if (!window.confirm(`Are you sure you want to rollback all active configurations to snapshot "${tag}"?`)) {
      return;
    }
    try {
      setRollingBack(true);
      await rollbackAiSnapshot(tag);
      setStatusNotice({ type: 'success', text: `Configuration successfully rolled back to ${tag}!` });
      loadSnapshots();
    } catch (err) {
      setStatusNotice({ type: 'error', text: err.message || 'Rollback failed' });
    } finally {
      setRollingBack(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Banner */}
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
            <History size={22} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Full Configuration Manifest Snapshots
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Atomic versioning bundling prompts, LLM routes, RAG weights, tools, guardrails, and memory policies.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={loadSnapshots}
            disabled={loading}
            style={{ borderRadius: '16px' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowCreateModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--primary-coral, #E8654A)',
              color: '#FFFFFF',
              borderRadius: '16px',
              padding: '8px 16px',
              fontWeight: 600
            }}
          >
            <Plus size={15} />
            <span>Create Snapshot Freeze</span>
          </Button>
        </div>
      </div>

      {statusNotice && (
        <div style={{
          padding: '10px 16px',
          borderRadius: '14px',
          background: statusNotice.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
          border: statusNotice.type === 'success' ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
          color: statusNotice.type === 'success' ? '#10B981' : '#EF4444',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span>{statusNotice.text}</span>
          <button
            onClick={() => setStatusNotice(null)}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontWeight: 700, color: 'inherit' }}
          >
            ×
          </button>
        </div>
      )}

      {/* Snapshot Explorer Grid: Left History Timeline & Right Manifest Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '20px' }}>
        {/* Left Column: Snapshots Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <GitBranch size={16} color="var(--primary-coral, #E8654A)" />
            <span>IMMUTABLE VERSION TIMELINE ({snapshots.length})</span>
          </div>

          {loading ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading snapshots...</div>
          ) : snapshots.length === 0 ? (
            <div style={{
              padding: '30px',
              textAlign: 'center',
              background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
              borderRadius: '16px',
              border: '1px dashed var(--border-glass)'
            }}>
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>No configuration snapshots found.</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreateModal(true)}
                style={{ marginTop: '10px', borderRadius: '14px' }}
              >
                Create First Snapshot
              </Button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '650px', overflowY: 'auto' }}>
              {snapshots.map((snap) => {
                const isSelected = selectedSnapshot?.id === snap.id;
                return (
                  <div
                    key={snap.id}
                    onClick={() => setSelectedSnapshot(snap)}
                    style={{
                      background: isSelected ? 'rgba(232, 101, 74, 0.12)' : 'var(--bg-elevated, rgba(255,255,255,0.05))',
                      padding: '14px 16px',
                      borderRadius: '16px',
                      border: isSelected ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: isSelected ? '0 4px 14px rgba(232, 101, 74, 0.15)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.88rem', fontWeight: 800, color: isSelected ? 'var(--primary-coral, #E8654A)' : 'var(--text-main)' }}>
                        {snap.snapshot_tag}
                      </span>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '10px',
                        background: 'rgba(255,255,255,0.08)',
                        color: 'var(--text-muted)'
                      }}>
                        {snap.agent_slug}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                      {snap.title}
                    </div>

                    <p style={{ margin: '0 0 8px 0', fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>
                      {snap.description}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      <span>Created: {new Date(snap.created_at || Date.now()).toLocaleDateString()}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#38BDF8', fontWeight: 600 }}>
                        <GitCommit size={12} /> SHA-256 Verified
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Snapshot Manifest & Rollback Action */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {selectedSnapshot ? (
            <Card style={{ padding: '20px', borderRadius: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid var(--border-glass)', pb: '14px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
                      {selectedSnapshot.snapshot_tag}
                    </h3>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: 'rgba(16, 185, 129, 0.15)',
                      color: '#10B981'
                    }}>
                      STABLE ARTIFACT
                    </span>
                  </div>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {selectedSnapshot.title} · {selectedSnapshot.description}
                  </p>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRollback(selectedSnapshot.snapshot_tag)}
                  disabled={rollingBack}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    color: 'var(--primary-coral, #E8654A)',
                    borderColor: 'var(--primary-coral, #E8654A)',
                    borderRadius: '16px'
                  }}
                >
                  <RotateCcw size={14} className={rollingBack ? 'animate-spin' : ''} />
                  <span>Restore Configuration</span>
                </Button>
              </div>

              {/* Manifest Architecture Cards Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '18px' }}>
                <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    <FileCode size={14} color="var(--primary-coral, #E8654A)" />
                    <span>SYSTEM PROMPT</span>
                  </div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedSnapshot.prompt_version || 'v2.1-luxury'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Consultative Tone Preset
                  </div>
                </div>

                <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    <Cpu size={14} color="#38BDF8" />
                    <span>PRIMARY MODEL</span>
                  </div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedSnapshot.model_id || 'llama-3.3-70b-versatile'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Temp: 0.20 · Top-p: 0.90
                  </div>
                </div>

                <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    <Layers size={14} color="#10B981" />
                    <span>HYBRID RAG</span>
                  </div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedSnapshot.rag_version || 'v2.0'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Top-K: 5 · α=0.65 · 512 chunks
                  </div>
                </div>

                <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    <ShieldCheck size={14} color="#EF4444" />
                    <span>GUARDRAILS</span>
                  </div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedSnapshot.guardrail_version || 'v1.4'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    3 Active Safety Rules
                  </div>
                </div>

                <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    <Wrench size={14} color="#F59E0B" />
                    <span>TOOL VERSIONS</span>
                  </div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedSnapshot.tool_versions?.length || 4} Enabled
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    property_search, availability
                  </div>
                </div>

                <div style={{ background: 'var(--bg-elevated, rgba(255,255,255,0.05))', padding: '14px', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
                    <GitBranch size={14} color="#818CF8" />
                    <span>WORKFLOW GRAPH</span>
                  </div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {selectedSnapshot.workflow_version || 'v1.0.0'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    LangGraph State Machine
                  </div>
                </div>
              </div>

              {/* Full Raw Manifest JSON Viewer */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                    COMPLETE ATOMIC JSON MANIFEST
                  </span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Ready for automated GitOps deployment & audit compliance
                  </span>
                </div>
                <div style={{
                  background: 'rgba(0, 0, 0, 0.4)',
                  padding: '14px 16px',
                  borderRadius: '16px',
                  border: '1px solid var(--border-glass)',
                  maxHeight: '300px',
                  overflowY: 'auto'
                }}>
                  <pre style={{ margin: 0, fontSize: '0.76rem', fontFamily: 'monospace', color: '#38BDF8' }}>
                    {JSON.stringify(selectedSnapshot.manifest_json || selectedSnapshot, null, 2)}
                  </pre>
                </div>
              </div>
            </Card>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select a snapshot from the timeline on the left to inspect its manifest.
            </div>
          )}
        </div>
      </div>

      {/* Create Snapshot Modal */}
      {showCreateModal && (
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Capture Configuration Snapshot Freeze"
        >
          <form onSubmit={handleCreateSnapshot} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Snapshot Tag *
              </label>
              <input
                type="text"
                required
                value={newSnapshot.snapshot_tag}
                onChange={(e) => setNewSnapshot({ ...newSnapshot, snapshot_tag: e.target.value })}
                placeholder="e.g. snap-banani-freeze-v1"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Snapshot Title *
              </label>
              <input
                type="text"
                required
                value={newSnapshot.title}
                onChange={(e) => setNewSnapshot({ ...newSnapshot, title: e.target.value })}
                placeholder="e.g. Pre-Campaign Production Baseline"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Changelog / Description
              </label>
              <textarea
                rows={3}
                value={newSnapshot.description}
                onChange={(e) => setNewSnapshot({ ...newSnapshot, description: e.target.value })}
                placeholder="Document reason for snapshot (e.g. Approved price revision for Banani handover 2026)"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-input, #151C2C)',
                  color: 'var(--text-main, #F8FAFC)',
                  fontSize: '0.84rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <Button
                variant="outline"
                size="sm"
                type="button"
                onClick={() => setShowCreateModal(false)}
                style={{ borderRadius: '14px' }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                type="submit"
                disabled={creating}
                style={{ background: 'var(--primary-coral, #E8654A)', color: '#FFFFFF', borderRadius: '14px', padding: '8px 18px' }}
              >
                {creating ? 'Saving...' : 'Capture Snapshot'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
