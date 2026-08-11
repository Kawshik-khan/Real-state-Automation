import { workflow, trigger, node, ifElse, splitInBatches, nextBatch, expr, newCredential } from '@n8n/workflow-sdk';

// ── Trigger: Schedule (every hour) ──
const scheduleTrigger = trigger('n8n-nodes-base.scheduleTrigger', 1.3, {
  name: 'Hourly Retry Check',
  parameters: {
    rule: {
      interval: {},
    },
    scheduling: {
      timezone: 'UTC',
      activation: { hour: -1, minute: 0, weekday: -1, dayOfMonth: -1, month: -1 },
    },
  },
  output: [{ timestamp: '2026-07-27T14:00:00Z' }],
});

// ── Find Failed AI Requests ──
const findFailedRequests = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Find Failed AI Requests',
  parameters: {
    method: 'GET',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/failed'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      failures: [
        {
          id: 'fail_001',
          originalRequest: { userId: 'user_123', message: 'Hello', channel: 'whatsapp' },
          error: 'Rate limit exceeded',
          retryCount: 0,
          createdAt: '2026-07-27T13:00:00Z',
        },
        {
          id: 'fail_002',
          originalRequest: { userId: 'user_456', message: 'I need information', channel: 'facebook' },
          error: 'Timeout',
          retryCount: 1,
          createdAt: '2026-07-27T12:30:00Z',
        },
      ],
    },
  ],
});

// ── Check if Failures Exist ──
const hasFailures = ifElse({
  version: 2.3,
  config: {
    name: 'Has Failures?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
        conditions: [
          {
            id: 'fail-check',
            leftValue: expr('{{ $json.failures }}'),
            operator: { type: 'array', operation: 'notEmpty' },
            rightValue: '',
          },
        ],
        combinator: 'and',
      },
    },
  },
});

// ── Normalize Failures ──
const normalizeFailures = node('n8n-nodes-base.code', 2, {
  name: 'Normalize Failures',
  parameters: {
    mode: 'runOnceForAllItems',
    jsCode: `
      const failures = $input.first().json.failures || [];
      if (!Array.isArray(failures) || failures.length === 0) {
        return [{ json: { hasItems: false } }];
      }
      return failures.map(f => ({ json: { ...f, hasItems: true } }));
    `,
  },
  output: [
    { id: 'fail_001', originalRequest: { userId: 'user_123', message: 'Hello' }, error: 'Rate limit', retryCount: 0, hasItems: true },
  ],
});

// ── Split Into Batches ──
const splitBatches = splitInBatches({
  version: 3,
  config: {
    name: 'Process Failures in Batches',
    parameters: {
      batchSize: 1,
      options: {},
    },
  },
});

// ── Check Retry Limit ──
const canRetry = ifElse({
  version: 2.3,
  config: {
    name: 'Can Retry? (retryCount < 3)',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
        conditions: [
          {
            id: 'retry-limit',
            leftValue: expr('{{ $json.retryCount }}'),
            operator: { type: 'number', operation: 'smaller' },
            rightValue: 3,
          },
        ],
        combinator: 'and',
      },
    },
  },
});

// ── Retry via AI API ──
const retryAIRequest = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Retry AI API Request',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/message'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { userId: $json.originalRequest.userId, message: $json.originalRequest.message, channel: $json.originalRequest.channel, isRetry: true, retryId: $json.id } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ success: true, aiResponse: 'Here is the information you requested...', messageId: 'ai_retry_001' }],
});

// ── Mark as Resolved ──
const markResolved = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Mark as Resolved',
  parameters: {
    method: 'PATCH',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/failed/' + $json.id + '/resolve'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { status: "resolved", resolvedAt: new Date().toISOString() } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ updated: true, status: 'resolved' }],
});

// ── Notify Admin (max retries reached) ──
const notifyAdminMaxRetries = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Notify Admin (Max Retries)',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/email'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { to: "admin@glgassets.com", subject: "AI Retry Failed - Max Retries Reached - " + $json.id, body: "The following AI request has failed after maximum retries.\\n\\nFailure ID: " + $json.id + "\\nUser: " + $json.originalRequest.userId + "\\nError: " + $json.error + "\\nRetry Count: " + $json.retryCount + "\\n\\nManual intervention required." } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ messageId: 'alert_email_001', accepted: true }],
});

// ── Mark as Notified (stop retrying) ──
const markExhausted = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Mark as Exhausted',
  parameters: {
    method: 'PATCH',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/failed/' + $json.id + '/resolve'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { status: "exhausted", notified: true, resolvedAt: new Date().toISOString() } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ updated: true, status: 'exhausted' }],
});

// ── Log Summary ──
const logSummary = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Log Retry Summary',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { workflow: "wf-failed-ai-replies", status: "completed", timestamp: new Date().toISOString(), failuresProcessed: 1 } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ logged: true }],
});

// ── Build and Export ──
export default workflow('wf-failed-ai-replies', 'Failed AI Replies Retry Handler')
  .description(
    'Triggers every hour. Fetches failed AI requests from the backend. If failures exist, ' +
    'processes them in batches. For each failure with fewer than 3 retries, retries the AI API call. ' +
    'On success, marks the failure as resolved. On reaching max retries, notifies the admin and marks as exhausted.'
  )
  .onError('stopWorkflow')
  .add(scheduleTrigger)
  .to(findFailedRequests)
  .to(hasFailures.onTrue(normalizeFailures))
  .to(splitBatches)
  .to(
    canRetry
      .onTrue(retryAIRequest.to(markResolved))
      .onFalse(notifyAdminMaxRetries.to(markExhausted))
  )
  .to(nextBatch(splitBatches))
  .to(logSummary);
