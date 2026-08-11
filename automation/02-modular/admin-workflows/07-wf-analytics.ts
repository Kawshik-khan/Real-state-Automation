import { workflow, trigger, node, merge, setNode, expr, newCredential } from '@n8n/workflow-sdk';

// ── Trigger: Schedule (nightly at 11PM) ──
const scheduleTrigger = trigger('n8n-nodes-base.scheduleTrigger', 1.3, {
  name: 'Nightly Analytics (11PM)',
  parameters: {
    rule: {
      interval: {},
    },
    scheduling: {
      timezone: 'UTC',
      activation: { hour: 23, minute: 0, weekday: -1, dayOfMonth: -1, month: -1 },
    },
  },
  output: [{ timestamp: '2026-07-27T23:00:00Z' }],
});

// ── Fetch Daily Analytics ──
const fetchDailyAnalytics = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Fetch Daily Analytics',
  parameters: {
    method: 'GET',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/analytics/daily'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      date: '2026-07-27',
      totalConversations: 145,
      newUsers: 23,
      messagesSent: 890,
      activeProjects: 12,
    },
  ],
});

// ── Fetch Engagement Metrics ──
const fetchEngagement = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Fetch Engagement Metrics',
  parameters: {
    method: 'GET',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/analytics/engagement'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      likes: 345,
      shares: 89,
      comments: 56,
      clickThroughRate: 3.2,
      topPerformingPost: 'Check out our luxury villas',
    },
  ],
});

// ── Fetch Failed Replies ──
const fetchFailedReplies = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Fetch Failed Replies',
  parameters: {
    method: 'GET',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/analytics/failed-replies'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      totalFailed: 5,
      failures: [
        { id: 'fail_001', reason: 'Rate limit exceeded', timestamp: '2026-07-27T14:30:00Z' },
        { id: 'fail_002', reason: 'Invalid recipient', timestamp: '2026-07-27T16:45:00Z' },
      ],
    },
  ],
});

// ── Merge Analytics Data ──
const mergeAnalytics = merge({
  version: 2.4,
  config: {
    name: 'Merge Analytics Data',
    parameters: {
      mode: 'combine',
      combinationMode: 'mergeByPosition',
      options: {},
    },
  },
});

// ── Compile Report ──
const compileReport = node('n8n-nodes-base.code', 2, {
  name: 'Compile Report',
  parameters: {
    mode: 'runOnceForAllItems',
    jsCode: `
      const daily = $('Fetch Daily Analytics').first().json;
      const engagement = $('Fetch Engagement Metrics').first().json;
      const failed = $('Fetch Failed Replies').first().json;

      const report = {
        date: daily.date || new Date().toISOString().slice(0, 10),
        summary: {
          totalConversations: daily.totalConversations || 0,
          newUsers: daily.newUsers || 0,
          messagesSent: daily.messagesSent || 0,
          activeProjects: daily.activeProjects || 0,
        },
        engagement: {
          likes: engagement.likes || 0,
          shares: engagement.shares || 0,
          comments: engagement.comments || 0,
          clickThroughRate: engagement.clickThroughRate || 0,
          topPost: engagement.topPerformingPost || 'N/A',
        },
        failures: {
          total: failed.totalFailed || 0,
          details: failed.failures || [],
        },
        generatedAt: new Date().toISOString(),
      };

      return [{ json: report }];
    `,
  },
  output: [
    {
      date: '2026-07-27',
      summary: { totalConversations: 145, newUsers: 23, messagesSent: 890, activeProjects: 12 },
      engagement: { likes: 345, shares: 89, comments: 56, clickThroughRate: 3.2, topPost: 'Check out our luxury villas' },
      failures: { total: 5, details: [] },
      generatedAt: '2026-07-27T23:00:00Z',
    },
  ],
});

// ── Send Email Report ──
const sendEmailReport = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Send Email Report',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/notifications/email'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { to: "admin@glgassets.com", subject: "Daily Analytics Report - " + $json.date, body: "GLG Assets Daily Analytics\\n\\n=== Summary ===\\nConversations: " + $json.summary.totalConversations + "\\nNew Users: " + $json.summary.newUsers + "\\nMessages Sent: " + $json.summary.messagesSent + "\\nActive Projects: " + $json.summary.activeProjects + "\\n\\n=== Engagement ===\\nLikes: " + $json.engagement.likes + "\\nShares: " + $json.engagement.shares + "\\nComments: " + $json.engagement.comments + "\\nClick-through Rate: " + $json.engagement.clickThroughRate + "%\\nTop Post: " + $json.engagement.topPost + "\\n\\n=== Failed Replies ===\\nTotal Failed: " + $json.failures.total + "\\n\\nGenerated at: " + $json.generatedAt } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ messageId: 'report_email_001', accepted: true }],
});

// ── Log Completion ──
const logAnalyticsRun = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Log Analytics Run',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { workflow: "wf-analytics", status: "completed", date: $json.date, timestamp: $json.generatedAt } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ logged: true }],
});

// ── Build and Export ──
export default workflow('wf-analytics', 'Nightly Analytics Reporter')
  .description(
    'Triggers nightly at 11PM UTC. Fetches daily analytics, engagement metrics, and failed replies from the backend. ' +
    'Merges the data, compiles a report using a Code node, sends the report via email, and logs the run.'
  )
  .onError('stopWorkflow')
  .add(scheduleTrigger)
  .to([fetchDailyAnalytics, fetchEngagement, fetchFailedReplies])
  .to(mergeAnalytics)
  .to(compileReport)
  .to(sendEmailReport)
  .to(logAnalyticsRun);
