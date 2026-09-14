import React, { useState, useEffect, useMemo } from 'react';
import {
  Database,
  Search,
  Plus,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Download,
  FileJson,
  Layers,
  Sparkles,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Tag
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import { getAiDatasets, getAiDatasetExamples, addAiDatasetExample } from '../../services/aiControlPlaneApi';

export default function DatasetStudioView({ agentSlug }) {
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [examples, setExamples] = useState([]);
  const [loading, setLoading] = useState(true);
  const [examplesLoading, setExamplesLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [domainFilter, setDomainFilter] = useState('ALL');
  const [showAddModal, setShowAddModal] = useState(false);
  const [savingExample, setSavingExample] = useState(false);
  const [statusNotice, setStatusNotice] = useState(null);

  // New Example Form State
  const [newExample, setNewExample] = useState({
    input_message: '',
    expected_response: '',
    expected_facts: '',
    category: 'PRICE_INQUIRY',
    grounding_source: 'GLG_Sky_Tower_Brochure_2026.pdf'
  });

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const res = await getAiDatasets();
      const list = res.datasets || [];
      setDatasets(list);
      if (list.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadExamples = async (dsId) => {
    if (!dsId) return;
    try {
      setExamplesLoading(true);
      const res = await getAiDatasetExamples(dsId);
      setExamples(res.examples || []);
    } catch (err) {
      console.error('Failed to load dataset examples:', err);
    } finally {
      setExamplesLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDatasetId) {
      loadExamples(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  const activeDataset = useMemo(() => {
    return datasets.find((d) => d.id === selectedDatasetId) || datasets[0];
  }, [datasets, selectedDatasetId]);

  const filteredDatasets = useMemo(() => {
    return datasets.filter((d) => {
      const matchSearch = d.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.description?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchDomain = domainFilter === 'ALL' || d.category === domainFilter;
      return matchSearch && matchDomain;
    });
  }, [datasets, searchQuery, domainFilter]);

  const handleCreateExample = async (e) => {
    e.preventDefault();
    if (!selectedDatasetId || !newExample.input_message.trim()) return;

    try {
      setSavingExample(true);
      const factsArray = newExample.expected_facts
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      const payload = {
        input_message: newExample.input_message,
        expected_response: newExample.expected_response,
        expected_facts: factsArray,
        category: newExample.category,
        grounding_source: newExample.grounding_source
      };

      await addAiDatasetExample(selectedDatasetId, payload);
      setStatusNotice({ type: 'success', text: 'Golden benchmark case added successfully!' });
      setShowAddModal(false);
      setNewExample({
        input_message: '',
        expected_response: '',
        expected_facts: '',
        category: 'PRICE_INQUIRY',
        grounding_source: 'GLG_Sky_Tower_Brochure_2026.pdf'
      });
      loadExamples(selectedDatasetId);
    } catch (err) {
      setStatusNotice({ type: 'error', text: err.message || 'Failed to add example' });
    } finally {
      setSavingExample(false);
    }
  };

  const handleExportJsonl = () => {
    if (!examples.length) return;
    const jsonlContent = examples.map((ex) => JSON.stringify(ex)).join('\n');
    const blob = new Blob([jsonlContent], { type: 'application/jsonl' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeDataset?.name || 'dataset'}_export.jsonl`;
    a.click();
    URL.revokeObjectURL(url);
  };

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
              Golden Datasets & Grounding Corpus
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Curated ground-truth test suites, fine-tuning samples, and domain evaluation sets.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={loadDatasets}
            disabled={loading}
            style={{ borderRadius: '16px' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportJsonl}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '16px'
            }}
          >
            <Download size={14} />
            <span>Export JSONL</span>
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

      {/* Main Studio Grid: Left Sidebar (Datasets) & Right Workspace (Examples) */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
        {/* Left Column: Datasets Directory */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Search & Domain Filter */}
          <div style={{
            background: 'var(--bg-card)',
            padding: '14px',
            borderRadius: '20px',
            border: '1px solid var(--border-glass)',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px'
          }}>
            <div style={{ position: 'relative' }}>
              <Search size={15} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search datasets..."
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

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {['ALL', 'EVALUATION', 'FINE_TUNING', 'RED_TEAM'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setDomainFilter(cat)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '20px',
                    fontSize: '0.7rem',
                    fontWeight: domainFilter === cat ? 700 : 500,
                    border: '1px solid',
                    borderColor: domainFilter === cat ? 'var(--primary-coral, #E8654A)' : 'var(--border-glass)',
                    background: domainFilter === cat ? 'rgba(232, 101, 74, 0.15)' : 'var(--bg-elevated, rgba(255,255,255,0.05))',
                    color: domainFilter === cat ? 'var(--primary-coral, #E8654A)' : 'var(--text-muted)',
                    cursor: 'pointer'
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Dataset Cards List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '600px', overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading datasets...</div>
            ) : filteredDatasets.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No matching datasets.</div>
            ) : (
              filteredDatasets.map((ds) => {
                const isSelected = ds.id === selectedDatasetId;
                return (
                  <div
                    key={ds.id}
                    onClick={() => setSelectedDatasetId(ds.id)}
                    style={{
                      background: isSelected ? 'rgba(232, 101, 74, 0.12)' : 'var(--bg-elevated, rgba(255,255,255,0.05))',
                      padding: '14px',
                      borderRadius: '16px',
                      border: isSelected ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: isSelected ? '0 4px 14px rgba(232, 101, 74, 0.15)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: isSelected ? 'var(--primary-coral, #E8654A)' : 'var(--text-main)' }}>
                        {ds.name}
                      </span>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '12px',
                        background: 'rgba(255,255,255,0.08)',
                        color: 'var(--text-muted)'
                      }}>
                        {ds.category || 'DATASET'}
                      </span>
                    </div>

                    <p style={{ margin: '0 0 10px 0', fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>
                      {ds.description || 'Golden grounding benchmark corpus.'}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Layers size={13} /> {ds.total_examples || 0} cases
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10B981', fontWeight: 600 }}>
                        <CheckCircle2 size={13} /> {ds.quality_score_pct || 99}% QA Score
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Dataset Details & Interactive Examples Table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {activeDataset && (
            <Card style={{ padding: '20px', borderRadius: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {activeDataset.name}
                  </h3>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    ID: <code style={{ background: 'var(--bg-input, #151C2C)', color: 'var(--text-main)', padding: '2px 6px', borderRadius: '6px' }}>{activeDataset.id}</code> · Format: <b>JSONL</b> · Split: <b>80% Train / 10% Val / 10% Test</b>
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setShowAddModal(true)}
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
                    <Plus size={14} />
                    <span>Add Example</span>
                  </Button>
                </div>
              </div>

              {/* Examples List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0, fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    Annotated Golden Cases ({examples.length})
                  </h4>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    Ground-truth factual checks validated against Banani & Gulshan portfolio
                  </span>
                </div>

                {examplesLoading ? (
                  <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading test cases...</div>
                ) : examples.length === 0 ? (
                  <div style={{
                    padding: '40px 20px',
                    textAlign: 'center',
                    background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                    borderRadius: '16px',
                    border: '1px dashed var(--border-glass)'
                  }}>
                    <FileJson size={32} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600 }}>
                      No test cases in this dataset yet.
                    </p>
                    <p style={{ margin: '4px 0 12px 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      Add ground-truth prompts with expected pricing and handover facts.
                    </p>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setShowAddModal(true)}
                      style={{ borderRadius: '14px' }}
                    >
                      Add First Example
                    </Button>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {examples.map((ex, idx) => (
                      <div
                        key={ex.id || idx}
                        style={{
                          background: 'var(--bg-elevated, rgba(255,255,255,0.05))',
                          borderRadius: '16px',
                          border: '1px solid var(--border-glass)',
                          padding: '14px 16px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            padding: '3px 10px',
                            borderRadius: '12px',
                            background: 'rgba(232, 101, 74, 0.15)',
                            color: 'var(--primary-coral, #E8654A)'
                          }}>
                            CASE #{idx + 1} · {ex.category || 'FACT_CHECK'}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: '#10B981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle2 size={12} /> PII Masked & Clean
                          </span>
                        </div>

                        <div>
                          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)' }}>USER PROMPT:</span>
                          <p style={{ margin: '2px 0 0 0', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-main)' }}>
                            "{ex.input_message}"
                          </p>
                        </div>

                        {ex.expected_facts && ex.expected_facts.length > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)' }}>EXPECTED FACTS:</span>
                            {ex.expected_facts.map((fact, fIdx) => (
                              <span
                                key={fIdx}
                                style={{
                                  fontSize: '0.7rem',
                                  padding: '2px 8px',
                                  borderRadius: '10px',
                                  background: 'rgba(59, 130, 246, 0.15)',
                                  color: '#60A5FA',
                                  fontWeight: 600
                                }}
                              >
                                {fact}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Add Example Modal */}
      {showAddModal && (
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add Golden Ground-Truth Case"
        >
          <form onSubmit={handleCreateExample} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Customer Inquiry / User Prompt *
              </label>
              <textarea
                required
                rows={2}
                value={newExample.input_message}
                onChange={(e) => setNewExample({ ...newExample, input_message: e.target.value })}
                placeholder="e.g. What is the handover schedule and square footage for 3 BHK in GLG Sky Tower Banani?"
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
                Expected Verified Facts (comma-separated keywords required for PASS gate) *
              </label>
              <input
                type="text"
                required
                value={newExample.expected_facts}
                onChange={(e) => setNewExample({ ...newExample, expected_facts: e.target.value })}
                placeholder="e.g. December 2026, 2150 sq.ft., 1.85 Crore"
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                  Category
                </label>
                <select
                  value={newExample.category}
                  onChange={(e) => setNewExample({ ...newExample, category: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '14px',
                    border: '1px solid var(--border-glass)',
                    fontSize: '0.84rem',
                    background: 'var(--bg-input, #151C2C)',
                    color: 'var(--text-main, #F8FAFC)'
                  }}
                >
                  <option value="PRICE_INQUIRY">PRICE_INQUIRY</option>
                  <option value="HANDOVER_TIMELINE">HANDOVER_TIMELINE</option>
                  <option value="PAYMENT_MILESTONES">PAYMENT_MILESTONES</option>
                  <option value="AMENITIES_SPECS">AMENITIES_SPECS</option>
                  <option value="LEGAL_TITLE">LEGAL_TITLE</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                  Provenance Document
                </label>
                <input
                  type="text"
                  value={newExample.grounding_source}
                  onChange={(e) => setNewExample({ ...newExample, grounding_source: e.target.value })}
                  placeholder="e.g. GLG_Sky_Tower_Brochure_2026.pdf"
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
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <Button
                variant="outline"
                size="sm"
                type="button"
                onClick={() => setShowAddModal(false)}
                style={{ borderRadius: '14px' }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                type="submit"
                disabled={savingExample}
                style={{ background: 'var(--primary-coral, #E8654A)', color: '#FFFFFF', borderRadius: '14px', padding: '8px 18px' }}
              >
                {savingExample ? 'Saving...' : 'Save Case'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
