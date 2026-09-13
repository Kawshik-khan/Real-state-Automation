const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  return 'https://real-state-automation.onrender.com';
};

const API_BASE_URL = getApiBaseUrl();
const AUTOMATION_SECRET = import.meta.env.VITE_AUTOMATION_SECRET || '3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8';

/**
 * Helper to handle fetch responses and errors
 */
async function handleResponse(response) {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP Error ${response.status}`);
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
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${convId}/takeover`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${convId}/reply`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${convId}/message`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/analytics/weekly-digest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Delete a conversation
 */
export async function deleteConversation(convId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${convId}`, {
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
  return `${API_BASE_URL}/api/v1/conversations/stream`;
}

export function getWebSocketUrl() {
  const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss:' : 'ws:';
  const cleanHost = API_BASE_URL.replace(/^https?:\/\//, '');
  return `${wsProtocol}//${cleanHost}/api/v1/ws/chat`;
}

/**
 * Fetch n8n Workflow & Node Health Telemetry
 */
export async function getN8nTelemetry() {
  const response = await fetch(`${API_BASE_URL}/api/v1/automation/n8n/health`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/automation/n8n/workflows/${workflowId}/toggle`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/automation/n8n/workflows/${workflowId}/test`, {
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
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/system-health`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Simulate Webhook Payload through AI Pipeline (Developer only)
 */
export async function simulateDeveloperWebhook(payload) {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/simulate-webhook`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Run RAG Vector Search Benchmark (Developer only)
 */
export async function benchmarkDeveloperRAG(payload) {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/rag-benchmark`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}
 
/**
 * Trigger live Supabase and Pinecone database & vector sync (Developer only)
 */
export async function syncDeveloperDatabases() {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/sync-databases`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Fetch Executive Cross-Role Summary Intelligence Report
 */
export async function getCrossRoleSummaryReport(period = '7d') {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/analytics/cross-role-summary?period=${encodeURIComponent(period)}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Fetch real-time system logs from live buffer (Developer only)
 */
export async function getDeveloperLogs(params = {}) {
  const token = localStorage.getItem('glg_token');
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/logs${query ? `?${query}` : ''}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Clear live system log buffer (Developer only)
 */
export async function clearDeveloperLogs() {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/logs`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Get SSE URL for live log streaming
 */
export function getDeveloperLogsStreamUrl() {
  return `${API_BASE_URL}/api/v1/developer/logs/stream`;
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
export async function runDeveloperEvals(suite = 'all', sampleSize = null) {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/evals/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: JSON.stringify({ suite, sample_size: sampleSize }),
  });
  return handleResponse(response);
}

/**
 * Fetch latest developer evaluation scorecard and quality gates
 */
export async function getLatestDeveloperEvals() {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/evals/latest`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
}

/**
 * Fetch list of available evaluation benchmark suites
 */
export async function getDeveloperEvalSuites() {
  const token = localStorage.getItem('glg_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/developer/evals/suites`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
  });
  return handleResponse(response);
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


