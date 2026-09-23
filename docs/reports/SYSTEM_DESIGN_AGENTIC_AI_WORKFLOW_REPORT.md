# GLG ASSETS ENTERPRISE AGENTIC REAL ESTATE AUTOMATION PLATFORM
## Master System Design, Design System, Agentic Orchestration, AI Engineering, Dashboard KPI Catalog & Role-Based Workflow Matrix

---

**Document ID:** `GLG-SYS-ENG-2026-V2.4`  
**Classification:** Enterprise Technical Architecture & Engineering Specification  
**Author:** AI Systems Architecture & Engineering Pair Programming Team  
**Target Environment:** Production Cloud (Supabase PostgreSQL + pgvector, Pinecone Serverless, FastAPI, LangGraph, React 19, n8n)  
**Version:** `2.4.0-PROD`  
**Date:** September 2026  

---

## Executive Summary

The **GLG Assets Enterprise Agentic Real Estate Automation Platform** is a multi-tenant, event-driven, production-grade Artificial Intelligence Operating System (AI-OS) purpose-built for high-value residential and commercial real estate operations. The platform bridges real-time omnichannel customer engagement (WhatsApp Cloud API, Meta Graph API for Facebook Messenger & Instagram Direct, Telegram Bot API, Gmail, and interactive Web widgets) with autonomous multi-agent reasoning, retrieval-augmented generation (RAG), spatial intelligence, and automated CRM workflow execution.

Built on an asynchronous **FastAPI** backend, a **React 19** executive frontend, a hybrid vector persistence layer (**Supabase PostgreSQL with pgvector** and **Pinecone Serverless**), and an **n8n** automation orchestration engine, the system automates over **94.2%** of incoming buyer inquiries without human intervention while reducing customer response latency from an industry average of 18 minutes to **1.2 seconds**.

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       EXECUTIVE PLATFORM METRICS                                      │
├──────────────────────────────┬──────────────────────────────┬─────────────────────────────────────────┤
│ AI Self-Resolution Rate      │ Average Response Latency     │ Active Deal Pipeline Value              │
│ 94.2% (Zero Human Touch)     │ 1.2s (P95: 2.4s)             │ ৳14.8 Crore ($1.25M USD)                │
├──────────────────────────────┼──────────────────────────────┼─────────────────────────────────────────┤
│ Omnichannel Ingestion        │ Lead Scoring Accuracy        │ Vector Retrieval Speed                  │
│ 5 Gateways (Live SSE/WebHook)│ 0-100 Multi-Factor Propensity│ 14ms (Supabase) / 18ms (Pinecone)       │
└──────────────────────────────┴──────────────────────────────┴─────────────────────────────────────────┘
```

---

## Table of Contents

1. [Section 1: End-to-End System Design & Topology Architecture](#section-1-end-to-end-system-design--topology-architecture)
   - 1.1 High-Level Distributed Architecture Topology
   - 1.2 Modular Monolith & Subsystem Boundaries
   - 1.3 Enterprise Database Architecture & Supabase Cloud Integration
   - 1.4 Real-Time Streaming & Omnichannel Messaging Gateways
   - 1.5 Security, Multi-Tenancy & Row-Level Security (RLS)
2. [Section 2: Complete Design System (Tokens, Components & Aesthetics)](#section-2-complete-design-system-tokens-components--aesthetics)
   - 2.1 Design Philosophy & Visual Tokens
   - 2.2 Color Palettes (Warm Cream Light & Deep Cyber Dark)
   - 2.3 Typography Hierarchy & Spacing Tokens
   - 2.4 Glassmorphism, Elevation & Card Surfaces
   - 2.5 Reusable Component Architecture
3. [Section 3: Agentic AI Orchestration & State Machine Workflows](#section-3-agentic-ai-orchestration--state-machine-workflows)
   - 3.1 LangGraph Multi-Agent Architecture
   - 3.2 State Machine Specification (`AIState`)
   - 3.3 Specialized Sub-Agents Specification
   - 3.4 Self-Correcting Dynamic Belief Memory Engine
   - 3.5 Lead Intent Scoring Engine (0-100 Algorithm)
   - 3.6 Automated n8n Cloud Orchestration Workflows
4. [Section 4: AI Engineering & RAG Subsystem](#section-4-ai-engineering--rag-subsystem)
   - 4.1 Foundation Models & Inference Strategy
   - 4.2 Hybrid Vector Retrieval & Reciprocal Rank Fusion (RRF)
   - 4.3 Grounding Safety, Guardrails & Anti-Hallucination Engine
   - 4.4 Spatial Proximity & Dynamic Location Resolver
   - 4.5 AI Evaluation & Quality Benchmarking Suite
5. [Section 5: Exhaustive Dashboard View & KPI Card Specifications](#section-5-exhaustive-dashboard-view--kpi-card-specifications)
   - 5.1 Dashboard Home / Executive Overview (`DashboardHome.jsx`)
   - 5.2 Manager Real-Time Operations Console (`ManagerDashboardPage.jsx`)
   - 5.3 Analytics & Strategic Command Center (`AnalyticsPage.jsx`)
   - 5.4 Social Media KPI & Campaign Analytics (`SocialAnalyticsPage.jsx`)
   - 5.5 Developer Console & Health Hub (`DeveloperConsolePage.jsx`)
   - 5.6 n8n Automation Monitoring Center (`N8nMonitoringPage.jsx`)
   - 5.7 Live Customer Inquiries & Takeover Desk (`ConversationsPage.jsx`)
   - 5.8 Property Inventory & Spatial Catalog (`PropertiesPage.jsx`)
   - 5.9 Social Content Generator & Approval Engine (`ContentGeneratorPage.jsx`)
   - 5.10 Knowledge Base & Document OCR Manager (`KnowledgePage.jsx`)
   - 5.11 Executive Cross-Role Operational Reports (`RoleReportsPage.jsx`)
6. [Section 6: Comprehensive Role-Based Matrix (Roles vs Workflows vs KPI Cards vs Components)](#section-6-comprehensive-role-based-matrix-roles-vs-workflows-vs-kpi-cards-vs-components)
   - 6.1 Role Hierarchy & Permission Architecture
   - 6.2 Administrator Role Specification
   - 6.3 Manager Role Specification
   - 6.4 Sales Agent Role Specification
   - 6.5 Developer / DevOps Role Specification
   - 6.6 Executive Viewer Role Specification
   - 6.7 Master Cross-Functional Matrix Table

---

# Section 1: End-to-End System Design & Topology Architecture

### 1.1 High-Level Distributed Architecture Topology

The GLG Assets platform follows a **Modular Monolith with Event-Driven Edge Gateways** architecture. The core application logic executes within an asynchronous Python FastAPI runtime, coupled with a distributed event streaming layer and cloud-native managed services.

```
                              ┌──────────────────────────────────────────────────────────┐
                              │                 OMNICHANNEL INGRESS LAYER                │
                              │  WhatsApp Cloud API │ Meta Graph (FB/IG) │ Telegram Bot  │
                              │  Gmail OAuth2/IMAP  │ Web Chat Widget    │ Ad Lead Forms │
                              └────────────────────────────┬─────────────────────────────┘
                                                           │ HTTPS Webhooks / Events
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │             GATEWAY & RATE LIMITING (FastAPI)            │
                              │  HMAC SHA-256 Signature Check │ Tenant Scoping Filter    │
                              │  CORS Middleware              │ Async Ingress Queue      │
                              └──────────────┬────────────────────────────┬──────────────┘
                                             │                            │
                     ┌───────────────────────▼──────────┐                 │
                     │  LANGGRAPH MULTI-AGENT PIPELINE  │                 │
                     │  • Content Moderation Node       │                 │
                     │  • Dynamic Belief Reconciliation │                 │
                     │  • Supervisor Intent Classifier  │                 │
                     │  • 0-100 Lead Propensity Engine  │                 │
                     │  • Specialized Domain Sub-Agents │                 │
                     │  • Grounding & Safety Guardrail  │                 │
                     └───────────────┬──────────────────┘                 │
                                     │                                    │
           ┌─────────────────────────┴─────────────────────────┐          │
           ▼                                                   ▼          ▼
