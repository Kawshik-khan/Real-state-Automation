import {
  workflow, node, trigger, sticky, merge, ifElse, switchCase,
  expr, newCredential
} from '@n8n/workflow-sdk';

// ============================================================
// GLG Assets - Backend Integration Hub (v2.0)
// Connects to ALL FastAPI backend endpoints with proper auth
// ============================================================

// --- Trigger ---
const manualTrigger = trigger({
  type: 'n8n-nodes-base.manualTrigger',
  version: 1,
  config: { name: 'Manual Trigger' }
});

// ============================================================
// 1. HEALTH CHECK
// ============================================================
const healthCheck = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '1. Health Check',
    parameters: {
      method: 'GET',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/health',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: { timeout: 10000 }
    }
  }
});

// ============================================================
// 2. DAILY DIGEST
// ============================================================
const dailyDigest = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '2. Daily Digest (GET)',
    parameters: {
      method: 'GET',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/daily-digest',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: { timeout: 15000 }
    },
    executeOnce: true
  }
});

// ============================================================
// 3. CREATE BOOKING
// ============================================================
const createBooking = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '3. Create Booking (POST)',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/booking',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "name": $json.name, "email": $json.email, "phone": $json.phone, "propertyId": $json.propertyId, "tourDate": $json.tourDate, "tourTime": $json.tourTime, "message": $json.message, "source": $json.source || "website", "tenantId": $json.tenantId || $env.DEFAULT_TENANT_ID } }}',
      options: { timeout: 15000 }
    }
  }
});

// ============================================================
// 4. SEND NOTIFICATION
// ============================================================
const sendNotification = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '4. Send Notification (POST)',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/notify',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "channels": $json.channels || ["email"], "type": $json.type || "info", "title": $json.title, "message": $json.message, "recipient": $json.recipient, "tenantId": $json.tenantId || $env.DEFAULT_TENANT_ID } }}',
      options: { timeout: 15000 }
    }
  }
});

// ============================================================
// 5. CLASSIFY LEAD (with retry + error handling)
// ============================================================
const classifyLead = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '5. Classify Lead (POST)',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/classify',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "leadId": $json.leadId, "name": $json.name, "email": $json.email, "phone": $json.phone, "message": $json.message, "source": $json.source || "unknown", "tenantId": $json.tenantId || $env.DEFAULT_TENANT_ID } }}',
      options: { timeout: 15000 }
    },
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 2000,
    onError: 'continueErrorOutput'
  }
});

// ============================================================
// 6. AI CHAT (with retry + error handling)
// ============================================================
const aiChat = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '6. AI Chat (POST)',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/chat',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "channel": $json.channel || "whatsapp", "userId": $json.userId, "sessionId": $json.sessionId, "message": $json.message, "messageId": $json.messageId, "metadata": $json.metadata || {}, "tenantId": $json.tenantId || $env.DEFAULT_TENANT_ID } }}',
      options: { timeout: 30000 }
    },
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 2000,
    onError: 'continueErrorOutput'
  }
});

// ============================================================
// 7. INGEST LOGS
// ============================================================
const ingestLogs = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '7. Ingest Logs (POST)',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/logs',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "workflowId": $json.workflowId || $execution.id, "workflowName": $json.workflowName, "status": $json.status || "completed", "duration": $json.duration, "error": $json.error || null, "tenantId": $json.tenantId || $env.DEFAULT_TENANT_ID, "loggedAt": $now.toISO() } }}',
      options: { timeout: 10000 }
    }
  }
});

// ============================================================
// 8. LEAD PRIORITY ROUTING
// ============================================================
const checkPriority = ifElse({
  version: 2.2,
  config: {
    name: '8A. High Priority Lead?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, typeValidation: 'loose' },
        conditions: [
          {
            leftValue: '={{ $json.priority }}',
            operator: { type: 'string', operation: 'equals' },
            rightValue: 'high'
          }
        ],
        combinator: 'or'
      }
    }
  }
});

const urgentNotify = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '8B. Notify Urgent Lead',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/notify',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "channels": ["email", "slack"], "type": "urgent_lead", "title": "URGENT: High-Value Lead - " + $json.name, "message": "Name: " + $json.name + "\\nPhone: " + $json.phone + "\\nEmail: " + $json.email + "\\nSource: " + $json.source, "tenantId": $json.tenantId || $env.DEFAULT_TENANT_ID } }}',
      options: { timeout: 15000 }
    },
    onError: 'continueErrorOutput'
  }
});

const normalAck = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '8C. Log Normal Lead',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "http://localhost:8000" }}/api/v1/automation/logs',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '={{ { "workflowId": $execution.id, "workflowName": "Lead Classification", "status": "classified", "tenantId": $json.tenantId || $env.DEFAULT_TENANT_ID, "loggedAt": $now.toISO() } }}',
      options: { timeout: 10000 }
    }
  }
});

// ============================================================
// COMPOSE WORKFLOW
// ============================================================

export default workflow('glg-assets-backend-hub', 'GLG Assets - Backend Integration Hub')
  // Branch 1: Health Check
  .add(manualTrigger)
  .to(healthCheck)

  // Branch 2: Daily Digest
  .add(manualTrigger)
  .to(dailyDigest)

  // Branch 3: Create Booking
  .add(manualTrigger)
  .to(createBooking)

  // Branch 4: Send Notification
  .add(manualTrigger)
  .to(sendNotification)

  // Branch 5: Classify Lead → Route by Priority
  .add(manualTrigger)
  .to(classifyLead)
  .to(checkPriority
    .onTrue(urgentNotify)
    .onFalse(normalAck)
  )

  // Branch 6: AI Chat
  .add(manualTrigger)
  .to(aiChat)

  // Branch 7: Ingest Logs
  .add(manualTrigger)
  .to(ingestLogs);
