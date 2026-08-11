import { workflow, trigger, node, switchCase, expr, newCredential, placeholder } from '@n8n/workflow-sdk';

// ── Trigger: Webhook ──
const webhookTrigger = trigger('n8n-nodes-base.webhook', 2.1, {
  name: 'Project Images Webhook',
  parameters: {
    httpMethod: 'POST',
    path: placeholder('project-images'),
    responseMode: 'lastNode',
    responseData: 'firstEntryJson',
  },
  output: [
    {
      body: {
        projectId: 'proj_456',
        channel: 'whatsapp',
        recipientId: 'user_123',
      },
    },
  ],
});

// ── Normalize Input ──
const normalizeInput = node('n8n-nodes-base.set', 3.4, {
  name: 'Normalize Input',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'ni-project', name: 'projectId', value: expr('{{ $json.body?.projectId ?? $json.projectId ?? "" }}'), type: 'string' },
        { id: 'ni-channel', name: 'channel', value: expr('{{ $json.body?.channel ?? $json.channel ?? "" }}'), type: 'string' },
        { id: 'ni-recipient', name: 'recipientId', value: expr('{{ $json.body?.recipientId ?? $json.recipientId ?? "" }}'), type: 'string' },
      ],
    },
  },
  output: [{ projectId: 'proj_456', channel: 'whatsapp', recipientId: 'user_123' }],
});

// ── Fetch Image URLs from Backend ──
const fetchImages = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Fetch Image URLs',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/image'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { projectId: $json.projectId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      success: true,
      images: [
        { url: 'https://cdn.example.com/img1.jpg', caption: 'Exterior view' },
        { url: 'https://cdn.example.com/img2.jpg', caption: 'Living room' },
        { url: 'https://cdn.example.com/img3.jpg', caption: 'Kitchen' },
      ],
    },
  ],
});

// ── Assemble Image Data ──
const assembleImages = node('n8n-nodes-base.set', 3.4, {
  name: 'Assemble Image Data',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'ai-images', name: 'images', value: expr('{{ $json.images }}'), type: 'array' },
        { id: 'ai-channel', name: 'channel', value: expr('{{ $json.channel }}'), type: 'string' },
        { id: 'ai-recipient', name: 'recipientId', value: expr('{{ $json.recipientId }}'), type: 'string' },
        { id: 'ai-project', name: 'projectId', value: expr('{{ $json.projectId }}'), type: 'string' },
      ],
    },
  },
  output: [
    {
      images: [{ url: 'https://cdn.example.com/img1.jpg', caption: 'Exterior view' }],
      channel: 'whatsapp',
      recipientId: 'user_123',
      projectId: 'proj_456',
    },
  ],
});

// ── Route by Channel ──
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
              conditions: [
                { leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'whatsapp' },
              ],
              combinator: 'and',
            },
          },
          {
            outputKey: 'facebook',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [
                { leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'facebook' },
              ],
              combinator: 'and',
            },
          },
          {
            outputKey: 'instagram',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [
                { leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'instagram' },
              ],
              combinator: 'and',
            },
          },
        ],
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'Unknown Channel' },
    },
  },
});

// ── Send WhatsApp Media ──
const sendWhatsApp = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Send WhatsApp Media',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/whatsapp/media'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { recipientId: $json.recipientId, type: "template", template: "project_images", components: [{ type: "header", parameters: [{ type: "image", image: $json.images[0].url }] }, { type: "body", parameters: [{ type: "text", text: "Check out these project images" }] }] } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ success: true, messageId: 'wa_media_001' }],
});

// ── Send Facebook Carousel ──
const sendFacebook = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Send Facebook Carousel',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/facebook/carousel'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { recipientId: $json.recipientId, images: $json.images, message: "Project images from GLG Assets" } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ success: true, postId: 'fb_carousel_001' }],
});

// ── Send Instagram Album ──
const sendInstagram = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Send Instagram Album',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/instagram/album'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { recipientId: $json.recipientId, mediaUrls: $json.images.map(i => i.url), caption: "Explore our latest property images" } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ success: true, mediaId: 'ig_album_001' }],
});

// ── Log Action ──
const logAction = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Log to Backend',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { workflow: "wf-project-images", status: "completed", channel: $json.channel, projectId: $json.projectId, recipientId: $json.recipientId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ logged: true }],
});

// ── Build and Export ──
export default workflow('wf-project-images', 'Project Images Sender')
  .description(
    'Receives a webhook with projectId, channel, and recipientId. Fetches image URLs from the AI/image endpoint, ' +
    'assembles a media carousel/album, routes by channel, sends via the appropriate platform API, and logs completion.'
  )
  .onError('stopWorkflow')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(fetchImages)
  .to(assembleImages)
  .to(
    routeByChannel
      .onCase(0, sendWhatsApp.to(logAction))
      .onCase(1, sendFacebook.to(logAction))
      .onCase(2, sendInstagram.to(logAction))
  );
