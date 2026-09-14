import { resilientFetch, fetchWithAuth } from './api';

const AUTOMATION_SECRET = import.meta.env.VITE_AUTOMATION_SECRET || '3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8';

function getAuthHeaders(isJson = false) {
  const token = localStorage.getItem('glg_token');
  const headers = {
    'X-Automation-Secret': AUTOMATION_SECRET,
  };
  if (isJson) {
    headers['Content-Type'] = 'application/json';
  }
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(resp) {
  if (!resp.ok) {
    const errorText = await resp.text();
    let msg = `HTTP error ${resp.status}`;
    try {
      const parsed = JSON.parse(errorText);
      msg = parsed.detail || parsed.message || msg;
    } catch {
      msg = errorText || msg;
    }
    throw new Error(msg);
  }
  return resp.json();
}

// ── 1. Overview & Telemetry ──

export async function getAiOverview(timeRange = '7d', agent = null) {
  const query = new URLSearchParams({ time_range: timeRange });
  if (agent && agent !== 'all') query.append('agent', agent);
  const resp = await resilientFetch(`/api/v1/ai-control/overview?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

// ── 2. Agents ──

export async function getAiAgents() {
  const resp = await resilientFetch('/api/v1/ai-control/agents', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function getAiAgent(slug) {
  const resp = await resilientFetch(`/api/v1/ai-control/agents/${encodeURIComponent(slug)}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function saveAiAgent(agentData) {
  const resp = await resilientFetch('/api/v1/ai-control/agents', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(agentData),
  });
  return handleResponse(resp);
}

export async function publishAiAgent(slug, changelog) {
  const resp = await resilientFetch(`/api/v1/ai-control/agents/${encodeURIComponent(slug)}/publish`, {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ changelog }),
  });
  return handleResponse(resp);
}

export async function validateAiPrompt(promptText) {
  const resp = await resilientFetch('/api/v1/ai-control/prompts/validate', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ prompt_text: promptText }),
  });
  return handleResponse(resp);
}

// ── 3. Models & Providers ──

export async function getAiProviders() {
  const resp = await resilientFetch('/api/v1/ai-control/providers', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function getAiModels() {
  const resp = await resilientFetch('/api/v1/ai-control/models', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function testAiModelConnection(providerKey, modelId = null) {
  const resp = await resilientFetch('/api/v1/ai-control/models/test-connection', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ provider_key: providerKey, model_id: modelId }),
  });
  return handleResponse(resp);
}

// ── 4. Routing ──

export async function getAiRoutingRules() {
  const resp = await resilientFetch('/api/v1/ai-control/routing/rules', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function simulateAiRouting(task, complexity, agentSlug) {
  const resp = await resilientFetch('/api/v1/ai-control/routing/simulate', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ task, complexity, agent_slug: agentSlug }),
  });
  return handleResponse(resp);
}

// ── 5. Tools ──

export async function getAiTools() {
  const resp = await resilientFetch('/api/v1/ai-control/tools', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function testAiTool(toolKey, parameters = {}) {
  const resp = await resilientFetch('/api/v1/ai-control/tools/test', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ tool_key: toolKey, parameters }),
  });
  return handleResponse(resp);
}

// ── 6. Workflows ──

export async function getAiWorkflows() {
  const resp = await resilientFetch('/api/v1/ai-control/workflows', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function validateAiWorkflow(nodes, edges) {
  const resp = await resilientFetch('/api/v1/ai-control/workflows/validate', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ nodes, edges }),
  });
  return handleResponse(resp);
}

// ── 7. RAG ──

export async function testAiRagRetrieval(query, topK = 4, alpha = 0.65) {
  const resp = await resilientFetch('/api/v1/ai-control/rag/retrieve-test', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ query, top_k: topK, alpha }),
  });
  return handleResponse(resp);
}

// ── 8. Guardrails ──

export async function getAiGuardrails() {
  const resp = await resilientFetch('/api/v1/ai-control/guardrails', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function testAiGuardrail(ruleId, testText) {
  const resp = await resilientFetch('/api/v1/ai-control/guardrails/test', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ rule_id: ruleId, test_text: testText }),
  });
  return handleResponse(resp);
}

// ── 9. Playground ──

export async function runAiPlayground(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/playground/run', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

// ── 10. Evaluations ──

export async function getAiEvaluations() {
  const resp = await resilientFetch('/api/v1/ai-control/evaluations', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function runAiEvaluation(datasetId, agentSlug) {
  const resp = await resilientFetch('/api/v1/ai-control/evaluations/run', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ dataset_id: datasetId, agent_slug: agentSlug }),
  });
  return handleResponse(resp);
}

// ── 11. Cost Optimization ──

