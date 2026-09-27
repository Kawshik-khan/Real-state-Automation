import baselineEvalReport from '../assets/baseline_eval_report.json';
import benchmarkSuitesData from '../assets/benchmark_suites.json';
import { clearSession, getAccessToken, setSession } from './session';

/**
 * API transport layer.
 *
 * Security model:
 * - The browser authenticates ONLY with the logged-in user's short-lived access token
 *   (`Authorization: Bearer`), held in memory (see ./session.js). No service secret is
 *   ever shipped to or sent from the browser.
 * - The API base URL comes from build configuration and the page's own location only —
 *   never from localStorage or other runtime-writable state — and credentials are only
 *   attached to requests whose origin is on that allow-list.
 * - EventSource/WebSocket connections use short-lived stream tickets (they cannot send
 *   an Authorization header).
 */

const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || '8000';
const CLIENT_HEADER = { 'X-GLG-Client': 'dashboard' };

/** True for loopback / RFC1918 / mDNS hosts used during local development. */
export function isLocalOrLanHost(hostname) {
  if (!hostname) return false;
  return (
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname === '0.0.0.0' ||
    hostname.endsWith('.local') ||
    /^10\./.test(hostname) ||
    /^192\.168\./.test(hostname) ||
    /^172\.(1[6-9]|2\d|3[01])\./.test(hostname)
  );
}

/**
 * When VITE_API_BASE_URL points at localhost but the dashboard is opened from another
 * device on the LAN, swap in the page's hostname so the device can reach the backend.
 */
export function resolveDynamicHost(targetUrl) {
  if (!targetUrl || typeof window === 'undefined') return targetUrl;
  const currentHost = window.location.hostname;
  if (currentHost && currentHost !== 'localhost' && currentHost !== '127.0.0.1' && isLocalOrLanHost(currentHost)) {
    return targetUrl
      .replace('://localhost:', `://${currentHost}:`)
      .replace('://127.0.0.1:', `://${currentHost}:`);
  }
  return targetUrl;
}

export const getApiBaseUrl = () => {
  // 1. Explicit build-time configuration
  if (import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== '') {
    return resolveDynamicHost(import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, ''));
  }

  if (typeof window === 'undefined') return '';
  const { protocol, hostname, port } = window.location;
  const isHttps = protocol === 'https:';

  // 2. Local dev server (e.g. Vite on 5173) talking straight to the backend port
  if (isLocalOrLanHost(hostname) && port && port !== BACKEND_PORT && !isHttps) {
    if (import.meta.env.VITE_USE_PROXY === 'true') return '';
    return `http://${hostname}:${BACKEND_PORT}`;
  }

  // 3. Render convention: xxx-frontend.onrender.com -> xxx-backend.onrender.com
  if (hostname.endsWith('.onrender.com')) {
    if (hostname.includes('-frontend.')) {
      return `https://${hostname.replace('-frontend.', '-backend.')}`;
    }
    return 'https://glg-realestate-backend.onrender.com';
  }

  // 4. Same origin (reverse proxy)
  return '';
};

export const API_BASE_URL = getApiBaseUrl();

export function buildApiUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const base = getApiBaseUrl();
  return base ? `${base.replace(/\/+$/, '')}${cleanPath}` : cleanPath;
}

/**
 * Candidate URLs for a path, derived only from build config and the page location
 * (never from storage an attacker could write to).
 */
export function getBackendCandidates(path = '') {
  const cleanPath = path ? (path.startsWith('/') ? path : `/${path}`) : '';
  const candidates = [];

  const primaryBase = getApiBaseUrl();
  if (primaryBase) candidates.push(`${primaryBase.replace(/\/+$/, '')}${cleanPath}`);

  // Same origin (Vite dev proxy or reverse proxy)
  candidates.push(cleanPath || '/');

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    if (isLocalOrLanHost(hostname) && protocol !== 'https:') {
      candidates.push(`http://${hostname}:${BACKEND_PORT}${cleanPath}`);
      if (hostname === 'localhost') candidates.push(`http://127.0.0.1:${BACKEND_PORT}${cleanPath}`);
      else if (hostname === '127.0.0.1') candidates.push(`http://localhost:${BACKEND_PORT}${cleanPath}`);
    }
  }

  return [...new Set(candidates.filter(Boolean))];
}

