// Formatting helpers for synced ad-platform metrics. Values that the backend
// could not compute arrive as null and are rendered as an em dash, never as 0.

export const DASH = '—';

export function isNum(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

export function formatNumber(value) {
  return isNum(value) ? Math.round(value).toLocaleString('en-IN') : DASH;
}

export function formatBDT(value) {
  if (!isNum(value)) return DASH;
  const digits = Math.abs(value) < 100 && value !== 0 ? 2 : 0;
  return `৳${value.toLocaleString('en-IN', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
}

export function formatPct(value, digits = 1) {
  return isNum(value) ? `${value.toFixed(digits)}%` : DASH;
}

export function formatSeconds(value) {
  if (!isNum(value)) return DASH;
  if (value < 60) return `${value.toFixed(value < 10 ? 1 : 0)}s`;
  if (value < 3600) return `${Math.round(value / 60)} min`;
  return `${(value / 3600).toFixed(1)} h`;
}

export function timeAgo(iso) {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  const mins = Math.round((Date.now() - then) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (hours < 48) return `${hours} h ago`;
  return `${Math.round(hours / 24)} days ago`;
}

export function formatDate(iso) {
  if (!iso) return DASH;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return DASH;
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function shortDate(isoDate) {
  if (!isoDate) return '';
  const d = new Date(`${isoDate}T00:00:00`);
  return Number.isNaN(d.getTime()) ? isoDate : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

export const PERIOD_OPTIONS = [
  { id: 'today', label: 'Today' },
  { id: '7d', label: '7 Days' },
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
];

export const CAMPAIGN_TYPE_LABELS = {
  lead_generation: 'Lead Generation',
  messages: 'Messages / Click-to-WhatsApp',
  traffic: 'Traffic',
  engagement: 'Engagement',
  brand_awareness: 'Brand Awareness',
  video_views: 'Video Views',
  sales: 'Sales / Conversions',
  other: 'Other',
};

export const REACH_METHOD_NOTES = {
  account_dedup: 'De-duplicated per ad account by each platform',
  campaign_sum: 'Sum of campaign reach — people reached by two campaigns count twice',
  unavailable: 'Reach is not available for this selection',
  demo: 'Demo seed value',
};
