import baselineEvalReport from '../assets/baseline_eval_report.json';
import benchmarkSuitesData from '../assets/benchmark_suites.json';

/**
 * Dynamic API Base URL resolver:
 * 1. Honors explicit VITE_API_BASE_URL (stripping trailing slashes).
 *    If client is accessing via mobile/LAN and target was set to localhost/127.0.0.1,
 *    it dynamically replaces it with current window hostname so the device can reach the backend.
 * 2. In browser local dev or LAN (localhost, 127.0.0.1, 192.168.x.x, 10.x.x.x, *.local):
 *    Directly routes to ${protocol}//${hostname}:${backendPort} (default port 8000, or VITE_BACKEND_PORT).
 * 3. In production or behind reverse proxy (same-origin / port matching):
 *    Returns '' (relative path) to leverage same-origin routing with zero CORS and zero mixed-content issues.
 */
export function resolveDynamicHost(targetUrl) {
  if (!targetUrl || typeof window === 'undefined') return targetUrl;
  const currentHost = window.location.hostname;
  if (currentHost && currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
    return targetUrl
      .replace('://localhost:', `://${currentHost}:`)
      .replace('://127.0.0.1:', `://${currentHost}:`);
  }
  return targetUrl;
}

export const getApiBaseUrl = () => {
  // 1. Explicit environment variable override
  if (import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== '') {
    const raw = import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, '');
    return resolveDynamicHost(raw);
  }

  // 2. Runtime global or storage override (allows dynamic cloud configuration)
  if (typeof window !== 'undefined') {
    if (window.__GLG_API_BASE_URL__) {
      return window.__GLG_API_BASE_URL__.replace(/\/+$/, '');
    }
    try {
      const stored = localStorage.getItem('glg_api_base_url');
      if (stored) return stored.replace(/\/+$/, '');
    } catch {
      // Ignore storage access errors
    }

    const { protocol, hostname, port } = window.location;
    const isHttps = protocol === 'https:';
    const httpProto = isHttps ? 'https:' : 'http:';
    const backendPort = import.meta.env.VITE_BACKEND_PORT || '8000';

    const isLocalOrLan = (
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '0.0.0.0' ||
      hostname.startsWith('192.168.') ||
      hostname.startsWith('10.') ||
      hostname.startsWith('172.') ||
      hostname.endsWith('.local')
    );

    // If local dev server (e.g. Vite on 5173) and not HTTPS, target backendPort
    if (isLocalOrLan && port && port !== backendPort && !isHttps) {
      if (import.meta.env.VITE_USE_PROXY === 'true') {
        return '';
      }
      return `${httpProto}//${hostname}:${backendPort}`;
    }

    // Auto-detect Render hosting convention:
    // If frontend is deployed on `xxx-frontend.onrender.com`, default backend is `https://xxx-backend.onrender.com`
    // Or if hostname ends with `.onrender.com`, fallback to default production backend `https://glg-realestate-backend.onrender.com`
    if (hostname.endsWith('.onrender.com')) {
      if (hostname.includes('-frontend.')) {
        return `https://${hostname.replace('-frontend.', '-backend.')}`;
      }
      return 'https://glg-realestate-backend.onrender.com';
    }

    // In production or when co-located behind reverse proxy
    return '';
  }

  return '';
};

export const API_BASE_URL = getApiBaseUrl();
const AUTOMATION_SECRET = import.meta.env.VITE_AUTOMATION_SECRET || '3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8';

/**
 * Robust API URL builder that correctly joins base URL and path
 * avoiding double slashes or missing slashes.
 */
export function buildApiUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const base = getApiBaseUrl();
  return base ? `${base.replace(/\/+$/, '')}${cleanPath}` : cleanPath;
}

/**
 * Dynamic candidate generator for resilient fetching, authentication fallback, and health probing.
 */