/** Candidate base URLs (without path) — used for health probing. */
export function getApiCandidates() {
  return getBackendCandidates('').map((url) => (url === '/' ? '' : url));
}

function originOf(url) {
  try {
    return new URL(url, typeof window !== 'undefined' ? window.location.href : 'http://localhost').origin;
  } catch {
    return null;
  }
}

/** Only these origins ever receive the user's bearer token. */
export function isTrustedApiUrl(url) {
  const target = originOf(url);
  if (!target) return false;
  const trusted = new Set(getBackendCandidates('/').map(originOf).filter(Boolean));
  if (typeof window !== 'undefined') trusted.add(window.location.origin);
  return trusted.has(target);
}

// ── Session refresh (single-flight) ────────────────────────────────────────

let refreshInFlight = null;

/**
 * Exchange the httpOnly refresh cookie for a new access token. Concurrent callers share
 * one request (rotation makes the old refresh token single-use).
 * Resolves to { access_token, user } or null.
 */
export function refreshSession() {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const resp = await fetch(buildApiUrl('/api/v1/auth/refresh'), {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json', ...CLIENT_HEADER },
          body: '{}',
        });
        if (!resp.ok) {
          clearSession();
          return null;
        }
        const data = await resp.json();
        if (!data.access_token) {
          clearSession();
          return null;
        }
        setSession(data.access_token, data.user ?? undefined);
        return data;
      } catch {
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

/**
 * fetch() for API calls: attaches the bearer token (trusted origins only) and, on a 401,
 * refreshes the session once and retries.
 */
export async function apiFetch(url, options = {}) {
  const trusted = isTrustedApiUrl(url);
  const build = () => {
    const headers = { ...(options.headers || {}) };
    const token = getAccessToken();
    if (trusted && token) headers.Authorization = `Bearer ${token}`;
    else delete headers.Authorization;
    return { ...options, headers };
  };

  let response = await fetch(url, build());
  if (response.status === 401 && trusted && !String(url).includes('/api/v1/auth/')) {
    const refreshed = await refreshSession();
    if (refreshed) response = await fetch(url, build());
  }
  return response;
}

/** Backwards-compatible alias. */
export const fetchWithAuth = apiFetch;

/**
 * Try allow-listed candidate URLs in order (dev convenience when the backend may be
 * reachable via proxy or direct port). Skips SPA HTML fallbacks.
 */
export async function resilientFetch(path, options = {}) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  let lastErr = null;

  for (const url of getBackendCandidates(cleanPath)) {
    try {
      const resp = await apiFetch(url, options);
      const contentType = resp.headers.get('content-type') || '';
      if (contentType.includes('text/html') && !cleanPath.endsWith('.html') && !cleanPath.endsWith('.svg')) {
        lastErr = new Error(`Endpoint ${url} returned HTML fallback instead of API response.`);
        continue;
      }
      return resp;
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error('Network error: unable to reach backend API');
}

// ── Streams (EventSource / WebSocket) ───────────────────────────────────────

async function getStreamTicket() {
  const resp = await apiFetch(buildApiUrl('/api/v1/auth/stream-ticket'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
  if (!resp.ok) throw new Error(`Stream ticket request failed (HTTP ${resp.status})`);
  const data = await resp.json();
  return data.ticket;
}

function withTicket(url, ticket) {
  return `${url}${url.includes('?') ? '&' : '?'}ticket=${encodeURIComponent(ticket)}`;
}

/**
 * EventSource-like handle for an authenticated SSE stream. Assign onopen / onmessage /
 * onerror as on a native EventSource. Reconnects with a fresh ticket (exponential backoff,
 * max 30 s) until close() is called.
 */
export function openAuthedEventSource(path) {
  const handle = { onopen: null, onmessage: null, onerror: null, closed: false, close: null };
  let source = null;
  let timer = null;
  let attempt = 0;

  const scheduleReconnect = () => {
    if (handle.closed) return;
    const delay = Math.min(30000, 1000 * 2 ** attempt);
    attempt += 1;
    timer = setTimeout(connect, delay);
  };

  async function connect() {
    if (handle.closed) return;
    try {
      const ticket = await getStreamTicket();
      if (handle.closed) return;
      source = new EventSource(withTicket(buildApiUrl(path), ticket));
      source.onopen = (e) => {
        attempt = 0;
        handle.onopen?.(e);
      };
      source.onmessage = (e) => handle.onmessage?.(e);
      source.onerror = (e) => {
        source?.close();
        handle.onerror?.(e);
        scheduleReconnect();
      };
    } catch (err) {
      handle.onerror?.(err);
      scheduleReconnect();
    }
  }

  handle.close = () => {
    handle.closed = true;
    if (timer) clearTimeout(timer);
    source?.close();
  };

  connect();
  return handle;
}

export function getWebSocketUrl(subpath = '/api/v1/ws/chat') {
  const cleanSubpath = subpath.startsWith('/') ? subpath : `/${subpath}`;

  if (import.meta.env.VITE_WS_BASE_URL) {
    return `${import.meta.env.VITE_WS_BASE_URL.replace(/\/+$/, '')}${cleanSubpath}`;
  }

  const apiBase = getApiBaseUrl();
  if (apiBase && apiBase.startsWith('http')) {
    return `${apiBase.replace(/^http/, 'ws')}${cleanSubpath}`;
  }

  if (typeof window !== 'undefined') {
    const { protocol, hostname, host, port } = window.location;
    const wsProto = protocol === 'https:' ? 'wss:' : 'ws:';
    if (isLocalOrLanHost(hostname) && port && port !== BACKEND_PORT && protocol !== 'https:') {
      return `${wsProto}//${hostname}:${BACKEND_PORT}${cleanSubpath}`;
    }
    return `${wsProto}//${host}${cleanSubpath}`;
  }

  return `ws://127.0.0.1:${BACKEND_PORT}${cleanSubpath}`;
}

/**
 * WebSocket-like handle authenticated with a stream ticket. Assign onopen / onmessage /
 * onerror / onclose as on a native WebSocket. Does not auto-reconnect (callers decide);
 * each call fetches a fresh ticket.
 */
export function openAuthedWebSocket(subpath = '/api/v1/ws/chat') {
  const handle = { onopen: null, onmessage: null, onerror: null, onclose: null, closed: false, socket: null };
  handle.close = () => {
    handle.closed = true;
    handle.socket?.close();
  };
  handle.send = (data) => handle.socket?.send(data);

  getStreamTicket()
    .then((ticket) => {
      if (handle.closed) return;
      const ws = new WebSocket(withTicket(getWebSocketUrl(subpath), ticket));
      handle.socket = ws;
      ws.onopen = (e) => handle.onopen?.(e);
      ws.onmessage = (e) => handle.onmessage?.(e);
      ws.onerror = (e) => handle.onerror?.(e);
      ws.onclose = (e) => handle.onclose?.(e);
    })
    .catch((err) => {
      handle.onerror?.(err);
      if (!handle.closed) handle.onclose?.({ code: 4401, reason: String(err?.message || err) });
    });

  return handle;
}

/**
 * Helper to handle fetch responses and errors
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      const text = await response.text().catch(() => '');
      if (text) errorDetail = text;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

/**
 * Send a chat message to the FastAPI backend supervisor graph
 */
export async function sendChatMessage(payload) {
  const response = await apiFetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Generate multi-platform social media content
 */
export async function generateContent(payload) {
  const response = await apiFetch(`${API_BASE_URL}/api/content`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Upload a document (PDF, TXT, MD) to the RAG Knowledge Base with OCR
 */
export async function uploadKnowledgeDocument(file, metadata = {}) {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append('file', file);
  if (metadata.project) formData.append('project', metadata.project);
  if (metadata.category) formData.append('category', metadata.category);
  if (metadata.document_type) formData.append('document_type', metadata.document_type);

  const headers = {
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await apiFetch(`${API_BASE_URL}/api/knowledge/upload`, {
    method: 'POST',
    headers,
    body: formData,
  });
  return handleResponse(response);
}

/**
 * Fetch all indexed RAG documents from backend
 */
export async function getKnowledgeDocuments() {
  const token = getAccessToken();
  const headers = {
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await apiFetch(`${API_BASE_URL}/api/v1/knowledge/documents`, {
    headers,
  });
  return handleResponse(response);
}

/**
 * Perform content moderation check
 */
export async function checkModeration(text) {
  const response = await apiFetch(`${API_BASE_URL}/api/moderation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });
  return handleResponse(response);
}

/**
 * Get all real-estate projects
 */
export async function getProjects() {
  const response = await apiFetch(`${API_BASE_URL}/api/projects`, {
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Get single real-estate project by ID
 */
export async function getProjectById(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/api/project/${projectId}`, {
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Query Hybrid RAG Vector Search directly
 */
export async function searchKnowledge(query, filter = {}) {
  const response = await apiFetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, filter }),
  });
  return handleResponse(response);
}

/**
 * Fetch active conversations list
 */
export async function getConversations() {
  const response = await apiFetch(buildApiUrl('/api/v1/conversations'), {
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Fetch full message history for a conversation (limit default 60)
 */
export async function getConversationMessages(convId, limit = 60) {
  const response = await apiFetch(buildApiUrl(`/api/v1/conversations/${convId}/messages?limit=${limit}`), {
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Toggle human takeover state for a conversation
 */
export async function toggleTakeover(convId) {
  const response = await apiFetch(buildApiUrl(`/api/v1/conversations/${convId}/takeover`), {
    method: 'POST',
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Send manual human agent reply to customer conversation
 */
export async function sendAgentReply(convId, text) {
  const response = await apiFetch(buildApiUrl(`/api/v1/conversations/${convId}/reply`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });
  return handleResponse(response);
}

/**
 * Create a new customer conversation / simulation lead
 */
export async function createConversation(payload) {
  const response = await apiFetch(buildApiUrl('/api/v1/conversations'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Send customer message (triggers AI graph pipeline if AI is active)
 */
export async function sendCustomerMessage(convId, text, channel = 'website') {
  const response = await apiFetch(buildApiUrl(`/api/v1/conversations/${convId}/message`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, channel }),
  });
  return handleResponse(response);
}

/**
 * Fetch executive analytics weekly report
 */
export async function getAnalyticsReport() {
  const response = await apiFetch(buildApiUrl('/api/v1/analytics/weekly-digest'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse(response);
}

/**
 * Fetch dynamic manager overview analytics and active campaigns
 */
export async function getManagerOverview() {
  const response = await apiFetch(buildApiUrl('/api/v1/analytics/manager-overview'), {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse(response);
}

/**
 * Update campaign status (ACTIVE / PAUSED)
 */
export async function updateCampaignStatus(campaignId, status) {
  const response = await apiFetch(buildApiUrl(`/api/v1/analytics/campaigns/${campaignId}/status`), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  });
  return handleResponse(response);
}


/**
 * Delete a conversation
 */
export async function deleteConversation(convId) {
  const response = await apiFetch(buildApiUrl(`/api/v1/conversations/${convId}`), {
    method: 'DELETE',
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Fetch n8n Workflow & Node Health Telemetry
 */
export async function getN8nTelemetry() {
  const response = await resilientFetch('/api/v1/automation/n8n/health', {
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Enable or disable an n8n workflow
 */
export async function toggleN8nWorkflow(workflowId, active) {
  const response = await resilientFetch(`/api/v1/automation/n8n/workflows/${workflowId}/toggle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ active }),
  });
  return handleResponse(response);
}

/**
 * Run latency ping test on an n8n workflow
 */
export async function testN8nWorkflow(workflowId) {
  const response = await resilientFetch(`/api/v1/automation/n8n/workflows/${workflowId}/test`, {
    method: 'POST',
    headers: {
    },
  });
  return handleResponse(response);
}

/**
 * Fetch Developer System Health diagnostics
 */
export async function getDeveloperSystemHealth() {
  const token = getAccessToken();
  const headers = {
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/system-health', {
    headers,
  });
  return handleResponse(response);
}

/**
 * Simulate Webhook Payload through AI Pipeline (Developer only)
 */
export async function simulateDeveloperWebhook(payload) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/simulate-webhook', {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Run RAG Vector Search Benchmark (Developer only)
 */
export async function benchmarkDeveloperRAG(payload) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/rag-benchmark', {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}
 
/**
 * Trigger live Supabase and Pinecone database & vector sync (Developer only)
 */
export async function syncDeveloperDatabases() {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/sync-databases', {
    method: 'POST',
    headers,
  });
  return handleResponse(response);
}

/**
 * Fetch Executive Cross-Role Summary Intelligence Report
 */
export async function getCrossRoleSummaryReport(period = '7d') {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/analytics/cross-role-summary?period=${encodeURIComponent(period)}`, {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Fetch real-time system logs from live buffer (Developer only)
 */
export async function getDeveloperLogs(params = {}) {
  const token = getAccessToken();
  const query = new URLSearchParams(params).toString();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/developer/logs${query ? `?${query}` : ''}`, {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Clear live system log buffer (Developer only)
 */
export async function clearDeveloperLogs() {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/logs', {
    method: 'DELETE',
    headers,
  });
  return handleResponse(response);
}

/**
 * Fetch Social Media KPI Analytics for Admin Command Center
 */
export async function getSocialAnalyticsKPIs(params = {}) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  let query = '';
  if (typeof params === 'string') {
    query = `period=${params}`;
  } else if (typeof params === 'object' && params !== null) {
    query = new URLSearchParams(params).toString();
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/analytics/social-kpis${query ? `?${query}` : ''}`, {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Simulate Facebook/Instagram Comment to Private DM Lead Bridge
 */
export async function simulateSocialCommentToDm(payload) {
  const response = await apiFetch(`${API_BASE_URL}/api/v1/social/simulator/comment-to-dm`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Run developer evaluation suites with progress streaming / HTTP fallback
 */
export async function runDeveloperEvals(suite = 'all', sampleSize = null, background = false) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/evals/run', {
    method: 'POST',
    headers,
    body: JSON.stringify({ suite, sample_size: sampleSize, background }),
  });
  return handleResponse(response);
}

/**
 * Quick check if FastAPI backend is online and reachable using dynamic candidate discovery
 */
export async function checkBackendHealth() {
  const endpoints = [
    ...getBackendCandidates('/health'),
    ...getBackendCandidates('/api/v1/developer/system-health')
  ];
  const uniqueEndpoints = [...new Set(endpoints)];

  for (const ep of uniqueEndpoints) {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 2000);
      const resp = await apiFetch(ep, { signal: controller.signal });
      clearTimeout(id);
      // Any response indicating server process is alive!
      if (resp && (resp.ok || resp.status === 401 || resp.status === 403)) {
        return true;
      }
    } catch {
      // continue to next candidate endpoint
    }
  }
  return false;
}

/**
 * Fetch latest developer evaluation scorecard and quality gates
 */
export async function getLatestDeveloperEvals() {
  try {
    const token = getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token && token !== 'null' && token !== 'undefined') {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await resilientFetch('/api/v1/developer/evals/latest', {
      method: 'GET',
      headers,
    });
    const res = await handleResponse(response);
    if (res && res.report) {
      return res;
    }
  } catch (err) {
    console.debug('[EvalsAPI] Backend latest report unreachable, using bundled baseline:', err.message);
  }

  // Resilient fallback: return bundled baseline scorecard
  return {
    success: true,
    status: 'success',
    report: baselineEvalReport,
    is_fallback: true,
  };
}

/**
 * Fetch live evaluation engine execution status and progress
 */
export async function getDeveloperEvalsStatus() {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/evals/status', {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Fetch list of available evaluation benchmark suites
 */
export async function getDeveloperEvalSuites() {
  try {
    const token = getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token && token !== 'null' && token !== 'undefined') {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await resilientFetch('/api/v1/developer/evals/suites', {
      method: 'GET',
      headers,
    });
    const res = await handleResponse(response);
    if (res && res.suites && res.suites.length > 0) {
      return res;
    }
  } catch (err) {
    console.debug('[EvalsAPI] Backend suites unreachable, using bundled suites:', err.message);
  }

  // Resilient fallback: return bundled suite metadata
  return {
    success: true,
    status: 'success',
    suites: benchmarkSuitesData.suites,
    is_fallback: true,
  };
}

/**
 * Create a new real-estate project
 */
export async function createProject(projectData) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/projects`, {
    method: 'POST',
    headers,
    body: JSON.stringify(projectData),
  });
  return handleResponse(response);
}

/**
 * Fetch inbound email threads for review
 */
export async function getEmailThreads() {
  const token = getAccessToken();
  const headers = {
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/email/threads`, {
    headers,
  });
  return handleResponse(response);
}

/**
 * Approve AI email draft reply and dispatch via worker
 */
export async function approveEmailDraft(threadId, payload = {}) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/email/threads/${threadId}/approve`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Reject AI email draft reply
 */
export async function rejectEmailDraft(threadId) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/email/threads/${threadId}/reject`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ thread_id: threadId }),
  });
  return handleResponse(response);
}

/**
 * Update access permission tag on a knowledge document
 */
export async function updateKnowledgeAccess(docId, accessLevel) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/knowledge/documents/${docId}/access`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ access_level: accessLevel }),
  });
  return handleResponse(response);
}

/**
 * Fetch calendar events and upcoming property critical dates
 */
export async function getCalendarEvents() {
  const token = getAccessToken();
  const headers = {
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/calendar/milestones`, {
    headers,
  });
  return handleResponse(response);
}

/**
 * Fetch calendar milestones (site visits, signings, payments, handovers)
 */
export async function getCalendarMilestones(params = {}) {
  const token = getAccessToken();
  const headers = {
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/api/v1/calendar/milestones${query ? `?${query}` : ''}`;
  const response = await apiFetch(url, { headers });
  return handleResponse(response);
}

/**
 * Create a new calendar milestone
 */
export async function createCalendarMilestone(milestoneData) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/calendar/milestones`, {
    method: 'POST',
    headers,
    body: JSON.stringify(milestoneData),
  });
  return handleResponse(response);
}

/**
 * Create a site tour booking
 */
export async function createSiteTourBooking(bookingData) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/automation/booking`, {
    method: 'POST',
    headers,
    body: JSON.stringify(bookingData),
  });
  return handleResponse(response);
}

/**
 * Publish or schedule social media post
 */
export async function publishSocialPost(postData) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiFetch(`${API_BASE_URL}/api/v1/content/publish`, {
    method: 'POST',
    headers,
    body: JSON.stringify(postData),
  });
  return handleResponse(response);
}

/**
 * Fetch social media post history and content calendar entries
 */
export async function getSocialPosts(params = {}) {
  const token = getAccessToken();
  const headers = {
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/api/v1/content/posts${query ? `?${query}` : ''}`;
  const response = await apiFetch(url, { headers });
  return handleResponse(response);
}

/**
 * Fetch analytics volume timeseries (inquiries, visits, bookings)
 */
export async function getTimeSeriesAnalytics(params = {}) {
  const token = getAccessToken();
  const headers = {
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/api/v1/analytics/volume-timeseries${query ? `?${query}` : ''}`;
  const response = await apiFetch(url, { headers });
  return handleResponse(response);
}
// Alias for backward compatibility
export const getSocialKPIs = getSocialAnalyticsKPIs;

/**
 * Fetch Multi-Tier L1/L2 and Semantic Cache Diagnostics
 */
export async function getDeveloperCacheStats() {
  const token = getAccessToken();
  const headers = {
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/cache/stats', { headers });
  return handleResponse(response);
}

/**
 * Flush all L1/L2 and Semantic caches
 */
export async function flushDeveloperCaches() {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/cache/flush', {
    method: 'POST',
    headers,
  });
  return handleResponse(response);
}

/**
 * Unlock account locked out by brute-force protection (Admin/Manager only)
 */
export async function unlockUserAccount(email) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/auth/unlock', {
    method: 'POST',
    headers,
    body: JSON.stringify({ email }),
  });
  return handleResponse(response);
}

// ── AI & Agent Customization Studio API ──────────────────────

/**
 * Fetch all agent configurations from PostgreSQL/Supabase
 */
export async function getAgentConfigs() {
  const token = getAccessToken();
  const headers = {
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/agent-config', { headers });
  return handleResponse(response);
}

/**
 * Fetch single agent configuration
 */
export async function getAgentConfig(agentKey) {
  const token = getAccessToken();
  const headers = {
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/developer/agent-config/${encodeURIComponent(agentKey)}`, { headers });
  return handleResponse(response);
}

/**
 * Save or update agent configuration directly in PostgreSQL/Supabase
 */
export async function saveAgentConfig(configData) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/agent-config', {
    method: 'POST',
    headers,
    body: JSON.stringify(configData),
  });
  return handleResponse(response);
}

/**
 * Reset agent configuration to canonical system defaults
 */
export async function resetAgentConfig(agentKey = null) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/agent-config/reset', {
    method: 'POST',
    headers,
    body: JSON.stringify({ agent_key: agentKey }),
  });
  return handleResponse(response);
}

/**
 * Fetch real-time token telemetry and cost analytics (USD and BDT)
 */
export async function getTokenUsageTelemetry() {
  const token = getAccessToken();
  const headers = {
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/token-usage', { headers });
  return handleResponse(response);
}

/**
 * Fetch fine-tuning jobs and active LoRA adapters
 */
export async function getFineTuningJobs() {
  const token = getAccessToken();
  const headers = {
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/finetuning/jobs', { headers });
  return handleResponse(response);
}

/**
 * Trigger a new fine-tuning job
 */
export async function triggerFineTuningJob(payload) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/finetuning/jobs', {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Generate synthetic Q&A dataset pairs
 */
export async function generateSyntheticData(targetAgent = 'property_agent', count = 50) {
  const token = getAccessToken();
  const headers = {
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/developer/finetuning/synthetic-data?target_agent=${encodeURIComponent(targetAgent)}&count=${count}`, {
    method: 'POST',
    headers,
  });
  return handleResponse(response);
}

/**
 * Test agent prompt in interactive developer playground
 */
export async function testAgentPlayground(payload) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/developer/agent-playground/test', {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * ==========================================================
 * SCHEDULED REPORTS & MULTI-CHANNEL DELIVERY API
 * ==========================================================
 */

/**
 * Fetch all report schedules with configured recipients and channels
 */
export async function getReportSchedules() {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/reports/schedules', {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Create or configure a new report schedule (Admin only)
 */
export async function createReportSchedule(scheduleData) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/reports/schedules', {
    method: 'POST',
    headers,
    body: JSON.stringify(scheduleData),
  });
  return handleResponse(response);
}

/**
 * Toggle an automated schedule active/paused
 */
export async function toggleReportSchedule(scheduleId, isActive) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/reports/schedules/${encodeURIComponent(scheduleId)}/toggle`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ is_active: isActive }),
  });
  return handleResponse(response);
}

/**
 * Manually trigger immediate report generation & multi-channel delivery ("Run Now")
 */
export async function triggerReportNow(scheduleId, payload = {}) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/reports/schedules/${encodeURIComponent(scheduleId)}/trigger`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Fetch report execution history & channel delivery audit logs
 */
export async function getReportHistory(limit = 20) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/reports/history?limit=${limit}`, {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Fetch single report detail including rendered HTML preview
 */
export async function getReportDetail(reportId) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch(`/api/v1/reports/history/${encodeURIComponent(reportId)}`, {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Send an immediate test brief across Email, Telegram, or WhatsApp
 */
export async function sendTestReport(payload) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await resilientFetch('/api/v1/reports/test-dispatch', {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

