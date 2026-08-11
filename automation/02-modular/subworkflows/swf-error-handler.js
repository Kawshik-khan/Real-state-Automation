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
          { name: 'workflowName', type: 'string' },
          { name: 'nodeName', type: 'string' },
          { name: 'errorMessage', type: 'string' },
          { name: 'errorDetails', type: 'object' }
        ]
      }
    }
  },
  output: [{ workflowName: 'swf-ai-api-caller', nodeName: 'Call AI API', errorMessage: 'Connection refused', errorDetails: { code: 'ECONNREFUSED', stack: 'Error: connect ECONNREFUSED' } }]
});

const normalizeInput = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Input',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'err-workflow', name: 'workflowName', value: expr('{{ $json.workflowName }}'), type: 'string' },
          { id: 'err-node', name: 'nodeName', value: expr('{{ $json.nodeName }}'), type: 'string' },
          { id: 'err-message', name: 'errorMessage', value: expr('{{ $json.errorMessage }}'), type: 'string' },
          { id: 'err-details', name: 'errorDetails', value: expr('{{ $json.errorDetails }}'), type: 'object' }
        ]
      }
    }
  },
  output: [{ workflowName: 'swf-ai-api-caller', nodeName: 'Call AI API', errorMessage: 'Connection refused', errorDetails: { code: 'ECONNREFUSED' } }]
});

const buildErrorLog = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Build Error Log',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'log-level', name: 'level', value: 'error', type: 'string' },
          { id: 'log-source', name: 'source', value: expr('{{ $json.workflowName }}'), type: 'string' },
          { id: 'log-action', name: 'action', value: expr('{{ $json.nodeName }}'), type: 'string' },
          { id: 'log-message', name: 'message', value: expr('{{ $json.errorMessage }}'), type: 'string' },
          { id: 'log-metadata', name: 'metadata', value: expr('{{ $json.errorDetails }}'), type: 'object' }
        ]
      }
    }
  },
  output: [{ level: 'error', source: 'swf-ai-api-caller', nodeName: 'Call AI API', errorMessage: 'Connection refused', errorDetails: { code: 'ECONNREFUSED' } }]
});

const logError = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Log Error to API',
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
  output: [{ status: 'logged' }]
});

const sendSlackAlert = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Slack Alert',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.SLACK_WEBHOOK_URL }}'),
      authentication: 'none',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: {
        text: expr('{{ "[ERROR] " + $node["Build Error Log"].json["workflowName"] + " / " + $node["Build Error Log"].json["nodeName"] + ": " + $node["Build Error Log"].json["errorMessage"] }}'),
        attachments: [
          {
            color: 'danger',
            title: 'Error Details',
            text: expr('{{ JSON.stringify($node["Build Error Log"].json["errorDetails"]) }}')
          }
        ]
      },
      options: { timeout: 10000 }
    }
  },
  output: [{ ok: true }]
});

const finalize = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Finalize Output',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'err-handled', name: 'handled', value: true, type: 'boolean' },
          { id: 'err-workflow', name: 'workflowName', value: expr('{{ $node["Build Error Log"].json["workflowName"] }}'), type: 'string' },
          { id: 'err-node', name: 'nodeName', value: expr('{{ $node["Build Error Log"].json["nodeName"] }}'), type: 'string' },
          { id: 'err-msg', name: 'errorMessage', value: expr('{{ $node["Build Error Log"].json["errorMessage"] }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ handled: true, workflowName: 'swf-ai-api-caller', nodeName: 'Call AI API', errorMessage: 'Connection refused' }]
});

export default workflow('swf-error-handler', 'SWF-Error-Handler')
  .add(executeTrigger)
  .to(normalizeInput)
  .to(buildErrorLog)
  .to(logError)
  .to(sendSlackAlert)
  .to(finalize);
