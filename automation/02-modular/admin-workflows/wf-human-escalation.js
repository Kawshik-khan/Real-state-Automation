import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: { name: 'Escalation Webhook', path: placeholder('human-escalation'), options: {} },
  output: [{ body: { conversationId: 'conv_001', userId: 'user_123', message: 'I want to speak to a human', channel: 'whatsapp', aiResponse: 'I understand you need help', action: 'escalate', confidence: 0.65 } }]
});

const normalizeInput = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Input',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'ni-conv', name: 'conversationId', value: expr('{{ $json.body?.conversationId ?? $json.conversationId ?? "" }}'), type: 'string' },
          { id: 'ni-user', name: 'userId', value: expr('{{ $json.body?.userId ?? $json.userId ?? "" }}'), type: 'string' },
          { id: 'ni-msg', name: 'message', value: expr('{{ $json.body?.message ?? $json.message ?? "" }}'), type: 'string' },
          { id: 'ni-ch', name: 'channel', value: expr('{{ $json.body?.channel ?? $json.channel ?? "" }}'), type: 'string' },
          { id: 'ni-ai', name: 'aiResponse', value: expr('{{ $json.body?.aiResponse ?? $json.aiResponse ?? "" }}'), type: 'string' },
          { id: 'ni-action', name: 'action', value: expr('{{ $json.body?.action ?? $json.action ?? "" }}'), type: 'string' },
          { id: 'ni-conf', name: 'confidence', value: expr('{{ $json.body?.confidence ?? $json.confidence ?? 1 }}'), type: 'number' }
        ]
      }
    }
  },
  output: [{ conversationId: 'conv_001', userId: 'user_123', message: 'I want to speak to a human', channel: 'whatsapp', aiResponse: 'I understand', action: 'escalate', confidence: 0.65 }]
});

const checkEscalation = ifElse({
  version: 2.3,
  config: {
    name: 'Check Escalation',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.action }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'escalate' },
          { leftValue: expr('{{ $json.confidence }}'), operator: { type: 'number', operation: 'smaller' }, rightValue: 0.75 }
        ],
        combinator: 'or'
      }
    }
  }
});

const notifySlack = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Slack',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/slack'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'channel', value: '#support-escalations' },
          { name: 'text', value: expr('Escalation needed for conversation {{ $json.conversationId }} from user {{ $json.userId }} on {{ $json.channel }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, slackTs: '1234567890.123456' }]
});

const notifyTelegram = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Telegram',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/telegram'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'chatId', value: expr('{{ $env.TELEGRAM_SUPPORT_CHAT_ID }}') },
          { name: 'text', value: expr('Escalation: {{ $json.conversationId }} - {{ $json.userId }} said: {{ $json.message }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, messageId: 'tg_123' }]
});

const notifyEmail = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Email',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/email'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'to', value: expr('{{ $env.SUPPORT_EMAIL }}') },
          { name: 'subject', value: expr('Support Escalation: {{ $json.conversationId }}') },
          { name: 'body', value: expr('User {{ $json.userId }} requested escalation on {{ $json.channel }}.\\nMessage: {{ $json.message }}\\nAI Response: {{ $json.aiResponse }}\\nConfidence: {{ $json.confidence }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, emailId: 'email_123' }]
});

const logEscalation = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Log Escalation',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'workflow', value: 'wf-human-escalation' },
          { name: 'type', value: 'escalation' },
          { name: 'conversationId', value: expr('{{ $json.conversationId }}') },
          { name: 'userId', value: expr('{{ $json.userId }}') },
          { name: 'channel', value: expr('{{ $json.channel }}') },
          { name: 'status', value: 'escalated' }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ logged: true }]
});

const notifyNoEscalation = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'No Escalation Needed',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'ne-status', name: 'status', value: 'no_escalation_needed', type: 'string' }
        ]
      }
    }
  },
  output: [{ status: 'no_escalation_needed' }]
});

export default workflow('wf-human-escalation', 'Human Escalation')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(checkEscalation
    .onTrue(
      notifySlack
        .to(notifyTelegram)
        .to(notifyEmail)
        .to(logEscalation)
    )
    .onFalse(notifyNoEscalation)
  );
