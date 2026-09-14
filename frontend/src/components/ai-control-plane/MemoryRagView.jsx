import React, { useState } from 'react';
import {
  Layers,
  Search,
  Database,
  Sliders,
  CheckCircle2,
  FileText,
  Sparkles,
  Zap,
  Bookmark,
  ShieldCheck
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { testAiRagRetrieval } from '../../services/aiControlPlaneApi';

const KNOWLEDGE_SOURCES = [
  { id: 'kb_sky_tower', title: 'GLG Sky Tower Gulshan-2 Master Factsheet', chunks: 142, dims: 1536, status: 'Indexed', type: 'PDF' },
  { id: 'kb_crown_jewel', title: 'GLG Crown Jewel Banani Unit Specifications', chunks: 98, dims: 1536, status: 'Indexed', type: 'PDF' },
  { id: 'kb_diplomatic', title: 'Diplomatic Heights Baridhara Brochure & Pricing', chunks: 116, dims: 1536, status: 'Indexed', type: 'PDF' },
  { id: 'kb_re_law', title: 'Bangladesh Real Estate Registration & RAJUK Compliance', chunks: 210, dims: 1536, status: 'Indexed', type: 'Markdown' }
];

export default function MemoryRagView({ agentSlug }) {
  const [topK, setTopK] = useState(4);
  const [alpha, setAlpha] = useState(0.65);
  const [chunkSize, setChunkSize] = useState(512);
  const [chunkOverlap, setChunkOverlap] = useState(64);
  const [query, setQuery] = useState('What are the payment milestones and handover date for GLG Sky Tower in Gulshan-2?');
  const [retrieving, setRetrieving] = useState(false);
  const [retrievalResult, setRetrievalResult] = useState(null);
  const [retrievalError, setRetrievalError] = useState(null);

  const [enableDynamicBelief, setEnableDynamicBelief] = useState(true);
  const [stmWindow, setStmWindow] = useState(10);

  const handleTestRetrieval = async () => {
    if (!query.trim()) return;
    setRetrieving(true);
    setRetrievalError(null);
    setRetrievalResult(null);
    try {
      const res = await testAiRagRetrieval(query, topK, alpha);
      setRetrievalResult(res);
    } catch (err) {
      setRetrievalError(err.message || 'RAG retrieval test failed');
    } finally {
      setRetrieving(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Banner */}
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
            <Layers size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              Hybrid RAG & Dynamic Belief Memory Engine
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Configure dense vector & sparse BM25 fusion (RRF k=60), inspect knowledge chunks, and test provenance grounding.
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
            pgvector HNSW Active
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Knowledge Sources & Chunking */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <Card style={{ padding: '20px', borderRadius: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Database size={18} color="var(--primary-coral, #E8654A)" />
                <h3 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
                  Indexed Knowledge Documents
                </h3>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748B)' }}>
                4 Sources / 566 Chunks
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {KNOWLEDGE_SOURCES.map((ks) => (
                <div key={ks.id} style={{
                  padding: '12px 14px',
                  borderRadius: '16px',
                  border: '1px solid var(--border-glass)',
                  background: 'var(--bg-elevated, #1E293B)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <FileText size={16} color="var(--primary-coral, #E8654A)" />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-main, #1E293B)' }}>
                        {ks.title}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted, #64748B)' }}>
                        {ks.chunks} chunks • {ks.dims} dims • {ks.type}
                      </div>
                    </div>
                  </div>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '20px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#10B981'
                  }}>
                    {ks.status}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* RAG Retrieval Parameters */}
          <Card style={{ padding: '20px', borderRadius: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Sliders size={18} color="var(--primary-coral, #E8654A)" />
              <h3 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700 }}>
                Hybrid Search Hyperparameters
              </h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>
                    Hybrid Balance (Alpha): <strong style={{ color: 'var(--primary-coral, #E8654A)' }}>{alpha.toFixed(2)}</strong>
                  </label>
                  <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                    {alpha > 0.5 ? 'Dense Vector Dominated' : 'Sparse Keyword Dominated'}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={alpha}
                  onChange={(e) => setAlpha(parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary-coral, #E8654A)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94A3B8' }}>
                  <span>0.00 (Pure BM25 / FTS)</span>
                  <span>0.50 (Balanced)</span>
                  <span>1.00 (Pure Vector HNSW)</span>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>
                    Top-K Retrieved Chunks: <strong style={{ color: 'var(--primary-coral, #E8654A)' }}>{topK}</strong>
                  </label>
                  <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Context Window Budget</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary-coral, #E8654A)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748B', marginBottom: '4px' }}>
                    CHUNK TOKEN SIZE
                  </label>
                  <input
                    type="number"
                    value={chunkSize}
                    onChange={(e) => setChunkSize(parseInt(e.target.value))}
                    style={{ width: '100%', padding: '6px 10px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.82rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748B', marginBottom: '4px' }}>
                    CHUNK OVERLAP
                  </label>
                  <input
                    type="number"
                    value={chunkOverlap}
                    onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
                    style={{ width: '100%', padding: '6px 10px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.82rem' }}
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Dynamic Belief & Memory */}
          <Card style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Bookmark size={18} color="var(--primary-coral, #E8654A)" />
              <h3 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700 }}>
                Memory & Dynamic Belief State
              </h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={enableDynamicBelief}
                  onChange={(e) => setEnableDynamicBelief(e.target.checked)}
                  style={{ width: '16px', height: '16px', accentColor: 'var(--primary-coral, #E8654A)' }}
                />
                <div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: '#1E293B' }}>
                    Enable Dynamic Belief Reflection
                  </div>
                  <div style={{ fontSize: '0.74rem', color: '#64748B' }}>
                    Extracts user budget, preferred locations, and family constraints into persistent profile memory.
                  </div>
                </div>
              </label>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748B', marginBottom: '4px' }}>
                  SHORT-TERM MEMORY BUFFER (TURNS)
                </label>
                <input
                  type="number"
                  value={stmWindow}
                  onChange={(e) => setStmWindow(parseInt(e.target.value))}
                  style={{ width: '100%', padding: '6px 10px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.82rem' }}
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Live RAG Retrieval Test Console */}
        <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Search size={18} color="var(--primary-coral, #E8654A)" />
              <h3 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700 }}>
                Live Hybrid RAG Provenance Test
              </h3>
            </div>
            <Button
              onClick={handleTestRetrieval}
              disabled={retrieving}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', fontSize: '0.82rem' }}
            >
              <Zap size={14} />
              <span>{retrieving ? 'Retrieving...' : 'Execute Hybrid Search'}</span>
            </Button>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', marginBottom: '6px' }}>
              REAL-ESTATE CUSTOMER INQUIRY
            </label>
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter customer question to test RAG retrieval..."
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '14px',
                border: '1px solid var(--border-glass)',
                background: 'var(--bg-input, #151C2C)',
                color: 'var(--text-main, #F8FAFC)',
                fontSize: '0.85rem',
                outline: 'none',
                resize: 'vertical'
              }}
            />
          </div>

          {retrievalError && (
            <div style={{ padding: '12px', borderRadius: '14px', background: 'rgba(239, 68, 68, 0.1)', color: '#DC2626', fontSize: '0.8rem' }}>
              {retrievalError}
            </div>
          )}

          {retrievalResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--bg-elevated, #1E293B)',
                border: '1px solid var(--border-glass)',
                color: 'var(--text-main, #CBD5E1)',
                borderRadius: '14px',
                fontSize: '0.78rem'
              }}>
                <span>Total Matches: <strong>{retrievalResult.results?.length || 0}</strong></span>
                <span>Latency: <strong>{retrievalResult.latency_ms || 18}ms</strong></span>
                <span>Fusion: <strong>RRF (k=60, α={alpha})</strong></span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '420px', overflowY: 'auto' }}>
                {retrievalResult.results?.map((item, idx) => (
                  <div key={idx} style={{
                    padding: '14px',
                    borderRadius: '16px',
                    border: '1px solid var(--border-glass)',
                    background: 'var(--bg-elevated, #1E293B)',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.02)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{
                          background: 'var(--primary-coral, #E8654A)',
                          color: '#FFFFFF',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '20px'
                        }}>
                          Rank #{idx + 1}
                        </span>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-main, #1E293B)' }}>
                          {item.title || item.source_file || 'GLG Knowledge Chunk'}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#10B981' }}>
                        Score: {(item.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-main, #CBD5E1)', lineHeight: '1.4', background: 'var(--bg-input, #151C2C)', padding: '10px 12px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
                      "{item.chunk_content || item.text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!retrieving && !retrievalResult && (
            <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted, #94A3B8)', fontSize: '0.84rem' }}>
              Click "Execute Hybrid Search" to simulate pgvector + BM25 reciprocal rank fusion against your knowledge base.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
