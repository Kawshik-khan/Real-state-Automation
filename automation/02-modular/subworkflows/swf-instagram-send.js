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
          { name: 'igUserId', type: 'string' },
          { name: 'message', type: 'string' },
          { name: 'recipientId', type: 'string' },
          { name: 'accessToken', type: 'string' }
        ]
      }
    }
  },
  output: [{ igUserId: '178414000000000', message: 'Hello from GLG Assets', recipientId: '999888777', accessToken: 'IGQVJ...' }]
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
          { id: 'ig-userId', name: 'igUserId', value: expr('{{ $json.igUserId }}'), type: 'string' },
          { id: 'ig-recipient', name: 'recipientId', value: expr('{{ $json.recipientId }}'), type: 'string' },
          { id: 'ig-message', name: 'message', value: expr('{{ $json.message }}'), type: 'string' },
          { id: 'ig-token', name: 'accessToken', value: expr('{{ $json.accessToken }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ igUserId: '178414000000000', recipientId: '999888777', message: 'Hello from GLG Assets', accessToken: 'IGQVJ...' }]
});

const sendInstagram = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Instagram Reply',
    parameters: {
      method: 'POST',
      url: expr('{{ "https://graph.facebook.com/v18.0/" + $json.igUserId + "/messages" }}'),
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
        message: { text: expr('{{ $json.message }}') }
      },
      options: { timeout: 15000 }
    },
    onError: 'continueErrorOutput'
  },
  output: [{ recipient_id: '999888777', message_id: 'instagram_m_xyz' }]
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
          { id: 'ig-success', name: 'success', value: true, type: 'boolean' },
          { id: 'ig-messageId', name: 'messageId', value: expr('{{ $json.message_id }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ success: true, messageId: 'instagram_m_xyz' }]
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
          { id: 'ig-success', name: 'success', value: false, type: 'boolean' },
          { id: 'ig-error', name: 'error', value: expr('{{ $json.error?.message || "Instagram send failed" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ success: false, error: 'Instagram send failed' }]
});

export default workflow('swf-instagram-send', 'SWF-Instagram-Send')
  .add(executeTrigger)
  .to(normalizePayload)
  .to(sendInstagram)
  .to(checkSuccess
    .onTrue(prepareSuccess)
    .onFalse(handleError)
  );
