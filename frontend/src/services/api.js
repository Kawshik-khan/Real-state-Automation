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
const AUTOMATION_SECRET = import.meta.env.VITE_AUTOMATION_SECRET || 'glg-secret-key';

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
  const formData = new FormData();
  formData.append('file', file);
  if (metadata.project) formData.append('project', metadata.project);
  if (metadata.category) formData.append('category', metadata.category);
  if (metadata.document_type) formData.append('document_type', metadata.document_type);

  const response = await fetch(`${API_BASE_URL}/api/knowledge/upload`, {
    method: 'POST',
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
    body: formData,
  });
  return handleResponse(response);
}

/**
 * Fetch all indexed RAG documents from backend
 */
export async function getKnowledgeDocuments() {
  const response = await fetch(`${API_BASE_URL}/api/v1/knowledge/documents`, {
    headers: {
      'X-Automation-Secret': AUTOMATION_SECRET,
    },
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


