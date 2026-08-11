import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: { name: 'Brochure Webhook', path: placeholder('brochure-sender'), options: {} },
  output: [{ body: { userId: 'user_123', projectId: 'proj_456', channel: 'whatsapp' } }]
});

const normalizeData = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Input',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'norm-user-id', name: 'userId', value: expr('{{ $json.body?.userId ?? $json.userId ?? "" }}'), type: 'string' },
          { id: 'norm-proj-id', name: 'projectId', value: expr('{{ $json.body?.projectId ?? $json.projectId ?? "" }}'), type: 'string' },
          { id: 'norm-channel', name: 'channel', value: expr('{{ $json.body?.channel ?? $json.channel ?? "" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ userId: 'user_123', projectId: 'proj_456', channel: 'whatsapp' }]
});

const fetchBrochureData = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Fetch Brochure Data',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/booking'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'userId', value: expr('{{ $json.userId }}') },
          { name: 'projectId', value: expr('{{ $json.projectId }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    brochure: {
      pdfUrl: 'https://cdn.example.com/brochure.pdf',
      imageUrls: ['https://cdn.example.com/img1.jpg', 'https://cdn.example.com/img2.jpg'],
      videoUrl: 'https://cdn.example.com/video.mp4',
      mapsLink: 'https://maps.google.com/?q=location',
      projectName: 'Luxury Villa',
      description: 'A beautiful 5BR villa in the hills'
    }
  }]
});

const assembleData = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Assemble Brochure Package',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'as-pdf', name: 'pdfUrl', value: expr('{{ $json.brochure.pdfUrl }}'), type: 'string' },
          { id: 'as-images', name: 'imageUrls', value: expr('{{ $json.brochure.imageUrls }}') },
          { id: 'as-video', name: 'videoUrl', value: expr('{{ $json.brochure.videoUrl }}'), type: 'string' },
          { id: 'as-maps', name: 'mapsLink', value: expr('{{ $json.brochure.mapsLink }}'), type: 'string' },
          { id: 'as-project', name: 'projectName', value: expr('{{ $json.brochure.projectName }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{
    pdfUrl: 'https://cdn.example.com/brochure.pdf',
    imageUrls: ['https://cdn.example.com/img1.jpg'],
    videoUrl: 'https://cdn.example.com/video.mp4',
    mapsLink: 'https://maps.google.com/?q=location',
    projectName: 'Luxury Villa',
    channel: 'whatsapp',
    userId: 'user_123'
  }]
});

const routeByChannel = switchCase({
  version: 3.4,
  config: {
    name: 'Route by Channel',
    parameters: {
      mode: 'rules',
      rules: {
        values: [
          {
            outputKey: 'whatsapp',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [{ leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'whatsapp' }],
              combinator: 'and'
            }
          },
          {
            outputKey: 'facebook',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [{ leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'facebook' }],
              combinator: 'and'
            }
          },
          {
            outputKey: 'instagram',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [{ leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'instagram' }],
              combinator: 'and'
            }
          }
        ]
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'Unknown Channel' }
    }
  }
});

const sendWhatsApp = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send WhatsApp Brochure',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/whatsapp/send'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'userId', value: expr('{{ $json.userId }}') },
          { name: 'type', value: 'brochure' },
          { name: 'pdfUrl', value: expr('{{ $json.pdfUrl }}') },
          { name: 'imageUrls', value: expr('{{ $json.imageUrls }}') },
          { name: 'videoUrl', value: expr('{{ $json.videoUrl }}') },
          { name: 'mapsLink', value: expr('{{ $json.mapsLink }}') },
          { name: 'projectName', value: expr('{{ $json.projectName }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, messageId: 'wa_msg_001' }]
});

const sendFacebook = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Facebook Brochure',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/facebook/send'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'recipientId', value: expr('{{ $json.userId }}') },
          { name: 'type', value: 'brochure' },
          { name: 'pdfUrl', value: expr('{{ $json.pdfUrl }}') },
          { name: 'imageUrls', value: expr('{{ $json.imageUrls }}') },
          { name: 'videoUrl', value: expr('{{ $json.videoUrl }}') },
          { name: 'mapsLink', value: expr('{{ $json.mapsLink }}') },
          { name: 'projectName', value: expr('{{ $json.projectName }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, postId: 'fb_post_001' }]
});

const sendInstagram = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Instagram Brochure',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/instagram/send'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'recipientId', value: expr('{{ $json.userId }}') },
          { name: 'type', value: 'brochure' },
          { name: 'imageUrls', value: expr('{{ $json.imageUrls }}') },
          { name: 'videoUrl', value: expr('{{ $json.videoUrl }}') },
          { name: 'projectName', value: expr('{{ $json.projectName }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, mediaId: 'ig_media_001' }]
});

const logToBackend = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Log to Backend',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'workflow', value: 'wf-brochure-sender' },
          { name: 'status', value: 'completed' },
          { name: 'channel', value: expr('{{ $json.channel }}') },
          { name: 'userId', value: expr('{{ $json.userId }}') },
          { name: 'projectId', value: expr('{{ $json.projectId }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ logged: true }]
});

export default workflow('wf-brochure-sender', 'Brochure Sender')
  .add(webhookTrigger)
  .to(normalizeData)
  .to(fetchBrochureData)
  .to(assembleData)
  .to(routeByChannel
    .onCase(0, sendWhatsApp.to(logToBackend))
    .onCase(1, sendFacebook.to(logToBackend))
    .onCase(2, sendInstagram.to(logToBackend))
  );
