import { workflow, trigger, node, ifElse, expr, newCredential, placeholder } from '@n8n/workflow-sdk';

// ── Trigger: Form ──
const formTrigger = trigger('n8n-nodes-base.formTrigger', 2.6, {
  name: 'Content Generator Form',
  parameters: {
    formTitle: 'Generate Social Media Content',
    formDescription: 'Fill in the details to generate AI-powered social media content',
    formFields: {
      values: [
        {
          fieldType: 'text',
          fieldLabel: 'Project Name',
          placeholder: 'e.g., Lakeside Luxury Apartments',
          requiredField: true,
          parameterName: 'projectName',
        },
        {
          fieldType: 'textarea',
          fieldLabel: 'Project Features',
          placeholder: 'Describe key features (bedrooms, location, amenities...)',
          requiredField: true,
          parameterName: 'features',
        },
        {
          fieldType: 'text',
          fieldLabel: 'Image URL',
          placeholder: 'https://cdn.example.com/image.jpg',
          requiredField: false,
          parameterName: 'imageUrl',
        },
        {
          fieldType: 'text',
          fieldLabel: 'Target Audience',
          placeholder: 'e.g., first-time buyers, investors, families',
          requiredField: false,
          parameterName: 'targetAudience',
        },
        {
          fieldType: 'text',
          fieldLabel: 'Content Tone',
          placeholder: 'e.g., professional, casual, luxurious',
          requiredField: false,
          parameterName: 'tone',
        },
      ],
    },
    options: {
      respondWithWebhook: false,
      buttonLabel: 'Generate Content',
    },
  },
  output: [
    {
      projectName: 'Lakeside Luxury Apartments',
      features: '3BR, 4BR options, lake view, swimming pool, gym, 24/7 security',
      imageUrl: 'https://cdn.example.com/lakeside.jpg',
      targetAudience: 'families, investors',
      tone: 'luxurious',
    },
  ],
});

// ── Assemble AI Prompt ──
const assemblePrompt = node('n8n-nodes-base.set', 3.4, {
  name: 'Assemble AI Prompt',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'ap-prompt', name: 'prompt', value: expr('{{ "Generate a social media post for GLG Assets real estate.\\nProject: " + $json.projectName + "\\nFeatures: " + $json.features + "\\nTone: " + ($json.tone || "professional") + "\\nTarget: " + ($json.targetAudience || "general audience") + "\\nImage: " + ($json.imageUrl || "none") + "\\n\\nProvide: 1) Post caption 2) Hashtags 3) Best posting time" }}'), type: 'string' },
        { id: 'ap-project', name: 'projectName', value: expr('{{ $json.projectName }}'), type: 'string' },
        { id: 'ap-features', name: 'features', value: expr('{{ $json.features }}'), type: 'string' },
        { id: 'ap-image', name: 'imageUrl', value: expr('{{ $json.imageUrl || "" }}'), type: 'string' },
        { id: 'ap-audience', name: 'targetAudience', value: expr('{{ $json.targetAudience || "" }}'), type: 'string' },
        { id: 'ap-tone', name: 'tone', value: expr('{{ $json.tone || "professional" }}'), type: 'string' },
      ],
    },
  },
  output: [
    {
      prompt: 'Generate a social media post for...',
      projectName: 'Lakeside Luxury Apartments',
      features: '3BR, 4BR options, lake view, swimming pool, gym, 24/7 security',
      imageUrl: 'https://cdn.example.com/lakeside.jpg',
      targetAudience: 'families, investors',
      tone: 'luxurious',
    },
  ],
});

