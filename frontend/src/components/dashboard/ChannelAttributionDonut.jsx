import React, { useState, useEffect } from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer 
} from 'recharts';
import Card from '../ui/Card';
import CustomDropdown from '../ui/CustomDropdown';
import { 
  Share2, 
  ChevronRight, 
  Sparkles
} from 'lucide-react';
import { getSocialAnalyticsKPIs } from '../../services/api';

const formatCpl = (value) => (typeof value === 'number' ? `৳${Math.round(value).toLocaleString('en-IN')}` : '—');

export default function ChannelAttributionDonut({ onNavigateSocial }) {
  const [period, setPeriod] = useState('30d');
  const [channels, setChannels] = useState([]);
  const [status, setStatus] = useState('loading'); // loading | ready | empty | error
  const [activeHover, setActiveHover] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setStatus('loading');
      try {
        const res = await getSocialAnalyticsKPIs({ period });
        if (!isMounted) return;
        const rows = (res?.data_source === 'live' ? res.platforms || [] : [])
          .filter((p) => (p.leads || 0) > 0)
          .map((p) => ({ id: p.id, name: p.name, shortName: p.name, value: p.leads, color: p.color, cpl: formatCpl(p.cpl_bdt) }))
          .sort((a, b) => b.value - a.value);
        setChannels(rows);
        setStatus(rows.length ? 'ready' : 'empty');
      } catch {
        if (isMounted) {
          setChannels([]);
          setStatus('error');
        }
      }
    }

    loadData();
    return () => { isMounted = false; };
  }, [period]);

  const totalLeads = channels.reduce((sum, c) => sum + (c.value || 0), 0);
  const topChannel = channels[0];
  const topShare = topChannel && totalLeads > 0 ? Math.round((topChannel.value / totalLeads) * 100) : 0;

  // Active slice display metrics
  const activeShare = (activeHover && totalLeads > 0)
    ? Math.round((activeHover.value / totalLeads) * 100)
    : 0;

  const periodOptions = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' }
  ];

  return (
    <Card 
      className="channel-attribution-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: '440px',
        padding: '20px 22px',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* ── Card Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'rgba(232, 101, 74, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Share2 size={16} color="var(--primary-coral)" />
            </div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
              Lead Acquisition & Channels
            </h3>
          </div>
          <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
            Ad leads by channel, synced from Meta, Google Ads & TikTok
          </p>
        </div>

        {/* Period Selector */}
        <CustomDropdown
          value={period}
          onChange={setPeriod}
          options={periodOptions}
          minWidth="130px"
          buttonStyle={{ padding: '4px 10px', fontSize: '0.74rem' }}
          ariaLabel="Select Attribution Period"
        />
      </div>

      {/* ── Donut Chart & Center KPI Display ── */}
      <div style={{ position: 'relative', width: '100%', height: '210px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={channels}
              innerRadius={68}
              outerRadius={98}
              paddingAngle={4}
              cornerRadius={5}
              dataKey="value"
              animationDuration={600}
              onMouseLeave={() => setActiveHover(null)}
            >
              {channels.map((entry) => {
                const isSliceActive = activeHover?.id === entry.id;
                return (
                  <Cell 
                    key={`cell-${entry.id}`} 
                    fill={entry.color} 
                    stroke="var(--bg-card)" 
                    strokeWidth={2}
                    onMouseEnter={() => setActiveHover(entry)}
                    style={{
                      filter: isSliceActive 
                        ? `brightness(1.18) drop-shadow(0 4px 12px ${entry.color}88)` 
                        : 'none',
                      opacity: activeHover && !isSliceActive ? 0.6 : 1,
                      cursor: 'pointer',
                      transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                    }}
                  />
                );
              })}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Centered Donut KPI Metric */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          pointerEvents: 'none',
          width: '130px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          userSelect: 'none'
        }}>
          {activeHover ? (
            <>
              <div style={{
                fontSize: '1.65rem',
                fontWeight: 800,
                color: activeHover.color,
                lineHeight: 1.05,
                letterSpacing: '-0.02em',
                transition: 'color 0.15s ease'
              }}>
                {activeHover.value.toLocaleString()}
              </div>
              <div style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                color: 'var(--text-main)',
                marginTop: '3px',
                maxWidth: '124px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {activeHover.shortName || activeHover.name}
              </div>
              <div style={{
                fontSize: '0.62rem',
                fontWeight: 700,
                color: activeHover.color,
                marginTop: '3px',
                background: `${activeHover.color}1c`,
                padding: '1px 8px',
                borderRadius: '10px'
              }}>
                {activeShare}% Share
              </div>
              <div style={{
                fontSize: '0.58rem',
                color: 'var(--text-muted)',
                marginTop: '3px',
                fontWeight: 500
              }}>
                CPL {activeHover.cpl}
              </div>
            </>
          ) : (
            <>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: 800,
                color: 'var(--text-main)',
                lineHeight: 1.05,
                letterSpacing: '-0.02em'
              }}>
                {totalLeads.toLocaleString()}
              </div>
              <div style={{
                fontSize: '0.76rem',
                fontWeight: 700,
                color: 'var(--text-main)',
                marginTop: '4px'
              }}>
                Total Leads
              </div>
              <div style={{
                fontSize: '0.64rem',
                color: 'var(--text-muted)',
                marginTop: '2px'
              }}>
                {channels.length ? `Across ${channels.length} channel${channels.length === 1 ? '' : 's'}` : status === 'loading' ? 'Loading…' : status === 'error' ? 'Could not load' : 'No synced ad leads'}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Channel Attribution Legend List ── */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '7px',
        marginTop: '10px',
        borderTop: '1px solid var(--border-glass)',
        paddingTop: '12px'
      }}>
        {channels.map((channel) => {
          const pct = totalLeads > 0 ? Math.round((channel.value / totalLeads) * 100) : 0;
          const isHovered = activeHover?.id === channel.id;

          return (
            <div
              key={channel.id}
              onMouseEnter={() => setActiveHover(channel)}
              onMouseLeave={() => setActiveHover(null)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '4px 8px',
                borderRadius: '8px',
                background: isHovered ? 'var(--bg-glass-hover, rgba(255, 255, 255, 0.05))' : 'transparent',
                boxShadow: isHovered ? `inset 0 0 0 1px ${channel.color}33` : 'none',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {/* Channel Dot & Name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '145px' }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: channel.color,
                  boxShadow: isHovered ? `0 0 10px ${channel.color}` : `0 0 6px ${channel.color}66`
                }} />
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: isHovered ? 700 : 600,
                  color: isHovered ? 'var(--text-main)' : 'var(--text-muted)'
                }}>
                  {channel.name}
                </span>
              </div>

              {/* Progress Bar */}
              <div style={{ flex: 1, maxWidth: '75px', margin: '0 12px', background: 'var(--bg-main)', height: '5px', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: channel.color,
                  borderRadius: '3px',
                  transition: 'width 0.4s ease'
                }} />
              </div>

              {/* Metrics */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {isHovered && (
                  <span style={{ 
                    fontSize: '0.62rem', 
                    color: '#059669', 
                    fontWeight: 600,
                    marginRight: '2px'
                  }}>
                    {channel.cpl}
                  </span>
                )}
                <span style={{ fontSize: '0.76rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  {channel.value}
                </span>
                <span style={{
                  fontSize: '0.68rem',
                  color: isHovered ? channel.color : 'var(--text-muted)',
                  fontWeight: isHovered ? 700 : 500,
                  width: '28px',
                  textAlign: 'right'
                }}>
                  {pct}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Footer KPI Callout & Navigation Link ── */}
      <div style={{
        marginTop: 'auto',
        paddingTop: '12px',
        borderTop: '1px solid var(--border-glass)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{
            fontSize: '0.68rem',
            padding: '2px 8px',
            borderRadius: '12px',
            background: 'rgba(37, 211, 102, 0.15)',
            color: '#25D366',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <Sparkles size={11} /> {topChannel ? `Top: ${topChannel.name} (${topShare}%)` : 'No leads in this period'}
          </span>
        </div>

        {onNavigateSocial && (
          <button
            onClick={onNavigateSocial}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary-coral)',
              fontSize: '0.72rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              padding: 0
            }}
          >
            <span>Full Campaign KPIs</span>
            <ChevronRight size={13} />
          </button>
        )}
      </div>
    </Card>
  );
}