export function getBackendCandidates(path = '') {
  const cleanPath = path ? (path.startsWith('/') ? path : `/${path}`) : '';
  const candidates = [];

  // 1. Primary resolved base URL
  const primaryBase = getApiBaseUrl();
  if (primaryBase) {
    candidates.push(`${primaryBase.replace(/\/+$/, '')}${cleanPath}`);
  }

  // 2. Relative path (same origin or Vite dev proxy)
  candidates.push(cleanPath || '/');

  // 3. Last known working backend from auth session
  if (typeof window !== 'undefined') {
    try {
      const working = localStorage.getItem('glg_working_backend');
      if (working) {
        candidates.push(`${working.replace(/\/+$/, '')}${cleanPath}`);
      }
    } catch {
      // Ignore storage access errors
    }

    // 4. Local dev / LAN alternate endpoints
    const { protocol, hostname } = window.location;
    const isHttps = protocol === 'https:';
    const httpProto = isHttps ? 'https:' : 'http:';
    const backendPort = import.meta.env.VITE_BACKEND_PORT || '8000';

    const isLocalOrLan = (
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '0.0.0.0' ||
      hostname.startsWith('192.168.') ||
      hostname.startsWith('10.') ||
      hostname.startsWith('172.') ||
      hostname.endsWith('.local')
    );

    if (isLocalOrLan && !isHttps) {
      candidates.push(`${httpProto}//${hostname}:${backendPort}${cleanPath}`);
      if (hostname === 'localhost') {
        candidates.push(`${httpProto}//127.0.0.1:${backendPort}${cleanPath}`);
      } else if (hostname === '127.0.0.1') {
        candidates.push(`${httpProto}//localhost:${backendPort}${cleanPath}`);
      }
    }

    // Render candidate fallback
    if (hostname.endsWith('.onrender.com')) {
      candidates.push(`https://glg-realestate-backend.onrender.com${cleanPath}`);
    }
  }

  // Deduplicate and filter empty
  const unique = [];
  for (const c of candidates) {
    if (c && !unique.includes(c)) {
      unique.push(c);
    }
  }
  return unique;
}

/**
 * Returns candidate base URLs (for auth service and health checks)
 */
export function getApiCandidates() {
  const candidates = getBackendCandidates('/api/v1/health');
  return [...new Set(candidates.map(url => {
    if (url.endsWith('/api/v1/health')) {
      return url.slice(0, -'/api/v1/health'.length);
    }
    return url;
  }))];
}

/**
 * Resilient fetch with dynamic multi-candidate fallback:
 * 1. Resolved primary base URL
 * 2. Same-origin relative path (through Vite proxy in dev, Vercel/Nginx proxy in prod -> zero CORS)
 * 3. Last known working backend
 * 4. Local dev / LAN direct host
 */
export async function resilientFetch(path, options = {}) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const candidates = getBackendCandidates(cleanPath);
  let lastErr = null;

  for (const url of candidates) {
    try {
      const resp = await fetch(url, options);
      if (resp) {
        // If an API request returned HTML (static SPA rewrite fallback), discard and try next candidate
        const contentType = resp.headers.get('content-type') || '';
        if (contentType.includes('text/html') && !cleanPath.endsWith('.html') && !cleanPath.endsWith('.svg')) {
          lastErr = new Error(`Endpoint ${url} returned HTML fallback instead of API response.`);
          continue;
        }
        return resp;
      }
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error('Network error: unable to reach backend API');
}

let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
}

/**
 * Enhanced fetch wrapper with automatic 401 retry via Refresh Token Rotation (RTR).
 */
export async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('glg_token');
  const headers = { ...(options.headers || {}) };
  if (token && token !== 'null' && token !== 'undefined' && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(url, { ...options, headers, credentials: 'include' });

  // If 401 Unauthorized and not calling auth endpoints directly, attempt silent refresh
  if (response.status === 401 && !url.includes('/api/v1/auth/')) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const { authService } = await import('./auth');
        const newToken = await authService.refreshToken();
        isRefreshing = false;
        if (newToken) {
          onTokenRefreshed(newToken);
          headers['Authorization'] = `Bearer ${newToken}`;
          return fetch(url, { ...options, headers, credentials: 'include' });
        }
      } catch (err) {
        isRefreshing = false;
        throw err;
      }
    } else {
      return new Promise((resolve) => {
        subscribeTokenRefresh((newToken) => {
          headers['Authorization'] = `Bearer ${newToken}`;
          resolve(fetch(url, { ...options, headers, credentials: 'include' }));
        });
      });
    }
  }

  return response;
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
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Generate multi-platform social media content
 */
