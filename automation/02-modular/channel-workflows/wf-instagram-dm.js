import { workflow, node, trigger, newCredential, ifElse, expr } from '@n8n/workflow-sdk';

// --- Trigger: Webhook (Meta sends IG events here) ---
const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Instagram DM Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'instagram/dm',
      responseMode: 'responseNode',
      options: {}
    }
  },
  output: [{
    headers: { 'content-type': 'application/json' },
    params: {},
    query: {},
    body: {
      entry: [{
        messaging: [{
          sender: { id: 'ig_sender_123' },
          message: { text: 'Hello, I saw your listing!', mid: 'ig_mid_456' },
          timestamp: 1743033600
        }],
        id: 'ig_page_789'
      }],
      object: 'instagram'
    }
  }]
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
          { id: 'channel', name: 'channel', value: 'instagram_dm', type: 'string' },
          { id: 'sender', name: 'sender', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.sender?.id ?? $json.sender?.id ?? $json.from ?? "" }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.message?.text ?? $json.body ?? $json.text ?? "" }}'), type: 'string' },
          { id: 'messageId', name: 'messageId', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.message?.mid ?? $json.messageId ?? "" }}'), type: 'string' },
          { id: 'timestamp', name: 'timestamp', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.timestamp ?? $json.timestamp ?? $now.toISO() }}'), type: 'string' },
          { id: 'igUserId', name: 'igUserId', value: expr('{{ $json.body?.entry?.[0]?.id ?? $json.igUserId ?? "" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{
    channel: 'instagram_dm',
    sender: 'ig_sender_123',
    body: 'Hello, I saw your listing!',
    messageId: 'ig_mid_456',
    timestamp: '1743033600',
    igUserId: 'ig_page_789'
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
    confidence: 0.91,
    reply: 'Hi there! Would you like to schedule a viewing?',
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

// --- HTTP Request to Instagram Graph API to Reply ---
const sendInstagramReply = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Send Instagram DM Reply',
    parameters: {
      method: 'POST',
      url: expr('https://graph.facebook.com/v18.0/{{ $json.igUserId }}/messages'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBearerAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('={{"recipient":{"id":$json.sender},"message":{"text":$json.reply},"messaging_type":"RESPONSE"}}'),
      options: { timeout: 15000 }
    },
    credentials: {
      httpBearerAuth: newCredential('Instagram Graph API Token')
    },
    onError: 'continueRegularOutput'
  },
  output: [{
    recipient_id: 'ig_sender_123',
    message_id: 'ig_sent_987'
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

// --- Log Conversation ---
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
export default workflow('wf-instagram-dm', 'WF-Instagram-DM')
  .add(webhookTrigger)
  .to(normalizePayload)
  .to(callAIAPI)
  .to(checkConfidence
    .onTrue(sendInstagramReply.to(logConversation))
    .onFalse(escalateToHuman.to(logConversation))
  );
