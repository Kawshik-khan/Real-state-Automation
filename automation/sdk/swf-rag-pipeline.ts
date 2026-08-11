import { workflow, trigger, node, languageModel, embedding, vectorStore, tool, expr, newCredential } from '@n8n/workflow-sdk';

const triggerNode = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.2,
  config: {
    name: 'Execute Workflow Trigger',
    parameters: {
      inputSource: 'workflowInputs',
      workflowInputs: { values: [
        { name: 'query', type: 'string' },
        { name: 'conversation_id', type: 'string' },
        { name: 'top_k', type: 'number' }
      ]}
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
    credentials: { openAiApi: newCredential('OpenAI') }
  }
});

const embeddingsOpenAi = embedding({
  type: '@n8n/n8n-nodes-langchain.embeddingsOpenAi',
  version: 1.2,
  config: {
    name: 'OpenAI Embeddings',
    parameters: {
      model: 'text-embedding-3-small',
      options: { dimensions: 1536 }
    },
    credentials: { openAiApi: newCredential('OpenAI') }
  }
});

const vectorStoreNode = vectorStore({
  type: '@n8n/n8n-nodes-langchain.vectorStoreInMemory',
  config: {
    name: 'Property Knowledge Base',
    parameters: { mode: 'retrieve', memoryKey: 'glg-rag-store' },
    subnodes: { embedding: embeddingsOpenAi }
  }
});

const retrieverTool = tool({
  type: '@n8n/n8n-nodes-langchain.toolVectorStore',
  config: {
    name: 'KB Retriever Tool',
    parameters: {
      description: 'GLG Assets property database, listings, and real estate knowledge base. Use for questions about properties, pricing, availability, and policies.',
      topK: expr('{{ $("Execute Workflow Trigger").item.json.top_k || 4 }}')
    },
    subnodes: { vectorStore: vectorStoreNode, model: openAiModel }
  }
});

const aiAgent = node({
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: 'RAG AI Agent',
    parameters: {
      promptType: 'define',
      text: expr('{{ $("Execute Workflow Trigger").item.json.query }}'),
      hasOutputParser: false,
      options: {
        systemMessage: 'You are a knowledgeable real estate assistant for GLG Assets. Answer questions using the knowledge base tool. If you don\'t find relevant information in the knowledge base, say so and offer general guidance. Always cite your sources when possible.',
        maxIterations: 8,
        enableStreaming: false
      }
    },
    subnodes: { model: openAiModel, tools: [retrieverTool] }
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
      assignments: { assignments: [
        { id: 'reply', name: 'reply', value: expr('{{ $json.output }}'), type: 'string' },
        { id: 'conversation_id', name: 'conversation_id', value: expr('{{ $("Execute Workflow Trigger").item.json.conversation_id }}'), type: 'string' },
        { id: 'success', name: 'success', value: true, type: 'boolean' }
      ]}
    }
  }
});

export default workflow('SWF-RAG-Pipeline', 'GLG Assets - RAG Pipeline')
  .add(triggerNode)
  .to(aiAgent)
  .to(formatResponse);
