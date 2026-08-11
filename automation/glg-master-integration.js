import { workflow, node, trigger, newCredential, expr } from '@n8n/workflow-sdk';

const backendCred = newCredential('FastAPI Backend Auth');

const manualTrigger = trigger({
  type: 'n8n-nodes-base.manualTrigger',
  version: 1,
  config: { name: 'Manual Trigger' }
});

// All URLs use $env.FASTAPI_BASE_URL with fallback
const checkHealth = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Backend Health Check',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/health'),
      authentication: 'none',
      options: { timeout: 10000 }
    }
  }
});

const sendBooking = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Booking Create',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/booking'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ $json }}'),
      options: { timeout: 15000 }
    },
    credentials: { httpHeaderAuth: backendCred }
  }
});

const sendNotify = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Notify Send',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/notify'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ $json }}'),
      options: { timeout: 15000 }
    },
    credentials: { httpHeaderAuth: backendCred }
  }
});

const classifyLead = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Classify Lead',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/classify'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ $json }}'),
      options: { timeout: 15000 }
    },
    credentials: { httpHeaderAuth: backendCred }
  }
});

const aiChat = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'AI Chat',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/chat'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ $json }}'),
      options: { timeout: 30000 }
    },
    credentials: { httpHeaderAuth: backendCred }
  }
});

const dailyDigest = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Daily Digest',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/daily-digest'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: { timeout: 15000 }
    },
    credentials: { httpHeaderAuth: backendCred },
    executeOnce: true
  }
});

const getLogs = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Automation Logs',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/logs'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: { timeout: 10000 }
    },
    credentials: { httpHeaderAuth: backendCred },
    executeOnce: true
  }
});

export default workflow('glg-master-integration', 'GLG Assets - Master Integration Hub')
  .add(manualTrigger)
  .to(checkHealth)
  .add(manualTrigger)
  .to(sendBooking)
  .add(manualTrigger)
  .to(sendNotify)
  .add(manualTrigger)
  .to(classifyLead)
  .add(manualTrigger)
  .to(aiChat)
  .add(manualTrigger)
  .to(dailyDigest)
  .add(manualTrigger)
  .to(getLogs);
