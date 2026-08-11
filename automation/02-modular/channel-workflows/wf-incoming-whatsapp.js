import { workflow, node, trigger, newCredential, ifElse, expr } from '@n8n/workflow-sdk';

// --- Trigger ---
const whatsappTrigger = trigger({
  type: 'n8n-nodes-base.whatsAppTrigger',
  version: 1,
  config: {
    name: 'WhatsApp Trigger',
    parameters: {
      updates: ['messages']
    },
    credentials: {
      whatsAppTriggerApi: newCredential('WhatsApp Trigger API')
    }
  }
});

// --- Normalize Payload ---
const normalizePayload = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Payload',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'channel', name: 'channel', value: 'whatsapp', type: 'string' },
          { id: 'sender', name: 'sender', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.messages?.[0]?.from ?? $json.from ?? "" }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.messages?.[0]?.text?.body ?? $json.body ?? "" }}'), type: 'string' },
          { id: 'messageId', name: 'messageId', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.messages?.[0]?.id ?? $json.messageId ?? "" }}'), type: 'string' },
          { id: 'timestamp', name: 'timestamp', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.messages?.[0]?.timestamp ?? $json.timestamp ?? $now.toISO() }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{
    channel: 'whatsapp',
    sender: '1234567890',
    body: 'Hello, I am interested in this property',
    messageId: 'wamid.ABC123',
    timestamp: '1743033600'
  }]
});

// --- Execute Sub-workflow: AI-API-Caller ---
const callAIAPI = node({
  type: 'n8n-nodes-base.executeWorkflow',
  version: 1.3,
  config: {
    name: 'Call AI API',
    parameters: {
      mode: 'once',
      source: 'database',
      workflowId: { __rl: true, mode: 'id', value: 'swf-ai-api-caller', cachedResultName: 'SWF-AI-API-Caller' },
      options: { waitForSubWorkflow: true }
    }
  },
  output: [{
    confidence: 0.92,
    reply: 'Sure! Let me show you available properties.',
    intent: 'inquiry',
    escalated: false
  }]
});

// --- IF: Check Confidence >= 0.75 ---
const checkConfidence = ifElse({
  version: 2.2,
  config: {
    name: 'Check Confidence',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [{
          leftValue: expr('{{ $json.confidence }}'),
          operator: { type: 'number', operation: 'largerEqual' },
          rightValue: 0.75
        }],
        combinator: 'and'
      }
    }
  }
});

// --- Execute Sub-workflow: WhatsApp-Send (on high confidence) ---
const sendWhatsAppReply = node({
  type: 'n8n-nodes-base.executeWorkflow',
  version: 1.3,
  config: {
    name: 'Send WhatsApp Reply',
    parameters: {
      mode: 'once',
      source: 'database',
      workflowId: { __rl: true, mode: 'id', value: 'swf-whatsapp-send', cachedResultName: 'SWF-WhatsApp-Send' },
      options: { waitForSubWorkflow: true }
    }
  },
  output: [{
    success: true,
    messageId: 'wamid.SENT987'
  }]
});

// --- Execute Sub-workflow: Notification (on low confidence) ---
const escalateToHuman = node({
  type: 'n8n-nodes-base.executeWorkflow',
  version: 1.3,
  config: {
    name: 'Escalate to Human',
    parameters: {
      mode: 'once',
      source: 'database',
      workflowId: { __rl: true, mode: 'id', value: 'swf-notification', cachedResultName: 'SWF-Notification' },
      options: { waitForSubWorkflow: true }
    }
  },
  output: [{
    notified: true,
    channel: 'slack',
    timestamp: '2024-01-01T00:00:00.000Z'
  }]
});

// --- Log Conversation to Backend ---
const logConversation = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Log Conversation',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/logs'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      headerParameters: {
        parameters: [
          { name: 'Content-Type', value: 'application/json' }
        ]
      },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('={{ $json }}'),
      options: { timeout: 5000 }
    },
    credentials: {
      httpHeaderAuth: newCredential('Backend API Key')
    },
    onError: 'continueRegularOutput'
  },
  output: [{ logged: true, timestamp: '2024-01-01T00:00:00.000Z' }]
});

// --- Compose Workflow ---
export default workflow('wf-incoming-whatsapp', 'WF-Incoming-WhatsApp')
  .add(whatsappTrigger)
  .to(normalizePayload)
  .to(callAIAPI)
  .to(checkConfidence
    .onTrue(sendWhatsAppReply.to(logConversation))
    .onFalse(escalateToHuman.to(logConversation))
  );
