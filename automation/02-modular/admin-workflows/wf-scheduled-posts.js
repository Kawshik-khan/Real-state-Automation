import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily Schedule (9AM)',
    parameters: {
      rule: {
        interval: [{ field: 'days', minutesInterval: 1440 }]
      }
    }
  },
  output: [{}]
});

const fetchApprovedPosts = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Fetch Approved Posts',
    parameters: {
      method: 'GET',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/content/approved?status=pending'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    posts: [
      { id: 'post_001', platform: 'facebook', headline: 'Check out this property!', body: 'Amazing 5BR villa...', images: ['https://cdn.example.com/img1.jpg'], scheduledAt: '2025-01-02T09:00:00Z' },
      { id: 'post_002', platform: 'instagram', headline: 'Stunning views', body: 'Sunset at the villa...', images: ['https://cdn.example.com/img2.jpg'], scheduledAt: '2025-01-02T09:00:00Z' }
    ]
  }]
});

const extractPosts = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Extract Posts Array',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `const posts = $json.posts || [];
if (posts.length === 0) return [];
return posts.map(p => ({
  ...p,
  json: p
}));`
    }
  },
  output: [
    { id: 'post_001', platform: 'facebook', headline: 'Check out this property!', body: 'Amazing 5BR villa...', images: ['https://cdn.example.com/img1.jpg'], scheduledAt: '2025-01-02T09:00:00Z' }
  ]
});

const splitByPost = splitInBatches({
  version: 3,
  config: { name: 'Process Each Post', parameters: { batchSize: 1 } }
});

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
              conditions: [{ leftValue: expr('{{ $json.platform }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'facebook' }],
              combinator: 'and'
            }
          },
          {
            outputKey: 'instagram',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [{ leftValue: expr('{{ $json.platform }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'instagram' }],
              combinator: 'and'
            }
          },
          {
            outputKey: 'linkedin',
            conditions: {
              options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
              conditions: [{ leftValue: expr('{{ $json.platform }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'linkedin' }],
              combinator: 'and'
            }
          }
        ]
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'Unknown Platform' }
    }
  }
});

const postToFacebook = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Post to Facebook',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/facebook/post'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'postId', value: expr('{{ $json.id }}') },
          { name: 'message', value: expr('{{ $json.headline }}\\n\\n{{ $json.body }}') },
          { name: 'images', value: expr('{{ $json.images }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, platformPostId: 'fb_98765' }]
});

const postToInstagram = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Post to Instagram',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/instagram/post'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'postId', value: expr('{{ $json.id }}') },
          { name: 'caption', value: expr('{{ $json.headline }}\\n\\n{{ $json.body }}') },
          { name: 'images', value: expr('{{ $json.images }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, platformPostId: 'ig_54321' }]
});

const postToLinkedIn = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Post to LinkedIn',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/linkedin/post'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'postId', value: expr('{{ $json.id }}') },
          { name: 'headline', value: expr('{{ $json.headline }}') },
          { name: 'body', value: expr('{{ $json.body }}') },
          { name: 'images', value: expr('{{ $json.images }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, platformPostId: 'li_11111' }]
});

const updatePostStatus = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Update Post Status',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/content/update-status'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'postId', value: expr('{{ $json.id }}') },
          { name: 'status', value: 'published' },
          { name: 'publishedAt', value: expr('{{ $now.toISO() }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, updated: true }]
});

const finalizeBatch = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Finalize Batch',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'fb-complete', name: 'batchCompleted', value: true, type: 'boolean' },
          { id: 'fb-time', name: 'completedAt', value: expr('{{ $now.toISO() }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ batchCompleted: true, completedAt: '2025-01-01T09:05:00Z' }]
});

export default workflow('wf-scheduled-posts', 'Scheduled Posts')
  .add(scheduleTrigger)
  .to(fetchApprovedPosts)
  .to(extractPosts)
  .to(splitByPost
    .onDone(finalizeBatch)
    .onEachBatch(
      routeByPlatform
        .onCase(0, postToFacebook.to(updatePostStatus))
        .onCase(1, postToInstagram.to(updatePostStatus))
        .onCase(2, postToLinkedIn.to(updatePostStatus))
        .onCase(3, updatePostStatus)
        .to(nextBatch(splitByPost))
    )
  );