// ── Call AI Content API ──
const callAIContentAPI = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Call AI Content API',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/ai/content'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { prompt: $json.prompt, model: "gpt-4", maxTokens: 500 } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [
    {
      success: true,
      content: {
        caption: 'Discover luxury living at Lakeside Luxury Apartments...',
        hashtags: '#LuxuryLiving #LakeView #GLGAssets #RealEstate',
        bestTime: '10:00 AM - 12:00 PM',
        variations: [
          { caption: 'Option 2 caption...', hashtags: '#Luxury #RealEstate' },
          { caption: 'Option 3 caption...', hashtags: '#DreamHome' },
        ],
      },
    },
  ],
});

// ── Parse AI Response ──
const parseResponse = node('n8n-nodes-base.set', 3.4, {
  name: 'Parse AI Response',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'pr-caption', name: 'caption', value: expr('{{ $json.content.caption }}'), type: 'string' },
        { id: 'pr-hashtags', name: 'hashtags', value: expr('{{ $json.content.hashtags }}'), type: 'string' },
        { id: 'pr-time', name: 'bestTime', value: expr('{{ $json.content.bestTime }}'), type: 'string' },
        { id: 'pr-variations', name: 'variations', value: expr('{{ $json.content.variations }}'), type: 'array' },
        { id: 'pr-project', name: 'projectName', value: expr('{{ $json.projectName }}'), type: 'string' },
      ],
    },
  },
  output: [
    {
      caption: 'Discover luxury living at Lakeside Luxury Apartments...',
      hashtags: '#LuxuryLiving #LakeView #GLGAssets',
      bestTime: '10:00 AM - 12:00 PM',
      variations: [],
      projectName: 'Lakeside Luxury Apartments',
    },
  ],
});

// ── Check Approval (simulated via IF) ──
const checkApproval = ifElse({
  version: 2.3,
  config: {
    name: 'Approved?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
        conditions: [
          {
            id: 'approval-check',
            leftValue: expr('{{ $json.caption }}'),
            operator: { type: 'string', operation: 'notEmpty' },
            rightValue: '',
          },
        ],
        combinator: 'and',
      },
    },
  },
});

// ── Schedule Post ──
const schedulePost = node('n8n-nodes-base.httpRequest', 4.4, {
  name: 'Schedule Post via Platform API',
  parameters: {
    method: 'POST',
    url: expr('{{ $env.FASTAPI_BASE_URL }}/api/v1/social/schedule'),
    authentication: 'genericCredentialType',
    genericAuthType: 'httpHeaderAuth',
    sendBody: true,
    contentType: 'json',
    specifyBody: 'json',
    jsonBody: expr('{{ { projectName: $json.projectName, caption: $json.caption, hashtags: $json.hashtags, imageUrl: $json.imageUrl, scheduledFor: $json.bestTime, status: "approved" } }}'),
    options: {},
  },
  credentials: { httpHeaderAuth: newCredential('HTTP Header Auth') },
  output: [{ scheduleId: 'sch_001', status: 'scheduled' }],
});

// ── Needs Review ──
const needsReview = node('n8n-nodes-base.set', 3.4, {
  name: 'Mark for Review',
  parameters: {
    mode: 'manual',
    includeOtherFields: true,
    assignments: {
      assignments: [
        { id: 'nr-review', name: 'needsReview', value: true, type: 'boolean' },
        { id: 'nr-msg', name: 'message', value: 'Content generation failed - no caption returned', type: 'string' },
      ],
    },
  },
  output: [{ needsReview: true, message: 'Content generation failed - no caption returned' }],
});

// ── Build and Export ──
export default workflow('wf-content-generator', 'Content Generator')
  .description(
    'Admin fills a form with project name, features, images, and preferences. The workflow assembles an AI prompt, ' +
    'calls the AI content API, parses the response, and presents content options. On approval, ' +
    'it schedules the post via the platform API. If content generation fails, it marks the item for review.'
  )
  .onError('stopWorkflow')
  .add(formTrigger)
  .to(assemblePrompt)
  .to(callAIContentAPI)
  .to(parseResponse)
  .to(
    checkApproval
      .onTrue(schedulePost)
      .onFalse(needsReview)
  );