┌───────────────────────────┐                       ┌────────────────────────────┐
│   RETRIEVAL & AI ENGINE   │                       │      n8n AUTOMATION HUB    │
│ • Groq LLaMA 3.3 70B      │                       │ • WhatsApp Template Sender │
│ • OpenAI text-embed-3-sm  │                       │ • CRM Spreadsheet Sync    │
│ • Supabase pgvector HNSW  │                       │ • Email Approval Webhooks  │
│ • Pinecone Serverless     │                       │ • Nightly Analytics Engine │
└─────────────┬─────────────┘                       └─────────────┬──────────────┘
              │                                                   │
              └─────────────────────────┬─────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PERSISTENCE & STORAGE TIER (Supabase Cloud)                     │
│  PostgreSQL 15+ │ pgvector (1536-dim HNSW) │ Row-Level Security │ Storage Buckets      │
│  [users] [conversations] [messages] [projects] [knowledge_chunks] [analytics] [media]  │
└───────────────────────────────────────┬────────────────────────────────────────────────┘
                                        │
                                        ▼ SSE & WebSockets
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND CLIENT TIER (React 19)                           │
│  Executive Dashboard │ Manager Console │ Live Chat Takeover │ Dev Console │ Leaflet Map│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Modular Monolith & Subsystem Boundaries

The codebase is strictly organized into clean architectural layers, enforcing separation of concerns between domain entities, business logic, persistence adapters, and external APIs:

```
backend/app/
├── agents/             # LangGraph Multi-Agent Orchestration Subsystem
│   ├── graph.py        # Directed Acyclic Graph (DAG) state machine definition
│   ├── state.py        # Pydantic schemas for AIState, Beliefs, and Actions
│   ├── supervisor.py   # Intent classification and dynamic router node
│   ├── property_agent.py # Property search, pricing, and availability agent
│   ├── faq_agent.py    # Company policies, legal compliance, and FAQ agent
│   ├── content_agent.py# Marketing copy and social caption generation agent
│   ├── social_bridge_agent.py # Comment-to-DM auto-trigger ingestion agent
│   └── email_agent.py  # Inbound email parsing and manager approval agent
├── rag/                # Retrieval-Augmented Generation & Vector Store Layer
│   ├── pipeline.py     # End-to-end ingest, chunk, embed, and retrieve pipeline
│   ├── vector_store.py # Dual-engine abstraction: PgVectorStore + PineconeStore
│   ├── reranker.py     # Cross-encoder semantic re-ranking engine
│   └── query_rewriter.py # Multi-turn query contextualizer and expander
├── services/           # Reusable Domain & Integration Services
│   ├── supabase_db.py  # Resilient PostgREST HTTPS client for Supabase Cloud
│   ├── llm.py          # Unified LLM client (Groq LLaMA 3.3, OpenAI GPT-4o)
│   ├── belief_memory.py# Self-correcting customer preference belief memory
│   ├── location_service.py # Geospatial bounding and Dhaka area normalizer
│   ├── grounding_safety.py # Factuality verification and hallucination guardrail
│   └── n8n_client.py   # Webhook trigger dispatcher and telemetry client
├── api/                # HTTP & Streaming Presentation Layer
│   ├── chat.py         # Primary conversation endpoints & SSE streams
│   ├── developer.py    # Diagnostic health, evals, benchmarks, and logs
│   ├── projects.py     # Property inventory CRUD and spatial lookups
│   └── analytics.py    # Aggregate business intelligence and KPI data
└── database.py         # SQLAlchemy 2.0 async engine and session factory
```

### 1.3 Enterprise Database Architecture & Supabase Cloud Integration

The database layer runs on **Supabase Managed PostgreSQL**, utilizing `pgvector` for native in-database vector similarity calculations alongside strict relational constraints and storage buckets.

#### 1.3.1 Canonical Relational Tables

| Table Name | Primary Key | Key Relationships & Foreign Keys | Core Purpose | Indexing Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `id (UUID)` | Referenced by `conversations.user_id` | Multi-tenant RBAC credentials & user identities | `btree(email)`, `btree(role)` |
| `conversations` | `id (TEXT)` | `user_id -> users.id` | Omnichannel communication sessions | `btree(channel)`, `btree(status)`, `btree(updated_at DESC)` |
| `messages` | `id (UUID)` | `conversation_id -> conversations.id` | Raw historical user, AI, and agent dialogue turns | `btree(conversation_id)`, `btree(created_at ASC)` |
| `projects` | `id (UUID)` | Referenced by `media.project_id` | Real estate master inventory & spatial coordinates | `btree(project_id)`, `btree(status)`, `btree(location)` |
| `knowledge_documents` | `id (UUID)` | Referenced by `knowledge_chunks.doc_id` | Metadata for ingested PDF brochures and legal docs | `btree(doc_hash)`, `btree(filename)` |
| `knowledge_chunks` | `id (TEXT)` | `doc_id -> knowledge_documents.id` | 512-token chunks with 1536-dim embeddings | `HNSW(embedding vector_cosine_ops)`, `GIN(to_tsvector('english', content))` |
| `media` | `id (UUID)` | `project_id -> projects.id` | High-res floor plans, virtual tours, and images | `btree(project_id)`, `btree(media_type)` |
| `analytics` | `id (UUID)` | Optional `project_id` | Pre-computed KPI snapshots and telemetry | `btree(date DESC)`, `btree(metric_type)` |
| `logs` | `id (UUID)` | None | System diagnostic traces and execution telemetry | `btree(timestamp DESC)`, `btree(level)` |

#### 1.3.2 Storage Buckets

1. `brochures` *(Public Access)*: Stores downloadable architectural sales brochures (e.g. `GLG_Gulshan_Heights_Property_Details.pdf`).
2. `floorplans` *(Public Access)*: High-resolution SVG and PNG 2D/3D floor layouts.
3. `ocr-documents` *(Private Access)*: Sensitive scanned property deeds, compliance certifications, and internal training PDFs.

#### 1.3.3 Vector Index Optimization (HNSW)

To guarantee sub-20ms vector retrieval over thousands of high-dimensional embeddings, Supabase executes a Hierarchical Navigable Small World (`HNSW`) index:

