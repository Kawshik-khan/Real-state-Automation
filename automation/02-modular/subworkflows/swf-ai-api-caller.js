import { workflow, node, trigger, ifElse, expr, newCredential } from '@n8n/workflow-sdk';

const executeTrigger = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.2,
  config: {
    name: 'Execute Workflow Trigger',
    parameters: {
      inputSource: 'workflowInputs',
      workflowInputs: {
        values: [
          { name: 'channel', type: 'string' },
          { name: 'userId', type: 'string' },
          { name: 'sessionId', type: 'string' },
          { name: 'message', type: 'string' },
          { name: 'messageId', type: 'string' },
          { name: 'metadata', type: 'object' }
        ]
      }
    }
  },
  output: [{ channel: 'whatsapp', userId: 'user_abc123', sessionId: 'sess_xyz', message: 'Hello, I am interested in the property', messageId: 'msg_001', metadata: { source: 'whatsapp', client_ref: 'ref_001' } }]
});

const buildPayload = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Build API Payload',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'ai-channel', name: 'channel', value: expr('{{ $json.channel }}'), type: 'string' },
          { id: 'ai-userId', name: 'userId', value: expr('{{ $json.userId }}'), type: 'string' },
          { id: 'ai-sessionId', name: 'sessionId', value: expr('{{ $json.sessionId }}'), type: 'string' },
          { id: 'ai-message', name: 'message', value: expr('{{ $json.message }}'), type: 'string' },
          { id: 'ai-messageId', name: 'messageId', value: expr('{{ $json.messageId }}'), type: 'string' },
          { id: 'ai-metadata', name: 'metadata', value: expr('{{ $json.metadata }}'), type: 'object' },
          { id: 'ai-retryCount', name: 'retryCount', value: 0, type: 'number' }
        ]
      }
    }
  },
  output: [{ channel: 'whatsapp', userId: 'user_abc123', sessionId: 'sess_xyz', message: 'Hello, I am interested in the property', messageId: 'msg_001', metadata: { source: 'whatsapp' }, retryCount: 0 }]
});

const callAiApi = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Call AI API',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/chat'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: {
        channel: expr('{{ $json.channel }}'),
        user_id: expr('{{ $json.userId }}'),
        session_id: expr('{{ $json.sessionId }}'),
        message: expr('{{ $json.message }}'),
        message_id: expr('{{ $json.messageId }}'),
        metadata: expr('{{ $json.metadata }}')
      },
      sendHeaders: true,
      headerParameters: {
        parameters: [
          { name: 'X-Tenant-Id', value: expr('{{ $env.TENANT_ID || "glg-assets" }}') }
        ]
      },
      options: {
        timeout: 30000,
        retryOnFail: true,
        maxTries: 3,
        waitBetweenTries: 1000
      }
    },
    credentials: {
      httpHeaderAuth: newCredential('Backend API Key')
    },
    onError: 'continueErrorOutput'
  },
  output: [{ success: true, reply: 'Sure, I can help you with that property.', action: 'inquire', confidence: 0.95, project_ids: ['proj_001'], error_message: null }]
});

const validateResponse = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Validate Response',
    parameters: {
      jsCode: `// Validate the AI API response
const items = $input.all();
return items.map(item => {
  const json = item.json;
  const isHttpError = json.error && json.statusCode;
  const responseBody = json.data || json;
  const valid = !isHttpError && responseBody && (responseBody.success === true || responseBody.reply);
  return {
    json: {
      apiSuccess: valid,
      reply: responseBody.reply || "",
      action: responseBody.action || "unknown",
      confidence: responseBody.confidence || 0,
      project_ids: responseBody.project_ids || [],
      error_message: responseBody.error_message || (isHttpError ? "HTTP error from AI API" : ""),
      rawResponse: JSON.stringify(responseBody)
    }
  };
});`
    }
  },
  output: [{ apiSuccess: true, reply: 'Sure, I can help you with that property.', action: 'inquire', confidence: 0.95, project_ids: ['proj_001'], error_message: null, rawResponse: '{}' }]
});

const checkSuccess = ifElse({
  version: 2.3,
  config: {
    name: 'API Success?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          {
            leftValue: expr('{{ $json.apiSuccess }}'),
            operator: { type: 'boolean', operation: 'isTrue' }
          }
        ],
        combinator: 'and'
      }
    }
  }
});

const prepareOutput = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Prepare Output',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'ai-finalSuccess', name: 'success', value: true, type: 'boolean' },
          { id: 'ai-finalReply', name: 'reply', value: expr('{{ $json.reply }}'), type: 'string' },
          { id: 'ai-finalAction', name: 'action', value: expr('{{ $json.action }}'), type: 'string' },
          { id: 'ai-finalConf', name: 'confidence', value: expr('{{ $json.confidence }}'), type: 'number' },
          { id: 'ai-finalProjects', name: 'project_ids', value: expr('{{ $json.project_ids }}'), type: 'object' },
          { id: 'ai-finalError', name: 'error_message', value: '', type: 'string' }
        ]
      }
    }
  },
  output: [{ success: true, reply: 'Sure, I can help you with that property.', action: 'inquire', confidence: 0.95, project_ids: ['proj_001'], error_message: '' }]
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
        level: 'error',
        source: expr('{{ $node["Build API Payload"].json.channel || "unknown" }}'),
        action: 'call_ai_api',
        message: expr('{{ $json.error_message || "AI API call failed" }}'),
        metadata: {}
      },
      options: { timeout: 10000 }
    },
    credentials: {
      httpHeaderAuth: newCredential('Backend API Key')
    }
  },
  output: [{ status: 'logged' }]
});

const prepareErrorOutput = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Prepare Error Output',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'fail-success', name: 'success', value: false, type: 'boolean' },
          { id: 'fail-reply', name: 'reply', value: '', type: 'string' },
          { id: 'fail-action', name: 'action', value: 'error', type: 'string' },
          { id: 'fail-confidence', name: 'confidence', value: 0, type: 'number' },
          { id: 'fail-projects', name: 'project_ids', value: [], type: 'object' },
          { id: 'fail-error', name: 'error_message', value: expr('{{ $json.error_message || "AI API call failed after retries" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ success: false, reply: '', action: 'error', confidence: 0, project_ids: [], error_message: 'AI API call failed' }]
});

export default workflow('swf-ai-api-caller', 'SWF-AI-API-Caller')
  .add(executeTrigger)
  .to(buildPayload)
  .to(callAiApi)
  .to(validateResponse)
  .to(checkSuccess
    .onTrue(prepareOutput)
    .onFalse(logError.to(prepareErrorOutput))
  );
