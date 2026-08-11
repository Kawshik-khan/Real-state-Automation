import { workflow, trigger, node, languageModel, memory, tool, expr, newCredential } from '@n8n/workflow-sdk';

const triggerNode = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.2,
  config: {
    name: 'Execute Workflow Trigger',
    parameters: {
      inputSource: 'workflowInputs',
      workflowInputs: {
        values: [
          { name: 'message', type: 'string' },
          { name: 'conversation_id', type: 'string' },
          { name: 'system_message', type: 'string' }
        ]
      }
    }
  }
});

const openAiModel = languageModel({
  type: '@n8n/n8n-nodes-langchain.lmChatOpenAi',
  version: 1.3,
  config: {
    name: 'OpenAI Chat Model',
    parameters: {
      model: { __rl: true, mode: 'list', value: 'gpt-5-mini' },
      responsesApiEnabled: true
    },
    credentials: {
      openAiApi: newCredential('OpenAI')
    }
  }
});

const memoryNode = memory({
  type: '@n8n/n8n-nodes-langchain.memoryBufferWindow',
  version: 1.2,
  config: {
    name: 'Conversation Memory',
    parameters: {
      sessionIdType: 'customKey',
      sessionKey: expr('{{ $("Execute Workflow Trigger").item.json.conversation_id }}'),
      contextWindowLength: 10
    }
  }
});

const aiAgent = node({
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: 'GLG AI Agent',
    parameters: {
      promptType: 'define',
      text: expr('{{ $("Execute Workflow Trigger").item.json.message }}'),
      hasOutputParser: false,
      options: {
        systemMessage: expr('{{ $("Execute Workflow Trigger").item.json.system_message || "You are a helpful real estate assistant for GLG Assets. You help with property inquiries, customer service, and sales lead qualification. Be concise and professional." }}'),
        maxIterations: 10,
        enableStreaming: false,
        passthroughBinaryImages: true
      }
    },
    subnodes: {
      model: openAiModel,
      memory: memoryNode
    }
  }
});

const formatResponse = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Format Response',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'reply', name: 'reply', value: expr('{{ $json.output }}'), type: 'string' },
          { id: 'conversation_id', name: 'conversation_id', value: expr('{{ $("Execute Workflow Trigger").item.json.conversation_id }}'), type: 'string' },
          { id: 'success', name: 'success', value: true, type: 'boolean' }
        ]
      }
    }
  }
});

export default workflow('SWF-AI-Engine', 'GLG Assets - AI Engine')
  .add(triggerNode)
  .to(aiAgent)
  .to(formatResponse);
