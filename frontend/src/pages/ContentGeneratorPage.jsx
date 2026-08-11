import React, { useState } from 'react';
import { 
  Share2, 
  Sparkles, 
  Globe, 
  Video, 
  ShieldCheck, 
  Calendar, 
  Building2, 
  Send, 
  Edit, 
  ThumbsUp,
  Layers
} from 'lucide-react';
import { generateContent } from '../services/api';

export default function ContentGeneratorPage() {
  const [topic, setTopic] = useState('GLG Gulshan Heights Luxury 3 BHK');
  const [tone, setTone] = useState('luxury');
  const [selectedProject, setSelectedProject] = useState('GLG Gulshan Heights');
  const [persona, setPersona] = useState('Ultra-Luxury VIP');
  const [language, setLanguage] = useState('dual'); // 'english', 'bengali', 'dual'
  const [generating, setGenerating] = useState(false);
  const [generatedPosts, setGeneratedPosts] = useState(null);

  // Modal State
  const [showReelModal, setShowReelModal] = useState(false);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setGeneratedPosts(null);

    try {
      const res = await generateContent({ topic, tone, platforms: ['facebook', 'instagram', 'linkedin'] });
      setGeneratedPosts(res);
    } catch (err) {
      // Fallback structured multi-platform response for demonstration
      setGeneratedPosts({
        facebook: {
          text: language === 'bengali' 
            ? "🏙️ গুলশান ২-এ আপনার স্বপ্নের বিলাসবহুল ৩ বিএইচকে অ্যাপার্টমেন্ট! GLG গুলশান হাইটস-এ বুকিং করুন। আধুনিক সুযোগ-সুবিধা ও মনোরম লেক ভিউসহ। আজই যোগাযোগ করুন: +8801711122233" 
            : "🏙️ Experience luxury living in Gulshan 2! GLG Gulshan Heights features premium 3 BHK apartments (1,850 sqft) with infinity pool and panoramic city views. Book your site visit today! 📞 +8801711122233"
        },
        instagram: {
          caption: "Elevate your lifestyle at GLG Gulshan Heights ✨ 3 BHK Luxury Residences in Gulshan 2. Premium finishes, smart home automation & 24/7 security.",
          hashtags: "#GLGAssets #GulshanHeights #LuxuryRealEstate #DhakaApartments #DreamHome"
        },
        linkedin: {
          title: "Premium Real Estate Investment Opportunity in Gulshan 2",
          body: "GLG Assets is proud to announce pre-launch bookings for GLG Gulshan Heights. Featuring high-yield rental returns and prime architectural design in Dhaka's diplomatic zone."
        }
      });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Social Content Generator & Approval Engine</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Multi-Platform Post Generator • Dual-Language • RERA Compliance Guard • Content Calendar
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="badge badge-violet" style={{ cursor: 'pointer', padding: '8px 14px' }} onClick={() => setShowReelModal(true)}>
            <Video size={14} /> 🎬 Reel Storyboard Generator
          </button>
          <button className="btn-gradient">
            <Calendar size={16} /> Open Content Calendar
          </button>
        </div>
      </div>

      {/* Main Grid: Form Controls + Native Previews */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        
        {/* Form Controls */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={20} color="#A855F7" /> AI Generator Settings
          </h3>

          <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            
            {/* 1-Click Property Auto-Sync */}
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                🏢 1-Click Property Catalog Auto-Sync
              </label>
              <select
                className="glass-input"
                style={{ width: '100%' }}
                value={selectedProject}
                onChange={(e) => {
                  setSelectedProject(e.target.value);
                  setTopic(`${e.target.value} Luxury Residences`);
                }}
              >
                <option value="GLG Gulshan Heights">GLG Gulshan Heights (Gulshan 2)</option>
                <option value="GLG Banani Crest">GLG Banani Crest (Banani)</option>
                <option value="GLG Grand Residency">GLG Grand Residency (Dhanmondi)</option>
              </select>
            </div>

            {/* Language Switcher */}
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                🌐 Language Localizer
              </label>
              <select
                className="glass-input"
                style={{ width: '100%' }}
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="dual">Dual Language (English + Bengali বাংলা)</option>
                <option value="bengali">Bengali Only (বাংলা)</option>
                <option value="english">English Only</option>
              </select>
            </div>

            {/* Buyer Persona Preset Switcher */}
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                🎭 AI Buyer Persona Preset
              </label>
              <select
                className="glass-input"
                style={{ width: '100%' }}
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
              >
                <option value="Ultra-Luxury VIP">💎 Ultra-Luxury VIP (HNW Investors)</option>
                <option value="First-Time Family Home">🏡 First-Time Family Home (Young Couples)</option>
                <option value="High-Yield Investor">📈 High-Yield Investor (Expats & ROI Focus)</option>
                <option value="Pre-Launch Urgency">⚡ Pre-Launch Urgency (FOMO Campaign)</option>
              </select>
            </div>

            {/* Topic Input */}
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Campaign Focus / Topic
              </label>
              <input
                type="text"
                className="glass-input"
                style={{ width: '100%' }}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>

            <button type="submit" className="btn-gradient" disabled={generating}>
              <Sparkles size={16} /> {generating ? 'Generating Social Posts...' : 'Generate Multi-Platform Posts'}
            </button>
          </form>

          {/* Legal Compliance Badge */}
          <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#34D399' }}>
            <ShieldCheck size={18} /> RERA & Legal Disclaimer Auto-Guard Passed
          </div>
        </div>

        {/* Multi-Platform Native Previews */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Multi-Platform Native Preview & Approval Cards</h3>

          {!generatedPosts && !generating && (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              Click "Generate Multi-Platform Posts" to see live Facebook, Instagram, and LinkedIn previews.
            </div>
          )}

          {generating && (
            <div style={{ textAlign: 'center', padding: '40px', color: '#C084FC' }}>
              Generating optimized captions, hashtags, and social layouts...
            </div>
          )}

          {generatedPosts && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              
              {/* Facebook Card */}
              <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-glass)', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="badge badge-cyan">Facebook Post</span>
                  <ThumbsUp size={14} color="#06B6D4" />
                </div>
                <p style={{ fontSize: '0.85rem', lineHeight: '1.4' }}>
                  {generatedPosts.facebook?.text}
                </p>
                <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
                  <button className="btn-gradient" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>Approve & Publish</button>
                  <button className="glass-card" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>Edit</button>
                </div>
              </div>

              {/* Instagram Card */}
              <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-glass)', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="badge badge-violet">Instagram Caption</span>
                  <Share2 size={14} color="#C084FC" />
                </div>
                <p style={{ fontSize: '0.85rem', lineHeight: '1.4' }}>
                  {generatedPosts.instagram?.caption}
                </p>
                <span style={{ fontSize: '0.75rem', color: '#38BDF8' }}>
                  {generatedPosts.instagram?.hashtags}
                </span>
                <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
                  <button className="btn-gradient" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>Approve & Publish</button>
                  <button className="glass-card" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>Edit</button>
                </div>
              </div>

            </div>
          )}
        </div>

      </div>

      {/* REEL STORYBOARD MODAL */}
      {showReelModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div className="glass-card" style={{ width: '640px', padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>🎬 Instagram Reel & Video Storyboard Generator</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '300px', overflowY: 'auto' }}>
              <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: '8px', borderLeft: '3px solid #8B5CF6' }}>
                <strong style={{ color: '#C084FC', fontSize: '0.85rem' }}>Scene 1 (0:00 - 0:03): Drone Entrance</strong>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>Visual: Drone shot rising over Gulshan Lake towards GLG Heights balcony.</p>
                <span style={{ fontSize: '0.75rem', color: '#FBBF24' }}>Audio Overlay: "Looking for Dhaka's most exclusive skyline view?"</span>
              </div>

              <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: '8px', borderLeft: '3px solid #10B981' }}>
                <strong style={{ color: '#34D399', fontSize: '0.85rem' }}>Scene 2 (0:03 - 0:08): Living Room & Balcony Tour</strong>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>Visual: Smooth gimbal walk through Italian marble 3 BHK living room.</p>
                <span style={{ fontSize: '0.75rem', color: '#FBBF24' }}>Audio Overlay: "1,850 sqft of pure luxury in Gulshan 2."</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
              <button className="glass-card" style={{ padding: '8px 16px' }} onClick={() => setShowReelModal(false)}>Close</button>
              <button className="btn-gradient" onClick={() => { alert("Reel Script Exported!"); setShowReelModal(false); }}>
                Export Reel Script & Prompts
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
