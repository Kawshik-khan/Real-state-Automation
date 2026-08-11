import { workflow, trigger, node, ifElse, expr, newCredential, placeholder } from '@n8n/workflow-sdk';

// ── Trigger: Webhook ──
const webhookTrigger = trigger('n8n-nodes-base.webhook', 2.1, {
  name: 'Knowledge Upload Webhook',
  parameters: {
    httpMethod: 'POST',
    path: placeholder('knowledge-upload'),
    responseMode: 'lastNode',
    responseData: 'firstEntryJson',
  },
  output: [
    {
      body: {
        documentUrl: 'https://cdn.example.com/docs/project-brochure.pdf',
        documentType: 'pdf',
        projectId: 'proj_456',
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
        { id: 'ni-doc-url', name: 'documentUrl', value: expr('{{ $json.body?.documentUrl ?? $json.documentUrl ?? "" }}'), type: 'string' },
        { id: 'ni-doc-type', name: 'documentType', value: expr('{{ $json.body?.documentType ?? $json.documentType ?? "" }}'), type: 'string' },
        { id: 'ni-proj', name: 'projectId', value: expr('{{ $json.body?.projectId ?? $json.projectId ?? "" }}'), type: 'string' },
      ],
    },
  },
  output: [
    { documentUrl: 'https://cdn.example.com/docs/project-brochure.pdf', documentType: 'pdf', projectId: 'proj_456' },
  ],
});

// ── Download Document ──
const downloadDocument = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Download Document',
  parameters: {
    method: 'GET',
    url: expr('{{ $json.documentUrl }}'),
    authentication: 'none',
    options: {
      response: {
        response: {
          responseFormat: 'file',
          outputPropertyName: 'documentData',
        },
      },
    },
  },
  output: [{ fileName: 'project-brochure.pdf', mimeType: 'application/pdf', documentData: null }],
});

// ── Upload to Backend File Store ──
const uploadToBackend = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Upload to Backend',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/upload'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { documentUrl: $json.documentUrl, documentType: $json.documentType, projectId: $json.projectId, source: "knowledge-upload" } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ uploadId: 'up_001', status: 'uploaded' }],
});

// ── Trigger OCR via Backend ──
const triggerOCR = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Trigger OCR Processing',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/ocr'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { documentUrl: $json.documentUrl, documentType: $json.documentType, projectId: $json.projectId, uploadId: $json.uploadId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ ocrId: 'ocr_001', status: 'processing', text: 'Extracted text from document...' }],
});

// ── Generate Embeddings ──
const generateEmbeddings = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Generate Embeddings',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/embeddings'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { text: $json.text, documentType: $json.documentType, projectId: $json.projectId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ embeddingId: 'emb_001', chunkCount: 5, status: 'completed' }],
});

// ── Update Knowledge Index ──
const updateIndex = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Update Knowledge Index',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/knowledge/index'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { projectId: $json.projectId, documentUrl: $json.documentUrl, embeddingId: $json.embeddingId, status: "indexed" } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ indexId: 'idx_001', status: 'indexed' }],
});

// ── Notify Admin ──
const notifyAdmin = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Notify Admin',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/email'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { to: "admin@glgassets.com", subject: "Knowledge Upload Complete - " + $json.documentType, body: "Document has been processed successfully.\\n\\nDocument URL: " + $json.documentUrl + "\\nType: " + $json.documentType + "\\nProject: " + $json.projectId + "\\nChunks: " + $json.chunkCount + "\\nIndex: " + $json.indexId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ messageId: 'notif_001', accepted: true }],
});

// ── Build and Export ──
export default workflow('wf-knowledge-upload', 'Knowledge Upload Pipeline')
  .description(
    'Receives a webhook with documentUrl, documentType, and projectId. Downloads the document, ' +
    'uploads it to the backend, triggers OCR processing, generates embeddings, updates the knowledge index, ' +
    'and notifies the admin upon completion.'
  )
  .onError('stopWorkflow')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(downloadDocument)
  .to(uploadToBackend)
  .to(triggerOCR)
  .to(generateEmbeddings)
  .to(updateIndex)
  .to(notifyAdmin);
