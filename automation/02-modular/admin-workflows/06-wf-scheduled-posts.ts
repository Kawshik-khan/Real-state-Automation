import { workflow, trigger, node, switchCase, splitInBatches, nextBatch, expr, newCredential } from '@n8n/workflow-sdk';

// ── Trigger: Schedule (daily at 9AM) ──
const scheduleTrigger = trigger('n8n-nodes-base.scheduleTrigger', 1.3, {
  name: 'Daily Schedule (9AM)',
  parameters: {
    rule: {
      interval: {},
    },
    scheduling: {
      timezone: 'UTC',
      activation: { hour: 9, minute: 0, weekday: -1, dayOfMonth: -1, month: -1 },
    },
  },
  output: [{ timestamp: '2026-07-27T09:00:00Z' }],
});

// ── Fetch Approved Posts ──
const fetchApprovedPosts = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Fetch Approved Posts',
  parameters: {
    method: 'GET',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/posts?status=approved&scheduledFor=' + new Date().toISOString().slice(0, 10)),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      posts: [
        { id: 'post_001', platform: 'facebook', caption: 'Check out our new project!', imageUrl: 'https://cdn.example.com/img1.jpg', hashtags: '#RealEstate' },
        { id: 'post_002', platform: 'instagram', caption: 'Luxury living at its finest', imageUrl: 'https://cdn.example.com/img2.jpg', hashtags: '#Luxury' },
        { id: 'post_003', platform: 'linkedin', caption: 'New development announcement', imageUrl: 'https://cdn.example.com/img3.jpg', hashtags: '#Investment' },
      ],
    },
  ],
});

// ── Extract Posts Array ──
const extractPosts = node('n8n-nodes-base.code', 2, {
  name: 'Extract Posts Array',
  parameters: {
    mode: 'runOnceForAllItems',
    jsCode: `
      const posts = $input.first().json.posts || [];
      if (!Array.isArray(posts)) {
        return [{ json: { posts: [] } }];
      }
      return posts.map(post => ({ json: post }));
    `,
  },
  output: [
    { id: 'post_001', platform: 'facebook', caption: 'Check out our new project!' },
  ],
});

// ── Split Into Batches ──
const splitBatches = splitInBatches({
  version: 3,
  config: {
    name: 'Process Posts in Batches',
    parameters: {
      batchSize: 1,
      options: {},
    },
  },
});

// ── Route by Platform ──
const routeByPlatform = switchCase({
  version: 3.4,
  config: {
    name: 'Route by Platform',
    parameters: {
      mode: 'rules',
      rules: {
        values: [
          {
            outputKey: 'facebook',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [
                { leftValue: expr('{{ $json.platform }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'facebook' },
              ],
              combinator: 'and',
            },
          },
          {
            outputKey: 'instagram',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [
                { leftValue: expr('{{ $json.platform }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'instagram' },
              ],
              combinator: 'and',
            },
          },
          {
            outputKey: 'linkedin',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [
                { leftValue: expr('{{ $json.platform }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'linkedin' },
              ],
              combinator: 'and',
            },
          },
        ],
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'Unknown Platform' },
    },
  },
});

// ── Facebook Publisher ──
const publishFacebook = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Publish to Facebook',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/facebook/publish'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { postId: $json.id, caption: $json.caption, imageUrl: $json.imageUrl, hashtags: $json.hashtags } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ success: true, platformPostId: 'fb_pub_001' }],
});

// ── Instagram Publisher ──
const publishInstagram = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Publish to Instagram',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/instagram/publish'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { postId: $json.id, caption: $json.caption + "\\n\\n" + $json.hashtags, imageUrl: $json.imageUrl } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ success: true, platformPostId: 'ig_pub_001' }],
});

// ── LinkedIn Publisher ──
const publishLinkedIn = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Publish to LinkedIn',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/linkedin/publish'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { postId: $json.id, caption: $json.caption, imageUrl: $json.imageUrl } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ success: true, platformPostId: 'li_pub_001' }],
});

// ── Update Post Status ──
const updateStatus = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Update Post Status',
  parameters: {
    method: 'PATCH',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/posts/' + $json.id + '/status'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { status: "published", publishedAt: new Date().toISOString(), platformPostId: $json.platformPostId } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ updated: true }],
});

// ── Log Completion ──
const logCompletion = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Log Batch Completion',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/automation/log'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { workflow: "wf-scheduled-posts", status: "completed", timestamp: new Date().toISOString(), postsProcessed: 3 } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ logged: true }],
});

// ── Build and Export ──
export default workflow('wf-scheduled-posts', 'Scheduled Posts Publisher')
  .description(
    'Triggers daily at 9AM UTC. Fetches approved posts from the backend that are scheduled for today, ' +
    'processes each post in batches, routes by platform (Facebook, Instagram, LinkedIn), publishes via the ' +
    'respective API, updates the post status, and logs completion.'
  )
  .onError('stopWorkflow')
  .add(scheduleTrigger)
  .to(fetchApprovedPosts)
  .to(extractPosts)
  .to(splitBatches)
  .to(
    routeByPlatform
      .onCase(0, publishFacebook.to(updateStatus))
      .onCase(1, publishInstagram.to(updateStatus))
      .onCase(2, publishLinkedIn.to(updateStatus))
  )
  .to(nextBatch(splitBatches))
  .to(logCompletion);
