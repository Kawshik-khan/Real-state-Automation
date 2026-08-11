import { workflow, node, trigger, expr } from '@n8n/workflow-sdk';

const executeTrigger = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.2,
  config: {
    name: 'Execute Workflow Trigger',
    parameters: {
      inputSource: 'workflowInputs',
      workflowInputs: {
        values: [
          { name: 'channels', type: 'object' },
          { name: 'type', type: 'string' },
          { name: 'title', type: 'string' },
          { name: 'message', type: 'string' },
          { name: 'recipient', type: 'string' }
        ]
      }
    }
  },
  output: [{ channels: ['slack', 'telegram', 'email'], type: 'new_inquiry', title: 'New Property Inquiry', message: 'A client has inquired about property XYZ', recipient: 'agent@glgassets.com' }]
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
          { id: 'notif-channels', name: 'channels', value: expr('{{ $json.channels }}'), type: 'object' },
          { id: 'notif-type', name: 'type', value: expr('{{ $json.type }}'), type: 'string' },
          { id: 'notif-title', name: 'title', value: expr('{{ $json.title }}'), type: 'string' },
          { id: 'notif-message', name: 'message', value: expr('{{ $json.message }}'), type: 'string' },
          { id: 'notif-recipient', name: 'recipient', value: expr('{{ $json.recipient }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ channels: ['slack', 'telegram', 'email'], type: 'new_inquiry', title: 'New Property Inquiry', message: 'A client has inquired about property XYZ', recipient: 'agent@glgassets.com' }]
});

const sendSlack = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Slack Notification',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.SLACK_WEBHOOK_URL }}'),
      authentication: 'none',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: {
        text: expr('{{ "[" + $json.type + "] " + $json.title }}'),
        attachments: [
          {
            color: 'good',
            fields: [
              { title: 'Message', value: expr('{{ $json.message }}'), short: false },
              { title: 'Type', value: expr('{{ $json.type }}'), short: true }
            ]
          }
        ]
      },
      options: { timeout: 10000 }
    }
  },
  output: [{ ok: true }]
});

const sendTelegram = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Telegram Notification',
    parameters: {
      method: 'POST',
      url: expr('{{ "https://api.telegram.org/bot" + $env.TELEGRAM_BOT_TOKEN + "/sendMessage" }}'),
      authentication: 'none',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: {
        chat_id: expr('{{ $json.recipient }}'),
        text: expr('{{ "*" + $json.title + "*\\n\\n" + $json.message + "\\n\\nType: " + $json.type }}'),
        parse_mode: 'Markdown'
      },
      options: { timeout: 10000 }
    }
  },
  output: [{ ok: true, result: { message_id: 123 } }]
});

const sendEmail = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Email Notification',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.EMAIL_API_URL || "https://api.sendgrid.com/v3/mail/send" }}'),
      authentication: 'none',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: {
        personalizations: [
          {
            to: [{ email: expr('{{ $json.recipient }}') }],
            subject: expr('{{ "[" + $json.type + "] " + $json.title }}')
          }
        ],
        from: { email: expr('{{ $env.FROM_EMAIL || "noreply@glgassets.com" }}') },
        content: [
          {
            type: 'text/plain',
            value: expr('{{ $json.message }}')
          }
        ]
      },
      sendHeaders: true,
      headerParameters: {
        parameters: [
          { name: 'Authorization', value: expr('{{ "Bearer " + $env.EMAIL_API_KEY }}') }
        ]
      },
      options: { timeout: 15000 }
    }
  },
  output: [{ status: '202 Accepted' }]
});

const prepareResponse = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Prepare Response',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'notif-success', name: 'success', value: true, type: 'boolean' },
          { id: 'notif-sent', name: 'sentChannels', value: expr('{{ $json.channels }}'), type: 'object' }
        ]
      }
    }
  },
  output: [{ success: true, sentChannels: ['slack', 'telegram', 'email'] }]
});

export default workflow('swf-notification', 'SWF-Notification')
  .add(executeTrigger)
  .to(normalizePayload)
  .to(sendSlack)
  .to(sendTelegram)
  .to(sendEmail)
  .to(prepareResponse);
