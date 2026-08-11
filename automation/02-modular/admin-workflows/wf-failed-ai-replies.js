import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Hourly Schedule',
    parameters: {
      rule: {
        interval: [{ field: 'hours', hoursInterval: 1 }]
      }
    }
  },
  output: [{}]
});

const fetchFailedRequests = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Fetch Failed Requests',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/failed?limit=50'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    items: [
      { id: 'fail_001', conversationId: 'conv_001', userId: 'user_123', message: 'Hello', channel: 'whatsapp', error: 'API timeout', retryCount: 0, maxRetries: 3 },
      { id: 'fail_002', conversationId: 'conv_002', userId: 'user_456', message: 'Price?', channel: 'facebook', error: 'Rate limit', retryCount: 1, maxRetries: 3 }
    ]
  }]
});

const checkHasItems = ifElse({
  version: 2.3,
  config: {
    name: 'Has Failed Items?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.items }}'), operator: { type: 'array', operation: 'notEmpty' } }
        ],
        combinator: 'and'
      }
    }
  }
});

const extractItems = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Extract Items Array',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `const items = $json.items || [];
if (items.length === 0) return [];
return items.map(i => ({ json: i }));`
    }
  },
  output: [
    { id: 'fail_001', conversationId: 'conv_001', userId: 'user_123', message: 'Hello', channel: 'whatsapp', error: 'API timeout', retryCount: 0, maxRetries: 3 }
  ]
});

const splitByItem = splitInBatches({
  version: 3,
  config: { name: 'Process Each Failed Item', parameters: { batchSize: 1 } }
});

const retryAiCall = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Retry AI API Call',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/retry'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'failedId', value: expr('{{ $json.id }}') },
          { name: 'conversationId', value: expr('{{ $json.conversationId }}') },
          { name: 'userId', value: expr('{{ $json.userId }}') },
          { name: 'message', value: expr('{{ $json.message }}') },
          { name: 'channel', value: expr('{{ $json.channel }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, retryId: 'retry_001', status: 'completed' }]
});

const checkRetrySuccess = ifElse({
  version: 2.3,
  config: {
    name: 'Retry Successful?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
        conditions: [
          { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'completed' }
        ],
        combinator: 'and'
      }
    }
  }
});

const markAsResolved = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Mark as Resolved',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/failed/resolve'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'failedId', value: expr('{{ $json.id }}') },
          { name: 'status', value: 'resolved' }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, resolved: true }]
});

const notifyAdmin = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Admin of Failure',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/email'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'to', value: expr('{{ $env.ADMIN_EMAIL }}') },
          { name: 'subject', value: expr('AI Reply Failed After Retry: {{ $json.conversationId }}') },
          { name: 'body', value: expr('Failed conversation {{ $json.conversationId }} for user {{ $json.userId }}.\\nError: {{ $json.error }}\\nRetry count: {{ $json.retryCount }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, emailId: 'fail_notify_001' }]
});

const finalizeCheck = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Finalize Check',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'fc-complete', name: 'checkCompleted', value: true, type: 'boolean' }
        ]
      }
    }
  },
  output: [{ checkCompleted: true }]
});

export default workflow('wf-failed-ai-replies', 'Failed AI Replies')
  .add(scheduleTrigger)
  .to(fetchFailedRequests)
  .to(checkHasItems
    .onTrue(
      extractItems
        .to(splitByItem
          .onDone(finalizeCheck)
          .onEachBatch(
            retryAiCall
              .to(checkRetrySuccess
                .onTrue(markAsResolved.to(nextBatch(splitByItem)))
                .onFalse(notifyAdmin.to(nextBatch(splitByItem)))
              )
          )
        )
    )
    .onFalse(finalizeCheck)
  );
