import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: { name: 'Moderation Webhook', path: placeholder('moderation'), options: {} },
  output: [{ body: { text: 'Check out this amazing property!', source: 'facebook_comment', authorId: 'user_123' } }]
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
          { id: 'ni-text', name: 'text', value: expr('{{ $json.body?.text ?? $json.text ?? "" }}'), type: 'string' },
          { id: 'ni-source', name: 'source', value: expr('{{ $json.body?.source ?? $json.source ?? "" }}'), type: 'string' },
          { id: 'ni-author', name: 'authorId', value: expr('{{ $json.body?.authorId ?? $json.authorId ?? "" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ text: 'Check out this amazing property!', source: 'facebook_comment', authorId: 'user_123' }]
});

const callModerationApi = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Call Moderation API',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/moderation/spam'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'text', value: expr('{{ $json.text }}') },
          { name: 'source', value: expr('{{ $json.source }}') },
          { name: 'authorId', value: expr('{{ $json.authorId }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    isToxic: false,
    isSpam: false,
    confidence: 0.98,
    categories: [],
    verdict: 'clean'
  }]
});

const checkVerdict = ifElse({
  version: 2.3,
  config: {
    name: 'Check Verdict',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.isToxic }}'), operator: { type: 'boolean', operation: 'equals' }, rightValue: true },
          { leftValue: expr('{{ $json.isSpam }}'), operator: { type: 'boolean', operation: 'equals' }, rightValue: true },
          { leftValue: expr('{{ $json.verdict }}'), operator: { type: 'string', operation: 'notEqual' }, rightValue: 'clean' }
        ],
        combinator: 'or'
      }
    }
  }
});

const hideComment = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Hide Comment',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/{{ $json.source }}/hide'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'authorId', value: expr('{{ $json.authorId }}') },
          { name: 'text', value: expr('{{ $json.text }}') },
          { name: 'action', value: 'hide' }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, hidden: true }]
});

const flagForReview = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Flag for Review',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/moderation/flag'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'text', value: expr('{{ $json.text }}') },
          { name: 'source', value: expr('{{ $json.source }}') },
          { name: 'authorId', value: expr('{{ $json.authorId }}') },
          { name: 'isToxic', value: expr('{{ $json.isToxic }}') },
          { name: 'isSpam', value: expr('{{ $json.isSpam }}') },
          { name: 'categories', value: expr('{{ $json.categories }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, flagId: 'flag_001' }]
});

const notifyAdmin = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Admin',
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
          { name: 'subject', value: expr('Moderation Alert: Content Flagged from {{ $json.source }}') },
          { name: 'body', value: expr('Flagged content from {{ $json.authorId }} on {{ $json.source }}.\\nText: {{ $json.text }}\\nToxic: {{ $json.isToxic }}\\nSpam: {{ $json.isSpam }}\\nCategories: {{ $json.categories }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, emailId: 'mod_alert_001' }]
});

const allowContent = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Allow Content',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'ac-allow', name: 'allow', value: true, type: 'boolean' },
          { id: 'ac-verdict', name: 'verdict', value: 'clean', type: 'string' }
        ]
      }
    }
  },
  output: [{ allow: true, verdict: 'clean' }]
});

const logAction = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Log Moderation Action',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'workflow', value: 'wf-moderation' },
          { name: 'action', value: expr('{{ $json.isToxic || $json.isSpam ? "blocked" : "allowed" }}') },
          { name: 'text', value: expr('{{ $json.text }}') },
          { name: 'source', value: expr('{{ $json.source }}') },
          { name: 'authorId', value: expr('{{ $json.authorId }}') },
          { name: 'verdict', value: expr('{{ $json.verdict }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ logged: true }]
});

export default workflow('wf-moderation', 'Content Moderation')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(callModerationApi)
  .to(checkVerdict
    .onTrue(
      hideComment
        .to(flagForReview)
        .to(notifyAdmin)
        .to(logAction)
    )
    .onFalse(
      allowContent
        .to(logAction)
    )
  );
