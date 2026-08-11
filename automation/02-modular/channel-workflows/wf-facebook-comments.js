import { workflow, node, trigger, newCredential, expr } from '@n8n/workflow-sdk';

// --- Trigger: Webhook (for comment webhooks) ---
const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Facebook Comments Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'facebook/comments',
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
            post_id: 'post_123',
            from: { id: 'user_456', name: 'John Doe' },
            message: 'How much is this property?',
            comment_id: 'comment_789',
            created_time: 1743033600
          }
        }],
        id: 'page_012'
      }],
      object: 'page'
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
          { id: 'channel', name: 'channel', value: 'facebook_comment', type: 'string' },
          { id: 'sender', name: 'sender', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.from?.id ?? $json.sender?.id ?? $json.from ?? "" }}'), type: 'string' },
          { id: 'senderName', name: 'senderName', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.from?.name ?? $json.senderName ?? "" }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.message ?? $json.body ?? $json.text ?? "" }}'), type: 'string' },
          { id: 'commentId', name: 'commentId', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.comment_id ?? $json.commentId ?? "" }}'), type: 'string' },
          { id: 'postId', name: 'postId', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.post_id ?? $json.postId ?? "" }}'), type: 'string' },
          { id: 'pageId', name: 'pageId', value: expr('{{ $json.body?.entry?.[0]?.id ?? $json.pageId ?? "" }}'), type: 'string' },
          { id: 'timestamp', name: 'timestamp', value: expr('{{ $json.body?.entry?.[0]?.changes?.[0]?.value?.created_time ?? $json.timestamp ?? $now.toISO() }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{
    channel: 'facebook_comment',
    sender: 'user_456',
    senderName: 'John Doe',
    body: 'How much is this property?',
    commentId: 'comment_789',
    postId: 'post_123',
    pageId: 'page_012',
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
    confidence: 0.95,
    reply: 'This property is priced at $250,000. Would you like to schedule a visit?',
    intent: 'price_inquiry',
    escalated: false
  }]
});

// --- Facebook Graph API to Post Reply as Page ---
const postCommentReply = node({
  type: 'n8n-nodes-base.facebookGraphApi',
  version: 1,
  config: {
    name: 'Post Comment Reply',
    parameters: {
      authType: 'accessToken',
      hostUrl: 'graph.facebook.com',
      httpRequestMethod: 'POST',
      graphApiVersion: 'v18.0',
      node: expr('{{ $json.commentId }}'),
      edge: '',
      options: {
        queryParameters: {
          parameter: [
            { name: 'message', value: expr('{{ $json.reply }}') }
          ]
        }
      }
    },
    credentials: {
      facebookGraphApi: newCredential('Facebook Graph API')
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
export default workflow('wf-facebook-comments', 'WF-Facebook-Comments')
  .add(webhookTrigger)
  .to(normalizePayload)
  .to(callAIAPI)
  .to(postCommentReply)
  .to(logConversation);