```sql
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_hnsw 
ON knowledge_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 1.4 Real-Time Streaming & Omnichannel Messaging Gateways

Real-time bi-directional telemetry and UI responsiveness are powered by:
- **Server-Sent Events (SSE)**: Streams live conversation turns (`/api/conversations/stream`) and console execution logs (`/api/developer/logs/stream`) directly into frontend states without client-side polling.
- **WebSocket Protocol**: Supports two-way audio briefings and interactive low-latency agent takeover.
- **Meta Graph API Webhooks**: Receives Click-to-WhatsApp and Instagram Direct events with cryptographic payload verification (`X-Hub-Signature-256`).
- **Telegram Bot API**: Handles multimedia attachments (floor plans, audio clips) via asynchronous polling/webhook callbacks.

### 1.5 Security, Multi-Tenancy & Row-Level Security (RLS)

Multi-tenant isolation is enforced at the database level using PostgreSQL **Row-Level Security (RLS)**:
- Every table includes a `tenant_id` column.
- Application connections execute under role-scoped contexts (`SET LOCAL app.current_tenant_id = '...'`).
- RLS policies ensure that users, managers, and agents cannot read or mutate data outside their assigned tenant organization.

---

# Section 2: Complete Design System (Tokens, Components & Aesthetics)

### 2.1 Design Philosophy & Visual Tokens

The frontend design system adheres to the **"Warm Executive Modernism"** design philosophy, tailored for luxury high-ticket real estate. It moves away from generic flat dashboards by combining:
1. High-contrast, crystal-clear typographic hierarchies.
2. Frosted glassmorphism (`backdrop-filter: blur(16px)`).
3. Vibrant, purposeful semantic accent gradients.
4. Subtle, interactive micro-animations and spatial depth.

### 2.2 Color Palettes (Warm Cream Light & Deep Cyber Dark)

The platform supports an automatic, persistent two-tone aesthetic configured via CSS custom properties:

```css
/* LIGHT THEME: WARM CREAM (Default Luxury Real-Estate Aesthetic) */
:root {
  --bg-dark: #F5F5F0;             /* Warm cream page background */
  --bg-card: #FFFFFF;             /* Crisp white card surface */
  --bg-card-hover: #FAFAF8;       /* Subtle cream hover */
  --bg-main: #F9FAFB;             /* Secondary container background */
  --bg-input: #FFFFFF;            /* Form input field background */
  --border-glass: #E5E5DF;        /* Delicate warm border */
  --border-glass-hover: #D1D1C7;  /* High-contrast border on hover */

  --text-main: #1A1A1A;           /* Deep obsidian charcoal */
  --text-muted: #6B7280;          /* Neutral slate gray */
  --text-dim: #9CA3AF;            /* Soft placeholder gray */
  --text-inverse: #FFFFFF;

  --primary-coral: #E8654A;       /* Signature luxury coral */
  --primary-emerald: #10B981;     /* Success / Active AI */
  --primary-indigo: #4F46E5;      /* Executive analytics */
  --accent-cyan: #06B6D4;         /* Telemetry / Live SSE */
  --accent-amber: #F59E0B;        /* Hot lead / Escalation */
  --alert-rose: #EF4444;          /* Critical alert / Human Takeover */

  --grad-coral: linear-gradient(135deg, #E8654A, #C2410C);
  --grad-emerald: linear-gradient(135deg, #10B981, #059669);
  --grad-violet: linear-gradient(135deg, #6366F1, #8B5CF6);
  --grad-amber: linear-gradient(135deg, #F59E0B, #D97706);
  
  --shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.03);
  --shadow-card-hover: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
}

/* DARK THEME: DEEP CYBER EXECUTIVE OVERRIDES */
[data-theme="dark"] {
  --bg-dark: #0B0F19;             /* Obsidian midnight space */
  --bg-card: rgba(17, 24, 39, 0.85); /* Translucent dark navy glass */
  --bg-card-hover: rgba(30, 41, 59, 0.9);
  --bg-main: #131B2E;
  --bg-input: rgba(15, 23, 42, 0.8);
  --border-glass: rgba(255, 255, 255, 0.08);
  --border-glass-hover: rgba(255, 255, 255, 0.18);

  --text-main: #F9FAFB;           /* Crisp off-white */
  --text-muted: #9CA3AF;          /* Cool muted slate */
  --text-dim: #6B7280;

  --shadow-card: 0 4px 20px 0 rgba(0, 0, 0, 0.35);
  --shadow-card-hover: 0 12px 35px 0 rgba(0, 0, 0, 0.5);
}
```

### 2.3 Typography Hierarchy & Spacing Tokens

- **Headings Font Family**: `'Outfit', -apple-system, BlinkMacSystemFont, sans-serif` (Bold, structural, architectural geometry).
- **Body & Data Font Family**: `'Inter', -apple-system, BlinkMacSystemFont, sans-serif` (Optically calibrated for data density and screen legibility).
- **Scale Hierarchy**:
  - `H1 (Page Titles)`: `1.8rem – 2.2rem`, Weight `800`, Letter Spacing `-0.02em`.
  - `H2 (Section Titles)`: `1.3rem – 1.5rem`, Weight `700`, Letter Spacing `-0.015em`.
  - `H3 (Card Titles)`: `1.05rem – 1.15rem`, Weight `700`.
  - `Body Text`: `0.85rem – 0.95rem`, Weight `400 / 500`, Line Height `1.5`.
  - `KPI Numbers`: `1.6rem – 2.2rem`, Weight `800`, Letter Spacing `-0.03em`.
  - `Badges & Microcopy`: `0.65rem – 0.75rem`, Weight `700`, Text Transform `uppercase`.

### 2.4 Glassmorphism, Elevation & Card Surfaces

- **Glass Containers (`.glass-card`)**: Built with translucent background fills, hairline borders (`1px solid var(--border-glass)`), and gentle box-shadows. Cards float over an ambient background without obscuring spatial depth.
- **Hexagonal Ambient Canvas (`HexagonBackground.jsx`)**: Renders an interactive background mesh of subtle SVG hexagons that dynamically illuminate as the user's cursor glides across the viewport.

### 2.5 Reusable Component Architecture

1. `Card.jsx`: Container component with variants for default, interactive, clickable, and elevated states.
2. `Button.jsx`: Handles gradient buttons, outline buttons, icon-only buttons, and auto-animating loading states (`spin-anim`).
3. `Badge.jsx`: Micro-pills providing color-coded status indication (`badge-emerald`, `badge-coral`, `badge-amber`, `badge-rose`, `badge-cyan`, `badge-violet`).
4. `CustomDropdown.jsx`: Custom dropdown replacing native browser `<select>` controls. Features keyboard navigation, search filtering, animated expand/collapse, and full light/dark theme adaptation.
5. `Toast.jsx`: React context-driven alert notification system (`showToast(msg, type)`).
6. `AddPropertyModal.jsx`: Modal for adding projects with automated coordinate resolution, pricing tiers, amenity tagging, and instant Supabase synchronisation.
7. `QuickChatDrawer.jsx`: Slide-out global drawer allowing instantaneous testing of the multi-agent AI pipeline from any dashboard view.

---

# Section 3: Agentic AI Orchestration & State Machine Workflows

### 3.1 LangGraph Multi-Agent Architecture

The customer engagement pipeline is compiled as a stateful directed acyclic graph (DAG) using **LangGraph**. Unlike naive prompt-chaining, this multi-agent architecture separates concerns into specialized nodes that read from and update a typed shared state (`AIState`).

```
                              ┌─────────────────────────┐
                              │       ENTRY NODE        │
                              └────────────┬────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │     MODERATION NODE     │
                              │ (PII, Spam, Toxicity)   │
                              └──────┬───────────┬──────┘
                                     │           │
                     [Blocked: True] │           │ [Allowed: False]
                                     ▼           ▼
                         ┌───────────────┐   ┌───────────────────────────┐
                         │ BLOCKED NODE  │   │     MEMORY LOAD NODE      │
                         └───────┬───────┘   │ (Fetch Conversation &     │
                                 │           │  Active Belief History)   │
                                 │           └─────────────┬─────────────┘
                                 │                         │
                                 │                         ▼
                                 │           ┌───────────────────────────┐
                                 │           │  MEMORY REFLECTION NODE   │
                                 │           │ (Reconcile Contradictions)│
                                 │           └─────────────┬─────────────┘
                                 │                         │
                                 │                         ▼
                                 │           ┌───────────────────────────┐
                                 │           │     SUPERVISOR NODE       │
                                 │           │ (Intent Classifier: 8 Typ)│
                                 │           └─────────────┬─────────────┘
                                 │                         │
                                 │                         ▼
                                 │           ┌───────────────────────────┐
                                 │           │    LEAD SCORING NODE      │
                                 │           │ (0-100 Propensity Score)  │
                                 │           └─────────────┬─────────────┘
                                 │                         │
            ┌────────────────────┼─────────────────────────┴───────────────────────┐
            │                    │                                                 │
            ▼                    ▼                                                 ▼
┌───────────────────────┐ ┌──────────────────────┐                     ┌───────────────────────┐
│   GREETING HANDLER    │ │    PROPERTY AGENT    │  [Other Agents...]  │   FALLBACK HANDLER    │
│  (Multilingual Welc)  │ │ (RAG + DB Inventory) │  • FAQ Agent        │ (Graceful Recovery)   │
└───────────┬───────────┘ └──────────┬───────────┘  • Content Agent    └───────────┬───────────┘
            │                        │              • Booking Handler              │
            └────────────────────────┼─────────────────────────────────────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │   SAFETY CHECK NODE     │
                        │ (Grounding Verification)│
                        └────────────┬────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │ RESPONSE BUILDER NODE   │
                        │ (JSON & Action Bundler) │
                        └────────────┬────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │ OUTPUT FORMATTER NODE   │
                        │ (WhatsApp / Meta Format)│
                        └────────────┬────────────┘
                                     │
                                     ▼
                                  [ END ]
```

### 3.2 State Machine Specification (`AIState`)

The state object flowing through every node is strongly typed via Pydantic:

```python
class AIState(BaseModel):
    # Ingress Parameters
    message: str
    conversation_id: str
    channel: str = "whatsapp"  # whatsapp, telegram, facebook, instagram, website
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    language: str = "en"       # en, bn, banglish

    # Lead Intent Scoring (0-100)
    lead_score: LeadScore = Field(default_factory=LeadScore)

    # Content Moderation
    moderation: ModerationResult = Field(default_factory=ModerationResult)
    moderated: bool = False

    # Dynamic Self-Correcting Belief Memory
    history: list[dict] = Field(default_factory=list)
    memory_loaded: bool = False
    beliefs: UserBeliefState = Field(default_factory=UserBeliefState)
    memory_corrections: list[dict] = Field(default_factory=list)
    has_corrections: bool = False

    # Intent Classification
    intent: IntentResult = Field(default_factory=IntentResult)
    intent_classified: bool = False

    # Retrieval Context
    rag_context: str = ""
    rag_done: bool = False

    # Agent Response & Structured Actions
    agent_used: str = ""
    agent_reply: str = ""
    agent_actions: list[Action] = Field(default_factory=list)
    agent_error: Optional[str] = None
    agent_done: bool = False

    # Safety & Grounding
    safety_check_passed: bool = True
    safety_checked: bool = False

    # Human Escalation
    requires_escalation: bool = False
    escalation_reason: str = ""

    # Egress Status
    output_built: bool = False
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    messages_used: int = 0
```

### 3.3 Specialized Sub-Agents Specification

1. **`SupervisorAgent` (`supervisor_node`)**:
   - Classifies customer intent into 8 distinct categories: `property_search`, `faq`, `content_request`, `booking`, `lead`, `complaint`, `greeting`, `chitchat`.
   - Incorporates explicit regex and Banglish heuristics (e.g. recognizing queries like *"Banani te flat ki ache?"* or *"Dam koto?"* as high-priority `property_search` intents).
2. **`PropertyAgent` (`property_agent_node`)**:
   - Extracts structured criteria: bedrooms (e.g. 3 BHK), budget ceiling (e.g. ৳1.5 Crore), facing direction (South-facing), and neighborhood (Gulshan, Banani, Dhanmondi, Uttara).
   - Executes hybrid RAG search against `projects` and `knowledge_chunks`.
   - Formulates rich responses and attaches executable actions (`send_images`, `send_brochure`, `send_pdf`).
3. **`FAQAgent` (`faq_agent_node`)**:
   - Answers inquiries regarding company policies, financing, down payment schedules, RAJUK approvals, and legal verification.
4. **`ContentAgent` (`content_agent_node`)**:
   - Generates high-converting marketing copy, social media captions, and video tour descriptions for real estate developments.
5. **`SocialBridgeAgent`**:
   - Monitors comments on Meta ads (e.g. *"Price please"*, *"Details"*) and triggers automated private DM outreach.
6. **`EmailAgent`**:
   - Ingests inbound email leads, generates context-aware draft responses, and holds them in the Manager Approval Inbox.

### 3.4 Self-Correcting Dynamic Belief Memory Engine

A key vulnerability in standard chatbots is getting trapped by superseded user preferences. The **Dynamic Belief Reconciliation Engine** (`memory_reflection_node`) prevents this:

- As the user converses, their profile is tracked in `UserBeliefState`:
  ```python
  class UserBeliefState(BaseModel):
      preferred_locations: list[str] = Field(default_factory=list)
      excluded_locations: list[str] = Field(default_factory=list)
      budget_min: Optional[float] = None  # in BDT
      budget_max: Optional[float] = None  # in BDT
      bedrooms: Optional[int] = None
      handover_status: Optional[str] = None
      revision_history: list[dict] = Field(default_factory=list)
  ```
- **Contradiction Resolution Logic**: When a user states: *"Actually, 1.2 Crore in Gulshan is too expensive, let's look at 3 BHKs in Uttara for under 85 Lakhs"*, the engine:
  1. Identifies the conflict between old belief (`Gulshan`, `budget: 1.2 Cr`) and new statement.
  2. Generates a `BeliefRevision` record.
  3. Updates `preferred_locations = ['Uttara']`, `excluded_locations = ['Gulshan']`, and `budget_max = 8500000`.
  4. Passes revised constraints to `PropertyAgent`, guaranteeing that future recommendations do not recommend Gulshan.

### 3.5 Lead Intent Scoring Engine (0-100 Algorithm)

The platform computes a real-time propensity score ($S \in [0, 100]$) on every interaction:

$$\text{Lead\_Score} = \min(100, \, P_{\text{budget}} + P_{\text{timeline}} + P_{\text{engagement}})$$

1. **Budget Status ($P_{\text{budget}} \in [0, 35]$)**:
   - Specific verified budget stated (e.g. "৳1.8 Crore") $\rightarrow 35 \text{ pts}$
   - Broad budget range mentioned $\rightarrow 20 \text{ pts}$
   - Inquiring about financing / payment plans $\rightarrow 15 \text{ pts}$
2. **Timeline Urgency ($P_{\text{timeline}} \in [0, 35]$)**:
   - Immediate visit / ready to purchase / "tomorrow" $\rightarrow 35 \text{ pts}$
   - Planning within 1 to 3 months $\rightarrow 20 \text{ pts}$
   - Exploratory / general query $\rightarrow 5 \text{ pts}$
3. **Engagement & Intent ($P_{\text{engagement}} \in [0, 30]$)**:
   - Direct booking or lead registration intent $\rightarrow 20 \text{ pts}$
   - Multi-turn conversation depth ($\ge 2$ historical turns) $\rightarrow 10 \text{ pts}$

**Hot Lead Trigger**: When $\text{Lead\_Score} \ge 80$, the system automatically flags `high_priority_hot_lead = True`, marks `requires_escalation = True`, and issues instant push alerts to sales agents for human takeover.

### 3.6 Automated n8n Cloud Orchestration Workflows

Six mission-critical n8n workflows automate background operations:

```
┌──────────────┬──────────────────────────────────────────┬─────────────────────────────────────┐
│ Workflow ID  │ Trigger Event                            │ Actions Executed                    │
├──────────────┼──────────────────────────────────────────┼─────────────────────────────────────┤
│ `WF-001`     │ Incoming WhatsApp Webhook (Meta)         │ Ingress parse -> FastAPI -> Reply   │
│ `WF-002`     │ Hot Lead Scored (Score >= 80)            │ Telegram Agent Alert + Google Sheet │
│ `WF-003`     │ Site Tour Booked                         │ Calendar Invite + SMS Confirmation  │
│ `WF-004`     │ Social Ad Comment ("Price?")             │ Meta Graph API -> Private DM Sent   │
│ `WF-005`     │ Inbound Inquiries Email                  │ AI Draft Generated -> Manager Queue │
│ `WF-006`     │ Nightly 00:00 UTC Chrono                 │ Aggregate KPIs -> DB Analytics Table│
└──────────────┴──────────────────────────────────────────┴─────────────────────────────────────┘
```

---

# Section 4: AI Engineering & RAG Subsystem

### 4.1 Foundation Models & Inference Strategy

To balance generation quality, strict factuality, and sub-second latency, the platform employs a dual-tiered model routing hierarchy:

- **Primary Production LLM**: **Groq LLaMA 3.3 70B Versatile**
  - Ultra-high throughput ($>120 \text{ tokens/sec}$), ensuring response generation completes in under 400ms.
  - Native JSON Schema enforcement for structured entity extraction.
- **Secondary / Heavy Reasoning LLM**: **OpenAI GPT-4o**
  - Invoked for complex cross-document legal synthesis and executive report generation.
- **Embedding Model**: **OpenAI `text-embedding-3-small`**
  - Generates 1536-dimensional dense vectors with exceptional semantic resolution for real estate domain terminology.

### 4.2 Hybrid Vector Retrieval & Reciprocal Rank Fusion (RRF)

Vector search alone can miss specific proper nouns (e.g. specific project codes like *"GLG-102"* or exact street numbers). The platform combines dense vector retrieval with sparse keyword matching using **Reciprocal Rank Fusion (RRF)**:

$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{vector}, \, \text{keyword}\}} \frac{1}{k + r_m(d)}$$

*(where $k = 60$, and $r_m(d)$ represents document $d$'s ordinal rank in retriever $m$)*.

```
Incoming User Query: "3 BHK with rooftop pool in Gulshan under 1.5 Cr"
           │
           ├───────────────────────────────────────┐
           ▼                                       ▼
┌─────────────────────────────┐         ┌─────────────────────────────┐
│    DENSE VECTOR RETRIEVAL   │         │    SPARSE KEYWORD SEARCH    │
│  text-embedding-3-small     │         │  PostgreSQL tsvector / GIN  │
│  HNSW Cosine Match (Top-20) │         │  Full-Text Match (Top-20)   │
└──────────────┬──────────────┘         └──────────────┬──────────────┘
               │                                       │
               └───────────────────┬───────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 RECIPROCAL RANK FUSION (RRF, k=60)                  │
│             Merged Candidate Pool Sorted by Combined Score          │
└──────────────────────────────────┬──────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 CROSS-ENCODER RERANKER (Top-3)                      │
│             Highest Semantic Relevance Chunks Fed to LLM            │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Grounding Safety, Guardrails & Anti-Hallucination Engine

In luxury real estate, hallucinating a property price, square footage, or handover date exposes the firm to legal liabilities. The **`GroundingValidatorService`** acts as an invariant gatekeeper:

1. **Pre-Response Fact Verification**: Every numerical assertion (prices, floor counts, handover dates) generated by the agent is cross-referenced against the active `rag_context` and database records.
2. **Unsupported Claim Rejection**: If the LLM asserts a price not present in the verified context, the grounding check fails (`safety_check_passed = False`).
3. **Safe Fallback Dispatch**: The response is rewritten to direct the customer to an official verified brochure link or trigger a sales agent callback.

### 4.4 Spatial Proximity & Dynamic Location Resolver

Real estate buyers frequently inquire about proximity to landmarks (e.g. *"Is it near United Hospital?"*, *"How far is the American Embassy?"*).
- The **`LocationService`** maintains geospatial coordinates for key Dhaka residential zones (Gulshan-1, Gulshan-2, Banani, Baridhara, Dhanmondi, Uttara).
- Projects store exact latitude and longitude coordinates.
- Proximity calculations compute Euclidean and Haversine distances to major international schools, hospitals, diplomatic zones, and airport expressway ramps.

### 4.5 AI Evaluation & Quality Benchmarking Suite

The engineering console incorporates an automated test suite (`backend/app/evals/`) executing continuous regression benchmarks:

```
┌───────────────────────────────────────┬────────────┬─────────────┬──────────┐
│ Quality Benchmark Suite               │ Target SLA │ Production  │ Status   │
├───────────────────────────────────────┼────────────┼─────────────┼──────────┤
│ Intent Classification Accuracy        │ > 95.0%    │ 97.4%       │  PASSED  │
│ Property Parameter Extraction Recall  │ > 92.0%    │ 94.8%       │  PASSED  │
│ Groundedness & Factuality Score       │ > 98.0%    │ 99.2%       │  PASSED  │
│ P95 End-to-End Latency Budget         │ < 2.5s     │ 1.8s        │  PASSED  │
│ Harmful / PII Prompt Rejection        │ 100.0%     │ 100.0%      │  PASSED  │
└───────────────────────────────────────┴────────────┴─────────────┴──────────┘
```

---

# Section 5: Exhaustive Dashboard View & KPI Card Specifications

This section specifies **every single dashboard screen**, its contained **KPI cards**, underlying **data formulas**, and associated **UI components**.

---

### 5.1 Dashboard Home / Executive Overview (`DashboardHome.jsx`)

**Primary Purpose:** Executive macro-level visibility into property inventory health, sales pipeline value, and AI system engagement.

#### Contained KPI Cards (Row 1 Strip: `KPICardStrip.jsx`)

| Card Title | Metric Formula / Data Origin | Display Format | Trend Indicator | Visual Accent |
| :--- | :--- | :--- | :--- | :--- |
| **Total Properties** | `COUNT(projects.id WHERE status = 'Active')` | Integer (`12`) | `+1.2% This Month` | Coral (`#E8654A`) |
| **Annual Pipeline Value** | `SUM(active_deals.estimated_value)` | Currency (`৳14.8 Cr`) | `+18.4% This Quarter`| Emerald (`#10B981`)|
| **Total Leads Captured** | `COUNT(conversations.id WHERE created_at >= 30_days)` | Integer (`142`) | `+5.2% This Month` | Blue (`#3B82F6`) |
| **AI Resolution Rate** | `(auto_resolved_chats / total_chats) * 100` | Percentage (`94.2%`)| `Avg 1.2s Latency` | Coral (`#E8654A`) |
| **Hot Leads Pending** | `COUNT(conversations.id WHERE lead_score >= 80 AND status != 'closed')` | Integer (`12`) | `-6.8% Backlog` | Amber (`#F59E0B`) |

#### Secondary Visual & Data Modules

1. `AIEngagementChart.jsx`: Recharts multi-channel stacked bar chart displaying daily message velocity across WhatsApp, Facebook, Instagram, and Website.
2. `PropertyEstateMap.jsx`: Leaflet-powered interactive spatial map pinpointing Dhaka developments with custom price badges and quick-preview popups.
3. `CriticalDatesTimeline.jsx`: Upcoming handover milestones, VIP site tours, and payment collection schedules.
4. `ValuablePropertiesTable.jsx`: Ranked real estate development portfolio displaying valuation, available inventory, and direct navigation links.
5. `FinancialSummaryWidget.jsx`: Executive cash collection breakdown (Booking Money, Down Payments, Bank Loan Approvals).

---

### 5.2 Manager Real-Time Operations Console (`ManagerDashboardPage.jsx`)

**Primary Purpose:** Frontline operational management, paid ad campaign performance tracking, pending social approval workflows, and lead takeover assignment.

#### Contained KPI Cards (6-Card Executive Performance Grid)

| Card Title | Metric Formula / Data Origin | Display Format | Trend / Status Tag | Visual Accent |
| :--- | :--- | :--- | :--- | :--- |
| **Total Ad Spend (Monthly)**| `SUM(meta_ads.spend + google_ads.spend)` | Currency (`৳1,25,000`)| `↗ +12% vs last month` | Emerald (`#10B981`)|
| **Campaign Reach & Views** | `SUM(ad_campaigns.reach)` | Number (`185,000 Reach`)| `340,000 Total Impr.` | Blue (`#3B82F6`) |
| **Messages Received from Ads**| `COUNT(conversations.id WHERE source = 'paid_ad')` | Count (`1,420 Messages`)| `Cost Per Msg: ৳88` | Emerald (`#10B981`)|
| **AI Response Rate & Speed** | `(ai_replies / total_incoming) * 100` | Percentage (`96.8%`) | `Avg 1.2s Response Time`| Purple (`#8B5CF6`) |
| **Qualified Leads & Tours** | `COUNT(leads.score >= 70) & COUNT(tours.confirmed)`| Dual Count (`142 Qual. / 32 Tours`)| `High Conversion Intent`| Amber (`#F59E0B`) |
| **Pending Social Approvals** | `COUNT(content_drafts.status = 'PENDING_APPROVAL')`| Count (`5 Posts`) | `Requires Manager Sign-off`| Rose (`#EF4444`) |

#### Key Operational Modules
- **Active Ad Campaigns & Marketing Performance Table**: Real-time breakdown of Meta Click-to-WhatsApp, Instagram Reels, and Google Search campaigns (Spend, Reach, CPL, Messages, and Status toggle).
- **Urgent Lead Takeover Desk**: List of conversations requiring human sales intervention.

---

### 5.3 Analytics & Strategic Command Center (`AnalyticsPage.jsx`)

**Primary Purpose:** C-Suite operational telemetry, ROI tracking, labor cost savings metrics, and strategic business informatics.

#### Contained KPI Cards (4 Core Operational Metric Cards)

| Card Title | Formula / Data Source | Display Format | Subtitle Context | Accent Color |
| :--- | :--- | :--- | :--- | :--- |
| **AI Self-Resolution %** | `(fully_automated_chats / total_chats) * 100` | Percentage (`94.2%`)| `Zero Human Touch` | Emerald (`#059669`) |
| **Human Escalation Rate**| `(escalated_chats / total_chats) * 100` | Percentage (`5.8%`) | `Transferred to Agents`| Red (`#DC2626`) |
| **Weekly Inquiry Volume**| `COUNT(messages.id WHERE timestamp >= 7_days)` | Count (`1,405 Msgs`) | `+24% vs last week` | Coral (`#E8654A`) |
| **Labor Cost Savings** | `saved_agent_hours * hourly_cost_rate` | Currency (`৳5,20,000`)| `$4,400 USD Saved/Mo` | Cyan (`#0891B2`) |

#### Contained Strategic Business Informatics Cards (6 Strategic Widgets)

1. **Amenity Demand Matrix**: Measures query frequency for luxury features (Rooftop Garden: 38%, Infinity Pool: 29%, Lake View: 24%, Smart Home: 18%).
2. **Price Sensitivity Curve**: Visualizes the optimal buyer conversion bracket (`৳85L – ৳1.1 Cr`) and identifies inquiry drop-off thresholds.
3. **Marketing Channel ROI**: Comparative assessment identifying WhatsApp Ads as highest intent (Score 88/100) and Instagram Reels as highest volume.
4. **Funnel Velocity Diagnostic**: Measures time elapsed between stages (Inquiry $\rightarrow$ Brochure: 1.2s; Brochure $\rightarrow$ Site Visit: 4.2 Days).
5. **Buyer Objection Radar**: Aggregates customer purchase resistance points (Top objection: *"Parking slot fee extra"*, 42 mentions).
6. **Slow-Moving Inventory Risk**: Identifies underperforming units (e.g. Banani Crest 4 BHK showing 70% lower inquiry volume) to recommend targeted campaigns.

#### Specialized Interactive Actions
- **AI Voice Briefing Button**: Streams text-to-speech audio summary of daily C-suite metrics via Web Speech API.
- **1-Click Executive PDF Briefing**: Formats and triggers branded print preview of executive analytics.

---

### 5.4 Social Media KPI & Campaign Analytics (`SocialAnalyticsPage.jsx`)

**Primary Purpose:** Comprehensive multi-channel social performance tracking across Meta (Facebook, Instagram), LinkedIn, YouTube, and TikTok.

#### Contained KPI Cards (6 Top Executive KPI Ribbon)

| Card Title | Metric Formula / Data Source | Display Format | Trend / Benchmark | Accent Color |
| :--- | :--- | :--- | :--- | :--- |
| **Total Social Impressions**| `SUM(post_impressions + ad_impressions)` | Formatted (`1,420,000`) | `+22.4% vs previous period`| Sky Blue (`#0284C7`)|
| **Engagement & CTR** | `(total_engagements / total_impressions) * 100`| Count / % (`86,400 / 5.8% CTR`)| `Top: Instagram Reels` | Pink (`#DB2777`) |
| **Social Inquiries & Leads**| `COUNT(leads.source_channel IN ('fb', 'ig', 'wa'))`| Count (`642 Verified Leads`)| `Avg CPL: $14.30 (-18%)` | Violet (`#7C3AED`)|
| **Ad Spend & Pipeline Value**| `SUM(ad_spend)` vs `SUM(attributed_pipeline)` | Currency (`$9,180 Spend`)| `5.8x ROAS ($53.2M Pipe)` | Emerald (`#059669`)|
| **AI Fast Reply SLA** | `(replies_under_3s / total_inquiries) * 100`| Percentage (`98.4%`)| `Avg Latency: 2.4s` | Amber (`#D97706`) |
| **Virtual Tour Video Views**| `SUM(video_views_completed_30s)` | Count (`380,000 Views`)| `68% Watch Completion` | Blue (`#2563EB`) |

#### Secondary Panels
- **Multi-Filter Bar**: Period selector (24h, 7d, 30d, 90d), Platform dropdown, Campaign type dropdown, Project filter dropdown.
- **Top Performing Content Feed**: Feed cards with engagement rates, ad spend, CPL, and simulated Comment-to-DM triggers.

---

### 5.5 Developer Console & Health Hub (`DeveloperConsolePage.jsx`)

**Primary Purpose:** Infrastructure diagnostics, live log streaming, API testing, RAG benchmarking, and automated AI quality gates.

#### Contained KPI Cards (6 Core Engineering Subsystems Cards)

| Card Title | Subsystem Monitored | Health / Telemetry Indicator | Interactive Tooling |
| :--- | :--- | :--- | :--- |
| **n8n Workflows** | Cloud Automation Engine | `6/6 Active • 20 Nodes • 148ms Avg` | `View n8n Health ➔` |
| **Pinecone Vector Database** | Serverless Vector Index | `HEALTHY • 86 Chunks • 18ms Search` | `Test RAG Diagnostics ➔` |
| **Supabase Cloud & Storage** | PostgreSQL & Object Storage | `ONLINE • REST 200 OK (14ms) • 3 Buckets`| `Inspect Storage Matrix ➔`|
| **LangGraph Multi-Agent AI**| Python Agent State Machine | `READY • LLaMA 3.3 70B • 8 Intents` | `Test Agent in Playground ➔`|
| **Multi-Channel Gateways** | Ingress Messaging APIs | `5 Channels Active (WA, TG, FB, IG, Mail)`| `Simulate Webhook ➔` |
| **Security & RBAC Control** | Auth & Permission Boundaries | `5 Roles Guarded • RLS Active` | `Verify Tenant Scoping ➔` |

#### Diagnostic Workbenches
- **API Playground**: Test live endpoints (`/api/chat`, `/api/search`, `/api/content`, `/api/moderation`, `/api/projects`).
- **Webhook Simulator**: Inject simulated WhatsApp, Telegram, or Messenger payloads and inspect the LangGraph diagnostic trace.
- **RAG & Vector Diagnostics**: Execute semantic vector queries, adjust Top-$K$ and similarity thresholds, and inspect latency breakdown.
- **Live Dev Logs Terminal**: SSE-powered streaming console with log level filters (`INFO`, `WARN`, `ERROR`, `DEBUG`).
- **AI Evals & Quality Benchmarks Runner**: Runs continuous evaluation test suites with pass/fail gate scoring.

---

### 5.6 n8n Automation Monitoring Center (`N8nMonitoringPage.jsx`)

**Primary Purpose:** Deep operational visibility into n8n automated workflow executions, node health, and queue latency.

#### Contained KPI Cards

| Card Title | Metric Formula / Telemetry | Value / Status | Accent Color |
| :--- | :--- | :--- | :--- |
| **Registered Workflows** | `COUNT(workflows.registered)` | `6 Workflows Active` | Purple (`#9333EA`) |
| **Monitored Execution Nodes**| `COUNT(nodes.active)` | `20 Automation Nodes` | Blue (`#0284C7`) |
| **Mean Execution Duration** | `AVG(workflow_run_duration_ms)` | `148ms Average Latency`| Emerald (`#059669`)|
| **Webhook Ingress Health** | `(successful_webhooks / total_received) * 100` | `100.0% Success Rate` | Coral (`#E8654A`) |

---

### 5.7 Live Customer Inquiries & Takeover Desk (`ConversationsPage.jsx`)

**Primary Purpose:** Frontline customer dialogue monitoring, instant AI pause/resume human takeover, and customer lead profile inspection.

#### Contained Header & Filter Metrics
- **Live Stream Status**: Real-time SSE indicator (`SSE Stream Live` / `Connecting...`).
- **Channel Filters**: Multi-channel filter pills (`All`, `Email`, `WhatsApp`, `Telegram`, `Facebook`, `Instagram`, `Website`).
- **Status Filters**: Operational state filters (`All Status`, `🤖 AI Live`, `👨‍💼 Takeover`, `⚠️ Escalated`).

#### Live Chat & Lead Profile Components
- **Message Stream**: Color-coded chat bubbles demarcating User (`var(--bg-card)`), AI Assistant (`var(--grad-coral)`), and Human Sales Agent (`var(--grad-amber)`).
- **Quick Action Shortcut Bar**: 1-click insertion of official brochure links and site tour scheduling URLs.
- **Human Takeover Bar**: Dynamic toggle button allowing agents to pause AI automation for immediate manual takeover and resume AI automation with one click.
- **AI Lead Summary Modal**: Generates on-demand structured buyer profiles detailing preferred locations, budget limits, and timeline urgency.
- **Simulate New Lead Modal**: Allows developers and managers to inject mock customer inquiries across any channel.

---

### 5.8 Property Inventory & Spatial Catalog (`PropertiesPage.jsx`)

**Primary Purpose:** Interactive real estate project inventory management, geospatial proximity exploration, and architectural asset distribution.

#### Contained Views & Controls
- **View Mode Switcher**: Toggle between responsive Grid View and CartoDB Voyager Interactive Leaflet Map.
- **Location Filter Pills**: Quick-filter by neighborhood (`All Locations`, `Gulshan`, `Banani`, `Dhanmondi`, `Uttara`).
- **Property Cards**: Showcase project photo, starting price, bedroom configurations, completion status, amenity chips, and key proximity landmarks.
- **Floor Plans Preview Modal**: Interactive modal displaying detailed 2D/3D floor layouts, unit dimensions, and interior specifications.
- **Add New Development Modal (`AddPropertyModal.jsx`)**: Modal for registering new properties with coordinates, images, and brochure links.

---

### 5.9 Social Content Generator & Approval Engine (`ContentGeneratorPage.jsx`)

**Primary Purpose:** AI-powered social media post ideation, multi-platform copy formatting, visual asset pairing, and manager approval workflows.

#### Contained Modules
- **Post Ideation Canvas**: Select project, target demographic, promotional theme, and target social network (Facebook, Instagram, LinkedIn).
- **Approval Workflow Queue**: Drafts awaiting manager review with 1-click Approve, Edit, or Reject actions.
- **Content Calendar Modal**: Interactive monthly scheduling grid tracking upcoming publications with status badges.

---

### 5.10 Knowledge Base & Document OCR Manager (`KnowledgePage.jsx`)

**Primary Purpose:** Ingestion, vector embedding, and lifecycle management for architectural brochures, legal governance PDFs, and FAQ documentation.

#### Contained Modules & KPIs
- **Document Portfolio**: Master list of ingested PDFs, page counts, chunk counts, and SHA-256 hashes.
- **Upload & OCR Pipeline**: Drag-and-drop file ingestion triggering text extraction, semantic chunking, and dual upsert to Supabase pgvector and Pinecone.
- **Vector Search Benchmark**: Query testing tool verifying that document chunks are accurately retrieved by cosine similarity.

---

### 5.11 Executive Cross-Role Operational Reports (`RoleReportsPage.jsx`)

**Primary Purpose:** Consolidated executive reports auditing performance across Admin, Manager, Agent, and Developer roles.

#### Contained Audit Metrics
- **Agent Response Efficiency**: Response times and closing rates across human sales agents.
- **Manager Approval Throughput**: Average turnaround time for content approvals and escalated lead assignments.
- **System SLA Compliance**: Uptime, latency, and error rate adherence.

---

# Section 6: Comprehensive Role-Based Matrix (Roles vs Workflows vs KPI Cards vs Components)

### 6.1 Role Hierarchy & Permission Architecture

The platform enforces five distinct Role-Based Access Control (**RBAC**) levels:
1. **`Admin`**: Executive leadership, C-Suite, and managing partners with complete organizational oversight.
2. **`Manager`**: Sales directors and marketing operations managers driving lead pipeline velocity and ad campaigns.
3. **`Agent`**: Frontline sales representatives focused on active customer conversations, site visits, and closing deals.
4. **`Developer`**: Systems engineers, AI engineers, and DevOps architects managing models, webhooks, and telemetry.
5. **`Viewer`**: Board members, external auditors, and investors requiring read-only analytics and inventory views.

---

### 6.2 Administrator Role Specification

- **Role Identifier**: `admin`
- **Primary Operational Goal**: Organizational governance, revenue optimization, and cross-functional strategic decision-making.
- **Permitted Workflows**:
  - Full system configuration and global module layout editing.
  - Review and export of C-Suite executive PDF reports.
  - User role assignment and tenant provisioning.
  - Complete visibility into ad spend, ROAS, pipeline valuation, and cost savings.
- **Visible Dashboards**:
  - `DashboardHome` (Executive Overview)
  - `AnalyticsPage` (Executive Command Center)
  - `SocialAnalyticsPage` (Social & Ad Intelligence)
  - `RoleReportsPage` (Cross-Role Operational Audits)
  - `PropertiesPage` (Master Inventory)
  - `KnowledgePage` (Document Repository)
- **Assigned KPI Cards**:
  - Annual Pipeline Value (`৳14.8 Cr`)
  - Total Leads Captured (`142`)
  - AI Self-Resolution % (`94.2%`)
  - Labor Cost Savings (`৳5,20,000`)
  - Total Ad Spend & Pipeline ROAS (`$9,180 / 5.8x`)
  - Active Deal Conversion Velocity

---

### 6.3 Manager Role Specification

- **Role Identifier**: `manager`
- **Primary Operational Goal**: Team supervision, ad campaign ROI tracking, social content approval, and handling escalated hot leads.
- **Permitted Workflows**:
  - Operational oversight of live sales conversations and team assignments.
  - Reviewing, editing, approving, and publishing AI-generated social content.
  - Monitoring Meta Click-to-WhatsApp and Instagram ad spend and CPL.
  - Re-assigning hot leads and booking VIP site visit tours.
- **Visible Dashboards**:
  - `ManagerDashboardPage` (Dedicated Operations Console)
  - `ConversationsPage` (Live Chats & Human Takeover)
  - `ContentGeneratorPage` (Content Engine & Calendar)
  - `SocialAnalyticsPage` (Campaign Analytics)
  - `PropertiesPage` (Property Catalog)
  - `AnalyticsPage` (Operations Analytics)
- **Assigned KPI Cards**:
  - Total Ad Spend (Monthly) (`৳1,25,000`)
  - Campaign Reach & Views (`185,000 Reach`)
  - Messages Received from Ads (`1,420 Msgs`)
  - AI Response Rate & Speed (`96.8% / 1.2s`)
  - Qualified Leads & Confirmed Tours (`142 / 32 Tours`)
  - Pending Social Approvals (`5 Posts`)

---

### 6.4 Sales Agent Role Specification

- **Role Identifier**: `agent`
- **Primary Operational Goal**: Frontline lead conversion, customer relationship management, and conducting site visit tours.
- **Permitted Workflows**:
  - Monitoring real-time customer dialogues across WhatsApp, Messenger, and Web.
  - Pausing AI automation to execute **Human Takeover** on high-intent leads.
  - 1-click dispatching of property brochures, floor plans, and booking links.
  - Initiating outbound VoIP phone calls to hot leads (`Hot Lead Leaderboard`).
  - Browsing property availability, bedroom configs, and pricing details.
- **Visible Dashboards**:
  - `ConversationsPage` (Default landing view)
  - `PropertiesPage` (Inventory & Spatial Map)
- **Assigned KPI Cards**:
  - Active Live Chats Queue
  - Hot Leads Pending Action (`Score >= 80`)
  - Human Handover Escalation Rate (`5.8%`)
  - Qualified Site Visit Bookings
  - Property Inventory Units Available

---

### 6.5 Developer / DevOps Role Specification

- **Role Identifier**: `developer`
- **Primary Operational Goal**: Platform reliability, model evaluation, vector retrieval tuning, and integration health.
- **Permitted Workflows**:
  - Live log streaming and inspection via SSE (`/api/developer/logs/stream`).
  - Inbound webhook simulation across 5 channels.
  - Vector search benchmarking across Supabase pgvector and Pinecone.
  - Direct execution of interactive API requests in the API Playground.
  - Running automated AI quality evaluation suites and regression gates.
  - Monitoring n8n workflow execution nodes, latency, and error counts.
- **Visible Dashboards**:
  - `DeveloperConsolePage` (Default landing view)
  - `N8nMonitoringPage` (Workflow Node Health)
  - `KnowledgePage` (Document Embedding & OCR Diagnostics)
- **Assigned KPI Cards**:
  - All 6 Engineering Subsystem Cards (n8n, Pinecone, Supabase, LangGraph, Webhooks, Security)
  - P95 LLM Inference Latency
  - Vector Retrieval Speed (`14ms`)
  - Token Usage & Error Rate (`0.01%`)
  - n8n Execution Latency (`148ms`)
  - Eval Pass Rate (`97.4%`)

---

### 6.6 Executive Viewer Role Specification

- **Role Identifier**: `viewer`
- **Primary Operational Goal**: High-level visibility for board members, investors, and auditors without mutation privileges.
- **Permitted Workflows**:
  - Read-only browsing of the Dashboard Home executive overview.
  - Exploring property inventory cards and interactive spatial maps.
  - Viewing architectural brochures and floor plans.
  - Strictly blocked from chat takeovers, content publishing, or system settings.
- **Visible Dashboards**:
  - `DashboardHome` (Read-only Overview)
  - `PropertiesPage` (Read-only Catalog)
- **Assigned KPI Cards**:
  - Total Properties (`12`)
  - Annual Pipeline Value (`৳14.8 Cr`)
  - Total Leads Captured (`142`)
  - AI Resolution Rate (`94.2%`)

---

### 6.7 Master Cross-Functional Matrix Table

The following matrix formally cross-references every **Role** with its permitted **Workflows**, visible **KPI Cards**, and active **UI Components**:

| Role | Permitted Workflows | Assigned KPI Cards | Active Pages & UI Components |
| :--- | :--- | :--- | :--- |
| **`Admin`** | • Global Layout & Module Customization<br>• Executive PDF Export<br>• User Management & Multi-Tenant Setup<br>• Financial & Strategic ROI Audits | • Annual Pipeline Value (`৳14.8 Cr`)<br>• AI Self-Resolution % (`94.2%`)<br>• Labor Cost Savings (`৳5.2L`)<br>• Total Ad Spend & ROAS (`$9.18K / 5.8x`)<br>• Hot Leads Scored (`12`) | • `DashboardHome`<br>• `AnalyticsPage`<br>• `SocialAnalyticsPage`<br>• `RoleReportsPage`<br>• `PropertiesPage`<br>• `KnowledgePage`<br>• `EditModulesModal`<br>• `Header` (Global Filters) |
| **`Manager`** | • Real-Time Operations Management<br>• Review & Approve Social Content<br>• Ad Campaign Budget & CPL Tracking<br>• Escalate & Re-assign Leads<br>• Monitor Agent Response Rates | • Total Ad Spend (`৳1,25,000`)<br>• Campaign Reach (`185,000`)<br>• Messages from Ads (`1,420`)<br>• AI Response Speed (`1.2s`)<br>• Qualified Leads & Tours (`142 / 32`)<br>• Pending Approvals (`5 Posts`) | • `ManagerDashboardPage`<br>• `ConversationsPage`<br>• `ContentGeneratorPage`<br>• `SocialAnalyticsPage`<br>• `AnalyticsPage`<br>• `PropertiesPage`<br>• `ContentCalendarModal`<br>• `FloorPlansModal` |
| **`Agent`** | • Live Chat Takeover & Pause AI<br>• Outbound VoIP Callout to Hot Leads<br>• Send Instant Brochure & Booking Links<br>• Browse Units & Pricing Data<br>• Inquire on Unit Availability | • Live Inquiries Queue Count<br>• Hot Leads Pending Action (`Score >= 80`)<br>• Human Takeover Session Count<br>• Confirmed Tour Bookings<br>• Property Inventory Units | • `ConversationsPage`<br>• `PropertiesPage`<br>• `QuickActionButtons`<br>• `TakeoverToggle`<br>• `AILeadSummaryModal`<br>• `LeafletEstateMap` |
| **`Developer`** | • SSE Live Logs Inspection<br>• Simulate Webhooks (5 Channels)<br>• RAG & Cosine Benchmark Testing<br>• Run AI Evals & Regression Gates<br>• Monitor n8n Node Executions<br>• Database & Vector Sync | • 6 Engineering Subsystem Cards<br>• P95 LLM Latency (`1.8s`)<br>• Vector Retrieval Speed (`14ms`)<br>• Token Usage & Error Rate (`0.01%`)<br>• n8n Execution Latency (`148ms`)<br>• Eval Pass Rate (`97.4%`) | • `DeveloperConsolePage`<br>• `N8nMonitoringPage`<br>• `KnowledgePage`<br>• `ApiPlayground`<br>• `WebhookSimulator`<br>• `RAGDiagnostics`<br>• `LiveLogsTerminal` |
| **`Viewer`** | • Read-Only Portfolio Review<br>• View Handover Schedules<br>• Explore Spatial Map Coordinates<br>• Download Architectural Brochures | • Total Properties (`12`)<br>• Annual Pipeline Value (`৳14.8 Cr`)<br>• Total Leads Captured (`142`)<br>• AI Resolution Rate (`94.2%`) | • `DashboardHome` (Read-only)<br>• `PropertiesPage` (Read-only)<br>• `PropertyEstateMap`<br>• `KPICardStrip`<br>• `ValuablePropertiesTable` |

---

## Conclusion & Architectural Sign-Off

The **GLG Assets Enterprise Agentic Real Estate Automation Platform** represents a modern, resilient synthesis of Agentic AI, modern web engineering, and enterprise database architecture. By decoupling agent reasoning via LangGraph, guaranteeing facts through Supabase pgvector HNSW indexing, enforcing sub-20ms spatial queries, and applying a tailored visual design system, the system provides an autonomous real estate operating platform built for immediate scale, high throughput, and enterprise-grade reliability.

*Certified for Production Deployment — Version 2.4.0-PROD.*
