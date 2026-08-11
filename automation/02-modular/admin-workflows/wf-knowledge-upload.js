import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: { name: 'Knowledge Upload Webhook', path: placeholder('knowledge-upload'), options: {} },
  output: [{ body: { documentUrl: 'https://cdn.example.com/docs/project.pdf', documentType: 'pdf', projectId: 'proj_456' } }]
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
          { id: 'ni-doc', name: 'documentUrl', value: expr('{{ $json.body?.documentUrl ?? $json.documentUrl ?? "" }}'), type: 'string' },
          { id: 'ni-type', name: 'documentType', value: expr('{{ $json.body?.documentType ?? $json.documentType ?? "" }}'), type: 'string' },
          { id: 'ni-proj', name: 'projectId', value: expr('{{ $json.body?.projectId ?? $json.projectId ?? "" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ documentUrl: 'https://cdn.example.com/docs/project.pdf', documentType: 'pdf', projectId: 'proj_456' }]
});

const downloadDocument = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Download Document',
    parameters: {
      method: 'GET',
      url: expr('{{ $json.documentUrl }}'),
      authentication: 'none',
      options: { response: { response: { format: 'file' } } }
    }
  },
  output: [{ fileName: 'project.pdf', mimeType: 'application/pdf', fileSize: 1024000 }]
});

const sendToOcr = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send to OCR Endpoint',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/knowledge/ocr'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'documentUrl', value: expr('{{ $json.documentUrl }}') },
          { name: 'documentType', value: expr('{{ $json.documentType }}') },
          { name: 'projectId', value: expr('{{ $json.projectId }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, ocrId: 'ocr_001', text: 'Extracted text content from the document...', pages: 5 }]
});

const sendChunksToEmbedding = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Chunks to Embedding',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/knowledge/embed'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'ocrId', value: expr('{{ $json.ocrId }}') },
          { name: 'projectId', value: expr('{{ $json.projectId }}') },
          { name: 'text', value: expr('{{ $json.text }}') },
          { name: 'documentType', value: expr('{{ $json.documentType }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, chunkCount: 15, embeddingStatus: 'completed' }]
});

const updateIndex = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Update Vector Index',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/knowledge/index/update'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'projectId', value: expr('{{ $json.projectId }}') },
          { name: 'ocrId', value: expr('{{ $json.ocrId }}') },
          { name: 'chunkCount', value: expr('{{ $json.chunkCount }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, indexUpdated: true, vectorCount: 42 }]
});

const notifyAdmin = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Admin',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/email'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'to', value: expr('{{ $env.ADMIN_EMAIL }}') },
          { name: 'subject', value: expr('Knowledge Upload Complete: {{ $json.documentType }}') },
          { name: 'body', value: expr('Document {{ $json.documentUrl }} has been processed.\\nOCR ID: {{ $json.ocrId }}\\nChunks: {{ $json.chunkCount }}\\nIndex updated: {{ $json.indexUpdated }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, emailId: 'notif_001' }]
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
          { name: 'workflow', value: 'wf-knowledge-upload' },
          { name: 'status', value: 'completed' },
          { name: 'documentUrl', value: expr('{{ $json.documentUrl }}') },
          { name: 'projectId', value: expr('{{ $json.projectId }}') },
          { name: 'ocrId', value: expr('{{ $json.ocrId }}') },
          { name: 'chunkCount', value: expr('{{ $json.chunkCount }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ logged: true }]
});

export default workflow('wf-knowledge-upload', 'Knowledge Upload')
  .add(webhookTrigger)
  .to(normalizeInput)
  .to(downloadDocument)
  .to(sendToOcr)
  .to(sendChunksToEmbedding)
  .to(updateIndex)
  .to(notifyAdmin)
  .to(logCompletion);
