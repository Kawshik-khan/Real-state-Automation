import {
  workflow, node, trigger, ifElse, expr
} from '@n8n/workflow-sdk';

// Webhook trigger — external services POST leads here
const leadWebhook = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Lead Capture Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'leads/capture',
      responseMode: 'responseNode',
      options: { rawBody: true }
    }
  }
});

// Normalize incoming lead data regardless of payload structure
const normalizeLead = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Lead',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'lead-id', name: 'leadId', value: '={{ $json.body?.leadId ?? $json.leadId ?? $execution.id }}', type: 'string' },
          { id: 'name', name: 'name', value: '={{ $json.body?.name ?? $json.name ?? "" }}', type: 'string' },
          { id: 'email', name: 'email', value: '={{ $json.body?.email ?? $json.email ?? "" }}', type: 'string' },
          { id: 'phone', name: 'phone', value: '={{ $json.body?.phone ?? $json.phone ?? "" }}', type: 'string' },
          { id: 'message', name: 'message', value: '={{ $json.body?.message ?? $json.message ?? "" }}', type: 'string' },
          { id: 'source', name: 'source', value: '={{ $json.body?.source ?? $json.source ?? "webhook" }}', type: 'string' },
          { id: 'tenant-id', name: 'tenantId', value: '={{ $json.body?.tenantId ?? $json.tenantId ?? $env.DEFAULT_TENANT_ID }}', type: 'string' }
        ]
      }
    }
  }
});

// Classify via FastAPI backend
const classifyLead = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Classify via Backend',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/classify',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "leadId": $json.leadId, "name": $json.name, "email": $json.email, "phone": $json.phone, "message": $json.message, "source": $json.source, "tenantId": $json.tenantId } }}',
      options: { timeout: 20000 }
    },
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 2000,
    onError: 'continueErrorOutput'
  }
});

// Route: high priority → notify team immediately
const checkPriority = ifElse({
  version: 2.2,
  config: {
    name: 'High Priority?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, typeValidation: 'loose' },
        conditions: [
          { leftValue: '={{ $json.priority }}', operator: { type: 'string', operation: 'equals' }, rightValue: 'high' }
        ],
        combinator: 'or'
      }
    }
  }
});

const notifyUrgent = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Urgent Lead',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/notify',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "channels": ["email", "slack"], "type": "urgent_lead", "title": "URGENT: " + $json.name, "message": "Priority lead from " + $json.source + "\\nName: " + $json.name + "\\nPhone: " + ($json.phone || "N/A") + "\\nEmail: " + ($json.email || "N/A"), "tenantId": $json.tenantId } }}',
      options: { timeout: 15000 }
    },
    onError: 'continueErrorOutput'
  }
});

// Respond back to the webhook caller
const respondSuccess = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Respond Success',
    parameters: {
      respondWith: 'json',
      responseBody: '={{ { success: true, leadId: $json.leadId, priority: $json.priority, category: $json.category, assignedAgent: $json.assignedAgent } }}',
      options: {}
    }
  }
});

const respondError = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Respond Error',
    parameters: {
      respondWith: 'json',
      responseBody: '={{ { success: false, error: $json.error?.message || "Classification failed" } }}',
      options: { responseCode: 500 }
    }
  }
});

export default workflow('glg-lead-capture', 'GLG Assets - Lead Capture Webhook')
  .add(leadWebhook)
  .to(normalizeLead)
  .to(classifyLead)
  .to(checkPriority
    .onTrue(notifyUrgent.to(respondSuccess))
    .onFalse(respondSuccess)
  )
  .add(classifyLead)
  .to(respondError);
