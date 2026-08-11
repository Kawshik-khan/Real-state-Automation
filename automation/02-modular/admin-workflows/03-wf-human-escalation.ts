import { workflow, trigger, node, ifElse, merge, expr, newCredential, placeholder } from '@n8n/workflow-sdk';

// ── Trigger: Webhook ──
const webhookTrigger = trigger('n8n-nodes-base.webhook', 2.1, {
  name: 'Escalation Webhook',
  parameters: {
    httpMethod: 'POST',
    path: placeholder('human-escalation'),
    responseMode: 'lastNode',
    responseData: 'firstEntryJson',
  },
  output: [
    {
      body: {
        conversationId: 'conv_001',
        userId: 'user_123',
        message: 'I want to speak to a human agent',
        channel: 'whatsapp',
        aiResponse: 'I can help you with that...',
        action: 'escalate',
        confidence: 0.45,
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
        { id: 'ni-conv', name: 'conversationId', value: expr('{{ $json.body?.conversationId ?? $json.conversationId ?? "" }}'), type: 'string' },
        { id: 'ni-user', name: 'userId', value: expr('{{ $json.body?.userId ?? $json.userId ?? "" }}'), type: 'string' },
        { id: 'ni-msg', name: 'message', value: expr('{{ $json.body?.message ?? $json.message ?? "" }}'), type: 'string' },
        { id: 'ni-channel', name: 'channel', value: expr('{{ $json.body?.channel ?? $json.channel ?? "" }}'), type: 'string' },
        { id: 'ni-ai', name: 'aiResponse', value: expr('{{ $json.body?.aiResponse ?? $json.aiResponse ?? "" }}'), type: 'string' },
        { id: 'ni-action', name: 'action', value: expr('{{ $json.body?.action ?? $json.action ?? "escalate" }}'), type: 'string' },
        { id: 'ni-confidence', name: 'confidence', value: expr('{{ $json.body?.confidence ?? $json.confidence ?? 0 }}'), type: 'number' },
      ],
    },
  },
  output: [
    {
      conversationId: 'conv_001',
      userId: 'user_123',
      message: 'I want to speak to a human agent',
      channel: 'whatsapp',
      aiResponse: 'I can help you with that...',
      action: 'escalate',
      confidence: 0.45,
    },
  ],
});

// ── Check Escalation Condition ──
const shouldEscalate = ifElse({
  version: 2.3,
  config: {
    name: 'Should Escalate?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
        conditions: [
          {
            id: 'escalate-action',
            leftValue: expr('{{ $json.action }}'),
            operator: { type: 'string', operation: 'equals' },
            rightValue: 'escalate',
          },
          {
            id: 'low-confidence',
            leftValue: expr('{{ $json.confidence }}'),
            operator: { type: 'number', operation: 'smaller' },
            rightValue: 0.75,
          },
        ],
        combinator: 'or',
      },
    },
  },
});

// ── Slack Notification ──
const notifySlack = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Notify Slack',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/slack'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { channel: "#support-escalations", text: "🚨 Escalation Needed\\nUser: " + $json.userId + "\\nMessage: " + $json.message + "\\nChannel: " + $json.channel + "\\nConfidence: " + $json.confidence + "\\nConversation: " + $json.conversationId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ ok: true, ts: 'slack_ts_001' }],
});

// ── Telegram Notification ──
const notifyTelegram = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Notify Telegram',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/telegram'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { chatId: "@support-team", text: "🚨 Escalation: " + $json.userId + " needs human support on " + $json.channel } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ ok: true, messageId: 12345 }],
});

// ── Email Notification ──
const notifyEmail = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Notify via Email',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/email'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { to: "support@glgassets.com", subject: "Human Escalation Required - " + $json.conversationId, body: "A user requires human intervention.\\n\\nUser ID: " + $json.userId + "\\nChannel: " + $json.channel + "\\nMessage: " + $json.message + "\\nAI Response: " + $json.aiResponse + "\\nConfidence: " + $json.confidence + "\\nConversation: " + $json.conversationId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ messageId: 'email_001', accepted: true }],
});

// ── Merge Results ──
const mergeNotifications = merge({
  version: 2.4,
  config: {
    name: 'Merge Notifications',
    parameters: {
      mode: 'combine',
      combinationMode: 'mergeByPosition',
      options: {},
    },
  },
});

// ── Log Escalation ──
const logEscalation = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Log Escalation',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/escalations'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { conversationId: $json.conversationId, userId: $json.userId, channel: $json.channel, escalated: true, timestamp: new Date().toISOString() } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ id: 'esc_001', status: 'logged' }],
});

// ── No Escalation Needed (terminal node) ──
const noEscalation = node('n8n-nodes-base.set', 3.4, {
  name: 'No Escalation Needed',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'ne-escalated', name: 'escalated', value: false, type: 'boolean' },
      ],
    },
  },
  output: [{ escalated: false, message: 'AI handled successfully' }],
});

// ── Build and Export ──
export default workflow('wf-human-escalation', 'Human Escalation Handler')
  .description(
    'Listens for escalation webhooks. If action equals "escalate" or AI confidence is below 0.75, ' +
    'sends parallel notifications via Slack, Telegram, and email. Merges the results and logs the escalation. ' +
    'If no escalation is needed, simply returns escalated=false.'
  )
  .onError('stopWorkflow')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(
    shouldEscalate
      .onTrue(
        notifySlack.to(mergeNotifications),
        notifyTelegram.to(mergeNotifications),
        notifyEmail.to(mergeNotifications)
      )
      .chainMerge(mergeNotifications)
      .to(logEscalation)
      .onFalse(noEscalation)
  );
