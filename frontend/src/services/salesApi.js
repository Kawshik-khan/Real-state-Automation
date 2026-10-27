/**
 * Sales engine API client (/api/v1/sales). Every call uses the signed-in staff token.
 * Errors throw with the server's message, e.g. "Someone else changed this record; reload and try again".
 */
import { buildApiUrl, fetchWithAuth } from './api';

async function call(path, { method = 'GET', body, params } = {}) {
  let url = buildApiUrl(`/api/v1/sales${path}`);
  if (params) {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''));
    if ([...qs].length) url += `?${qs}`;
  }
  const res = await fetchWithAuth(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const err = new Error((data && (data.detail?.message || data.detail)) || `Request failed (${res.status})`);
    err.status = res.status;
    err.code = data && data.code;
    throw err;
  }
  return data;
}

export const salesApi = {
  overview: () => call('/overview'),
  projects: () => call('/projects'),

  units: (params) => call('/units', { params }),
  createUnit: (body) => call('/units', { method: 'POST', body }),
  updateUnit: (unitId, body) => call(`/units/${unitId}`, { method: 'PATCH', body }),

  plans: (projectId) => call('/payment-plans', { params: { project_id: projectId } }),
  createPlan: (body) => call('/payment-plans', { method: 'POST', body }),

  slots: (projectId) => call('/visit-slots', { params: { project_id: projectId } }),
  createSlot: (body) => call('/visit-slots', { method: 'POST', body }),
  deleteSlot: (slotId) => call(`/visit-slots/${slotId}`, { method: 'DELETE' }),
  freeSlots: (projectId) => call('/visit-slots/free', { params: { project_id: projectId } }),

  leads: (params) => call('/leads', { params }),
  lead: (leadId) => call(`/leads/${leadId}`),
  createLead: (body) => call('/leads', { method: 'POST', body }),
  updateLead: (leadId, body) => call(`/leads/${leadId}`, { method: 'PATCH', body }),
  setStage: (leadId, stage, lostReason) => call(`/leads/${leadId}/stage`, { method: 'POST', body: { stage, lost_reason: lostReason } }),
  addNote: (leadId, text) => call(`/leads/${leadId}/notes`, { method: 'POST', body: { text } }),
  bookVisit: (leadId, projectId, slotStart) => call(`/leads/${leadId}/visits`, { method: 'POST', body: { project_id: projectId, slot_start: slotStart } }),

  visits: (params) => call('/visits', { params }),
  updateVisit: (visitId, body) => call(`/visits/${visitId}`, { method: 'PATCH', body }),

  approvals: (status = 'PENDING') => call('/approvals', { params: { status } }),
  decide: (approvalId, decision, reason) => call(`/approvals/${approvalId}/decision`, { method: 'POST', body: { decision, reason } }),

  conversations: (mode) => call('/conversations', { params: { mode } }),
  messages: (conversationId) => call(`/conversations/${conversationId}/messages`),
  reply: (conversationId, text) => call(`/conversations/${conversationId}/reply`, { method: 'POST', body: { text } }),
  setChatMode: (conversationId, mode, reason) => call(`/conversations/${conversationId}/mode`, { method: 'POST', body: { mode, reason } }),
  rateDraft: (messageId, rating) => call(`/drafts/${messageId}/rating`, { method: 'POST', body: { rating } }),

  sequences: () => call('/sequences'),
  saveSequence: (trigger, body) => call(`/sequences/${trigger}`, { method: 'PUT', body }),
  installDefaultSequences: () => call('/sequences/install-defaults', { method: 'POST' }),

  settings: () => call('/settings'),
  updateSettings: (body) => call('/settings', { method: 'PATCH', body }),
  digestPreview: () => call('/digest/preview', { method: 'POST' }),
};

export const STAGES = [
  { id: 'NEW', label: 'New' },
  { id: 'QUALIFIED', label: 'Qualified' },
  { id: 'VISIT_BOOKED', label: 'Visit booked' },
  { id: 'VISITED', label: 'Visited' },
  { id: 'NEGOTIATING', label: 'Negotiating' },
  { id: 'BOOKING_MONEY', label: 'Booking money' },
  { id: 'WON', label: 'Won' },
  { id: 'LOST', label: 'Lost' },
];

export const stageLabel = (id) => STAGES.find((s) => s.id === id)?.label || id;

export function formatBdt(amount) {
  if (amount === null || amount === undefined) return '—';
  if (amount >= 10_000_000) return `৳${(amount / 10_000_000).toFixed(2).replace(/\.?0+$/, '')} Cr`;
  if (amount >= 100_000) return `৳${(amount / 100_000).toFixed(1).replace(/\.0$/, '')} L`;
  return `৳${amount.toLocaleString('en-IN')}`;
}

export function formatWhen(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('en-GB', { timeZone: 'Asia/Dhaka', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
}

export const canManage = (role) => ['admin', 'manager'].includes(role);
export const canWork = (role) => ['admin', 'manager', 'agent'].includes(role);
