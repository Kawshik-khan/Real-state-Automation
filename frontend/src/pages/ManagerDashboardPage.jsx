import React, { useState } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  MessageSquare, 
  Clock, 
  UserCheck, 
  Share2, 
  Sparkles, 
  ArrowUpRight, 
  Layers,
  ChevronRight,
  Filter,
  CheckCircle2
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Tooltip,
  BarChart,
  Bar,
  XAxis
} from 'recharts';
import { useAuth } from '../context/AuthContext';

export default function ManagerDashboardPage({ setActiveTab }) {
  const { user } = useAuth();

  // Ad Spend 6-Month Trend Data for Sparkline
  const adSpendTrendData = [
    { month: 'Apr', spend: 85000 },
    { month: 'May', spend: 92000 },
    { month: 'Jun', spend: 98000 },
    { month: 'Jul', spend: 106000 },
    { month: 'Aug', spend: 114000 },
    { month: 'Sep', spend: 125000 }
  ];

  // Weekly Qualified Leads vs Confirmed Site Tours Data
  const leadsVsToursData = [
    { period: 'W1', qualified: 28, tours: 6 },
    { period: 'W2', qualified: 34, tours: 8 },
    { period: 'W3', qualified: 38, tours: 8 },
    { period: 'W4', qualified: 42, tours: 10 }
  ];

  // Active Ad Campaigns Data (matches Supabase database seed)
  const [campaigns] = useState([
    {
      id: 'cmp-001',
      name: 'GLG Sky Tower - Gulshan 3BHK',
      platform: 'Meta Click-to-WhatsApp',
      spent: '৳45,000',
      reach: '65,000',
      messages: '520',
      leads: '58 Leads',
      cpl: '৳775 / lead',
      status: 'ACTIVE'
    },
    {
      id: 'cmp-002',
      name: 'Palm Beach Villa - Coastal Luxury',
      platform: 'Instagram Reels Video Ad',
      spent: '৳38,000',
      reach: '52,000',
      messages: '410',
      leads: '42 Leads',
      cpl: '৳904 / lead',
      status: 'ACTIVE'
    },
    {
      id: 'cmp-003',
      name: 'Dhanmondi Heights - Residential',
      platform: 'Google Search Text Ads',
      spent: '৳24,000',
      reach: '38,000',
      messages: '310',
      leads: '28 Leads',
      cpl: '৳857 / lead',
      status: 'ACTIVE'
    },
    {
      id: 'cmp-004',
      name: 'Bandra Skyline - Investment Units',
      platform: 'FB Instant Lead Form',
      spent: '৳18,000',
      reach: '30,000',
      messages: '180',
      leads: '14 Leads',
      cpl: '৳1,285 / lead',
      status: 'PAUSED'
    }
  ]);

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      
      {/* 1. Manager Real-Time Console Hero Banner (Cleaned up per user request) */}
      <div 
        className="glass-card manager-hero-banner" 
        style={{
          padding: '24px 30px',
          borderRadius: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px'
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Heading without emoji */}
          <h1 style={{
            fontSize: '1.6rem',
            fontWeight: 800,
            letterSpacing: '-0.02em',
            margin: 0
          }}>
            Welcome back, {user?.full_name || 'Sarah Connor (Manager)'}
          </h1>

          {/* Subtitle */}
          <p style={{
            fontSize: '0.85rem',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span>👔 Operations &amp; Team Performance Hub</span>
            <span>•</span>
            <span className="text-rose-themed" style={{ fontWeight: 600 }}>5 Social Posts Pending Review</span>
          </p>
        </div>
      </div>

      {/* 2. Manager 6-Card KPI Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px'
      }}>
        {/* KPI 1: Total Ad Spend with Mini Trend Sparkline */}
        <div className="glass-card" style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Total Ad Spend (Monthly)
            </span>
            <span className="text-emerald-themed" style={{ fontSize: '1.1rem', fontWeight: 800 }}>$</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '10px' }}>
            <div>
              <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
                ৳1,25,000
              </div>
              <div className="text-emerald-themed" style={{ fontSize: '0.75rem', fontWeight: 600, marginTop: '6px' }}>
                ↗ +12% vs last month
              </div>
            </div>
            <div style={{ width: '120px', height: '52px', flexShrink: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={adSpendTrendData} margin={{ top: 4, right: 2, left: 2, bottom: 0 }}>
                  <defs>
                    <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip 
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div style={{
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border-glass)',
                            padding: '4px 8px',
                            borderRadius: '8px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                            color: 'var(--text-main)'
                          }}>
                            ৳{payload[0].value.toLocaleString()}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Area type="monotone" dataKey="spend" stroke="#10B981" strokeWidth={2.2} fill="url(#spendGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* KPI 2: Campaign Reach & Views */}
        <div className="glass-card" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Campaign Reach &amp; Views
            </span>
            <TrendingUp size={18} className="text-blue-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            185,000 Reach
          </div>
          <div className="text-blue-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 500 }}>
            340,000 Total Impressions
          </div>
        </div>

        {/* KPI 3: Messages Received from Ads */}
        <div className="glass-card" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Messages Received from Ads
            </span>
            <MessageSquare size={18} className="text-emerald-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            1,420 Messages
          </div>
          <div className="text-emerald-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 500 }}>
            Cost Per Message: ৳88
          </div>
        </div>

        {/* KPI 4: AI Response Rate & Speed */}
        <div className="glass-card" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              AI Response Rate &amp; Speed
            </span>
            <Clock size={18} className="text-purple-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            96.8% Answered
          </div>
          <div className="text-purple-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 500 }}>
            Avg 1.2s AI Response Time
          </div>
        </div>

        {/* KPI 5: Qualified Leads & Tours with Interactive Performance Chart */}
        <div className="glass-card" style={{ padding: '20px 24px', gridColumn: 'span 2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Qualified Leads &amp; Tours
              </span>
              <span className="badge badge-amber" style={{ fontSize: '0.66rem', borderRadius: '999px', padding: '1px 8px' }}>
                22.5% Tour Conversion
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.72rem', fontWeight: 600 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B' }}></span>
                <span>Qualified Leads</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }}></span>
                <span>Site Tours</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '170px 1fr', gap: '20px', alignItems: 'center' }}>
            {/* Left: Summary Metrics */}
            <div style={{ borderRight: '1px solid var(--border-glass)', paddingRight: '16px' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                142 Qualified
              </div>
              <div className="text-amber-themed" style={{ fontSize: '0.8rem', marginTop: '6px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                <UserCheck size={14} /> 32 Confirmed Tours
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px', lineHeight: 1.3 }}>
                High-intent buyers matching budget &amp; location criteria
              </div>
            </div>

            {/* Right: Interactive Dual Series Bar Chart */}
            <div style={{ height: '85px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={leadsVsToursData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }} barGap={6}>
                  <XAxis 
                    dataKey="period" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 11, fill: 'var(--text-dim)' }} 
                  />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div style={{
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border-glass)',
                            padding: '6px 10px',
                            borderRadius: '10px',
                            fontSize: '0.74rem',
                            boxShadow: '0 6px 18px rgba(0,0,0,0.15)',
                            color: 'var(--text-main)'
                          }}>
                            <div style={{ fontWeight: 800, marginBottom: '2px' }}>Week: {label}</div>
                            <div style={{ color: '#F59E0B', fontWeight: 600 }}>Leads: {payload[0]?.value}</div>
                            <div style={{ color: '#10B981', fontWeight: 600 }}>Tours: {payload[1]?.value}</div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="qualified" fill="#F59E0B" radius={[4, 4, 0, 0]} maxBarSize={20} />
                  <Bar dataKey="tours" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* KPI 6: Pending Social Approvals (spans 2 columns on 4-col grid) */}
        <div className="glass-card" style={{ padding: '20px 22px', gridColumn: 'span 2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Pending Social Approvals
            </span>
            <Share2 size={18} className="text-rose-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            5 Posts
          </div>
          <div className="text-rose-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 700 }}>
            Requires Manager Sign-off
          </div>
        </div>
      </div>

      {/* 3. Active Ad Campaigns & Marketing Performance Table Card */}
      <div className="glass-card" style={{ padding: '24px 28px' }}>
        {/* Table Card Header (Button removed per user request) */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '20px'
        }}>
          <div>
            <h2 style={{
              fontSize: '1.1rem',
              fontWeight: 800,
              color: 'var(--text-main)',
              letterSpacing: '-0.02em',
              margin: 0
            }}>
              Active Ad Campaigns &amp; Marketing Performance
            </h2>
            <p style={{
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              margin: '4px 0 0 0'
            }}>
              Real-time advertising spend, reach, incoming message inquiries, and cost per lead (CPL).
            </p>
          </div>
        </div>

        {/* Campaigns Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '0.84rem',
            textAlign: 'left'
          }}>
            <thead>
              <tr style={{
                borderBottom: '1px solid var(--border-glass)',
                color: 'var(--text-muted)'
              }}>
                <th style={{ padding: '14px 12px', fontWeight: 600 }}>Campaign Name &amp; Platform</th>
                <th style={{ padding: '14px 12px', fontWeight: 600 }}>Ad Budget Spent</th>
                <th style={{ padding: '14px 12px', fontWeight: 600 }}>Reach</th>
                <th style={{ padding: '14px 12px', fontWeight: 600 }}>Messages Recv</th>
                <th style={{ padding: '14px 12px', fontWeight: 600 }}>Qualified Leads</th>
                <th style={{ padding: '14px 12px', fontWeight: 600 }}>Cost Per Lead (CPL)</th>
                <th style={{ padding: '14px 12px', fontWeight: 600, textAlign: 'center' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((cmp, idx) => (
                <tr 
                  key={cmp.id}
                  style={{
                    borderBottom: idx === campaigns.length - 1 ? 'none' : '1px solid var(--border-glass)',
                    transition: 'background 0.15s ease'
                  }}
                >
                  {/* Campaign Name & Platform */}
                  <td style={{ padding: '14px 12px' }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.88rem' }}>
                      {cmp.name}
                    </div>
                    <div className="text-sky-themed" style={{ fontSize: '0.74rem', marginTop: '2px', fontWeight: 600 }}>
                      {cmp.platform}
                    </div>
                  </td>

                  {/* Ad Budget Spent */}
                  <td className="text-emerald-themed" style={{ padding: '14px 12px', fontWeight: 700 }}>
                    {cmp.spent}
                  </td>

                  {/* Reach */}
                  <td style={{ padding: '14px 12px', color: 'var(--text-main)' }}>
                    {cmp.reach}
                  </td>

                  {/* Messages Recv */}
                  <td style={{ padding: '14px 12px', color: 'var(--text-main)' }}>
                    {cmp.messages}
                  </td>

                  {/* Qualified Leads */}
                  <td className="text-blue-themed" style={{ padding: '14px 12px', fontWeight: 600 }}>
                    {cmp.leads}
                  </td>

                  {/* Cost Per Lead (CPL) */}
                  <td className="text-rose-themed" style={{ padding: '14px 12px', fontWeight: 600 }}>
                    {cmp.cpl}
                  </td>

                  {/* Status Badge */}
                  <td style={{ padding: '14px 12px', textAlign: 'center' }}>
                    <span 
                      className={cmp.status === 'ACTIVE' ? 'badge-active' : 'badge-paused'}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '4px 12px',
                        borderRadius: '20px',
                        fontSize: '0.72rem',
                        fontWeight: 700
                      }}
                    >
                      <span style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: 'currentColor'
                      }} />
                      {cmp.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
