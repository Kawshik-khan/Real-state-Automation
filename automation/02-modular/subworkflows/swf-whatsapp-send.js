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
          { name: 'to', type: 'string' },
          { name: 'message', type: 'string' },
          { name: 'mediaUrl', type: 'string' },
          { name: 'mediaType', type: 'string' }
        ]
      }
    }
  },
  output: [{ to: '+1234567890', message: 'Hello from GLG Assets', mediaUrl: '', mediaType: 'text' }]
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
          { id: 'wa-to', name: 'recipientPhone', value: expr('{{ $json.to }}'), type: 'string' },
          { id: 'wa-message', name: 'textBody', value: expr('{{ $json.message }}'), type: 'string' },
          { id: 'wa-mediaUrl', name: 'mediaUrl', value: expr('{{ $json.mediaUrl }}'), type: 'string' },
          { id: 'wa-mediaType', name: 'mediaType', value: expr('{{ $json.mediaType || "text" }}'), type: 'string' },
          { id: 'wa-msgType', name: 'messageType', value: expr('{{ $json.mediaType && $json.mediaUrl ? $json.mediaType : "text" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ recipientPhone: '+1234567890', textBody: 'Hello from GLG Assets', mediaUrl: '', mediaType: 'text', messageType: 'text' }]
});

const sendWhatsApp = node({
  type: 'n8n-nodes-base.whatsApp',
  version: 1.1,
  config: {
    name: 'Send WhatsApp Message',
    parameters: {
      resource: 'message',
      operation: 'send',
      phoneNumberId: expr('{{ $env.WHATSAPP_PHONE_NUMBER_ID }}'),
      recipientPhoneNumber: expr('{{ $json.recipientPhone }}'),
      messageType: expr('{{ $json.messageType }}'),
      textBody: expr('{{ $json.textBody }}'),
      mediaUrl: expr('{{ $json.mediaUrl }}'),
      mediaFilename: ''
    },
    credentials: { whatsAppApi: newCredential('WhatsApp Business') }
  },
  output: [{ contacts: [{ input: '+1234567890', wa_id: '1234567890' }], messages: [{ id: 'wamid.ABC123' }], messaging_product: 'whatsapp' }]
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
            leftValue: expr('{{ $json.messages }}'),
            operator: { type: 'array', operation: 'notEmpty' }
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
          { id: 'wa-success', name: 'success', value: true, type: 'boolean' },
          { id: 'wa-messageId', name: 'messageId', value: expr('{{ $json.messages[0].id }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ success: true, messageId: 'wamid.ABC123' }]
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
          { id: 'wa-success', name: 'success', value: false, type: 'boolean' },
          { id: 'wa-error', name: 'error', value: 'WhatsApp send failed', type: 'string' }
        ]
      }
    }
  },
  output: [{ success: false, error: 'WhatsApp send failed' }]
});

export default workflow('swf-whatsapp-send', 'SWF-WhatsApp-Send')
  .add(executeTrigger)
  .to(normalizePayload)
  .to(sendWhatsApp)
  .to(checkSuccess
    .onTrue(prepareSuccess)
    .onFalse(handleError)
  );
