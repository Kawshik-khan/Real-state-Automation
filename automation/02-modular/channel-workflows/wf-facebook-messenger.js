import { workflow, node, trigger, newCredential, ifElse, expr } from '@n8n/workflow-sdk';

// --- Trigger ---
const facebookTrigger = trigger({
  type: 'n8n-nodes-base.facebookTrigger',
  version: 1,
  config: {
    name: 'Facebook Messenger Trigger',
    parameters: {
      authType: 'accessToken',
      appId: expr('{{ $env.FACEBOOK_APP_ID }}'),
      object: 'page',
      fields: ['messages'],
      options: { includeValues: true }
    },
    credentials: {
      facebookGraphAppApi: newCredential('Facebook App API')
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
          { id: 'channel', name: 'channel', value: 'facebook', type: 'string' },
          { id: 'sender', name: 'sender', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.sender?.id ?? $json.sender?.id ?? $json.from ?? "" }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.message?.text ?? $json.body ?? $json.text ?? "" }}'), type: 'string' },
          { id: 'messageId', name: 'messageId', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.message?.mid ?? $json.messageId ?? "" }}'), type: 'string' },
          { id: 'timestamp', name: 'timestamp', value: expr('{{ $json.body?.entry?.[0]?.messaging?.[0]?.timestamp ?? $json.timestamp ?? $now.toISO() }}'), type: 'string' },
          { id: 'pageId', name: 'pageId', value: expr('{{ $json.body?.entry?.[0]?.id ?? $json.pageId ?? "" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{
    channel: 'facebook',
    sender: '123456789',
    body: 'Hello, I am interested in this property',
    messageId: 'mid.ABC123',
    timestamp: '1743033600',
    pageId: '987654321'
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
    confidence: 0.88,
    reply: 'Thank you for your interest! Let me help you find the perfect property.',
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

// --- Facebook Graph API to Send Reply ---
const sendFacebookReply = node({
  type: 'n8n-nodes-base.facebookGraphApi',
  version: 1,
  config: {
    name: 'Send Facebook Reply',
    parameters: {
      authType: 'accessToken',
      hostUrl: 'graph.facebook.com',
      httpRequestMethod: 'POST',
      graphApiVersion: 'v18.0',
      node: expr('{{ $json.pageId }}'),
      edge: 'messages',
      options: {
        queryParameters: {
          parameter: [
            { name: 'recipient', value: expr('{\"id\":\"{{ $json.sender }}\"}') },
            { name: 'message', value: expr('{\"text\":\"{{ $json.reply }}\"}') },
            { name: 'messaging_type', value: 'RESPONSE' }
          ]
        }
      }
    },
    credentials: {
      facebookGraphApi: newCredential('Facebook Graph API')
    }
  },
  output: [{
    recipient_id: '123456789',
    message_id: 'mid.SENT987'
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
export default workflow('wf-facebook-messenger', 'WF-Facebook-Messenger')
  .add(facebookTrigger)
  .to(normalizePayload)
  .to(callAIAPI)
  .to(checkConfidence
    .onTrue(sendFacebookReply.to(logConversation))
    .onFalse(escalateToHuman.to(logConversation))
  );
