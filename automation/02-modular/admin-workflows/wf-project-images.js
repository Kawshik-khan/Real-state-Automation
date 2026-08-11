import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: { name: 'Project Images Webhook', path: placeholder('project-images'), options: {} },
  output: [{ body: { projectId: 'proj_456', channel: 'facebook', recipientId: 'user_123' } }]
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
          { id: 'ni-proj', name: 'projectId', value: expr('{{ $json.body?.projectId ?? $json.projectId ?? "" }}'), type: 'string' },
          { id: 'ni-channel', name: 'channel', value: expr('{{ $json.body?.channel ?? $json.channel ?? "" }}'), type: 'string' },
          { id: 'ni-recip', name: 'recipientId', value: expr('{{ $json.body?.recipientId ?? $json.recipientId ?? "" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ projectId: 'proj_456', channel: 'facebook', recipientId: 'user_123' }]
});

const fetchImages = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Fetch Project Images',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/image'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'projectId', value: expr('{{ $json.projectId }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    images: [
      { url: 'https://cdn.example.com/img1.jpg', caption: 'Living Room', order: 1 },
      { url: 'https://cdn.example.com/img2.jpg', caption: 'Kitchen', order: 2 },
      { url: 'https://cdn.example.com/img3.jpg', caption: 'Bedroom', order: 3 }
    ],
    projectName: 'Luxury Villa'
  }]
});

const buildCarousel = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Build Media Carousel',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `const images = $json.images || [];
const carousel = {
  type: "carousel",
  cards: images.map((img, idx) => ({
    title: img.caption || \`Image \${idx + 1}\`,
    imageUrl: img.url,
    subtitle: \`Project: \${$json.projectName || ""}\`
  }))
};

return [{
  ...$json,
  carousel,
  imageUrls: images.map(i => i.url),
  captions: images.map(i => i.caption)
}];`
    }
  },
  output: [{
    projectId: 'proj_456',
    channel: 'facebook',
    recipientId: 'user_123',
    imageUrls: ['https://cdn.example.com/img1.jpg'],
    captions: ['Living Room'],
    carousel: { type: 'carousel', cards: [{ title: 'Living Room', imageUrl: 'https://cdn.example.com/img1.jpg', subtitle: 'Project: Luxury Villa' }] }
  }]
});

const routeByPlatform = switchCase({
  version: 3.4,
  config: {
    name: 'Route by Platform',
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

const sendWhatsAppMedia = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send WhatsApp Media',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/whatsapp/template'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'recipientId', value: expr('{{ $json.recipientId }}') },
          { name: 'template', value: 'project_images' },
          { name: 'imageUrls', value: expr('{{ $json.imageUrls }}') },
          { name: 'captions', value: expr('{{ $json.captions }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, messageId: 'wa_media_001' }]
});

const sendFacebookCarousel = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Facebook Carousel',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/facebook/carousel'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'recipientId', value: expr('{{ $json.recipientId }}') },
          { name: 'carousel', value: expr('{{ $json.carousel }}') },
          { name: 'imageUrls', value: expr('{{ $json.imageUrls }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, postId: 'fb_carousel_001' }]
});

const sendInstagramAlbum = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Instagram Album',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/instagram/album'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'recipientId', value: expr('{{ $json.recipientId }}') },
          { name: 'mediaUrls', value: expr('{{ $json.imageUrls }}') },
          { name: 'captions', value: expr('{{ $json.captions }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, mediaId: 'ig_album_001' }]
});

const logCompletion = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Log Completion',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'workflow', value: 'wf-project-images' },
          { name: 'status', value: 'sent' },
          { name: 'projectId', value: expr('{{ $json.projectId }}') },
          { name: 'channel', value: expr('{{ $json.channel }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ logged: true }]
});

export default workflow('wf-project-images', 'Project Images')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(fetchImages)
  .to(buildCarousel)
  .to(routeByPlatform
    .onCase(0, sendWhatsAppMedia.to(logCompletion))
    .onCase(1, sendFacebookCarousel.to(logCompletion))
    .onCase(2, sendInstagramAlbum.to(logCompletion))
  );
