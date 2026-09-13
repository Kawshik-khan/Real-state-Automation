import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  Users, 
  AlertCircle, 
  FileSpreadsheet, 
  Volume2, 
  PieChart as PieChartIcon, 
  Sparkles,
  ArrowUpRight,
  Phone,
  Flame,
  Award,
  Zap,
  Activity
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { getAnalyticsReport } from '../services/api';

const DAILY_VOLUME_DATA = [
  { day: 'Mon', WhatsApp: 140, Facebook: 85, Instagram: 60, Website: 40 },
  { day: 'Tue', WhatsApp: 180, Facebook: 95, Instagram: 75, Website: 50 },
  { day: 'Wed', WhatsApp: 210, Facebook: 110, Instagram: 90, Website: 65 },
  { day: 'Thu', WhatsApp: 195, Facebook: 100, Instagram: 80, Website: 55 },
  { day: 'Fri', WhatsApp: 240, Facebook: 130, Instagram: 105, Website: 85 },
  { day: 'Sat', WhatsApp: 280, Facebook: 160, Instagram: 140, Website: 95 },
  { day: 'Sun', WhatsApp: 260, Facebook: 150, Instagram: 130, Website: 90 }
];

const INTENT_DATA = [
  { name: 'Property Search', value: 65, color: '#E8654A' },
  { name: 'FAQ & Pricing', value: 20, color: '#10B981' },
  { name: 'Site Visit Booking', value: 10, color: '#F59E0B' },
  { name: 'Other Queries', value: 5, color: '#06B6D4' }
];

const HOT_LEADS = [
  { name: 'John Doe', phone: '+880 1711-998877', score: 94, detail: '3 BHK in Gulshan 2 (Budget ৳1 Crore)', channel: 'whatsapp' },
  { name: 'Mahbub Alam', phone: '+880 1819-445566', score: 91, detail: '4 BHK Duplex in Banani (Budget ৳2 Crore)', channel: 'facebook' },
  { name: 'Farhana Ahmed', phone: '+880 1912-332211', score: 87, detail: '2 BHK in Dhanmondi 27 (Ready Handover)', channel: 'website' }
];

import { useToast } from '../components/ui/Toast';

