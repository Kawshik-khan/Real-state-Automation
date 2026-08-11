import { workflow, trigger, node, ifElse, expr, newCredential, placeholder } from '@n8n/workflow-sdk';

// ── Trigger: Webhook ──
const webhookTrigger = trigger('n8n-nodes-base.webhook', 2.1, {
  name: 'Moderation Webhook',
  parameters: {
    httpMethod: 'POST',
    path: placeholder('moderation'),
    responseMode: 'lastNode',
    responseData: 'firstEntryJson',
  },
  output: [
    {
      body: {
        text: 'Check out this amazing property offer!',
        source: 'facebook_comment',
        authorId: 'user_123',
      },
    },
  ],
});

// ── Normalize Input ──
const normalizeInput = node('n8n-nodes-base.set', 3.4, {
  name: 'Normalize Input',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'ni-text', name: 'text', value: expr('{{ $json.body?.text ?? $json.text ?? "" }}'), type: 'string' },
        { id: 'ni-source', name: 'source', value: expr('{{ $json.body?.source ?? $json.source ?? "" }}'), type: 'string' },
        { id: 'ni-author', name: 'authorId', value: expr('{{ $json.body?.authorId ?? $json.authorId ?? "" }}'), type: 'string' },
      ],
    },
  },
  output: [
    { text: 'Check out this amazing property offer!', source: 'facebook_comment', authorId: 'user_123' },
  ],
});

// ── Call Moderation API ──
const callModerationAPI = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Call Moderation API',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/moderation/spam'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { text: $json.text, source: $json.source, authorId: $json.authorId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      isToxic: false,
      isSpam: false,
      confidence: 0.98,
      categories: [],
      action: 'allow',
    },
  ],
});

// ── Check if Content is Toxic/Spam ──
const isToxicOrSpam = ifElse({
  version: 2.3,
  config: {
    name: 'Is Toxic or Spam?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
        conditions: [
          {
            id: 'toxic-check',
            leftValue: expr('{{ $json.isToxic }}'),
            operator: { type: 'boolean', operation: 'equals' },
            rightValue: true,
          },
          {
            id: 'spam-check',
            leftValue: expr('{{ $json.isSpam }}'),
            operator: { type: 'boolean', operation: 'equals' },
            rightValue: true,
          },
        ],
        combinator: 'or',
      },
    },
  },
});

// ── Hide Comment via Platform API ──
const hideComment = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Hide Comment',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/moderation/hide'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { text: $json.text, source: $json.source, authorId: $json.authorId, reason: $json.action || "toxic_or_spam" } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ hidden: true, moderationId: 'mod_hide_001' }],
});

// ── Flag for Review ──
const flagForReview = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Flag for Review',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/moderation/flag'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { text: $json.text, source: $json.source, authorId: $json.authorId, action: $json.action, isToxic: $json.isToxic, isSpam: $json.isSpam } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ flagged: true, flagId: 'flag_001' }],
});

// ── Notify Admin ──
const notifyModerationAdmin = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Notify Admin',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/slack'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { channel: "#moderation-alerts", text: "🚫 Content Flagged\\nAuthor: " + $json.authorId + "\\nSource: " + $json.source + "\\nText: " + $json.text.substring(0, 100) + "\\nToxic: " + $json.isToxic + "\\nSpam: " + $json.isSpam } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ ok: true, ts: 'mod_slack_001' }],
});

// ── Allow Content ──
const allowContent = node('n8n-nodes-base.set', 3.4, {
  name: 'Allow Content',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'ac-allow', name: 'allow', value: true, type: 'boolean' },
        { id: 'ac-msg', name: 'message', value: 'Content is clean. No action needed.', type: 'string' },
      ],
    },
  },
  output: [{ allow: true, message: 'Content is clean. No action needed.' }],
});

// ── Log All Actions ──
const logModerationAction = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Log Moderation Action',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { workflow: "wf-moderation", text: $json.text, authorId: $json.authorId, source: $json.source, isToxic: $json.isToxic, isSpam: $json.isSpam, action: $json.isToxic || $json.isSpam ? "blocked" : "allowed" } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ logged: true }],
});

// ── Build and Export ──
export default workflow('wf-moderation', 'Content Moderation')
  .description(
    'Receives a webhook with text, source, and authorId. Calls the moderation API to check if content is toxic or spam. ' +
    'If flagged: hides the comment via the platform API, flags for review, notifies admin on Slack, and logs the action. ' +
    'If clean: returns allow=true. All actions are logged.'
  )
  .onError('stopWorkflow')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(callModerationAPI)
  .to(
    isToxicOrSpam
      .onTrue(hideComment.to(flagForReview).to(notifyModerationAdmin).to(logModerationAction))
      .onFalse(allowContent.to(logModerationAction))
  );
