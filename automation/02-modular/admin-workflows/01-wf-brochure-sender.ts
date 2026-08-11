import { workflow, trigger, node, switchCase, splitInBatches, nextBatch, expr, newCredential, placeholder } from '@n8n/workflow-sdk';

// ── 1. Webhook Trigger ──
const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Brochure Sender Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'brochure-sender',
      responseMode: 'lastNode',
      responseData: 'firstEntryJson',
    },
  },
});

// ── 2. Normalize Input ──
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
          { id: 'ni-user', name: 'userId', value: expr('{{ $json.body.userId }}'), type: 'string' },
          { id: 'ni-proj', name: 'projectId', value: expr('{{ $json.body.projectId }}'), type: 'string' },
          { id: 'ni-chan', name: 'channel', value: expr('{{ $json.body.channel }}'), type: 'string' },
        ],
      },
    },
  },
});

// ── 3. Fetch Brochure Data ──
const fetchBrochure = node({
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
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ { userId: $json.userId, projectId: $json.projectId } }}'),
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  },
});

// ── 4. Assemble Brochure Package ──
const assemblePackage = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Assemble Brochure',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'as-pdf', name: 'pdfUrl', value: expr('{{ $json.brochure.pdfUrl }}'), type: 'string' },
          { id: 'as-img', name: 'imageUrls', value: expr('{{ $json.brochure.imageUrls }}'), type: 'array' },
          { id: 'as-vid', name: 'videoUrl', value: expr('{{ $json.brochure.videoUrl }}'), type: 'string' },
          { id: 'as-maps', name: 'mapsLink', value: expr('{{ $json.brochure.mapsLink }}'), type: 'string' },
          { id: 'as-name', name: 'projectName', value: expr('{{ $json.brochure.projectName }}'), type: 'string' },
          { id: 'as-chan', name: 'channel', value: expr('{{ $json.channel }}'), type: 'string' },
          { id: 'as-user', name: 'userId', value: expr('{{ $json.userId }}'), type: 'string' },
          { id: 'as-proj', name: 'projectId', value: expr('{{ $json.projectId }}'), type: 'string' },
        ],
      },
    },
  },
});

// ── 5. Route by Channel ──
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
              combinator: 'and',
            },
          },
          {
            outputKey: 'facebook',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [{ leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'facebook' }],
              combinator: 'and',
            },
          },
          {
            outputKey: 'instagram',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [{ leftValue: expr('{{ $json.channel }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'instagram' }],
              combinator: 'and',
            },
          },
        ],
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'Unknown' },
    },
  },
});

// ── 6. Send WhatsApp ──
const sendWhatsApp = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send WhatsApp',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/whatsapp/send'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ { userId: $json.userId, type: "brochure", pdfUrl: $json.pdfUrl, imageUrls: $json.imageUrls, videoUrl: $json.videoUrl, mapsLink: $json.mapsLink, projectName: $json.projectName } }}'),
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  },
});

// ── 7. Send Facebook ──
const sendFacebook = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Facebook',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/facebook/send'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ { recipientId: $json.userId, type: "brochure", pdfUrl: $json.pdfUrl, imageUrls: $json.imageUrls, videoUrl: $json.videoUrl, mapsLink: $json.mapsLink, projectName: $json.projectName } }}'),
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  },
});

// ── 8. Send Instagram ──
const sendInstagram = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Instagram',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/instagram/send'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ { recipientId: $json.userId, type: "brochure", imageUrls: $json.imageUrls, videoUrl: $json.videoUrl, projectName: $json.projectName } }}'),
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  },
});

// ── 9. Log Completion ──
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
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ { workflow: "wf-brochure-sender", status: "completed", channel: $json.channel, userId: $json.userId, projectId: $json.projectId } }}'),
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  },
});

export default workflow('wf-brochure-sender', 'Brochure Sender')
  .description('Receives a webhook with userId, projectId, channel. Fetches brochure data, assembles the package, routes by channel, sends via appropriate platform, and logs.')
  .onError('stopWorkflow')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(fetchBrochure)
  .to(assemblePackage)
  .to(routeByChannel
    .onCase(0, sendWhatsApp.to(logCompletion))
    .onCase(1, sendFacebook.to(logCompletion))
    .onCase(2, sendInstagram.to(logCompletion))
  );