export default function AnalyticsPage() {
  const { showToast } = useToast();
  const [playingAudio, setPlayingAudio] = useState(false);
  const [liveReport, setLiveReport] = useState(null);

  useEffect(() => {
    getAnalyticsReport()
      .then(res => setLiveReport(res))
      .catch(err => console.warn('Live analytics report fallback:', err));
  }, []);

  const toggleVoiceBriefing = () => {
    if ('speechSynthesis' in window) {
      if (playingAudio) {
        window.speechSynthesis.cancel();
        setPlayingAudio(false);
        showToast('AI Voice Briefing paused.', 'info');
      } else {
        window.speechSynthesis.cancel();
        const text = "Good morning executive team. The GLG Assets AI OS processed 240 customer inquiries with 94.2% resolution accuracy, capturing 12 hot leads valued at ৳14.8 Crore.";
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.05;
        utterance.onend = () => setPlayingAudio(false);
        utterance.onerror = () => setPlayingAudio(false);
        window.speechSynthesis.speak(utterance);
        setPlayingAudio(true);
        showToast('🔊 Streaming C-Suite Audio Briefing...', 'info');
      }
    } else {
      showToast('🔊 Audio briefing: 94.2% AI resolution accuracy across 240 inquiries.', 'info');
    }
  };

  const handleExportExecutivePDF = () => {
    showToast('Preparing branded C-Suite Executive Summary PDF briefing...', 'success');
    setTimeout(() => {
      window.print();
    }, 500);
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>Analytics &amp; Executive Command Center</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Operational Telemetry • Executive ROI Intelligence • Strategic Business Informatics
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="badge badge-amber" onClick={toggleVoiceBriefing} style={{ cursor: 'pointer', padding: '8px 14px' }}>
            <Volume2 size={14} /> {playingAudio ? '⏹ Stop Audio Briefing' : '🔊 Play AI Voice Briefing'}
          </button>
          <button className="btn-gradient" onClick={handleExportExecutivePDF}>
            <FileSpreadsheet size={16} /> 1-Click Executive PDF Briefing
          </button>
        </div>
      </div>

      {/* SECTION 1: CORE OPERATIONAL METRIC CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 500 }}>AI Self-Resolution %</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#059669', margin: '8px 0', letterSpacing: '-0.02em' }}>94.2%</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Zero Human Agent Intervention</span>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 500 }}>Human Escalation Rate</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#DC2626', margin: '8px 0', letterSpacing: '-0.02em' }}>5.8%</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Transferred to Sales Team</span>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 500 }}>Weekly Inquiry Volume</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--primary-coral)', margin: '8px 0', letterSpacing: '-0.02em' }}>1,405 Msgs</h3>
          <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>+24% vs last week</span>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 500 }}>Labor Cost Savings</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0891B2', margin: '8px 0', letterSpacing: '-0.02em' }}>৳5,20,000</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>$4,400 USD Saved This Month</span>
        </div>

      </div>

      {/* SECTION 2: CHARTS ROW (Daily Volume + Intent Breakdown) */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        
        {/* Daily Volume Bar Chart */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>Daily Message Volume by Channel</h3>
          <div style={{ height: '240px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={DAILY_VOLUME_DATA}>
                <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', borderRadius: '8px', color: 'var(--text-main)', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
                <Bar dataKey="WhatsApp" fill="#10B981" stackId="a" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Facebook" fill="#2563EB" stackId="a" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Instagram" fill="#E8654A" stackId="a" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Website" fill="#06B6D4" stackId="a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Customer Intent Pie Chart */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>Customer Intent Breakdown</h3>
          <div style={{ height: '200px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={INTENT_DATA} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={4}>
                  {INTENT_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-card)', borderRadius: '8px', color: 'var(--text-main)', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', border: '1px solid var(--border-glass)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.75rem' }}>
            {INTENT_DATA.map((item, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: item.color }} />
                <span style={{ color: 'var(--text-muted)' }}>{item.name} ({item.value}%)</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* SECTION 3: EXECUTIVE INTELLIGENCE CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        {/* Active Deal Pipeline Card */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)' }}>
              <DollarSign size={20} color="#059669" /> Active Deal Pipeline &amp; Conversion Velocity
            </h3>
            <span className="badge badge-emerald">৳14.8 Crore Active</span>
          </div>

          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            AI Response Speed: <strong style={{ color: 'var(--text-main)' }}>1.2 seconds</strong> vs Human Sales Agent Speed: <strong style={{ color: 'var(--text-main)' }}>18 minutes</strong>. 
            Lead qualification velocity accelerated by <strong style={{ color: '#059669' }}>15x</strong>.
          </p>

          <div style={{ padding: '16px', background: 'var(--bg-main)', borderRadius: '12px', border: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Qualified Leads</span>
              <h4 style={{ fontSize: '1.3rem', color: 'var(--text-main)', fontWeight: 800 }}>84</h4>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Avg Deal Size</span>
              <h4 style={{ fontSize: '1.3rem', color: '#059669', fontWeight: 800 }}>৳1.15 Crore</h4>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conversion Score</span>
              <h4 style={{ fontSize: '1.3rem', color: 'var(--primary-coral)', fontWeight: 800 }}>88/100</h4>
            </div>
          </div>
        </div>

        {/* Hot Lead Propensity Leaderboard Card */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)' }}>
              <Flame size={20} color="#DC2626" /> Hot Lead Propensity Leaderboard
            </h3>
            <span className="badge badge-rose">3 Action Required</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {HOT_LEADS.map((lead, i) => (
              <div key={i} style={{ padding: '12px 14px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)' }}>
                    {lead.name}
                    <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>Score {lead.score}/100</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{lead.detail}</span>
                </div>
                <button className="btn-gradient" style={{ padding: '6px 12px', fontSize: '0.75rem' }} onClick={() => showToast(`📞 Connecting outbound VoIP call to ${lead.name} (${lead.phone})...`, 'info')}>
                  <Phone size={12} /> Call Now
                </button>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* SECTION 4: STRATEGIC BUSINESS INFORMATICS GRID (6 WIDGETS) */}
      <div>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)' }}>
          <Sparkles size={20} color="var(--primary-coral)" /> 6 Strategic Business Informatics Widgets
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
          
          {/* Widget 1 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary-coral)', marginBottom: '8px' }}>
              1. 🏗️ Amenity Demand Matrix
            </h4>
            <ul style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.6', listStyle: 'none' }}>
              <li>• Rooftop Garden: <strong style={{ color: 'var(--text-main)' }}>38%</strong> of queries</li>
              <li>• Infinity Pool: <strong style={{ color: 'var(--text-main)' }}>29%</strong> of queries</li>
              <li>• Lake View Balcony: <strong style={{ color: 'var(--text-main)' }}>24%</strong> of queries</li>
              <li>• Smart Automation: <strong style={{ color: 'var(--text-main)' }}>18%</strong> of queries</li>
            </ul>
          </div>

          {/* Widget 2 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary-coral)', marginBottom: '8px' }}>
              2. 📉 Price Sensitivity Curve
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Optimal Conversion Bracket: <strong style={{ color: 'var(--text-main)' }}>৳85L – ৳1.1 Crore</strong>.<br />
              68% inquiry drop-off observed for units priced above ৳1.5 Crore in Banani.
            </p>
          </div>

          {/* Widget 3 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary-coral)', marginBottom: '8px' }}>
              3. 🎯 Marketing Channel ROI
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              WhatsApp Ads: <strong style={{ color: '#059669' }}>Highest Intent</strong> (Score 88/100).<br />
              Instagram Reels: <strong style={{ color: 'var(--primary-coral)' }}>Highest Lead Volume</strong> (420 msgs).
            </p>
          </div>

          {/* Widget 4 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary-coral)', marginBottom: '8px' }}>
              4. ⏱️ Funnel Velocity Diagnostic
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Inquiry &rarr; Brochure: <strong style={{ color: '#059669' }}>Immediate (1.2s)</strong><br />
              Brochure &rarr; Site Visit: <strong style={{ color: 'var(--text-main)' }}>Avg 4.2 Days</strong>
            </p>
          </div>

          {/* Widget 5 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary-coral)', marginBottom: '8px' }}>
              5. ⚔️ Buyer Objection Radar
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Top Objection: <em style={{ color: 'var(--text-main)' }}>"Parking slot fee extra"</em> (42 mentions).<br />
              Battlecard auto-dispatched to sales agents.
            </p>
          </div>

          {/* Widget 6 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary-coral)', marginBottom: '8px' }}>
              6. 🏠 Slow-Moving Inventory Risk
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Banani Crest 4 BHK Duplex units showing <strong style={{ color: '#DC2626' }}>70% lower inquiry volume</strong>.<br />
              Recommendation: Launch targeted expat ROI campaign.
            </p>
          </div>

        </div>
      </div>

    </div>
  );
}
