## n8n Workflows: AI Engine + RAG Pipeline

### SWF-AI-Engine (ID: nTrLp9MPyaDEoTic)
**URL:** https://shown.app.n8n.cloud/workflow/nTrLp9MPyaDEoTic

- **Trigger:** Execute Workflow Trigger (subworkflow)
- **Inputs:** `message` (string), `conversation_id` (string), `system_message` (string, optional)
- **Nodes:**
  1. Execute Workflow Trigger — receives message + conversation_id
  2. OpenAI Chat Model — gpt-5-mini with response API enabled
  3. Conversation Memory — Buffer Window (10 turns, keyed by conversation_id)
  4. GLG AI Agent — LangChain Agent with custom system prompt
  5. Format Response — returns `{ reply, conversation_id, success }`
- **Credentials needed:** OpenAI API key ("OpenAI" credential name)

### SWF-RAG-Pipeline (ID: sZIJPhahE5Y7p1pX)
**URL:** https://shown.app.n8n.cloud/workflow/sZIJPhahE5Y7p1pX

- **Trigger:** Execute Workflow Trigger (subworkflow)
- **Inputs:** `query` (string), `conversation_id` (string), `top_k` (number, optional)
- **Nodes:**
  1. Execute Workflow Trigger — receives query + conversation_id
  2. OpenAI Embeddings — text-embedding-3-small (1536d)
  3. Property Knowledge Base — vectorStoreInMemory (retrieve mode)
  4. KB Retriever Tool — toolVectorStore wrapping vector store + model
  5. OpenAI Chat Model — gpt-5-mini
  6. RAG AI Agent — LangChain Agent with RAG system prompt
  7. Format Response — returns `{ reply, conversation_id, success }`
- **Credentials needed:** OpenAI API key ("OpenAI" credential name)

### Connection to Project
- **WF-Incoming-WhatsApp (Modular)** — updated to call SWF-AI-Engine
  - Passes `message` (from WhatsApp text), `conversation_id` (messageId), `system_message` (GLG-specific)
  - Output confidence check → auto-reply or human escalation

### SDK Source Files
- `automation/sdk/swf-ai-engine.ts`
- `automation/sdk/swf-rag-pipeline.ts`
