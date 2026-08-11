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
  { name: 'Property Search', value: 65, color: '#8B5CF6' },
  { name: 'FAQ & Pricing', value: 20, color: '#10B981' },
  { name: 'Site Visit Booking', value: 10, color: '#F59E0B' },
  { name: 'Other Queries', value: 5, color: '#06B6D4' }
];

const HOT_LEADS = [
  { name: 'John Doe', phone: '+880 1711-998877', score: 94, detail: '3 BHK in Gulshan 2 (Budget ৳1 Crore)', channel: 'whatsapp' },
  { name: 'Mahbub Alam', phone: '+880 1819-445566', score: 91, detail: '4 BHK Duplex in Banani (Budget ৳2 Crore)', channel: 'facebook' },
  { name: 'Farhana Ahmed', phone: '+880 1912-332211', score: 87, detail: '2 BHK in Dhanmondi 27 (Ready Handover)', channel: 'website' }
];

export default function AnalyticsPage() {
  const [playingAudio, setPlayingAudio] = useState(false);
  const [liveReport, setLiveReport] = useState(null);

  useEffect(() => {
    getAnalyticsReport()
      .then(res => setLiveReport(res))
      .catch(err => console.warn('Live analytics report fallback:', err));
  }, []);

  const toggleVoiceBriefing = () => {
    setPlayingAudio(!playingAudio);
    if (!playingAudio) {
      alert("🔊 AI Voice Briefing Playing: 'Good morning executive team. Yesterday, AI processed 240 customer inquiries with 94.2% resolution accuracy, capturing 12 hot leads valued at ৳14.8 Crore.'");
    }
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Analytics & Executive Command Center</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Operational Telemetry • Executive ROI Intelligence • Strategic Business Informatics
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="badge badge-amber" onClick={toggleVoiceBriefing} style={{ cursor: 'pointer', padding: '8px 14px' }}>
            <Volume2 size={14} /> {playingAudio ? 'Pause Audio Briefing' : '🔊 Play AI Voice Briefing'}
          </button>
          <button className="btn-gradient" onClick={() => alert("Downloading Branded C-Suite Executive Summary PDF Report...")}>
            <FileSpreadsheet size={16} /> 1-Click Executive PDF Briefing
          </button>
        </div>
      </div>

      {/* SECTION 1: CORE OPERATIONAL METRIC CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>AI Self-Resolution %</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34D399', margin: '8px 0' }}>94.2%</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Zero Human Agent Intervention</span>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Human Escalation Rate</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#F87171', margin: '8px 0' }}>5.8%</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Transferred to Sales Team</span>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Weekly Inquiry Volume</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#C084FC', margin: '8px 0' }}>1,405 Msgs</h3>
          <span style={{ fontSize: '0.75rem', color: '#34D399', fontWeight: 600 }}>+24% vs last week</span>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Labor Cost Savings</div>
          <h3 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#22D3EE', margin: '8px 0' }}>৳5,20,000</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>$4,400 USD Saved This Month</span>
        </div>

      </div>

      {/* SECTION 2: CHARTS ROW (Daily Volume + Intent Breakdown) */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        
        {/* Daily Volume Bar Chart */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Daily Message Volume by Channel</h3>
          <div style={{ height: '240px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={DAILY_VOLUME_DATA}>
                <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip contentStyle={{ background: '#0F172A', border: '1px solid var(--border-glass)', borderRadius: '8px', color: '#FFF' }} />
                <Bar dataKey="WhatsApp" fill="#10B981" stackId="a" />
                <Bar dataKey="Facebook" fill="#6366F1" stackId="a" />
                <Bar dataKey="Instagram" fill="#A855F7" stackId="a" />
                <Bar dataKey="Website" fill="#06B6D4" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Customer Intent Pie Chart */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Customer Intent Breakdown</h3>
          <div style={{ height: '200px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={INTENT_DATA} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={4}>
                  {INTENT_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0F172A', borderRadius: '8px', color: '#FFF' }} />
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
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <DollarSign size={20} color="#10B981" /> Active Deal Pipeline & Conversion Velocity
            </h3>
            <span className="badge badge-emerald">৳14.8 Crore Active</span>
          </div>

          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            AI Response Speed: <strong>1.2 seconds</strong> vs Human Sales Agent Speed: <strong>18 minutes</strong>. 
            Lead qualification velocity accelerated by <strong>15x</strong>.
          </p>

          <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '10px', display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Qualified Leads</span>
              <h4 style={{ fontSize: '1.3rem', color: '#FFF' }}>84</h4>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Avg Deal Size</span>
              <h4 style={{ fontSize: '1.3rem', color: '#34D399' }}>৳1.15 Crore</h4>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conversion Score</span>
              <h4 style={{ fontSize: '1.3rem', color: '#C084FC' }}>88/100</h4>
            </div>
          </div>
        </div>

        {/* Hot Lead Propensity Leaderboard Card */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Flame size={20} color="#F43F5E" /> Hot Lead Propensity Leaderboard
            </h3>
            <span className="badge badge-rose">3 Action Required</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {HOT_LEADS.map((lead, i) => (
              <div key={i} style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {lead.name}
                    <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>Score {lead.score}/100</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{lead.detail}</span>
                </div>
                <button className="btn-gradient" style={{ padding: '6px 12px', fontSize: '0.75rem' }} onClick={() => alert(`Calling ${lead.name} at ${lead.phone}...`)}>
                  <Phone size={12} /> Call Now
                </button>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* SECTION 4: STRATEGIC BUSINESS INFORMATICS GRID (6 WIDGETS) */}
      <div>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={20} color="#06B6D4" /> 6 Strategic Business Informatics Widgets
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
          
          {/* Widget 1 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#22D3EE', marginBottom: '8px' }}>
              1. 🏗️ Amenity Demand Matrix
            </h4>
            <ul style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.6', listStyle: 'none' }}>
              <li>• Rooftop Garden: <strong>38%</strong> of queries</li>
              <li>• Infinity Pool: <strong>29%</strong> of queries</li>
              <li>• Lake View Balcony: <strong>24%</strong> of queries</li>
              <li>• Smart Automation: <strong>18%</strong> of queries</li>
            </ul>
          </div>

          {/* Widget 2 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#22D3EE', marginBottom: '8px' }}>
              2. 📉 Price Sensitivity Curve
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              Optimal Conversion Bracket: <strong>৳85L – ৳1.1 Crore</strong>.<br />
              68% inquiry drop-off observed for units priced above ৳1.5 Crore in Banani.
            </p>
          </div>

          {/* Widget 3 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#22D3EE', marginBottom: '8px' }}>
              3. 🎯 Marketing Channel ROI
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              WhatsApp Ads: Highest Intent (Score 88/100).<br />
              Instagram Reels: Highest Lead Volume (420 msgs).
            </p>
          </div>

          {/* Widget 4 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#22D3EE', marginBottom: '8px' }}>
              4. ⏱️ Funnel Velocity Diagnostic
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              Inquiry $\rightarrow$ Brochure: <strong>Immediate (1.2s)</strong><br />
              Brochure $\rightarrow$ Site Visit: <strong>Avg 4.2 Days</strong>
            </p>
          </div>

          {/* Widget 5 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#22D3EE', marginBottom: '8px' }}>
              5. ⚔️ Buyer Objection Radar
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              Top Objection: <em>"Parking slot fee extra"</em> (42 mentions).<br />
              Battlecard auto-dispatched to sales agents.
            </p>
          </div>

          {/* Widget 6 */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#22D3EE', marginBottom: '8px' }}>
              6. 🏠 Slow-Moving Inventory Risk
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              Banani Crest 4 BHK Duplex units showing <strong>70% lower inquiry volume</strong>.<br />
              Recommendation: Launch targeted expat ROI campaign.
            </p>
          </div>

        </div>
      </div>

    </div>
  );
}
