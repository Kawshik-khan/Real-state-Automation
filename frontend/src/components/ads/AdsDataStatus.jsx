import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Database,
  FlaskConical,
  PlugZap,
  RefreshCw,
} from 'lucide-react';
import { getAdsSyncStatus, triggerAdsSync } from '../../services/api';
import { isNum, timeAgo } from './adsFormat';

const SOURCE_STYLES = {
  live: { label: 'Synced', color: '#059669', bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.3)', Icon: CheckCircle2 },
  demo: { label: 'Demo data', color: '#B45309', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.35)', Icon: FlaskConical },
  empty: { label: 'No ad data yet', color: 'var(--text-muted)', bg: 'var(--bg-main)', border: 'var(--border-glass)', Icon: Database },
  unconfigured: { label: 'Database not configured', color: '#DC2626', bg: 'rgba(239, 68, 68, 0.1)', border: 'rgba(239, 68, 68, 0.3)', Icon: AlertTriangle },
};

/**
 * ▲ 12.4% / ▼ 3.1% versus the previous period.
 * inverse: a drop is good (cost per lead). neutral: direction carries no judgement (spend).
 */
export function DeltaBadge({ value, inverse = false, neutral = false, suffix = 'vs previous period' }) {
  if (!isNum(value)) {
    return (
      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }} title="The previous period has no value to compare against">
        No comparison
      </span>
    );
  }
  const good = inverse ? value < 0 : value > 0;
  const color = value === 0 || neutral ? 'var(--text-muted)' : good ? '#059669' : '#DC2626';
  const Icon = value >= 0 ? ArrowUpRight : ArrowDownRight;
  return (
    <span style={{ fontSize: '0.74rem', color, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
      <Icon size={12} />
      {Math.abs(value).toFixed(1)}% <span style={{ fontWeight: 500, color: 'var(--text-muted)' }}>{suffix}</span>
    </span>
  );
}

export function DataSourceBadge({ source, lastSyncedAt }) {
  const style = SOURCE_STYLES[source] || SOURCE_STYLES.empty;
  const ago = timeAgo(lastSyncedAt);
  return (
    <span
      title={lastSyncedAt ? `Last synced ${new Date(lastSyncedAt).toLocaleString()}` : undefined}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '999px',
        fontSize: '0.74rem', fontWeight: 700, color: style.color, background: style.bg, border: `1px solid ${style.border}`,
      }}
    >
      <style.Icon size={13} />
      <span>{style.label}</span>
      {source === 'live' && ago && <span style={{ fontWeight: 500, opacity: 0.8 }}>• {ago}</span>}
    </span>
  );
}

/** Starts a background sync and polls /ads/status until it finishes. */
export function SyncNowButton({ onSynced, disabled }) {
  const [state, setState] = useState('idle'); // idle | syncing | error
  const [message, setMessage] = useState(null);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const poll = (deadline) => {
    timer.current = setTimeout(async () => {
      try {
        const status = await getAdsSyncStatus();
        if (status.running && Date.now() < deadline) {
          poll(deadline);
          return;
        }
        const failed = (status.platforms || []).filter((p) => p.last_run?.status === 'failed');
        setState(failed.length ? 'error' : 'idle');
        setMessage(failed.length ? `${failed.map((p) => p.display_name).join(', ')}: ${failed[0].last_run.error || 'sync failed'}` : null);
        onSynced && onSynced();
      } catch (err) {
        setState('error');
        setMessage(err.message);
      }
    }, 4000);
  };

  const start = async () => {
    setState('syncing');
    setMessage(null);
    try {
      await triggerAdsSync({ lookback_days: 7 });
      poll(Date.now() + 180000);
    } catch (err) {
      setState('error');
      setMessage(err.message);
    }
  };

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <button
        onClick={start}
        disabled={disabled || state === 'syncing'}
        title="Pull the last 7 days from every connected ad account"
        style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '7px 14px', borderRadius: '8px',
          background: 'var(--bg-card)', border: '1px solid var(--border-glass)', color: 'var(--text-main)',
          fontSize: '0.78rem', fontWeight: 700, cursor: disabled || state === 'syncing' ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
        }}
      >
        <PlugZap size={14} className={state === 'syncing' ? 'spin-anim' : ''} />
        <span>{state === 'syncing' ? 'Syncing…' : 'Sync now'}</span>
      </button>
      {message && (
        <span style={{ fontSize: '0.72rem', color: '#DC2626', maxWidth: '360px' }} title={message}>
          {message.length > 90 ? `${message.slice(0, 90)}…` : message}
        </span>
      )}
    </div>
  );
}

export function RefreshButton({ onClick, loading }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '7px 14px', borderRadius: '8px',
        background: 'var(--bg-card)', border: '1px solid var(--border-glass)', color: 'var(--text-main)',
        fontSize: '0.78rem', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
      }}
    >
      <RefreshCw size={14} className={loading ? 'spin-anim' : ''} />
      <span>{loading ? 'Loading…' : 'Refresh'}</span>
    </button>
  );
}

export function DemoBanner({ onHide }) {
  return (
    <div
      className="glass-card"
      style={{
        padding: '12px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px',
        background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.35)', color: '#B45309',
        fontSize: '0.82rem', fontWeight: 600,
      }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <FlaskConical size={16} />
        Demo seed data — these are not real campaign results. Period, previous-period and reach comparisons do not apply.
      </span>
      <button
        onClick={onHide}
        style={{ background: 'transparent', border: '1px solid #B45309', color: '#B45309', borderRadius: '6px', padding: '4px 10px', fontSize: '0.74rem', fontWeight: 700, cursor: 'pointer' }}
      >
        Hide demo data
      </button>
    </div>
  );
}

export function WarningsBanner({ warnings }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <div
      className="glass-card"
      style={{
        padding: '10px 18px', display: 'flex', flexDirection: 'column', gap: '4px',
        background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#B45309', fontSize: '0.8rem',
      }}
    >
      {warnings.map((w) => (
        <span key={w} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={14} /> {w}
        </span>
      ))}
    </div>
  );
}

const EMPTY_COPY = {
  empty: {
    title: 'No ad platform data has been synced yet',
    body: 'Connect Meta Ads, Google Ads or TikTok Ads under Developer Console → Service Integrations → Ad Platforms (or set the credentials in the backend environment). The backend then syncs every hour and backfills the last 90 days on first run.',
  },
  unconfigured: {
    title: 'The analytics database is not configured',
    body: 'The backend needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to read synced ad metrics.',
  },
};

export function AdsEmptyState({ source, demoAvailable, onShowDemo, canSync, onSynced }) {
  const copy = EMPTY_COPY[source] || EMPTY_COPY.empty;
  return (
    <div
      className="glass-card"
      style={{ padding: '36px 28px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}
    >
      <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(232, 101, 74, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <PlugZap size={24} color="var(--accent-coral)" />
      </div>
      <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>{copy.title}</h2>
      <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', margin: 0, maxWidth: '640px', lineHeight: 1.5 }}>{copy.body}</p>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center', marginTop: '6px' }}>
        {canSync && source === 'empty' && <SyncNowButton onSynced={onSynced} />}
        {demoAvailable && (
          <button
            onClick={onShowDemo}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '7px 14px', borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.35)', color: '#B45309',
              fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer',
            }}
          >
            <FlaskConical size={14} /> Preview with demo data
          </button>
        )}
      </div>
    </div>
  );
}
