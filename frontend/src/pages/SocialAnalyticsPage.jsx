import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Share2,
  Eye,
  MousePointerClick,
  Target,
  Wallet,
  Zap,
  Video,
  Layers,
  Compass,
  BarChart2,
  ChevronRight,
  Copy,
  Check,
  X,
  Search,
  LayoutGrid,
  List,
  Heart,
  MessageCircle,
  Bookmark,
  ExternalLink,
  Sparkles,
  TrendingUp,
  MessageSquare,
  RefreshCw,
  CheckCircle2,
  Filter,
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { getSocialAnalyticsKPIs, simulateSocialCommentToDm } from '../services/api';
import { useAuth } from '../context/AuthContext';
import CustomDropdown from '../components/ui/CustomDropdown';
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
import {
  CAMPAIGN_TYPE_LABELS,
  DASH,
  PERIOD_OPTIONS,
  REACH_METHOD_NOTES,
  formatBDT,
  formatDate,
  formatNumber,
  formatPct,
  formatSeconds,
  isNum,
  shortDate,
} from '../components/ads/adsFormat';

const PLATFORM_GROUPS = {
  meta: { label: 'Meta Ads (all placements)', icon: 'facebook', color: '#1877F2' },
  google_ads: { label: 'Google Ads (all networks)', icon: 'google', color: '#4285F4' },
  tiktok: { label: 'TikTok Ads', icon: 'tiktok', color: '#00F2FE' },
};

const POST_PLATFORM_COLORS = { facebook: '#1877F2', instagram: '#E1306C' };

const TREND_METRICS = [
  { id: 'leads', label: 'Leads', color: '#8B5CF6', format: formatNumber },
  { id: 'spend_bdt', label: 'Spend (৳)', color: '#059669', format: formatBDT },
  { id: 'impressions', label: 'Impressions', color: '#0284C7', format: formatNumber },
  { id: 'clicks', label: 'Clicks', color: '#DB2777', format: formatNumber },
];

const cardStyle = {
  padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px',
  cursor: 'pointer', transition: 'all 0.2s ease', position: 'relative', overflow: 'hidden',
};

