import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Nightly Schedule (11PM)',
    parameters: {
      rule: {
        interval: [{ field: 'days', minutesInterval: 1440 }]
      }
    }
  },
  output: [{}]
});

const fetchDailyAnalytics = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Fetch Daily Analytics',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/analytics/daily'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    date: '2025-01-01',
    totalConversations: 150,
    newLeads: 23,
    messagesSent: 410,
    brochureRequests: 12,
    activeUsers: 85
  }]
});

const fetchEngagementAnalytics = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Fetch Engagement Analytics',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/analytics/engagement'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    facebookLikes: 45,
    facebookShares: 12,
    instagramLikes: 78,
    instagramComments: 23,
    linkedInImpressions: 1200,
    whatsappReadRate: 0.85
  }]
});

const fetchFailedReplies = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Fetch Failed Replies',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/analytics/failed-replies'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    failedCount: 3,
    failedReplies: [
      { conversationId: 'conv_001', error: 'API timeout', timestamp: '2025-01-01T10:00:00Z' },
      { conversationId: 'conv_002', error: 'Rate limit', timestamp: '2025-01-01T11:00:00Z' }
    ]
  }]
});

const compileReport = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Compile Report',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `const daily = $json;
const engagement = $json;
const failed = $json;

const report = \`=== Daily Analytics Report ===
Date: \${daily.date || "N/A"}
Total Conversations: \${daily.totalConversations || 0}
New Leads: \${daily.newLeads || 0}
Messages Sent: \${daily.messagesSent || 0}
Brochure Requests: \${daily.brochureRequests || 0}
Active Users: \${daily.activeUsers || 0}

--- Engagement ---
Facebook Likes: \${engagement.facebookLikes || 0} / Shares: \${engagement.facebookShares || 0}
Instagram Likes: \${engagement.instagramLikes || 0} / Comments: \${engagement.instagramComments || 0}
LinkedIn Impressions: \${engagement.linkedInImpressions || 0}
WhatsApp Read Rate: \${((engagement.whatsappReadRate || 0) * 100).toFixed(1)}%

--- Failed Replies Today: \${failed.failedCount || 0} ---
\${(failed.failedReplies || []).map(f => \`- \${f.conversationId}: \${f.error}\`).join("\\\\n")}\`;

return [{ report, generatedAt: new Date().toISOString(), date: daily.date }];`
    }
  },
  output: [{
    report: '=== Daily Analytics Report ===\\nDate: 2025-01-01\\n...',
    generatedAt: '2025-01-01T23:00:00Z',
    date: '2025-01-01'
  }]
});

const sendEmailReport = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send Email Report',
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
          { name: 'subject', value: expr('Daily Analytics Report - {{ $json.date }}') },
          { name: 'body', value: expr('{{ $json.report }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, emailId: 'report_email_001' }]
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
          { name: 'workflow', value: 'wf-analytics' },
          { name: 'status', value: 'completed' },
          { name: 'date', value: expr('{{ $json.date }}') },
          { name: 'generatedAt', value: expr('{{ $json.generatedAt }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ logged: true }]
});

export default workflow('wf-analytics', 'Analytics Report')
  .add(scheduleTrigger)
  .to(fetchDailyAnalytics)
  .to(fetchEngagementAnalytics)
  .to(fetchFailedReplies)
  .to(compileReport)
  .to(sendEmailReport)
  .to(logCompletion);
