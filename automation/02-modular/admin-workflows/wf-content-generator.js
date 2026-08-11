import { workflow, node, trigger, ifElse, switchCase, merge, splitInBatches, nextBatch, placeholder, newCredential, expr } from '@n8n/workflow-sdk';

const formTrigger = trigger({
  type: 'n8n-nodes-base.formTrigger',
  version: 2.6,
  config: {
    name: 'Content Generator Form',
    parameters: {
      formTitle: 'Generate Social Media Content',
      formDescription: 'Fill in the details to generate AI-powered social media content',
      formFields: {
        values: [
          { fieldLabel: 'Project Name', fieldType: 'text', requiredField: true, placeholder: 'e.g. Lakeside Villa', parameterName: 'projectName' },
          { fieldLabel: 'Key Features', fieldType: 'textarea', requiredField: true, placeholder: 'e.g. 5BR, pool, garden, mountain view', parameterName: 'features' },
          { fieldLabel: 'Image URLs (comma separated)', fieldType: 'text', requiredField: false, placeholder: 'https://...', parameterName: 'imageUrls' },
          { fieldLabel: 'Target Platform', fieldType: 'select', requiredField: true, placeholder: 'Select platform', parameterName: 'platform', selectOptions: { values: [{ option: 'Facebook' }, { option: 'Instagram' }, { option: 'LinkedIn' }, { option: 'All' }] } },
          { fieldLabel: 'Content Tone', fieldType: 'select', requiredField: true, placeholder: 'Select tone', parameterName: 'tone', selectOptions: { values: [{ option: 'Professional' }, { option: 'Casual' }, { option: 'Luxury' }, { option: 'Urgent' }] } }
        ]
      },
      options: {}
    }
  },
  output: [{ body: { projectName: 'Lakeside Villa', features: '5BR, pool, garden', imageUrls: 'https://cdn.example.com/img1.jpg,https://cdn.example.com/img2.jpg', platform: 'Facebook', tone: 'Luxury' } }]
});

const normalizeFormData = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Normalize Form Data',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'nf-proj', name: 'projectName', value: expr('{{ $json.body?.projectName ?? $json.projectName ?? "" }}'), type: 'string' },
          { id: 'nf-feat', name: 'features', value: expr('{{ $json.body?.features ?? $json.features ?? "" }}'), type: 'string' },
          { id: 'nf-img', name: 'imageUrls', value: expr('{{ $json.body?.imageUrls ?? $json.imageUrls ?? "" }}'), type: 'string' },
          { id: 'nf-plat', name: 'platform', value: expr('{{ $json.body?.platform ?? $json.platform ?? "" }}'), type: 'string' },
          { id: 'nf-tone', name: 'tone', value: expr('{{ $json.body?.tone ?? $json.tone ?? "Professional" }}'), type: 'string' }
        ]
      }
    }
  },
  output: [{ projectName: 'Lakeside Villa', features: '5BR, pool, garden', imageUrls: 'https://cdn.example.com/img1.jpg', platform: 'Facebook', tone: 'Luxury' }]
});

const assembleData = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Assemble AI Prompt',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `const images = ($json.imageUrls || "").split(",").map(u => u.trim()).filter(Boolean);
const prompt = \`Generate a \${$json.tone} social media post for "\${$json.projectName}".
Key features: \${$json.features}.
Platform: \${$json.platform}.
Include a compelling headline, body text, and 3 hashtags.\`;

return [{
  ...$json,
  prompt,
  imageUrlsArray: images
}];`
    }
  },
  output: [{
    projectName: 'Lakeside Villa',
    features: '5BR, pool, garden',
    imageUrls: 'https://cdn.example.com/img1.jpg',
    platform: 'Facebook',
    tone: 'Luxury',
    prompt: 'Generate a Luxury social media post...',
    imageUrlsArray: ['https://cdn.example.com/img1.jpg']
  }]
});

const callAiContentApi = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Call AI Content API',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/content/generate'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'prompt', value: expr('{{ $json.prompt }}') },
          { name: 'projectName', value: expr('{{ $json.projectName }}') },
          { name: 'platform', value: expr('{{ $json.platform }}') },
          { name: 'tone', value: expr('{{ $json.tone }}') },
          { name: 'imageUrls', value: expr('{{ $json.imageUrlsArray }}') }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{
    success: true,
    content: {
      headline: 'Discover Luxury Living at Lakeside Villa',
      body: 'Experience unparalleled luxury...',
      hashtags: ['#LuxuryLiving', '#LakesideVilla', '#DreamHome'],
      suggestedImages: ['https://cdn.example.com/img1.jpg']
    }
  }]
});

const parseAndPresent = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Parse and Present Content',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'pc-headline', name: 'headline', value: expr('{{ $json.content.headline }}'), type: 'string' },
          { id: 'pc-body', name: 'body', value: expr('{{ $json.content.body }}'), type: 'string' },
          { id: 'pc-tags', name: 'hashtags', value: expr('{{ $json.content.hashtags }}') },
          { id: 'pc-images', name: 'images', value: expr('{{ $json.content.suggestedImages }}') },
          { id: 'pc-status', name: 'status', value: 'pending_approval', type: 'string' }
        ]
      }
    }
  },
  output: [{
    headline: 'Discover Luxury Living at Lakeside Villa',
    body: 'Experience unparalleled luxury...',
    hashtags: ['#LuxuryLiving'],
    images: ['https://cdn.example.com/img1.jpg'],
    status: 'pending_approval',
    projectName: 'Lakeside Villa',
    platform: 'Facebook',
    tone: 'Luxury'
  }]
});

const checkApproval = ifElse({
  version: 2.3,
  config: {
    name: 'Check Approval',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
        conditions: [
          { leftValue: expr('{{ $json.status }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'approved' }
        ],
        combinator: 'and'
      }
    }
  }
});

const scheduleContent = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Schedule Content',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/content/schedule'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'projectName', value: expr('{{ $json.projectName }}') },
          { name: 'platform', value: expr('{{ $json.platform }}') },
          { name: 'headline', value: expr('{{ $json.headline }}') },
          { name: 'body', value: expr('{{ $json.body }}') },
          { name: 'hashtags', value: expr('{{ $json.hashtags }}') },
          { name: 'images', value: expr('{{ $json.images }}') },
          { name: 'status', value: 'scheduled' }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, scheduleId: 'sched_001', status: 'scheduled' }]
});

const markPending = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Mark as Pending Approval',
    parameters: {
      method: 'POST',
      url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/content/pending'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      specifyBody: 'json',
      bodyParameters: {
        parameters: [
          { name: 'projectName', value: expr('{{ $json.projectName }}') },
          { name: 'headline', value: expr('{{ $json.headline }}') },
          { name: 'body', value: expr('{{ $json.body }}') },
          { name: 'status', value: 'pending_approval' }
        ]
      },
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') }
  },
  output: [{ success: true, pendingId: 'pend_001' }]
});

export default workflow('wf-content-generator', 'Content Generator')
  .add(formTrigger)
  .to(normalizeFormData)
  .to(assembleData)
  .to(callAiContentApi)
  .to(parseAndPresent)
  .to(checkApproval
    .onTrue(scheduleContent)
    .onFalse(markPending)
  );
