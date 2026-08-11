import { workflow, node, trigger, newCredential, expr } from '@n8n/workflow-sdk';

// --- Trigger: Webhook ---
const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Live Chat Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'website/livechat',
      responseMode: 'responseNode',
      options: {}
    }
  },
  output: [{
    headers: { 'content-type': 'application/json' },
    params: {},
    query: {},
    body: {
      sessionId: 'sess_abc_123',
      userId: 'user_456',
      name: 'Jane Doe',
      email: 'jane@example.com',
      message: 'I am looking for a 3-bedroom apartment',
      pageUrl: 'https://glgassets.com/properties',
      timestamp: 1743033600
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
          { id: 'channel', name: 'channel', value: 'website_live_chat', type: 'string' },
          { id: 'sessionId', name: 'sessionId', value: expr('{{ $json.body?.sessionId ?? $json.sessionId ?? "" }}'), type: 'string' },
          { id: 'sender', name: 'sender', value: expr('{{ $json.body?.userId ?? $json.userId ?? $json.sender ?? "" }}'), type: 'string' },
          { id: 'senderName', name: 'senderName', value: expr('{{ $json.body?.name ?? $json.name ?? $json.senderName ?? "" }}'), type: 'string' },
          { id: 'senderEmail', name: 'senderEmail', value: expr('{{ $json.body?.email ?? $json.email ?? "" }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr('{{ $json.body?.message ?? $json.body ?? $json.message ?? "" }}'), type: 'string' },
          { id: 'pageUrl', name: 'pageUrl', value: expr('{{ $json.body?.pageUrl ?? $json.pageUrl ?? "" }}'), type: 'string' },
          { id: 'timestamp', name: 'timestamp', value: expr('{{ $json.body?.timestamp ?? $json.timestamp ?? $now.toISO() }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{
    channel: 'website_live_chat',
    sessionId: 'sess_abc_123',
    sender: 'user_456',
    senderName: 'Jane Doe',
    senderEmail: 'jane@example.com',
    body: 'I am looking for a 3-bedroom apartment',
    pageUrl: 'https://glgassets.com/properties',
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
    confidence: 0.94,
    reply: 'I can help with that! We have several 3-bedroom apartments available. Would you like to filter by budget or location?',
    intent: 'property_search',
    escalated: false
  }]
});

// --- HTTP Request to Push AI Reply to Website ---
const respondToClient = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Respond to Client',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/chat/respond'),
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
      jsonBody: expr('={{"sessionId":$json.sessionId,"userId":$json.sender,"message":$json.reply,"channel":"website_live_chat"}}'),
      options: { timeout: 10000 }
    },
    credentials: {
      httpHeaderAuth: newCredential('Backend API Key')
    },
    onError: 'continueRegularOutput'
  },
  output: [{
    success: true,
    delivered: true,
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
export default workflow('wf-website-live-chat', 'WF-Website-Live-Chat')
  .add(webhookTrigger)
  .to(normalizePayload)
  .to(callAIAPI)
  .to(respondToClient)
  .to(logConversation);
