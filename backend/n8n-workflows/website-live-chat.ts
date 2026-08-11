"""Workflow for Website Live Chat with n8n MCP Integration"""
import { workflow, node, trigger, expr, newCredential } from '@n8n/workflow-sdk';

const websiteChatTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Website Live Chat Webhook',
    parameters: {
      path: 'website-chat',
      method: 'POST',
      responseMode: 'responseNode'
    },
    position: [240, 300]
  },
  output: [{}]
});

const chatApiNode = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Chat API with Structured Format',
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
      jsonBody: expr('{{ {"message": $("Webhook Message").item.json.message, "conversation_id": $("Webhook Message").item.json.conversation_id, "channel": "website", "language": "en"} }}'),
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
    position: [540, 300]
  },
  output: [{ id: 1, title: 'Chat Response' }]
});

const parseResponseNode = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Parse Structured Response',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'clean-reply', name: 'cleanReply', value: expr('{{ $("Chat API").item.json.reply }}'), type: 'string' },
          { id: 'extract-actions', name: 'actions', value: expr('{{ $("Chat API").item.json.actions ?? [] }}'), type: 'string[]' }
        ]
      }
    },
    position: [840, 300]
  },
  output: [{ id: 1, title: 'Parsed Response' }]
});

const successResponseNode = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Send Success Response',
    parameters: {
      method: 'POST',
      url: 'https://api.example.com/webhook/success',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'Content-Type', value: 'application/json' }
        ]
      },
      sendBody: true,
      specifyBody: 'json',
      jsonBody: expr('{{ {"status": "success", "conversation_id": $("Chat API").item.json.conversation_id, "message": $("Parse Structured Response").item.json.cleanReply} }}')
    },
    position: [1140, 300]
  },
  output: [{ id: 1, title: 'Success Confirmation' }]
});

const errorHandlerNode = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Error Handler',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'error-message', name: 'errorMessage', value: expr('{{ "Chat API Error: " + $(\"Chat API\").item.json.status }}'), type: 'string' }
        ]
      }
    },
    position: [840, 500]
  },
  output: [{ id: 1, title: 'Error Response' }]
});

export default workflow('website-live-chat', 'Website Live Chat')
  .add(websiteChatTrigger)
  .to(parseResponseNode)
  .to(chatApiNode)
  .to(
    chatApiNode.output(0).to(successResponseNode)
  );
  
export default workflow('website-live-chat-with-error', 'Website Live Chat with Error')
  .add(websiteChatTrigger)
  .to(parseResponseNode)
  .to(chatApiNode)
  .to(
    chatApiNode.output(0).to(successResponseNode)
  )
  .add(errorHandlerNode)
  .to(
    chatApiNode.output(1).to(errorHandlerNode)
  );