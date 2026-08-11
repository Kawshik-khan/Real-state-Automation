import { workflow, node, trigger, ifElse, expr, newCredential } from '@n8n/workflow-sdk';

const executeTrigger = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.2,
  config: {
    name: 'Execute Workflow Trigger',
    parameters: {
      inputSource: 'workflowInputs',
      workflowInputs: {
        values: [
          { name: 'pageId', type: 'string' },
          { name: 'message', type: 'string' },
          { name: 'recipientId', type: 'string' },
          { name: 'accessToken', type: 'string' }
        ]
      }
    }
  },
  output: [{ pageId: '123456789', message: 'Hello from GLG Assets', recipientId: '987654321', accessToken: 'EAA...' }]
});

const normalizePayload = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Payload',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'fb-pageId', name: 'pageId', value: expr('{{ $json.pageId }}'), type: 'string' },
          { id: 'fb-recipient', name: 'recipientId', value: expr('{{ $json.recipientId }}'), type: 'string' },
          { id: 'fb-message', name: 'message', value: expr('{{ $json.message }}'), type: 'string' },
          { id: 'fb-token', name: 'accessToken', value: expr('{{ $json.accessToken }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ pageId: '123456789', recipientId: '987654321', message: 'Hello from GLG Assets', accessToken: 'EAA...' }]
});

const sendFacebook = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Facebook Message',
    parameters: {
      method: 'POST',
      url: expr('{{ "https://graph.facebook.com/v18.0/" + $json.pageId + "/messages" }}'),
      sendQuery: true,
      queryParameters: {
        parameters: [
          { name: 'access_token', value: expr('{{ $json.accessToken }}') }
        ]
      },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: {
        recipient: { id: expr('{{ $json.recipientId }}') },
        messaging_type: 'RESPONSE',
        message: { text: expr('{{ $json.message }}') }
      },
      options: { timeout: 15000 }
    },
    onError: 'continueErrorOutput'
  },
  output: [{ recipient_id: '987654321', message_id: 'm_abc123' }]
});

const checkSuccess = ifElse({
  version: 2.3,
  config: {
    name: 'Send Successful?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          {
            leftValue: expr('{{ $json.recipient_id }}'),
            operator: { type: 'string', operation: 'isNotEmpty' }
          }
        ],
        combinator: 'and'
      }
    }
  }
});

const prepareSuccess = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Prepare Success Output',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'fb-success', name: 'success', value: true, type: 'boolean' },
          { id: 'fb-messageId', name: 'messageId', value: expr('{{ $json.message_id }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ success: true, messageId: 'm_abc123' }]
});

const handleError = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Handle Error',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'fb-success', name: 'success', value: false, type: 'boolean' },
          { id: 'fb-error', name: 'error', value: expr('{{ $json.error?.message || "Facebook send failed" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ success: false, error: 'Facebook send failed' }]
});

export default workflow('swf-facebook-send', 'SWF-Facebook-Send')
  .add(executeTrigger)
  .to(normalizePayload)
  .to(sendFacebook)
  .to(checkSuccess
    .onTrue(prepareSuccess)
    .onFalse(handleError)
  );
