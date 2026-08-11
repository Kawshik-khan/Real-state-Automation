# GLG Assets — MVP Implementation Audit

**Date:** 2026-07-28  
**Audit scope:** Four core MVP services: Social Gateway, AI Engine, Knowledge Base, Automation

---

## MVP Four Core Services

### ✅ IMPLEMENTED

| Component | Status | Details |
|-----------|--------|---------|
| **POST /api/chat** | ✅ LIVE | Full AI pipeline: moderation → intent → agent routing → response |
| **POST /api/knowledge/upload** | ✅ LIVE | File + text upload, chunking, embedding, in-memory RAG store |
| **POST /api/moderation** | ✅ LIVE | LLM-based pre-check for spam/toxicity/PII |
| **POST /api/content** | ✅ LIVE | Content generation: captions, hashtags, descriptions |
| **POST /api/search** | ✅ LIVE | Semantic search across knowledge base |
| **GET /api/projects** | ✅ LIVE | Returns project list (from `SAMPLE_PROJECTS`) |
| **GET /api/project/{id}** | ✅ LIVE | Single project by name/location |
| **Supervisor Agent** | ✅ LIVE | LLM-based intent classification (8 intents) |
| **Property Agent** | ✅ LIVE | Keyword + LLM property search |
| **FAQ Agent** | ✅ LIVE | FAQ bank + LLM fallback |
| **Content Agent** | ✅ LIVE | Caption, hashtag, description generation |
| **Conversation Memory** | ✅ LIVE | In-memory, 20-turn, 24hr TTL |
| **26 n8n workflows** | ✅ IMPORTED | All channel workflows + subworkflows in local n8n |
| **DB Models** | ✅ DEFINED | 12 SQLAlchemy models (tenants, customers, conversations, messages, projects, inventory, leads, bookings, audit, events, outbox, inbox) |

### ⚠️ PARTIALLY IMPLEMENTED

| Component | Issue |
|-----------|-------|
| **Social Gateway** | Endpoints exist but return **canned stubs** — no actual Meta/WhatsApp API integration. No webhook receiving, no signature validation. |
| **RAG Pipeline** | In-memory only, no pgvector/PostgreSQL, no query rewriter, no hybrid search, no re-ranker |
| **LangGraph Orchestration** | Missing — uses manual if/else routing instead of an actual graph |
| **Structured JSON Response** | MVP spec shows `{"reply":"...", "actions":["send_images","send_brochure"]}` — current response includes actions but format doesn't match the spec |
| **n8n workflows** | All **inactive** (unpublished), untested — no live executions |
| **Slack/Telegram/Email escalation** | Stub endpoint returns canned response — not wired to real services |
| **Analytics** | Stub — returns hardcoded numbers (42 conversations, 38 resolved by AI) |

### ❌ MISSING

| Component | Required For |
|-----------|-------------|
| **Frontend** (admin, knowledge, analytics, conversations) | Not started — no `frontend/` directory |
| **LangGraph Supervisor** | MVP diagram shows LangGraph → Intent Engine → Memory Engine → Safety Layer → Agents |
| **pgvector + PostgreSQL** | All data is in-memory, no DB tables created, no alembic migrations |
| **Meta/WhatsApp Webhook validation** | No signature verification on incoming webhooks |
| **LlamaIndex integration** | MVP diagram shows LlamaIndex between RAG → pgvector |
| **Query rewriter + hybrid search** | MVP AI pipeline: Query Rewriter → Hybrid Search → Metadata Filter → Vector Search → Keyword Search → Re-rank |
| **Property Tool (SQL Search)** | MVP flow: "Show me ongoing projects" → Intent → Property Tool → SQL Search → RAG → LLM |
| **Human escalation routing** (Slack, Telegram, Email) | Stub only |
| **Analytics collection + nightly report** | Stub only |
| **Scheduled Posts / Content Generation approval** | Workflow exists but not wired |
| **Production secrets** | `automation_shared_secret` still `change-me-in-production` |
| **GPT/Claude switching** | Hardcoded to OpenAI only |
| **Safety Layer** | Moderation exists but no separate Safety Layer agent |
| **Send Images/Send PDF/Brochure** in reply | Not implemented in backend — relies on n8n, but n8n workflows are inactive |

---

## API Endpoints Coverage

| Endpoint | MVP Spec | Status |
|----------|----------|--------|
| `POST /api/chat` | ✔ | ✅ Live (full pipeline) |
| `POST /api/content` | ✔ | ✅ Live (captions/hashtags/descriptions) |
| `POST /api/knowledge/upload` | ✔ | ✅ Live (chunk + embed + index) |
| `POST /api/moderation` | ✔ | ✅ Live (LLM pre-check) |
| `GET /api/projects` | ✔ | ✅ Live (from sample data) |
| `GET /api/project/{id}` | ✔ | ✅ Live (name/location search) |
| `POST /api/search` | ✔ | ✅ Live (semantic search) |