export async function getAiCostRecommendations() {
  const resp = await resilientFetch('/api/v1/ai-control/cost/recommendations', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

// ── 12. Releases ──

export async function getAiReleases() {
  const resp = await resilientFetch('/api/v1/ai-control/releases', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function createAiRelease(releaseTag, title, description = '') {
  const resp = await resilientFetch('/api/v1/ai-control/releases', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ release_tag: releaseTag, title, description }),
  });
  return handleResponse(resp);
}

export async function deployAiRelease(releaseTag) {
  const resp = await resilientFetch('/api/v1/ai-control/releases/deploy', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ release_tag: releaseTag }),
  });
  return handleResponse(resp);
}

export async function rollbackAiRelease(releaseTag) {
  const resp = await resilientFetch('/api/v1/ai-control/releases/rollback', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ release_tag: releaseTag }),
  });
  return handleResponse(resp);
}

// ── 13. Approvals ──

export async function getAiApprovals(status = 'PENDING') {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  const resp = await resilientFetch(`/api/v1/ai-control/approvals${query}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function decideAiApproval(approvalId, status, notes = '', editedContent = null) {
  const resp = await resilientFetch(`/api/v1/ai-control/approvals/${encodeURIComponent(approvalId)}/decision`, {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ status, notes, edited_content: editedContent }),
  });
  return handleResponse(resp);
}

// ── 14. Incidents & Circuit Breakers ──

export async function getAiIncidents() {
  const resp = await resilientFetch('/api/v1/ai-control/incidents', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function createAiIncident(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/incidents', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

export async function updateAiIncident(incidentId, status, note = '', resolution = '') {
  const resp = await resilientFetch(`/api/v1/ai-control/incidents/${encodeURIComponent(incidentId)}`, {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ status, note, resolution }),
  });
  return handleResponse(resp);
}

export async function tripCircuitBreaker(agentSlug, reason = 'Emergency Stop triggered') {
  const resp = await resilientFetch('/api/v1/ai-control/circuit-breaker/trip', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ agent_slug: agentSlug, reason }),
  });
  return handleResponse(resp);
}

export async function resetCircuitBreaker(agentSlug) {
  const resp = await resilientFetch('/api/v1/ai-control/circuit-breaker/reset', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ agent_slug: agentSlug }),
  });
  return handleResponse(resp);
}

// ── 15. Traces & Observability ──

export async function getAiTraces(limit = 50, agent = null) {
  const query = new URLSearchParams({ limit: String(limit) });
  if (agent && agent !== 'all') query.append('agent', agent);
  const resp = await resilientFetch(`/api/v1/ai-control/traces?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function getAiTrace(traceId) {
  const resp = await resilientFetch(`/api/v1/ai-control/traces/${encodeURIComponent(traceId)}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

// ── 16. Budget & Tokens ──

export async function getAiBudget() {
  const resp = await resilientFetch('/api/v1/ai-control/budget', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function updateAiBudget(budgetData) {
  const resp = await resilientFetch('/api/v1/ai-control/budget', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(budgetData),
  });
  return handleResponse(resp);
}

// ── 17. Datasets & Benchmarks ──

export async function getAiDatasets() {
  const resp = await resilientFetch('/api/v1/ai-control/datasets', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function getAiDatasetExamples(datasetId) {
  const resp = await resilientFetch(`/api/v1/ai-control/datasets/${encodeURIComponent(datasetId)}/examples`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function addAiDatasetExample(datasetId, exampleData) {
  const resp = await resilientFetch(`/api/v1/ai-control/datasets/${encodeURIComponent(datasetId)}/examples`, {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(exampleData),
  });
  return handleResponse(resp);
}

// ── 18. Agent Version History & Rollback ──

export async function getAiAgentVersions(slug) {
  const resp = await resilientFetch(`/api/v1/ai-control/agents/${encodeURIComponent(slug)}/versions`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function rollbackAiAgent(slug, targetVersion) {
  const resp = await resilientFetch(`/api/v1/ai-control/agents/${encodeURIComponent(slug)}/rollback`, {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ target_version: targetVersion }),
  });
  return handleResponse(resp);
}

// ── 19. Red-Teaming, Stress Testing & Fine-Tuning ──

export async function runAiRedTeamTest(agentSlug) {
  const resp = await resilientFetch('/api/v1/ai-control/red-team/run', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ agent_slug: agentSlug }),
  });
  return handleResponse(resp);
}

export async function runAiStressTest(agentSlug, concurrency = 5, numRequests = 10) {
  const resp = await resilientFetch('/api/v1/ai-control/stress-test/run', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ agent_slug: agentSlug, concurrency, num_requests: numRequests }),
  });
  return handleResponse(resp);
}

export async function triggerAiFineTuning(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/fine-tuning/trigger', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

export async function getVectorStoreStatus() {
  const resp = await resilientFetch('/api/v1/ai-control/vector-store/status', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function applyCostOptimization(recommendationId) {
  const resp = await resilientFetch('/api/v1/ai-control/cost/apply-recommendation', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ recommendation_id: recommendationId }),
  });
  return handleResponse(resp);
}

// ── 20. Audit Logs ──

export async function getAiAuditLogs(limit = 100) {
  const resp = await resilientFetch(`/api/v1/ai-control/audit?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

// ── 21. Fine-Tuning Jobs ──

export async function getAiFineTuneJobs(agentSlug = null) {
  const query = agentSlug && agentSlug !== 'all' ? `?agent_slug=${encodeURIComponent(agentSlug)}` : '';
  const resp = await resilientFetch(`/api/v1/ai-control/fine-tuning/jobs${query}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function cancelAiFineTuneJob(jobId) {
  const resp = await resilientFetch(`/api/v1/ai-control/fine-tuning/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders(true),
  });
  return handleResponse(resp);
}

// ── 22. A/B Testing & Experiments ──

export async function getAiExperiments(agentSlug = null) {
  const query = agentSlug && agentSlug !== 'all' ? `?agent_slug=${encodeURIComponent(agentSlug)}` : '';
  const resp = await resilientFetch(`/api/v1/ai-control/experiments${query}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function createAiExperiment(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/experiments', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

export async function actOnAiExperiment(experimentId, action, winner = null) {
  const resp = await resilientFetch(`/api/v1/ai-control/experiments/${encodeURIComponent(experimentId)}/action`, {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify({ action: (action || '').toUpperCase(), winner }),
  });
  return handleResponse(resp);
}

// ── 23. Benchmarking ──

export async function getAiBenchmarks(agentSlug = null) {
  const query = agentSlug && agentSlug !== 'all' ? `?agent_slug=${encodeURIComponent(agentSlug)}` : '';
  const resp = await resilientFetch(`/api/v1/ai-control/benchmarks${query}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function runAiBenchmark(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/benchmarks/run', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

// ── 24. Scoped Memories ──

export async function getAiMemories(agentSlug = null, scope = null, customerId = null) {
  const params = new URLSearchParams();
  if (agentSlug && agentSlug !== 'all') params.append('agent_slug', agentSlug);
  if (scope) params.append('scope', scope);
  if (customerId) params.append('customer_id', customerId);
  const qStr = params.toString() ? `?${params.toString()}` : '';
  const resp = await resilientFetch(`/api/v1/ai-control/memories${qStr}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function createAiMemory(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/memories', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

export async function deleteAiMemory(memoryId) {
  const resp = await resilientFetch(`/api/v1/ai-control/memories/${encodeURIComponent(memoryId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

// ── 25. Configuration Snapshots (AI Versioning) ──

export async function getAiSnapshots(agentSlug = null) {
  const query = agentSlug && agentSlug !== 'all' ? `?agent_slug=${encodeURIComponent(agentSlug)}` : '';
  const resp = await resilientFetch(`/api/v1/ai-control/snapshots${query}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function createAiSnapshot(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/snapshots', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

export async function rollbackAiSnapshot(snapshotTag) {
  const resp = await resilientFetch(`/api/v1/ai-control/snapshots/${encodeURIComponent(snapshotTag)}/restore`, {
    method: 'POST',
    headers: getAuthHeaders(true),
  });
  return handleResponse(resp);
}

// ── 26. Policy Engine & Rule Builder ──

export async function getAiPolicies() {
  const resp = await resilientFetch('/api/v1/ai-control/policies', {
    headers: getAuthHeaders(),
  });
  return handleResponse(resp);
}

export async function createAiPolicy(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/policies', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

export async function simulateAiPolicy(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/policies/simulate', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}

// ── 27. Model Recommendation ──

export async function recommendAiModel(payload) {
  const resp = await resilientFetch('/api/v1/ai-control/models/recommend', {
    method: 'POST',
    headers: getAuthHeaders(true),
    body: JSON.stringify(payload),
  });
  return handleResponse(resp);
}



// ── 16. Real-Time SSE Stream ──

export function connectAiEventSource(onEvent, onError) {
  const token = localStorage.getItem('glg_token');
  const query = token ? `?token=${encodeURIComponent(token)}` : '';
  const url = `/api/v1/ai-control/events/stream${query}`;

  try {
    const es = new EventSource(url);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (onEvent) onEvent(data);
      } catch (err) {
        console.debug('SSE parse error:', err);
      }
    };
    es.onerror = (err) => {
      if (onError) onError(err);
      es.close();
    };
    return es;
  } catch (err) {
    if (onError) onError(err);
    return null;
  }
}