export async function generateContent(payload) {
  const response = await fetch(`${API_BASE_URL}/api/content`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Upload a document (PDF, TXT, MD) to the RAG Knowledge Base with OCR
 */
export async function uploadKnowledgeDocument(file, metadata = {}) {
  const token = localStorage.getItem('glg_token');
  const formData = new FormData();
  formData.append('file', file);
  if (metadata.project) formData.append('project', metadata.project);
  if (metadata.category) formData.append('category', metadata.category);
  if (metadata.document_type) formData.append('document_type', metadata.document_type);

  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/api/knowledge/upload`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/knowledge/documents`, {
    headers,
  });
  return handleResponse(response);
}

/**
 * Perform content moderation check
 */
export async function checkModeration(text) {
  const response = await fetch(`${API_BASE_URL}/api/moderation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify({ text }),
  });
  return handleResponse(response);
}

/**
 * Get all real-estate projects
 */
export async function getProjects() {
  const response = await fetch(`${API_BASE_URL}/api/projects`, {
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Get single real-estate project by ID
 */
export async function getProjectById(projectId) {
  const response = await fetch(`${API_BASE_URL}/api/project/${projectId}`, {
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Query Hybrid RAG Vector Search directly
 */
export async function searchKnowledge(query, filter = {}) {
  const response = await fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify({ query, filter }),
  });
  return handleResponse(response);
}

/**
 * Fetch active conversations list
 */
export async function getConversations() {
  const response = await fetch(buildApiUrl('/api/v1/conversations'), {
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Fetch full message history for a conversation (limit default 60)
 */
export async function getConversationMessages(convId, limit = 60) {
  const response = await fetch(buildApiUrl(`/api/v1/conversations/${convId}/messages?limit=${limit}`), {
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Toggle human takeover state for a conversation
 */
export async function toggleTakeover(convId) {
  const response = await fetch(buildApiUrl(`/api/v1/conversations/${convId}/takeover`), {
    method: 'POST',
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Send manual human agent reply to customer conversation
 */
export async function sendAgentReply(convId, text) {
  const response = await fetch(buildApiUrl(`/api/v1/conversations/${convId}/reply`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify({ text }),
  });
  return handleResponse(response);
}

/**
 * Create a new customer conversation / simulation lead
 */
export async function createConversation(payload) {
  const response = await fetch(buildApiUrl('/api/v1/conversations'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Send customer message (triggers AI graph pipeline if AI is active)
 */
export async function sendCustomerMessage(convId, text, channel = 'website') {
  const response = await fetch(buildApiUrl(`/api/v1/conversations/${convId}/message`), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify({ text, channel }),
  });
  return handleResponse(response);
}

/**
 * Fetch executive analytics weekly report
 */
export async function getAnalyticsReport() {
  const response = await fetch(buildApiUrl('/api/v1/analytics/weekly-digest'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Fetch dynamic manager overview analytics and active campaigns
 */
export async function getManagerOverview() {
  const response = await fetch(buildApiUrl('/api/v1/analytics/manager-overview'), {
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Update campaign status (ACTIVE / PAUSED)
 */
export async function updateCampaignStatus(campaignId, status) {
  const response = await fetch(buildApiUrl(`/api/v1/analytics/campaigns/${campaignId}/status`), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify({ status }),
  });
  return handleResponse(response);
}


/**
 * Delete a conversation
 */
export async function deleteConversation(convId) {
  const response = await fetch(buildApiUrl(`/api/v1/conversations/${convId}`), {
    method: 'DELETE',
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Get SSE stream URL for live conversation event listening
 */
export function getConversationsStreamUrl() {
  return buildApiUrl('/api/v1/conversations/stream');
}

export function getWebSocketUrl(subpath = '/api/v1/ws/chat') {
  const cleanSubpath = subpath.startsWith('/') ? subpath : `/${subpath}`;

  // 1. Explicit WebSocket URL override
  if (import.meta.env.VITE_WS_BASE_URL) {
    return `${import.meta.env.VITE_WS_BASE_URL.replace(/\/+$/, '')}${cleanSubpath}`;
  }

  // 2. Derive from resolved API base URL if explicitly set with http/https
  const apiBase = getApiBaseUrl();
  if (apiBase && apiBase.startsWith('http')) {
    const wsProto = apiBase.startsWith('https') ? 'wss:' : 'ws:';
    const cleanHost = apiBase.replace(/^https?:\/\//, '');
    return `${wsProto}//${cleanHost}${cleanSubpath}`;
  }

  // 3. In browser environment
  if (typeof window !== 'undefined') {
    const { protocol, hostname, host, port } = window.location;
    const wsProto = protocol === 'https:' ? 'wss:' : 'ws:';
    const backendPort = import.meta.env.VITE_BACKEND_PORT || '8000';

    const isLocalOrLan = (
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '0.0.0.0' ||
      hostname.startsWith('192.168.') ||
      hostname.startsWith('10.') ||
      hostname.startsWith('172.') ||
      hostname.endsWith('.local')
    );

    // If local dev running on frontend dev port (e.g. 5173), connect directly to backend port
    if (isLocalOrLan && port && port !== backendPort && protocol !== 'https:') {
      return `${wsProto}//${hostname}:${backendPort}${cleanSubpath}`;
    }

    // In production or reverse-proxied deployment
    return `${wsProto}//${host}${cleanSubpath}`;
  }

  const fallbackPort = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_PORT) || '8000';
  return `ws://127.0.0.1:${fallbackPort}${cleanSubpath}`;
}

