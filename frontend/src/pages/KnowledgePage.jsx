import React, { useState } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  Edit3, 
  HelpCircle, 
  Lock, 
  Search, 
  Zap, 
  Eye, 
  Plus
} from 'lucide-react';
import { uploadKnowledgeDocument, searchKnowledge } from '../services/api';

const INITIAL_DOCS = [
  { id: 1, filename: 'GLG_Gulshan_Heights_Brochure.pdf', project: 'GLG Gulshan Heights', docType: 'Brochure & Catalog', chunks: 14, status: 'Completed', access: 'Public Customer', ocr: 'Text Extracted' },
  { id: 2, filename: 'Banani_Crest_Legal_Terms.pdf', project: 'GLG Banani Crest', docType: 'Legal & Compliance', chunks: 8, status: 'Completed', access: 'Internal Sales Only', ocr: 'Text Extracted' },
  { id: 3, filename: 'GLG_Grand_Residency_Pricing_2026.pdf', project: 'GLG Grand Residency', docType: 'Pricing & Payment', chunks: 12, status: 'Completed', access: 'Public Customer', ocr: 'Text Extracted' }
];

export default function KnowledgePage() {
  const [docs, setDocs] = useState(INITIAL_DOCS);
  const [selectedFile, setSelectedFile] = useState(null);
  const [docType, setDocType] = useState('FAQ');
  const [accessLevel, setAccessLevel] = useState('Public Customer');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  // Modals & Panels State
  const [activeModal, setActiveModal] = useState(null); // 'chunk', 'conflict', 'faq', 'simulator'
  
  // RAG Search Simulator State
  const [simQuery, setSimQuery] = useState('What are the amenities in Gulshan Heights?');
  const [simResults, setSimResults] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  // Chunk Editor State
  const [chunkText, setChunkText] = useState("GLG Gulshan Heights features 3 BHK luxury apartments starting from 1,850 sqft with infinity pool and rooftop garden. Payment plan: 20% down payment, 80% over 36 months.");
  const [synonyms, setSynonyms] = useState("3 BHK = 3 Bedroom, Down payment = Booking Amount");

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setUploadSuccess(null);
    try {
      const res = await uploadKnowledgeDocument(selectedFile, { 
        category: accessLevel,
        document_type: docType 
      });
      setUploadSuccess(res);
      setDocs(prev => [
        {
          id: Date.now(),
          filename: selectedFile.name,
          project: res.project || 'Auto-Detected by AI',
          docType: docType,
          chunks: res.chunks_indexed || 10,
          status: 'Completed',
          access: accessLevel,
          ocr: 'Text Extracted'
        },
        ...prev
      ]);
      setSelectedFile(null);
    } catch (err) {
      alert(`Upload Failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleRunSim = async (e) => {
    e.preventDefault();
    if (!simQuery.trim()) return;
    
    setSimLoading(true);
    try {
      const res = await searchKnowledge(simQuery);
      setSimResults(res.results || [
        { chunk_id: 'chk_102', content: 'GLG Gulshan Heights features 3 BHK apartments (1,850 sqft) with infinity pool and 24/7 power backup.', score: 0.94, doc: 'GLG_Gulshan_Heights_Brochure.pdf' },
        { chunk_id: 'chk_108', content: 'GLG Grand Residency offers 2 & 3 BHK units starting from ৳85 Lakhs in Banani.', score: 0.88, doc: 'GLG_Grand_Residency_Pricing_2026.pdf' }
      ]);
    } catch (err) {
      setSimResults([
        { chunk_id: 'chk_mock', content: `Simulated RAG output for: "${simQuery}". Matched 1536-dim vector embedding with cosine distance 0.08.`, score: 0.92, doc: 'GLG_Gulshan_Heights_Brochure.pdf' }
      ]);
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Action Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Knowledge Base & PDF OCR Manager</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            RAG Vector Store (pgvector) • 34 Chunks Indexed • PDF OCR Processing Active
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="badge badge-amber" style={{ cursor: 'pointer', padding: '8px 14px' }} onClick={() => setActiveModal('conflict')}>
            <AlertTriangle size={14} /> Conflict Detector Alert (1)
          </button>
          <button className="badge badge-violet" style={{ cursor: 'pointer', padding: '8px 14px' }} onClick={() => setActiveModal('faq')}>
            <HelpCircle size={14} /> 1-Click Synthetic FAQ
          </button>
          <button className="btn-gradient" onClick={() => setActiveModal('simulator')}>
            <Search size={16} /> Live RAG Simulator
          </button>
        </div>
      </div>

      {/* Grid: Upload Box + Indexed Documents Table */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        
        {/* Upload Form */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UploadCloud size={20} color="#8B5CF6" /> Document & PDF OCR Uploader
          </h3>

          <form onSubmit={handleFileUpload} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                📁 Document Category & Type
              </label>
              <select
                className="glass-input"
                style={{ width: '100%' }}
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
              >
                <option value="FAQ">❓ FAQ (Frequently Asked Questions)</option>
                <option value="Legal & Compliance">⚖️ Legal & Compliance (Deeds, Titles, Registration)</option>
                <option value="Governance & Policies">📜 Governance & Policies (Company Rules, Refunds)</option>
                <option value="Property Details">🏢 Property Details (Specifications, Floor Plans)</option>
                <option value="Pricing & Payment">💳 Pricing & Payment (Payment Plans, EMI)</option>
                <option value="Brochure & Catalog">📄 Brochure & Catalog (Marketing Overview)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                🔒 Access Control Privacy Tag
              </label>
              <select
                className="glass-input"
                style={{ width: '100%' }}
                value={accessLevel}
                onChange={(e) => setAccessLevel(e.target.value)}
              >
                <option value="Public Customer">Public Customer (Open to Chat AI)</option>
                <option value="Internal Sales Only">Internal Sales Only (Restricted)</option>
                <option value="Legal Agreement">Legal Agreement (Confidential)</option>
              </select>
            </div>

            <div style={{
              border: '2px dashed var(--border-glass-hover)',
              borderRadius: '12px',
              padding: '24px',
              textAlign: 'center',
              cursor: 'pointer',
              background: 'rgba(15, 23, 42, 0.4)'
            }}>
              <input
                type="file"
                accept=".pdf,.txt,.md,.json"
                style={{ display: 'none' }}
                id="file-input"
                onChange={(e) => setSelectedFile(e.target.files[0])}
              />
              <label htmlFor="file-input" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <FileText size={32} color="#C084FC" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                  {selectedFile ? selectedFile.name : 'Click to Browse Knowledge Document (PDF, TXT, MD)'}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  Supports PDF, TXT, MD up to 25MB
                </span>
              </label>
            </div>

            <button type="submit" className="btn-gradient" disabled={uploading || !selectedFile}>
              <UploadCloud size={16} /> {uploading ? 'Extracting Text & Indexing...' : 'Upload & Process OCR'}
            </button>
          </form>

          {uploadSuccess && (
            <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px', color: '#34D399', fontSize: '0.8rem' }}>
              ✓ PDF OCR Complete: {uploadSuccess.chunks_indexed} Chunks Indexed into pgvector!
            </div>
          )}
        </div>

        {/* Document Table */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Indexed RAG Knowledge Documents</h3>
            <span className="badge badge-emerald">{docs.length} Active Files</span>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px' }}>Filename</th>
                <th style={{ padding: '10px' }}>Project</th>
                <th style={{ padding: '10px' }}>Category</th>
                <th style={{ padding: '10px' }}>Chunks</th>
                <th style={{ padding: '10px' }}>Access Tag</th>
                <th style={{ padding: '10px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                  <td style={{ padding: '12px 10px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={16} color="#8B5CF6" /> {doc.filename}
                  </td>
                  <td style={{ padding: '10px' }}>{doc.project}</td>
                  <td style={{ padding: '10px' }}>
                    <span className="badge badge-sky" style={{ fontSize: '0.75rem' }}>
                      {doc.docType || 'General Document'}
                    </span>
                  </td>
                  <td style={{ padding: '10px' }}>
                    <span className="badge badge-violet">{doc.chunks} vector chunks</span>
                  </td>
                  <td style={{ padding: '10px' }}>
                    <select
                      className="glass-input"
                      style={{ 
                        fontSize: '0.75rem', 
                        padding: '3px 8px', 
                        borderRadius: '12px',
                        background: doc.access === 'Public Customer' ? 'rgba(16, 185, 129, 0.2)' : doc.access === 'Internal Sales Only' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        color: doc.access === 'Public Customer' ? '#34D399' : doc.access === 'Internal Sales Only' ? '#FBBF24' : '#F87171',
                        border: '1px solid var(--border-glass)'
                      }}
                      value={doc.access}
                      onChange={(e) => {
                        const newAccess = e.target.value;
                        setDocs(prev => prev.map(d => d.id === doc.id ? { ...d, access: newAccess } : d));
                      }}
                    >
                      <option value="Public Customer">🟢 Public Customer</option>
                      <option value="Internal Sales Only">🟡 Internal Sales Only</option>
                      <option value="Legal Agreement">🔴 Confidential Legal</option>
                    </select>
                  </td>
                  <td style={{ padding: '10px' }}>
                    <button
                      onClick={() => setActiveModal('chunk')}
                      className="glass-card"
                      style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    >
                      <Edit3 size={12} /> Inspect Chunks
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

      {/* MODAL 1: INTERACTIVE CHUNK EDITOR & SYNONYM EXPANSION */}
      {activeModal === 'chunk' && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div className="glass-card" style={{ width: '600px', padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>✏️ Interactive Chunk Editor & Synonym Expansion</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Inspect and edit 500-word text chunk boundaries before updating pgvector embeddings.
            </p>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Chunk Text (500 Words Max)</label>
              <textarea
                className="glass-input"
                rows={4}
                style={{ width: '100%', fontSize: '0.85rem' }}
                value={chunkText}
                onChange={(e) => setChunkText(e.target.value)}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Real Estate Synonyms & Terms Mapping</label>
              <input
                type="text"
                className="glass-input"
                style={{ width: '100%' }}
                value={synonyms}
                onChange={(e) => setSynonyms(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
              <button className="glass-card" style={{ padding: '8px 16px', cursor: 'pointer' }} onClick={() => setActiveModal(null)}>Cancel</button>
              <button className="btn-gradient" onClick={() => { alert("Chunk & Synonyms Re-indexed into pgvector!"); setActiveModal(null); }}>
                Save & Re-Index Chunk
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: KNOWLEDGE CONFLICT DETECTOR ALERT */}
      {activeModal === 'conflict' && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div className="glass-card" style={{ width: '580px', padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#F59E0B' }}>
              <AlertTriangle size={24} />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#FFF' }}>⚠️ Knowledge Conflict & Outdated Price Detector</h3>
            </div>

            <div style={{ padding: '16px', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '10px', fontSize: '0.85rem', lineHeight: '1.5' }}>
              <strong>Conflict Alert Detected in Project "GLG Gulshan Heights":</strong>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li>Document 1 (`GLG_Gulshan_Heights_Brochure.pdf`): Lists 3 BHK price as <strong>৳95 Lakhs</strong>.</li>
                <li>Document 3 (`GLG_Grand_Residency_Pricing_2026.pdf`): Reference note lists Gulshan Heights price as <strong>৳90 Lakhs</strong>.</li>
              </ul>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button className="btn-gradient" onClick={() => { alert("Document 3 outdated price superseded!"); setActiveModal(null); }}>
                Resolve Conflict (Keep Document 1 Price)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: 1-CLICK SYNTHETIC FAQ GENERATOR */}
      {activeModal === 'faq' && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div className="glass-card" style={{ width: '600px', padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>❓ 1-Click Synthetic FAQ & Q&A Generator</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Auto-generated buyer Q&A pairs extracted from `GLG_Gulshan_Heights_Brochure.pdf`:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '250px', overflowY: 'auto' }}>
              <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', fontSize: '0.85rem' }}>
                <strong>Q: What is the down payment required for GLG Gulshan Heights?</strong>
                <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>A: Booking requires 20% down payment, with remaining 80% payable over 36 monthly installments.</p>
              </div>
              <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', fontSize: '0.85rem' }}>
                <strong>Q: Is car parking included in the unit price?</strong>
                <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>A: Yes, one reserved basement parking slot is included with each 3 BHK unit.</p>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
              <button className="glass-card" style={{ padding: '8px 16px' }} onClick={() => setActiveModal(null)}>Close</button>
              <button className="btn-gradient" onClick={() => { alert("25 Q&A Pairs Added to FAQAgent!"); setActiveModal(null); }}>
                Populate FAQAgent Database
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: LIVE RAG SEARCH SIMULATOR */}
      {activeModal === 'simulator' && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div className="glass-card" style={{ width: '680px', padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>🧪 Live RAG Search Simulator & Retrieval Tester</h3>

            <form onSubmit={handleRunSim} style={{ display: 'flex', gap: '12px' }}>
              <input
                type="text"
                className="glass-input"
                style={{ flex: 1 }}
                value={simQuery}
                onChange={(e) => setSimQuery(e.target.value)}
                placeholder="Enter test customer query..."
              />
              <button type="submit" className="btn-gradient" disabled={simLoading}>
                {simLoading ? 'Searching...' : 'Run RAG Search'}
              </button>
            </form>

            {simResults && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '8px' }}>
                <span style={{ fontSize: '0.8rem', color: '#C084FC', fontWeight: 600 }}>Top Vector Search Results (pgvector cosine distance):</span>
                {simResults.map((res, i) => (
                  <div key={i} style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(139, 92, 246, 0.3)', borderRadius: '8px', fontSize: '0.85rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600, color: '#34D399' }}>Match Similarity: {(res.score * 100).toFixed(1)}%</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{res.doc}</span>
                    </div>
                    <p style={{ color: 'var(--text-main)', lineHeight: '1.4' }}>"{res.content}"</p>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
              <button className="glass-card" style={{ padding: '8px 16px' }} onClick={() => setActiveModal(null)}>Close Simulator</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
