import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  MessageSquare,
  Clock,
  UserCheck,
  Share2,
  AlertCircle,
  Send,
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
import { getManagerOverview, triggerReportNow } from '../services/api';
import ChannelIcon from '../components/ads/ChannelIcon';
import {
  AdsEmptyState,
  DataSourceBadge,
  DeltaBadge,
  DemoBanner,
  RefreshButton,
  SyncNowButton,
  WarningsBanner,
} from '../components/ads/AdsDataStatus';
import { formatBDT, formatNumber, formatPct, formatSeconds, isNum, shortDate } from '../components/ads/adsFormat';

const PLATFORM_ICON = { meta: ['facebook', '#1877F2'], google_ads: ['google', '#4285F4'], tiktok: ['tiktok', '#00F2FE'] };

export default function ManagerDashboardPage({ setActiveTab }) {
  const { user } = useAuth();
  const canSync = ['admin', 'manager'].includes(user?.role);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [includeDemo, setIncludeDemo] = useState(false);
  const [dispatchingReport, setDispatchingReport] = useState(false);
  const [reportFeedback, setReportFeedback] = useState(null);

  const handleSendReportQuick = async () => {
    setDispatchingReport(true);
    try {
      await triggerReportNow('sched-daily-pulse');
      setReportFeedback('Daily briefing delivered to Admin & Manager across Email, Telegram, and WhatsApp!');
      setTimeout(() => setReportFeedback(null), 5000);
    } catch (err) {
      setReportFeedback(`Dispatch failed: ${err.message || 'Error'}`);
      setTimeout(() => setReportFeedback(null), 5000);
    } finally {
      setDispatchingReport(false);
    }
  };

  const fetchDashboardData = useCallback(async () => {
    setError(null);
    try {
      const res = await getManagerOverview({ period: '30d', include_demo: includeDemo });
      setData(res);
    } catch (err) {
      setError(`Could not load the manager overview: ${err.message || 'request failed'}`);
    } finally {
      setLoading(false);
    }
  }, [includeDemo]);

  // Ad metrics sync hourly, so a 60s refresh is plenty.
  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 60000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  const source = data?.data_source || 'empty';
  const hasAdData = source === 'live' || source === 'demo';
  const k = data?.kpis || {};
  const campaigns = data?.campaigns || [];
  const pending = k.pending_social_posts;
  const adValue = (v, fmt) => (hasAdData ? fmt(v) : '—');

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '22px' }}>

      {error && (
        <div className="glass-card" style={{ padding: '10px 18px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#EF4444', fontSize: '0.84rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
          <button onClick={fetchDashboardData} style={{ background: 'transparent', border: '1px solid #EF4444', color: '#EF4444', borderRadius: '6px', padding: '3px 10px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}>
            Retry
          </button>
        </div>
      )}

      {/* 1. Hero */}
      <div className="glass-card manager-hero-banner" style={{ padding: '24px 30px', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
            Welcome back{user?.full_name ? `, ${user.full_name}` : ''}
          </h1>
          <p style={{ fontSize: '0.85rem', margin: 0, display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span>👔 Operations &amp; Team Performance Hub</span>
            {data?.period && (
              <>
                <span>•</span>
                <span>{shortDate(data.period.since)} – {shortDate(data.period.until)}</span>
              </>
            )}
            {isNum(pending) && pending > 0 && (
              <>
                <span>•</span>
                <span className="text-rose-themed" style={{ fontWeight: 600 }}>
                  {pending} social post{pending === 1 ? '' : 's'} pending review
                </span>
              </>
            )}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {!loading && <DataSourceBadge source={source} lastSyncedAt={data?.last_synced_at} />}
          <RefreshButton onClick={fetchDashboardData} loading={loading} />
          {canSync && source !== 'unconfigured' && <SyncNowButton onSynced={fetchDashboardData} />}
          <button
            onClick={handleSendReportQuick}
            disabled={dispatchingReport}
            className="btn-gradient"
            title="Dispatch Daily Intelligence Briefing to Admin & Manager"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 14px', fontSize: '0.78rem', fontWeight: 800, cursor: dispatchingReport ? 'not-allowed' : 'pointer' }}
          >
            <Send size={13} className={dispatchingReport ? 'spin-anim' : ''} />
            <span>{dispatchingReport ? 'Dispatching...' : '⚡ Send Report (Email + TG + WA)'}</span>
          </button>
        </div>
      </div>

      {reportFeedback && (
        <div style={{ padding: '10px 16px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#059669', fontSize: '0.82rem', fontWeight: 700, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>✨ {reportFeedback}</span>
          {setActiveTab && (
            <button onClick={() => setActiveTab('role_reports')} style={{ background: 'transparent', border: 'none', color: '#059669', textDecoration: 'underline', cursor: 'pointer', fontWeight: 700 }}>
              View in Reports Hub &rarr;
            </button>
          )}
        </div>
      )}

      {source === 'demo' && <DemoBanner onHide={() => setIncludeDemo(false)} />}
      <WarningsBanner warnings={data?.warnings} />

      {/* 2. KPI grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Ad Spend (last 30 days)</span>
            <span className="text-emerald-themed" style={{ fontSize: '1.1rem', fontWeight: 800 }}>৳</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '10px' }}>
            <div>
              <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>{adValue(k.total_ad_spend_bdt, formatBDT)}</div>
              <div style={{ marginTop: '6px' }}>
                {source === 'live' ? <DeltaBadge value={k.ad_spend_delta_pct} neutral suffix="vs prior 30 days" /> : <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>{hasAdData ? 'Demo totals' : 'No synced ad data'}</span>}
              </div>
            </div>
            {source === 'live' && (
              <div style={{ width: '120px', height: '52px', flexShrink: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={k.spend_trend || []} margin={{ top: 4, right: 2, left: 2, bottom: 0 }}>
                    <defs>
                      <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Tooltip
                      content={({ active, payload }) => (active && payload && payload.length ? (
                        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', padding: '4px 8px', borderRadius: '8px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-main)' }}>
                          {shortDate(payload[0].payload.date)}: {formatBDT(payload[0].value)}
                        </div>
                      ) : null)}
                    />
                    <Area type="monotone" dataKey="spend_bdt" stroke="#10B981" strokeWidth={2.2} fill="url(#spendGrad)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Campaign Reach &amp; Impressions</span>
            <TrendingUp size={18} className="text-blue-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            {adValue(k.reach, formatNumber)} {hasAdData && isNum(k.reach) && <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>reach</span>}
          </div>
          <div className="text-blue-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 500 }}>
            {hasAdData ? `${formatNumber(k.impressions)} impressions` : 'No synced ad data'}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Chats Started from Ads</span>
            <MessageSquare size={18} className="text-emerald-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>{adValue(k.messages_received, formatNumber)}</div>
          <div className="text-emerald-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 500 }}>
            {hasAdData ? `Cost per chat: ${formatBDT(k.cost_per_message_bdt)}` : 'No synced ad data'}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>AI Reply Rate &amp; Speed</span>
            <Clock size={18} className="text-purple-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>{formatPct(k.ai_response_rate_pct)}</div>
          <div className="text-purple-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 500 }}>
            {isNum(k.ai_inbound_conversations) && k.ai_inbound_conversations > 0
              ? `Median first reply ${formatSeconds(k.ai_median_first_reply_seconds)} • ${k.ai_inbound_conversations} conversations`
              : 'No inbound conversations in this period'}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px 24px', gridColumn: 'span 2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>Leads &amp; Site Tours</span>
              {isNum(k.tour_conversion_pct) && (
                <span className="badge badge-amber" style={{ fontSize: '0.66rem', borderRadius: '999px', padding: '1px 8px' }}>
                  {formatPct(k.tour_conversion_pct)} of leads toured
                </span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.72rem', fontWeight: 600 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B' }}></span><span>Ad leads</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }}></span><span>Site tours</span>
              </div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '170px 1fr', gap: '20px', alignItems: 'center' }}>
            <div style={{ borderRight: '1px solid var(--border-glass)', paddingRight: '16px' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                {adValue(k.leads, formatNumber)} <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>leads</span>
              </div>
              <div className="text-amber-themed" style={{ fontSize: '0.8rem', marginTop: '6px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                <UserCheck size={14} /> {formatNumber(k.confirmed_tours)} confirmed tour{k.confirmed_tours === 1 ? '' : 's'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px', lineHeight: 1.3 }}>
                Leads as reported by the ad platforms; tours from bookings and the tour calendar.
              </div>
            </div>
            <div style={{ height: '85px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={k.leads_vs_tours || []} margin={{ top: 5, right: 10, left: 0, bottom: 0 }} barGap={6}>
                  <XAxis dataKey="period" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'var(--text-dim)' }} />
                  <Tooltip
                    content={({ active, payload, label }) => (active && payload && payload.length ? (
                      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', padding: '6px 10px', borderRadius: '10px', fontSize: '0.74rem', color: 'var(--text-main)' }}>
                        <div style={{ fontWeight: 800, marginBottom: '2px' }}>{label}</div>
                        <div style={{ color: '#F59E0B', fontWeight: 600 }}>Leads: {payload[0]?.value}</div>
                        <div style={{ color: '#10B981', fontWeight: 600 }}>Tours: {payload[1]?.value}</div>
                      </div>
                    ) : null)}
                  />
                  <Bar dataKey="leads" fill="#F59E0B" radius={[4, 4, 0, 0]} maxBarSize={20} />
                  <Bar dataKey="tours" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px 22px', gridColumn: 'span 2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Pending Social Approvals</span>
            <Share2 size={18} className="text-rose-themed" />
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            {formatNumber(pending)} {isNum(pending) && `post${pending === 1 ? '' : 's'}`}
          </div>
          <div className="text-rose-themed" style={{ fontSize: '0.75rem', marginTop: '6px', fontWeight: 700 }}>
            {isNum(pending) && pending > 0 ? 'Requires manager sign-off' : 'Nothing waiting for review'}
          </div>
        </div>
      </div>

      {/* 3. Campaigns */}
      {!hasAdData && !loading ? (
        <AdsEmptyState
          source={source}
          demoAvailable={data?.demo_available}
          onShowDemo={() => setIncludeDemo(true)}
          canSync={canSync}
          onSynced={fetchDashboardData}
        />
      ) : (
        <div className="glass-card" style={{ padding: '24px 28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', margin: 0 }}>
                Ad Campaigns — Last 30 Days
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Spend, chats started and leads per campaign. Status is managed in the ad platform.
              </p>
            </div>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              {campaigns.length} campaign{campaigns.length === 1 ? '' : 's'}{source === 'demo' ? ' (demo)' : ''}
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                  {['Campaign & Platform', 'Spend', 'Impressions', 'Chats Started', 'Leads', 'Cost Per Lead'].map((h) => (
                    <th key={h} style={{ padding: '14px 12px', fontWeight: 600 }}>{h}</th>
                  ))}
                  <th style={{ padding: '14px 12px', fontWeight: 600, textAlign: 'center' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.length === 0 && (
                  <tr><td colSpan={7} style={{ padding: '16px 12px', color: 'var(--text-muted)' }}>No campaign delivered in the last 30 days.</td></tr>
                )}
                {campaigns.map((cmp, idx) => {
                  const [icon, color] = PLATFORM_ICON[cmp.platform] || ['default', 'var(--text-muted)'];
                  const active = cmp.status === 'ACTIVE';
                  return (
                    <tr key={cmp.key} style={{ borderBottom: idx === campaigns.length - 1 ? 'none' : '1px solid var(--border-glass)' }}>
                      <td style={{ padding: '14px 12px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.88rem' }}>{cmp.name}</div>
                        <div className="text-sky-themed" style={{ fontSize: '0.74rem', marginTop: '2px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <ChannelIcon id={icon} color={color} size={11} />
                          {cmp.platform_name}{cmp.project ? ` • ${cmp.project}` : ''}
                        </div>
                      </td>
                      <td className="text-emerald-themed" style={{ padding: '14px 12px', fontWeight: 700 }}>{formatBDT(cmp.spend_bdt)}</td>
                      <td style={{ padding: '14px 12px', color: 'var(--text-main)' }}>{formatNumber(cmp.impressions)}</td>
                      <td style={{ padding: '14px 12px', color: 'var(--text-main)' }}>{formatNumber(cmp.messages)}</td>
                      <td className="text-blue-themed" style={{ padding: '14px 12px', fontWeight: 600 }}>{formatNumber(cmp.leads)}</td>
                      <td className="text-rose-themed" style={{ padding: '14px 12px', fontWeight: 600 }}>{formatBDT(cmp.cpl_bdt)}</td>
                      <td style={{ padding: '14px 12px', textAlign: 'center' }}>
                        <span
                          title="Synced from the ad platform"
                          className={active ? 'badge-active' : 'badge-paused'}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 12px', borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700 }}
                        >
                          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'currentColor' }} />
                          {cmp.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