---

## AI Pipeline Status

```
MVP Spec:                      Current Implementation:
┌─────────────────┐            ┌─────────────────┐
│ Incoming Message │     →     │ Incoming Message │
└────────┬────────┘            └────────┬────────┘
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ Conversation    │     →      │ Conversation    │  ✅
│ Memory          │            │ Memory (in-mem) │
└────────┬────────┘            └────────┬────────┘
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ Intent Detection│     ≈      │ Supervisor      │  ✅
└────────┬────────┘            │ (LLM classify)  │
         ▼                     └────────┬────────┘
┌─────────────────┐                     ▼
│ Query Rewriter  │     ✗     │ if/else routing │  ⚠️
├─────────────────┤            ┌────────┬────────┐
│ Hybrid Search   │     ✗          │         │
├─────────────────┤            ▼         ▼
│ Metadata Filter │     ✗   ┌──────┐ ┌──────┐
├─────────────────┤          │Prop  │ │ FAQ  │
│ Vector + Keyword│     ✗   │Agent │ │Agent │
├─────────────────┤          └──────┘ └──────┘
│ Re-rank         │     ✗
├─────────────────┤
│ Context Builder │     ≈     │ RAG Pipeline │
├─────────────────┤            (in-mem only)
│ Property Tool   │     ✗
├─────────────────┤
│ Context Merge   │     ✗
├─────────────────┤
│ LLM             │     ✅     │ OpenAI GPT-4o-mini │
├─────────────────┤
│ Safety Check    │     ≈     │ Moderation pre-check│
├─────────────────┤
│ Structured JSON │     ≈     │ ChatResponse model │
└─────────────────┘
```

---

## n8n Workflows (Local Instance — 22 Workflows)

| Workflow | Purpose | Status |
|----------|---------|--------|
| WF-Incoming-WhatsApp | WhatsApp message → backend | Inactive |
| WF-Facebook-Messenger | Facebook DM → backend | Inactive |
| WF-Instagram-DM | Instagram DM → backend | Inactive |
| WF-Website-Live-Chat | Website chat → backend | Inactive |
| WF-Knowledge-Upload | Admin upload → chunk → embed | Inactive |
| WF-Human-Escalation | Low confidence → Slack/Telegram/Email | Inactive |
| WF-Content-Generator | AI content generation | Inactive |
| WF-Moderation | Content moderation pipeline | Inactive |
| WF-Analytics | Daily report generation | Inactive |
| WF-Brochure-Sender | Send brochure on demand | Inactive |
| WF-Project-Images | Send property images | Inactive |
| WF-Scheduled-Posts | Scheduled social media posts | Inactive |
| SWF-AI-Engine | Core AI subworkflow (GPT + Memory) | Inactive |
| SWF-RAG-Pipeline | RAG retrieval subworkflow | Inactive |
| SWF-WhatsApp-Send | WhatsApp send message subworkflow | Inactive |
| SWF-Facebook-Send | Facebook send message subworkflow | Inactive |
| SWF-Instagram-Send | Instagram send message subworkflow | Inactive |
| SWF-AI-API-Caller | Backend API call subworkflow | Inactive |
| SWF-Error-Handler | Error handling subworkflow | Inactive |
| SWF-Log | Logging subworkflow | Inactive |
| SWF-Notification | Notification subworkflow | Inactive |
| SWF-Facebook-Send | Facebook send subworkflow | Inactive |

---

## Database Schema (Defined but no migrations)

| Table | Purpose |
|-------|---------|
| `tenants` | Multi-tenant support |
| `customers` | Customer profiles |
| `conversations` | Conversation threads |
| `messages` | Individual messages |
| `audit_logs` | Audit trail |
| `events` | Event bus |
| `outbox` | Outgoing messages queue |
| `inbox` | Incoming messages queue |
| `projects` | Real-estate projects |
| `inventory_units` | Individual units within projects |
| `leads` | Captured leads |
| `bookings` | Site visit bookings |

---

## Summary

- **Backend FastAPI: ~70% complete** for MVP — all endpoints exist, AI pipeline flows, agents wired
- **Critical gaps:** (1) No database persistence (in-memory only), (2) No Meta API integration (stubs), (3) No frontend, (4) n8n workflows inactive
- **Deliberately excluded (correct):** ERP, CRM, full accounting — outside MVP scope
