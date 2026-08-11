"""Workflow for WhatsApp Integration with n8n MCP"""
import { workflow, node, trigger, expr, newCredential } from '@n8n/workflow-sdk';

const whatsappWebhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'WhatsApp Webhook Trigger',
    parameters: {
      path: 'whatsapp-webhook',
      binaryData: true
    },
    position: [240, 300]
  },
  output: [{}]
});

const normalizeWebhookNode = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize WhatsApp Message',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'extract-body', name: 'message', value: expr('{{ (\$json.body ?? \$json.message) }}'), type: 'string' },
          { id: 'extract-user', name: 'userId', value: expr('{{ \$json.from || \$json.user_id }}'), type: 'string' },
          { id: 'extract-conversation', name: 'conversationId', value: expr('{{ \$json.conversation_id || \'whatsapp-convo-\' + (new Date().getTime()) }}'), type: 'string' },
          { id: 'set-channel', name: 'channel', value: expr('whatsapp'), type: 'string' },
          { id: 'set-language', name: 'language', value: expr('{{ \$json.language || \$json.lang || \"en\" }}'), type: 'string' }
        ]
      }
    },
    position: [540, 300]
  },
  output: [{ id: 1, title: 'Normalized Message' }]
});

const chatbotApiNode = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'WhatsApp Chat API with Structured Response',
    parameters: {
      method: 'POST',
      url: 'http://localhost:8000/api/v1/ai/chat',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'X-Format-Version', value: 'structured' },
          { name: 'X-Automation-Secret', value: newCredential('httpHeaderAuth') },
          { name: 'Content-Type', value: 'application/json' }
        ]
      },
      sendBody: true,
      specifyBody: 'json',
      jsonBody: expr('{{ {"message": $("Normalize WhatsApp Message").item.json.message, "conversation_id": $("Normalize WhatsApp Message").item.json.conversationId, "channel": "whatsapp", "language": $("Normalize WhatsApp Message").item.json.language, "user_id": $("Normalize WhatsApp Message").item.json.userId} }}'),
      options: {
        response: {
          response: {
            fullResponse: false,
            responseFormat: 'json'
          }
        }
      }
    },
    credentials: {
      httpHeaderAuth: newCredential('httpHeaderAuth')
    },
    position: [840, 300]
  },
  output: [{ id: 1, title: 'Chat Response' }]
});

const formatForWhatsAppNode = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Format Response for WhatsApp',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'whatsapp-reply', name: 'reply', value: expr('{{ $("Chatbot API").item.json.reply }}'), type: 'string' },
          { id: 'whatsapp-actions', name: 'actions', value: expr('{{ $("Chatbot API").item.json.actions ?? [] }}'), type: 'string[]' },
          { id: 'add-whatsapp-metadata', name: 'metadata', value: expr('{{ {\"channel\": \"whatsapp\", \"timestamp\": \" + new Date().toISOString() + \", \"format\": \"structured\" } }}'), type: 'object' }
        ]
      }
    },
    position: [1140, 300]
  },
  output: [{ id: 1, title: 'WhatsApp Response' }]
});

const sendToWhatsAppNode = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Send Response to WhatsApp',
    parameters: {
      method: 'POST',
      url: 'https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'Authorization', value: 'Bearer YOUR_ACCESS_TOKEN' },
          { name: 'Content-Type', value: 'application/json' }
        ]
      },
      sendBody: true,
      specifyBody: 'json',
      jsonBody: expr('{{ {"messaging_product": \"whatsapp\", "to": $("Normalize WhatsApp Message").item.json.userId, "type": \"template\", "template": {\"name\": \"chat_response\", \"language\": {\"code\": \"en\"}}, \"response\": {\"message\": "${"Chatbot API").item.json.reply", \"actions\": "${"Chatbot API").item.json.actions}} }}'),
      options: {
        response: {
          response: {
            fullResponse: true,
            responseFormat: 'json'
          }
        }
      }
    },
    credentials: {
      httpHeaderAuth: newCredential('httpHeaderAuth')
    },
    position: [1440, 300]
  },
  output: [{ id: 1, title: 'WhatsApp Delivery Confirmation' }]
});

export default workflow('incoming-whatsapp', 'Incoming WhatsApp')
  .add(whatsappWebhookTrigger)
  .to(normalizeWebhookNode)
  .to(chatbotApiNode)
  .to(formatForWhatsAppNode)
  .to(sendToWhatsAppNode);
  
export default workflow('incoming-whatsapp-with-analytics', 'Incoming WhatsApp with Analytics')
  .add(whatsappWebhookTrigger)
  .to(normalizeWebhookNode)
  .to(chatbotApiNode)
  .to(formatForWhatsAppNode)
  .to(sendToWhatsAppNode)
  .add(
    chatbotApiNode.onError(errorHandlerNode)
  );