function KpiCard({ title, Icon, color, value, delta, inverse, neutral, footer, onClick, highlight }) {
  return (
    <div
      onClick={onClick}
      className="glass-card clickable-card"
      style={{ ...cardStyle, ...(highlight ? { border: `1px solid ${color}55` } : {}) }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.78rem', color: highlight ? color : 'var(--text-muted)', fontWeight: highlight ? 700 : 600 }}>{title}</span>
        <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={16} color={color} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>{value}</div>
        <div style={{ marginTop: '2px', minHeight: '18px' }}>
          {delta !== undefined && <DeltaBadge value={delta} inverse={inverse} neutral={neutral} />}
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-glass)', gap: '8px' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{footer}</span>
        <span style={{ fontSize: '0.72rem', color, fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px', whiteSpace: 'nowrap' }}>
          Inspect <ChevronRight size={12} />
        </span>
      </div>
    </div>
  );
}

function MiniStat({ label, value, color = 'var(--text-main)' }) {
  return (
    <div style={{ padding: '8px 10px', borderRadius: '6px', background: 'var(--bg-main)' }}>
      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{label}</div>
      <div style={{ fontSize: '1.02rem', fontWeight: 800, color }}>{value}</div>
    </div>
  );
}

function StatusPill({ status }) {
  const active = status === 'ACTIVE';
  const paused = status === 'PAUSED';
  const color = active ? '#059669' : paused ? '#D97706' : 'var(--text-muted)';
  const bg = active ? 'rgba(16, 185, 129, 0.15)' : paused ? 'rgba(245, 158, 11, 0.15)' : 'var(--bg-main)';
  return (
    <span style={{ padding: '3px 8px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 700, background: bg, color, border: `1px solid ${active ? 'rgba(16,185,129,0.3)' : paused ? 'rgba(245,158,11,0.3)' : 'var(--border-glass)'}` }}>
      {status}
    </span>
  );
}

export default function SocialAnalyticsPage() {
  const { user } = useAuth();
  const canSync = ['admin', 'manager'].includes(user?.role);

  // Filters
  const [period, setPeriod] = useState('30d');
  const [channel, setChannel] = useState('all');
  const [campaignType, setCampaignType] = useState('all');
  const [projectId, setProjectId] = useState('all');
  const [includeDemo, setIncludeDemo] = useState(false);

  // Data
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Drawer
  const [selected, setSelected] = useState(null);

  // Section controls
  const [trendMetric, setTrendMetric] = useState('leads');
  const [postSearch, setPostSearch] = useState('');
  const [postPlatform, setPostPlatform] = useState('all');
  const [postSort, setPostSort] = useState('views');
  const [postView, setPostView] = useState('cards');

  // Comment-to-DM Lead Bridge Simulator State
  const [simPlatform, setSimPlatform] = useState('facebook');
  const [simAuthor, setSimAuthor] = useState('Mahmudur Rahman');
  const [simComment, setSimComment] = useState('Banani 3 BHK flat price koto? Details inbox korun');
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getSocialAnalyticsKPIs({
        period,
        platform: channel,
        campaign_type: campaignType,
        project_id: projectId,
        include_demo: includeDemo,
      });
      setData(res);
    } catch (err) {
      setError(err.message || 'Could not load social analytics');
    } finally {
      setLoading(false);
    }
  }, [period, channel, campaignType, projectId, includeDemo]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRunSimulator = async () => {
    if (!simComment.trim()) return;
    setSimLoading(true);
    try {
      const res = await simulateSocialCommentToDm({
        platform: simPlatform,
        author_name: simAuthor,
        comment_text: simComment,
      });
      if (res.success) {
        setSimResult(res);
      }
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimLoading(false);
    }
  };

  const source = data?.data_source || (error ? 'unconfigured' : 'empty');
  const hasData = source === 'live' || source === 'demo';
  const kpis = data?.kpis || {};
  const deltas = source === 'demo' ? {} : (data?.deltas || {});
  const sla = data?.ai_sla || {};
  const channels = data?.platforms || [];
  const campaigns = data?.campaigns || [];
  const series = data?.time_series || [];
  const insights = data?.insights || [];
  const periodLabel = data?.period ? `${shortDate(data.period.since)} – ${shortDate(data.period.until)}` : '';

  // Filter options come from what is actually in the database.
  const channelOptions = useMemo(() => {
    const available = data?.available?.channels || [];
    const platformsPresent = [...new Set(campaigns.map((c) => c.platform))].filter((p) => PLATFORM_GROUPS[p]);
    return [
      { value: 'all', label: 'All Channels', icon: <ChannelIcon id="default" color="var(--text-muted)" size={13} /> },
      ...platformsPresent.map((p) => ({ value: p, label: PLATFORM_GROUPS[p].label, icon: <ChannelIcon id={PLATFORM_GROUPS[p].icon} color={PLATFORM_GROUPS[p].color} size={13} /> })),
      ...available.map((c) => ({ value: c.id, label: c.name, icon: <ChannelIcon id={c.icon} color={c.color} size={13} /> })),
    ];
  }, [data, campaigns]);

  const campaignTypeOptions = useMemo(() => [
    { value: 'all', label: 'All Campaign Types', icon: <Target size={13} color="var(--accent-coral)" /> },
    ...(data?.available?.campaign_types || []).map((t) => ({ value: t, label: CAMPAIGN_TYPE_LABELS[t] || t })),
  ], [data]);

  const projectOptions = useMemo(() => [
    { value: 'all', label: 'All Projects', icon: <Layers size={13} color="var(--accent-coral)" /> },
    ...(data?.available?.projects || []).map((p) => ({ value: p.project_id, label: p.name })),
  ], [data]);

  const posts = useMemo(() => {
    const q = postSearch.trim().toLowerCase();
    const sortKey = { views: 'views', er: 'engagement_rate_pct', likes: 'likes', comments: 'comments', shares: 'shares', date: 'published_at' }[postSort];
    return (data?.posts || [])
      .filter((p) => postPlatform === 'all' || p.platform === postPlatform)
      .filter((p) => !q || [p.title, p.caption, p.project].some((v) => (v || '').toLowerCase().includes(q)))
      .sort((a, b) => {
        const av = a[sortKey];
        const bv = b[sortKey];
        if (sortKey === 'published_at') return String(bv || '').localeCompare(String(av || ''));
        return (isNum(bv) ? bv : -1) - (isNum(av) ? av : -1);
      });
  }, [data, postSearch, postPlatform, postSort]);

  const postPlatformsPresent = useMemo(() => [...new Set((data?.posts || []).map((p) => p.platform))], [data]);

  const breakdownFor = (metricKey) => {
    if (metricKey === 'ai_sla') {
      return (sla.channels || []).map((c) => ({
        id: c.channel, icon: c.icon, name: c.name, color: c.color,
        value: formatPct(c.response_rate_pct), sub: `${c.answered}/${c.inbound} answered • median ${formatSeconds(c.median_first_reply_seconds)}`,
        share: c.response_rate_pct,
      }));
    }
    const total = kpis[metricKey] || 0;
    const fmt = metricKey === 'spend_bdt' ? formatBDT : formatNumber;
    return channels.map((c) => ({
      id: c.id, icon: c.icon, name: c.name, color: c.color,
      value: fmt(c[metricKey]),
      sub: metricKey === 'leads' ? `CPL ${formatBDT(c.cpl_bdt)}` : metricKey === 'spend_bdt' ? `CPC ${formatBDT(c.cpc_bdt)} • CPM ${formatBDT(c.cpm_bdt)}` : metricKey === 'clicks' ? `CTR ${formatPct(c.ctr_pct, 2)}` : metricKey === 'video_views' ? `Completion ${formatPct(c.video_completion_pct)}` : `CTR ${formatPct(c.ctr_pct, 2)}`,
      share: total ? Math.round(((c[metricKey] || 0) / total) * 100) : 0,
    }));
  };

  const openMetric = (metricKey, title, description) => setSelected({ type: 'metric', metricKey, title, description });

  const handleCopySummary = () => {
    if (!hasData) return;
    const lines = [
      `GLG Assets — Social & Ads Summary (${periodLabel})${source === 'demo' ? ' [DEMO DATA]' : ''}`,
      `- Impressions: ${formatNumber(kpis.impressions)} • Reach: ${formatNumber(kpis.reach)}`,
      `- Clicks: ${formatNumber(kpis.clicks)} (CTR ${formatPct(kpis.ctr_pct, 2)})`,
      `- Leads: ${formatNumber(kpis.leads)} (CPL ${formatBDT(kpis.cpl_bdt)})`,
      `- Messaging conversations: ${formatNumber(kpis.messaging_conversations)}`,
      `- Ad spend: ${formatBDT(kpis.spend_bdt)}`,
      `- AI reply rate: ${formatPct(sla.response_rate_pct)} (median first reply ${formatSeconds(sla.median_first_reply_seconds)})`,
      `- Video views: ${formatNumber(kpis.video_views)}`,
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const simPlatformOptions = [
    { value: 'facebook', label: 'Facebook Page Post / Ad', icon: <ChannelIcon id="facebook" color="#1877F2" size={13} /> },
    { value: 'instagram', label: 'Instagram Business Post / Reel', icon: <ChannelIcon id="instagram" color="#E1306C" size={13} /> },
  ];

  const trend = TREND_METRICS.find((t) => t.id === trendMetric) || TREND_METRICS[0];

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px', position: 'relative' }}>

      {/* ── Header & filters ── */}
      <div className="glass-card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', zIndex: 30 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, var(--accent-coral), #8B5CF6)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(232, 101, 74, 0.25)' }}>
              <Share2 size={20} color="#FFFFFF" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', margin: 0 }}>
                Social Media KPI & Campaign Command Center
              </h1>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                Synced from Meta, Google Ads & TikTok{periodLabel ? ` • ${periodLabel}` : ''}
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <DataSourceBadge source={source} lastSyncedAt={data?.last_synced_at} />
            <RefreshButton onClick={fetchData} loading={loading} />
            {canSync && source !== 'unconfigured' && <SyncNowButton onSynced={fetchData} />}
            <button
              onClick={handleCopySummary}
              disabled={!hasData}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--accent-coral), #D95338)', border: 'none', color: '#FFFFFF',
                fontSize: '0.8rem', fontWeight: 700, cursor: hasData ? 'pointer' : 'not-allowed', opacity: hasData ? 1 : 0.5,
                boxShadow: '0 4px 14px rgba(232, 101, 74, 0.35)',
              }}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              <span>{copied ? 'Copied Summary!' : 'Export KPI Summary'}</span>
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-glass)', position: 'relative', zIndex: 35 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.78rem', fontWeight: 600 }}>
              <Filter size={14} color="var(--accent-coral)" />
              <span>Filters:</span>
            </div>
            <div style={{ display: 'flex', background: 'var(--bg-main)', padding: '2px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
              {PERIOD_OPTIONS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setPeriod(p.id)}
                  style={{
                    padding: '4px 10px', borderRadius: '6px', border: 'none',
                    background: period === p.id ? 'var(--accent-coral)' : 'transparent',
                    color: period === p.id ? '#FFFFFF' : 'var(--text-muted)',
                    fontSize: '0.74rem', fontWeight: 700, cursor: 'pointer',
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
            <CustomDropdown value={channel} onChange={setChannel} options={channelOptions} minWidth="190px" ariaLabel="Filter by channel" />
            <CustomDropdown value={campaignType} onChange={setCampaignType} options={campaignTypeOptions} minWidth="190px" ariaLabel="Filter by campaign type" />
            <CustomDropdown value={projectId} onChange={setProjectId} options={projectOptions} minWidth="180px" ariaLabel="Filter by project" />
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            {(data?.accounts_connected || []).length > 0
              ? `${data.accounts_connected.length} ad account${data.accounts_connected.length === 1 ? '' : 's'} connected • all money in BDT`
              : 'All money in BDT'}
          </div>
        </div>
      </div>

      {error && (
        <div className="glass-card" style={{ padding: '10px 18px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#DC2626', fontSize: '0.82rem' }}>
          {error}
        </div>
      )}
      {source === 'demo' && <DemoBanner onHide={() => setIncludeDemo(false)} />}
      <WarningsBanner warnings={data?.warnings} />
      {data?.last_sync?.status === 'failed' && (
        <WarningsBanner warnings={[`Last ${data.last_sync.platform} sync failed: ${data.last_sync.error || 'unknown error'}`]} />
      )}

      {!hasData && !loading && (
        <AdsEmptyState
          source={source}
          demoAvailable={data?.demo_available}
          onShowDemo={() => setIncludeDemo(true)}
          canSync={canSync}
          onSynced={fetchData}
        />
      )}

      {hasData && (
        <>
          {/* ── KPI ribbon ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
            <KpiCard
              title="Impressions" Icon={Eye} color="#0284C7"
              value={formatNumber(kpis.impressions)} delta={deltas.impressions}
              footer={<span title={REACH_METHOD_NOTES[data.reach_method]}>Reach: {formatNumber(kpis.reach)}</span>}
              onClick={() => openMetric('impressions', 'Impressions by channel', REACH_METHOD_NOTES[data.reach_method])}
            />
            <KpiCard
              title="Clicks & CTR" Icon={MousePointerClick} color="#DB2777"
              value={formatNumber(kpis.clicks)} delta={deltas.clicks}
              footer={`CTR ${formatPct(kpis.ctr_pct, 2)} • ${formatNumber(kpis.engagements)} engagements`}
              onClick={() => openMetric('clicks', 'Clicks by channel', 'Clicks as reported by each platform; CTR = clicks ÷ impressions.')}
            />
            <KpiCard
              title="Leads" Icon={Target} color="#7C3AED" highlight
              value={formatNumber(kpis.leads)} delta={deltas.leads}
              footer={`CPL ${formatBDT(kpis.cpl_bdt)} • ${formatNumber(kpis.messaging_conversations)} chats started`}
              onClick={() => openMetric('leads', 'Leads by channel', 'Meta lead actions, Google Ads conversions and TikTok lead-generation conversions.')}
            />
            <KpiCard
              title="Ad Spend" Icon={Wallet} color="#059669"
              value={formatBDT(kpis.spend_bdt)} delta={deltas.spend_bdt} neutral
              footer={`CPC ${formatBDT(kpis.cpc_bdt)} • CPM ${formatBDT(kpis.cpm_bdt)}`}
              onClick={() => openMetric('spend_bdt', 'Spend by channel', 'Converted to BDT with the rates in fx_rates.')}
            />
            <KpiCard
              title="AI Reply Rate" Icon={Zap} color="#D97706"
              value={formatPct(sla.response_rate_pct)}
              footer={isNum(sla.inbound_conversations) && sla.inbound_conversations > 0
                ? `${sla.unanswered_conversations} of ${sla.inbound_conversations} unanswered • median ${formatSeconds(sla.median_first_reply_seconds)}`
                : 'No inbound conversations in this period'}
              onClick={() => openMetric('ai_sla', 'AI replies by channel', 'Conversations that received an AI or agent reply after the customer’s first message.')}
            />
            <KpiCard
              title="Video Views" Icon={Video} color="#9333EA"
              value={formatNumber(kpis.video_views)} delta={deltas.video_views}
              footer={isNum(kpis.video_completion_pct) ? `${formatPct(kpis.video_completion_pct)} watched to the end` : 'No paid video plays in this period'}
              onClick={() => openMetric('video_views', 'Video views by channel', 'Paid video plays reported by Meta and TikTok.')}
            />
          </div>

          {/* ── Channel breakdown ── */}
          <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="var(--accent-coral)" /> Channel Breakdown
              </h2>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                Where the spend and leads came from. Meta campaigns are split by placement (Facebook, Instagram, Messenger…).
              </p>
            </div>
            {channels.length === 0 ? (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No delivery in this period for the selected filters.</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                {channels.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setSelected({ type: 'channel', ...c })}
                    className="clickable-card"
                    style={{ padding: '16px', borderRadius: '10px', background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '12px', cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: `${c.color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <ChannelIcon id={c.icon} color={c.color} size={16} />
                        </div>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>{c.name}</span>
                      </div>
                      {source !== 'demo' && <DeltaBadge value={c.leads_delta_pct} suffix="leads" />}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      <MiniStat label="Leads" value={formatNumber(c.leads)} />
                      <MiniStat label="CPL" value={formatBDT(c.cpl_bdt)} color="#0284C7" />
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-glass)', paddingTop: '8px' }}>
                      <span>Spend: <strong style={{ color: '#059669' }}>{formatBDT(c.spend_bdt)}</strong></span>
                      <span>CTR: <strong style={{ color: 'var(--text-main)' }}>{formatPct(c.ctr_pct, 2)}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Daily trend ── */}
          {source === 'live' && (
            <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <TrendingUp size={18} color="var(--accent-coral)" /> Daily Performance
                </h2>
                <div style={{ display: 'flex', background: 'var(--bg-main)', padding: '2px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                  {TREND_METRICS.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setTrendMetric(m.id)}
                      style={{ padding: '4px 10px', borderRadius: '6px', border: 'none', background: trendMetric === m.id ? 'var(--accent-coral)' : 'transparent', color: trendMetric === m.id ? '#FFFFFF' : 'var(--text-muted)', fontSize: '0.74rem', fontWeight: 700, cursor: 'pointer' }}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ height: '220px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={series} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={trend.color} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={trend.color} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" vertical={false} />
                    <XAxis dataKey="date" tickFormatter={shortDate} stroke="var(--text-dim)" fontSize={11} tickLine={false} />
                    <YAxis stroke="var(--text-dim)" fontSize={11} tickLine={false} axisLine={false} width={56} />
                    <Tooltip
                      formatter={(v) => [trend.format(v), trend.label]}
                      labelFormatter={shortDate}
                      contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', borderRadius: '8px', fontSize: '12px', color: 'var(--text-main)' }}
                    />
                    <Area type="monotone" dataKey={trend.id} stroke={trend.color} strokeWidth={2} fill="url(#trendGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ── Campaigns ── */}
          <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Compass size={18} color="var(--accent-coral)" /> Campaigns
                </h2>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                  Status is synced from the ad platform. Campaigns are linked to a project when the campaign name contains the project name.
                </p>
              </div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', fontWeight: 600 }}>{campaigns.length} campaign{campaigns.length === 1 ? '' : 's'}</span>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                    {['Campaign', 'Project', 'Status', 'Spend', 'Impressions', 'CTR', 'Leads', 'CPL', 'Chats'].map((h) => (
                      <th key={h} style={{ padding: '10px 12px', fontWeight: 700 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {campaigns.length === 0 && (
                    <tr><td colSpan={9} style={{ padding: '16px 12px', color: 'var(--text-muted)' }}>No campaigns match the selected filters.</td></tr>
                  )}
                  {campaigns.map((c) => (
                    <tr key={c.key} onClick={() => setSelected({ type: 'campaign', ...c })} className="table-row-hover" style={{ borderBottom: '1px solid var(--border-glass)', cursor: 'pointer' }}>
                      <td style={{ padding: '12px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{c.name}</div>
                        <div style={{ fontSize: '0.72rem', color: '#7C3AED', fontWeight: 600 }}>
                          {c.platform_name}{c.campaign_type ? ` • ${CAMPAIGN_TYPE_LABELS[c.campaign_type] || c.campaign_type}` : ''}
                        </div>
                      </td>
                      <td style={{ padding: '12px', color: c.project ? 'var(--text-main)' : 'var(--text-dim)' }}>{c.project || 'Unlinked'}</td>
                      <td style={{ padding: '12px' }}><StatusPill status={c.status} /></td>
                      <td style={{ padding: '12px', color: 'var(--text-main)', fontWeight: 600 }}>{formatBDT(c.spend_bdt)}</td>
                      <td style={{ padding: '12px', color: 'var(--text-main)' }}>{formatNumber(c.impressions)}</td>
                      <td style={{ padding: '12px', color: 'var(--text-main)' }}>{formatPct(c.ctr_pct, 2)}</td>
                      <td style={{ padding: '12px', color: 'var(--text-main)', fontWeight: 700 }}>{formatNumber(c.leads)}</td>
                      <td style={{ padding: '12px', color: '#0284C7', fontWeight: 700 }}>{formatBDT(c.cpl_bdt)}</td>
                      <td style={{ padding: '12px', color: 'var(--text-main)' }}>{formatNumber(c.messaging_conversations)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* ── Organic posts ── */}
      {(data?.posts || []).length > 0 && (
        <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BarChart2 size={20} color="var(--accent-coral)" />
                <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>Post Performance</h2>
                <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(232, 101, 74, 0.12)', color: 'var(--accent-coral)', fontWeight: 700 }}>
                  {posts.length} {posts.length === 1 ? 'Post' : 'Posts'}
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Page and Instagram posts from the last 90 days with the metrics Meta reports. A dash means the platform did not return that metric.
              </p>
            </div>
            <div style={{ display: 'flex', background: 'var(--bg-main)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
              {[{ id: 'cards', label: 'Cards', Icon: LayoutGrid }, { id: 'table', label: 'Table', Icon: List }].map(({ id, label, Icon }) => (
                <button
                  key={id}
                  onClick={() => setPostView(id)}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '5px 12px', borderRadius: '6px', border: 'none', background: postView === id ? 'var(--accent-coral)' : 'transparent', color: postView === id ? '#FFFFFF' : 'var(--text-muted)', fontSize: '0.74rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  <Icon size={13} /><span>{label}</span>
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', position: 'relative', zIndex: 15 }}>
            <div style={{ position: 'relative', flex: '1', minWidth: '240px', maxWidth: '380px' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={postSearch}
                onChange={(e) => setPostSearch(e.target.value)}
                placeholder="Search post text or project..."
                style={{ width: '100%', padding: '7px 12px 7px 32px', borderRadius: '6px', background: 'var(--bg-card)', border: '1px solid var(--border-glass)', color: 'var(--text-main)', fontSize: '0.78rem', outline: 'none' }}
              />
              {postSearch && (
                <button onClick={() => setPostSearch('')} style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}>
                  <X size={12} />
                </button>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', gap: '4px' }}>
                {['all', ...postPlatformsPresent].map((pl) => {
                  const color = POST_PLATFORM_COLORS[pl];
                  const active = postPlatform === pl;
                  return (
                    <button
                      key={pl}
                      onClick={() => setPostPlatform(pl)}
                      style={{ padding: '4px 9px', borderRadius: '6px', border: '1px solid', borderColor: active ? (color || 'var(--accent-coral)') : 'var(--border-glass)', background: active ? `${color || '#E8654A'}20` : 'var(--bg-card)', color: active ? (color || 'var(--accent-coral)') : 'var(--text-muted)', fontSize: '0.72rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', textTransform: 'capitalize' }}
                    >
                      {pl !== 'all' && <ChannelIcon id={pl} color={color} size={11} />}
                      <span>{pl === 'all' ? 'All' : pl}</span>
                    </button>
                  );
                })}
              </div>
              <CustomDropdown
                value={postSort}
                onChange={setPostSort}
                minWidth="170px"
                ariaLabel="Sort posts"
                options={[
                  { value: 'views', label: 'Sort: Most Views' },
                  { value: 'er', label: 'Sort: Highest ER %' },
                  { value: 'likes', label: 'Sort: Most Likes' },
                  { value: 'comments', label: 'Sort: Most Comments' },
                  { value: 'shares', label: 'Sort: Most Shares' },
                  { value: 'date', label: 'Sort: Newest' },
                ]}
              />
            </div>
          </div>

          {posts.length === 0 ? (
            <div style={{ padding: '28px', textAlign: 'center', borderRadius: '10px', background: 'var(--bg-main)', border: '1px dashed var(--border-glass)', fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              No posts match your search.
            </div>
          ) : postView === 'cards' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
              {posts.map((p) => {
                const color = POST_PLATFORM_COLORS[p.platform] || 'var(--accent-coral)';
                return (
                  <div key={p.id} onClick={() => setSelected({ type: 'post', ...p })} className="clickable-card" style={{ padding: '16px', borderRadius: '12px', background: 'var(--bg-card)', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '12px', cursor: 'pointer', boxShadow: 'var(--shadow-card)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <ChannelIcon id={p.platform} color={color} size={14} />
                        <span style={{ fontSize: '0.74rem', fontWeight: 700, color, textTransform: 'capitalize' }}>{p.platform}</span>
                        <span style={{ fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-main)', color: 'var(--text-muted)', fontWeight: 600 }}>{p.format}</span>
                      </div>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{formatDate(p.published_at)}</span>
                    </div>
                    <div>
                      <h3 style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0', lineHeight: 1.3 }}>{p.title}</h3>
                      <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.45, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{p.caption}</p>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', padding: '10px 8px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      {[
                        ['Views', p.views, Eye, '#7C3AED'],
                        ['Likes', p.likes, Heart, '#E11D48'],
                        ['Comments', p.comments, MessageCircle, '#2563EB'],
                        ['Shares', p.shares, Share2, '#059669'],
                        ['Saves', p.saves, Bookmark, '#D97706'],
                      ].map(([label, value, Icon, c]) => (
                        <div key={label} style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}><Icon size={10} color={c} /> {label}</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '2px' }}>{formatNumber(value)}</div>
                        </div>
                      ))}
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}><Zap size={10} color="var(--accent-coral)" /> ER %</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--accent-coral)', marginTop: '2px' }} title={p.engagement_rate_basis ? `Interactions ÷ ${p.engagement_rate_basis}` : undefined}>{formatPct(p.engagement_rate_pct)}</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                    {['Post', 'Channel', 'Published', 'Views', 'Reach', 'Likes', 'Comments', 'Shares', 'Saves', 'ER %'].map((h) => (
                      <th key={h} style={{ padding: '10px 12px', fontWeight: 700 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {posts.map((p) => (
                    <tr key={p.id} onClick={() => setSelected({ type: 'post', ...p })} className="table-row-hover" style={{ borderBottom: '1px solid var(--border-glass)', cursor: 'pointer' }}>
                      <td style={{ padding: '12px', fontWeight: 700, color: 'var(--text-main)', maxWidth: '320px' }}>{p.title}</td>
                      <td style={{ padding: '12px', textTransform: 'capitalize', color: POST_PLATFORM_COLORS[p.platform], fontWeight: 700 }}>{p.platform}</td>
                      <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{formatDate(p.published_at)}</td>
                      <td style={{ padding: '12px', fontWeight: 800, color: 'var(--text-main)' }}>{formatNumber(p.views)}</td>
                      <td style={{ padding: '12px', color: 'var(--text-main)' }}>{formatNumber(p.reach)}</td>
                      <td style={{ padding: '12px', color: '#E11D48', fontWeight: 700 }}>{formatNumber(p.likes)}</td>
                      <td style={{ padding: '12px', color: '#2563EB', fontWeight: 700 }}>{formatNumber(p.comments)}</td>
                      <td style={{ padding: '12px', color: '#059669', fontWeight: 700 }}>{formatNumber(p.shares)}</td>
                      <td style={{ padding: '12px', color: '#D97706', fontWeight: 700 }}>{formatNumber(p.saves)}</td>
                      <td style={{ padding: '12px', fontWeight: 800, color: 'var(--accent-coral)' }}>{formatPct(p.engagement_rate_pct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── FACEBOOK & INSTAGRAM COMMENT-TO-DM LEAD BRIDGE STUDIO ── */}
      <div 
        className="glass-card" 
        style={{ 
          padding: '24px 26px', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '18px', 
          background: 'linear-gradient(135deg, rgba(24, 119, 242, 0.04), rgba(225, 48, 108, 0.04), var(--bg-card))',
          border: '1px solid var(--border-glass)',
          borderRadius: '16px',
          boxShadow: 'var(--shadow-card)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', borderRadius: '10px', background: 'linear-gradient(135deg, #1877F2, #E1306C)', boxShadow: '0 4px 12px rgba(24, 119, 242, 0.25)' }}>
              <MessageSquare size={20} color="#FFFFFF" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                  Facebook & Instagram Auto-Comment to Private DM Lead Bridge
                </h2>
                <span style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', fontWeight: 700, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  ⚡ LIVE AI BRIDGE
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                Converts post comments directly into qualified Messenger & Instagram DM leads with automated public replies and private property brochures.
              </p>
            </div>
          </div>

          {/* Quick Pre-fill Pills */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { label: '🇧🇩 Banani 3 BHK Price?', text: 'Banani 3 BHK flat price koto? Details inbox korun' },
              { label: '🏢 Gulshan Brochure', text: 'Gulshan luxury project er brochure & payment plan pathan' },
              { label: '🇬🇧 English Inquiry', text: 'What is the price of 3BHK flat in Banani? Please send floor plans.' }
            ].map((pill, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSimComment(pill.text);
                  setSimResult(null);
                }}
                style={{
                  padding: '4px 10px',
                  borderRadius: '20px',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                {pill.label}
              </button>
            ))}
          </div>
        </div>

        {/* Simulator Input Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Target Social Platform
            </label>
            <CustomDropdown
              value={simPlatform}
              onChange={setSimPlatform}
              options={simPlatformOptions}
              minWidth="100%"
              buttonStyle={{ padding: '8px 12px', fontSize: '0.8rem' }}
              ariaLabel="Select Simulator Platform"
            />
          </div>

          <div>
            <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Commenter Name
            </label>
            <input
              type="text"
              value={simAuthor}
              onChange={(e) => setSimAuthor(e.target.value)}
              placeholder="e.g. Mahmudur Rahman"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-glass)',
                color: 'var(--text-main)',
                fontSize: '0.8rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ gridColumn: 'span 2' }}>
            <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              User's Public Comment (Bangla / Banglish / English)
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={simComment}
                onChange={(e) => setSimComment(e.target.value)}
                placeholder="Type any inquiry e.g. Price koto? Banani flat details inbox korun"
                style={{
                  flex: 1,
                  padding: '9px 14px',
                  borderRadius: '8px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.82rem',
                  outline: 'none'
                }}
              />
              <button
                onClick={handleRunSimulator}
                disabled={simLoading}
                style={{
                  padding: '9px 20px',
                  borderRadius: '8px',
                  background: simPlatform === 'facebook' ? 'linear-gradient(135deg, #1877F2, #0A58CA)' : 'linear-gradient(135deg, #E1306C, #C13584)',
                  border: 'none',
                  color: '#FFFFFF',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: simLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 4px 14px rgba(24, 119, 242, 0.4)',
                  whiteSpace: 'nowrap'
                }}
              >
                {simLoading ? <RefreshCw size={15} className="spin" /> : <Zap size={15} />}
                {simLoading ? 'Bridging...' : 'Execute Comment Bridge'}
              </button>
            </div>
          </div>
        </div>

        {/* Live Simulation Output Panel */}
        {simResult && (
          <div 
            style={{ 
              marginTop: '8px', 
              padding: '18px 20px', 
              borderRadius: '12px', 
              background: 'var(--bg-card)', 
              border: '1px solid var(--border-glass)',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              animation: 'fadeIn 0.3s ease'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={18} color="#059669" />
                <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  Comment-to-DM Bridge Executed Successfully
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px', background: 'rgba(139, 92, 246, 0.15)', color: '#7C3AED', fontWeight: 700 }}>
                  Lead Intent Score: {simResult.lead_score}/100
                </span>
                {simResult.is_hot_lead && (
                  <span style={{ fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.15)', color: '#DC2626', fontWeight: 800, border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                    🔥 HOT LEAD DETECTED
                  </span>
                )}
              </div>
            </div>

            {/* Dual Previews: Step 1 Public Reply & Step 2 Private DM */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
              
              {/* Step 1: Public Auto-Reply Card */}
              <div style={{ padding: '14px 16px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase' }}>
                    1. Public Comment Auto-Reply
                  </span>
                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', fontWeight: 700 }}>
                    POSTED (0.4s)
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5, background: 'var(--bg-card)', padding: '10px 12px', borderRadius: '8px', borderLeft: '3px solid #1877F2', border: '1px solid var(--border-glass)' }}>
                  {simResult.public_reply}
                </div>
              </div>

              {/* Step 2: Private DM Lead Hook Card */}
              <div style={{ padding: '14px 16px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#7C3AED', textTransform: 'uppercase' }}>
                    2. Private Messenger / IG Direct Message
                  </span>
                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(139, 92, 246, 0.15)', color: '#7C3AED', fontWeight: 700 }}>
                    DELIVERED (0.8s)
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-main)', lineHeight: 1.5, background: 'var(--bg-card)', padding: '10px 12px', borderRadius: '8px', borderLeft: '3px solid #E1306C', border: '1px solid var(--border-glass)', whiteSpace: 'pre-wrap' }}>
                  {simResult.private_dm}
                </div>

                {/* Quick Reply Buttons */}
                <div style={{ display: 'flex', gap: '6px', marginTop: '10px', flexWrap: 'wrap' }}>
                  {['📅 Book Site Tour', '📥 Download Brochure', '💬 Talk to Consultant'].map((btn, bidx) => (
                    <button
                      key={bidx}
                      style={{
                        padding: '4px 8px',
                        borderRadius: '6px',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-glass)',
                        color: 'var(--text-main)',
                        fontSize: '0.68rem',
                        fontWeight: 600,
                        cursor: 'default'
                      }}
                    >
                      {btn}
                    </button>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}
      </div>

      {/* ── Observations computed from the synced numbers ── */}
      {hasData && insights.length > 0 && (
        <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '14px', background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.06), rgba(139, 92, 246, 0.06))' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} color="var(--accent-coral)" />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>What the numbers say</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px' }}>
            {insights.map((rec) => (
              <div key={rec.title} style={{ padding: '14px', borderRadius: '8px', background: 'var(--bg-card)', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>{rec.title}</span>
                  <span style={{ fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(232, 101, 74, 0.12)', color: 'var(--accent-coral)', fontWeight: 700, whiteSpace: 'nowrap' }}>{rec.priority}</span>
                </div>
                <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>{rec.detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Detail drawer ── */}
      {selected && (
        <div onClick={() => setSelected(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.65)', backdropFilter: 'blur(4px)', zIndex: 9998 }}>
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ position: 'fixed', top: 0, right: 0, width: '540px', maxWidth: '92vw', height: '100vh', background: 'var(--bg-card)', borderLeft: '1px solid var(--border-glass)', boxShadow: '-10px 0 35px rgba(0, 0, 0, 0.12)', zIndex: 9999, display: 'flex', flexDirection: 'column', padding: '26px 24px', gap: '18px', overflowY: 'auto', animation: 'slideInRight 0.25s ease-out' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-glass)', paddingBottom: '14px', gap: '12px' }}>
              <div>
                <span style={{ fontSize: '0.72rem', padding: '3px 8px', borderRadius: '6px', background: 'rgba(232, 101, 74, 0.12)', color: 'var(--accent-coral)', fontWeight: 700, display: 'inline-block', marginBottom: '6px', textTransform: 'uppercase' }}>
                  {selected.type === 'post' ? `${selected.platform} post` : selected.type === 'campaign' ? selected.platform_name : selected.type === 'channel' ? 'Channel' : 'Metric'} • {periodLabel}
                </span>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0' }}>{selected.title || selected.name}</h2>
                {selected.description && <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>{selected.description}</div>}
              </div>
              <button onClick={() => setSelected(null)} style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', color: 'var(--text-main)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
                <X size={18} />
              </button>
            </div>

            {selected.type === 'metric' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {breakdownFor(selected.metricKey).length === 0 && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No data for this breakdown in the selected period.</div>
                )}
                {breakdownFor(selected.metricKey).map((item) => (
                  <div key={item.id} style={{ padding: '12px 14px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ChannelIcon id={item.icon} color={item.color} size={14} />
                        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>{item.name}</span>
                      </div>
                      <span style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-main)' }}>{item.value}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      <span>{item.sub}</span>
                      {isNum(item.share) && <span>{item.share}%{selected.metricKey === 'ai_sla' ? '' : ' share'}</span>}
                    </div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(0, 0, 0, 0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.max(item.share || 0, 2)}%`, height: '100%', background: item.color, borderRadius: '2px' }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {(selected.type === 'channel' || selected.type === 'campaign') && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <MiniStat label="Spend" value={formatBDT(selected.spend_bdt)} color="#059669" />
                <MiniStat label="Leads" value={formatNumber(selected.leads)} color="#7C3AED" />
                <MiniStat label="Cost per lead" value={formatBDT(selected.cpl_bdt)} color="#0284C7" />
                <MiniStat label="Chats started" value={formatNumber(selected.messaging_conversations)} />
                <MiniStat label="Impressions" value={formatNumber(selected.impressions)} />
                <MiniStat label="Clicks / CTR" value={`${formatNumber(selected.clicks)} / ${formatPct(selected.ctr_pct, 2)}`} />
                <MiniStat label="Engagements" value={formatNumber(selected.engagements)} />
                <MiniStat label="Video views" value={formatNumber(selected.video_views)} />
                {selected.type === 'campaign' && (
                  <>
                    <MiniStat label="Status" value={selected.status} />
                    <MiniStat label="Objective" value={selected.objective || DASH} />
                    <MiniStat label="Budget" value={isNum(selected.budget_amount) ? `${selected.budget_amount.toLocaleString('en-IN')} ${selected.currency || ''} ${selected.budget_type ? `/ ${selected.budget_type}` : ''}` : DASH} />
                    <MiniStat label="Project" value={selected.project || 'Unlinked'} />
                    <div style={{ gridColumn: 'span 2', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      Placements: {(selected.channels || []).join(', ') || DASH}
                    </div>
                  </>
                )}
              </div>
            )}

            {selected.type === 'post' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '12px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', fontSize: '0.78rem', color: 'var(--text-main)', lineHeight: 1.45, whiteSpace: 'pre-wrap' }}>
                  {selected.caption || DASH}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  <MiniStat label="Views" value={formatNumber(selected.views)} />
                  <MiniStat label="Reach" value={formatNumber(selected.reach)} />
                  <MiniStat label="ER %" value={formatPct(selected.engagement_rate_pct)} color="var(--accent-coral)" />
                  <MiniStat label="Likes" value={formatNumber(selected.likes)} color="#E11D48" />
                  <MiniStat label="Comments" value={formatNumber(selected.comments)} color="#2563EB" />
                  <MiniStat label="Shares" value={formatNumber(selected.shares)} color="#059669" />
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Published {formatDate(selected.published_at)}{selected.metrics_synced_at ? ` • metrics synced ${formatDate(selected.metrics_synced_at)}` : ''}
                </div>
                {selected.permalink && (
                  <a href={selected.permalink} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-coral)' }}>
                    Open on {selected.platform} <ExternalLink size={13} />
                  </a>
                )}
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', marginTop: 'auto', paddingTop: '14px', borderTop: '1px solid var(--border-glass)' }}>
              <button onClick={() => setSelected(null)} style={{ flex: 1, padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', color: 'var(--text-main)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
