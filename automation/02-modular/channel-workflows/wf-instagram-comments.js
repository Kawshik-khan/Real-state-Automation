import { workflow, node, trigger, newCredential, expr } from '@n8n/workflow-sdk';

// --- Trigger: Webhook ---
const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Instagram Comments Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'instagram/comments',
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
        changes: [{
          value: {
            id: 'comment_123',
            from: { id: 'ig_user_456', username: 'john_doe' },
            text: 'Love this property!',
            media: { id: 'media_789' },
            created_at: 1743033600
          }
        }],
        id: 'ig_user_012'
      }],
      object: 'instagram'
    }
  }]
});

// --- Normalize Comment Data ---
const normalizePayload = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Comment Data',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'channel', name: 'channel', value: 'instagram_comment', type: 'string' },
          { id: 'sender', name: 'sender', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.from?.id ?? $json.sender?.id ?? $json.from ?? "" }}'), type: 'string' },
          { id: 'senderUsername', name: 'senderUsername', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.from?.username ?? $json.senderUsername ?? "" }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.text ?? $json.body ?? $json.text ?? "" }}'), type: 'string' },
          { id: 'commentId', name: 'commentId', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.id ?? $json.commentId ?? "" }}'), type: 'string' },
          { id: 'mediaId', name: 'mediaId', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.media?.id ?? $json.mediaId ?? "" }}'), type: 'string' },
          { id: 'igUserId', name: 'igUserId', value: expr('{{ $json.body?.entry?.[0]?.id ?? $json.igUserId ?? "" }}'), type: 'string' },
          { id: 'timestamp', name: 'timestamp', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.created_at ?? $json.timestamp ?? $now.toISO() }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{
    channel: 'instagram_comment',
    sender: 'ig_user_456',
    senderUsername: 'john_doe',
    body: 'Love this property!',
    commentId: 'comment_123',
    mediaId: 'media_789',
    igUserId: 'ig_user_012',
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
    confidence: 0.93,
    reply: 'Thank you! Would you like to see more photos or schedule a tour?',
    intent: 'positive_feedback',
    escalated: false
  }]
});

// --- HTTP Request to Instagram Graph API to Reply ---
const postCommentReply = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Post Instagram Comment Reply',
    parameters: {
      method: 'POST',
      url: expr('https://graph.facebook.com/v18.0/{{ $json.igUserId }}/comments'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBearerAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('={{"message":$json.reply,"media_id":$json.mediaId}}'),
      options: { timeout: 15000 }
    },
    credentials: {
      httpBearerAuth: newCredential('Instagram Graph API Token')
    },
    onError: 'continueRegularOutput'
  },
  output: [{
    id: 'comment_reply_987'
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
export default workflow('wf-instagram-comments', 'WF-Instagram-Comments')
  .add(webhookTrigger)
  .to(normalizePayload)
  .to(callAIAPI)
  .to(postCommentReply)
  .to(logConversation);
