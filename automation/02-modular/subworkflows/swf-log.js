import { workflow, node, trigger, expr, newCredential } from '@n8n/workflow-sdk';

const executeTrigger = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.2,
  config: {
    name: 'Execute Workflow Trigger',
    parameters: {
      inputSource: 'workflowInputs',
      workflowInputs: {
        values: [
          { name: 'level', type: 'string' },
          { name: 'source', type: 'string' },
          { name: 'action', type: 'string' },
          { name: 'message', type: 'string' },
          { name: 'metadata', type: 'object' }
        ]
      }
    }
  },
  output: [{ level: 'info', source: 'swf-ai-api-caller', action: 'call_api', message: 'Log entry message', metadata: { key: 'value' } }]
});

const buildPayload = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Build Log Payload',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'log-level', name: 'level', value: expr('{{ $json.level }}'), type: 'string' },
          { id: 'log-source', name: 'source', value: expr('{{ $json.source }}'), type: 'string' },
          { id: 'log-action', name: 'action', value: expr('{{ $json.action }}'), type: 'string' },
          { id: 'log-message', name: 'message', value: expr('{{ $json.message }}'), type: 'string' },
          { id: 'log-metadata', name: 'metadata', value: expr('{{ $json.metadata }}'), type: 'object' }
        ]
      }
    }
  },
  output: [{ level: 'info', source: 'swf-ai-api-caller', action: 'call_api', message: 'Log entry message', metadata: { key: 'value' } }]
});

const sendLog = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Log to API',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/logs'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: {
        level: expr('{{ $json.level }}'),
        source: expr('{{ $json.source }}'),
        action: expr('{{ $json.action }}'),
        message: expr('{{ $json.message }}'),
        metadata: expr('{{ $json.metadata }}')
      },
      options: { timeout: 10000 }
    },
    credentials: {
      httpHeaderAuth: newCredential('Backend API Key')
    }
  },
  output: [{ status: 'logged', timestamp: '2025-01-01T00:00:00Z' }]
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
          { id: 'log-success', name: 'success', value: true, type: 'boolean' },
          { id: 'log-status', name: 'status', value: expr('{{ $json.status }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ success: true, status: 'logged' }]
});

export default workflow('swf-log', 'SWF-Log')
  .add(executeTrigger)
  .to(buildPayload)
  .to(sendLog)
  .to(prepareResponse);