/**
 * Fetch n8n Workflow & Node Health Telemetry
 */
export async function getN8nTelemetry() {
  const response = await resilientFetch('/api/v1/automation/n8n/health', {
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
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
      'X-Automation-Secret': AUTOMATION_SECRET,
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
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Fetch Developer System Health diagnostics
 */
export async function getDeveloperSystemHealth() {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const query = new URLSearchParams(params).toString();
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
 * Get SSE URL for live log streaming
 */
export function getDeveloperLogsStreamUrl() {
  return buildApiUrl('/api/v1/developer/logs/stream');
}

/**
 * Fetch Social Media KPI Analytics for Admin Command Center
 */
export async function getSocialAnalyticsKPIs(params = {}) {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const response = await fetch(`${API_BASE_URL}/api/v1/analytics/social-kpis${query ? `?${query}` : ''}`, {
    method: 'GET',
    headers,
  });
  return handleResponse(response);
}

/**
 * Simulate Facebook/Instagram Comment to Private DM Lead Bridge
 */
export async function simulateSocialCommentToDm(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/social/simulator/comment-to-dm`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Run developer evaluation suites with progress streaming / HTTP fallback
 */
export async function runDeveloperEvals(suite = 'all', sampleSize = null, background = false) {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
      const resp = await fetch(ep, {
        signal: controller.signal,
        headers: { 'X-Automation-Secret': AUTOMATION_SECRET }
      });
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
    const token = localStorage.getItem('glg_token');
    const headers = {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
    const token = localStorage.getItem('glg_token');
    const headers = {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/projects`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/email/threads`, {
    headers,
  });
  return handleResponse(response);
}

/**
 * Approve AI email draft reply and dispatch via worker
 */
export async function approveEmailDraft(threadId, payload = {}) {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/email/threads/${threadId}/approve`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/email/threads/${threadId}/reject`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/knowledge/documents/${docId}/access`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/calendar/milestones`, {
    headers,
  });
  return handleResponse(response);
}

/**
 * Fetch calendar milestones (site visits, signings, payments, handovers)
 */
export async function getCalendarMilestones(params = {}) {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/api/v1/calendar/milestones${query ? `?${query}` : ''}`;
  const response = await fetch(url, { headers });
  return handleResponse(response);
}

/**
 * Create a new calendar milestone
 */
export async function createCalendarMilestone(milestoneData) {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/calendar/milestones`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/automation/booking`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/content/publish`, {
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/api/v1/content/posts${query ? `?${query}` : ''}`;
  const response = await fetch(url, { headers });
  return handleResponse(response);
}

/**
 * Fetch analytics volume timeseries (inquiries, visits, bookings)
 */
export async function getTimeSeriesAnalytics(params = {}) {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/api/v1/analytics/volume-timeseries${query ? `?${query}` : ''}`;
  const response = await fetch(url, { headers });
  return handleResponse(response);
}
// Alias for backward compatibility
export const getSocialKPIs = getSocialAnalyticsKPIs;

/**
 * Fetch Multi-Tier L1/L2 and Semantic Cache Diagnostics
 */
export async function getDeveloperCacheStats() {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
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
  const token = localStorage.getItem('glg_token');
  const headers = {
    'Content-Type': 'application/json',
    'X-Automation-Secret': AUTOMATION_SECRET,
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

