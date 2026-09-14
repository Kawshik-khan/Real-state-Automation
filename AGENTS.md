# GLG ASSETS ENTERPRISE AGENTIC SYSTEM CONSTITUTION

> **Google Antigravity Master Project Rulebook (`AGENTS.md`)**  
> **Platform Version:** 2.4.0-PROD  
> **Operating System Root:** [`.agents/`](file:///d:/Softwear%20Project/Realstate%20Automation/.agents/)  
> **Target Architecture:** Supabase Cloud (PostgreSQL 15+ & pgvector), Pinecone Serverless, FastAPI, LangGraph, React 19, n8n

---

## 1. Operating System & Customizations Binding

This repository implements the **GLG Enterprise Agentic Engineering Operating System** managed in [`.agents/`](file:///d:/Softwear%20Project/Realstate%20Automation/.agents/). All agents, skills, rules, and workflows operating within this workspace are bound by the configurations defined herein.

### Canonical Directories
- **Rules (`.agents/rules/`)**: Inviolable architectural, backend, frontend, RAG, database, and security constitutions.
- **Skills (`.agents/skills/`)**: 21 standardized engineering runbooks and procedures.
- **Agents (`.agents/agents/`)**: 16 specialized engineering roles with dedicated prompts and separation of duties.
- **Context (`.agents/context/`)**: Machine-readable data schemas, API contracts, design system tokens, and SLA baselines.
- **Policies (`.agents/policies/`)**: Risk levels, tool authorities, human escalation, and Definition of Done.

---

## 2. Workspace Skills Catalog (21 Verified Skills)

Antigravity loads and executes the following specialized workspace skills located in [`.agents/skills/`](file:///d:/Softwear%20Project/Realstate%20Automation/.agents/skills/):

| Skill Name | Purpose & Workflow |
| :--- | :--- |
| **`agent-customization`** | Configure LLM models, hyperparameters, system prompts, hybrid RAG weights, LoRA fine-tuning adapters, and token telemetry in the AI Customization Studio. |
| **`agent-development`** | Implement stateful, observable, and bounded LangGraph nodes, dynamic belief memory reflection, and intent routing. |
| **`ai-evaluation`** | Quantitative benchmarking measuring intent accuracy, parameter extraction recall, groundedness, and hallucination rates. |
| **`architecture-planning`** | Author architectural decision records (ADRs), subsystem boundary plans, data flow diagrams, and interface contracts. |
| **`architecture-review`** | Audit modifications against modular boundaries, prevent architectural drift, and evaluate long-term technical debt. |
| **`archify`** | Create polished, validated architecture, workflow, sequence, data-flow, and lifecycle diagrams as explorable HTML/SVG. |
| **`backend-development`** | Develop FastAPI async endpoints, Pydantic v2 schemas, async domain services, and database persistence layers. |
| **`code-review`** | Independent peer review, defect discovery, severity classification (P0–P3), and remediation reporting. |
| **`database-development`** | PostgreSQL schemas, Supabase Row-Level Security (RLS), HNSW vector indexes, and Alembic migrations. |
| **`debugging`** | Forensic 10-step workflow for isolating root causes, reproducing defects with regression tests, and minimal fixes. |
| **`feature-development`** | 13-phase end-to-end workflow for designing, implementing, verifying, and delivering production features. |
| **`frontend-development`** | React 19 views, composable components, design token adherence, and SSE real-time listeners. |
| **`integration-development`** | External messaging channels, webhook ingestion, HMAC validation, and n8n cloud automation workflows. |
| **`migration-review`** | Auditing database schema migrations, backward compatibility, RLS policies, indexes, and rollback plans. |
| **`performance-audit`** | Profiling latency budgets, database query execution, memory footprint, and vector retrieval speeds. |
| **`rag-development`** | Document ingestion, 512/64 token chunking, dense pgvector search, sparse FTS, Reciprocal Rank Fusion (k=60), and grounding gates. |
| **`release`** | 11-step release gatekeeping procedure validating git diff, tests, type checks, lint, builds, and security audits. |
| **`repository-discovery`** | Discovering repository structure, active dependencies, existing abstractions, and configurations prior to implementation. |
| **`requirement-analysis`** | Decomposing user and business requirements, determining architectural scope, and identifying edge cases. |
| **`security-audit`** | Authentication, 5-tier RBAC authorization, multi-tenant isolation, RLS validation, and prompt injection defense. |
| **`testing`** | Adversarial testing methodologies, automated test execution protocols, and assertion design. |
| **`ui-quality-audit`** | Auditing React components against Warm Executive Modernism tokens, responsive behaviors, and accessibility. |

---

## 3. Mandatory Engineering Rules

When editing or creating files in this workspace, all agents must adhere to:

1. **Separation of Duties**: No agent may author code and certify its own review for changes rated `MEDIUM` risk or higher.
2. **Design System Adherence**: Always enforce the **Warm Executive Modernism** aesthetic. Never use generic browser default components, plain unstyled buttons, or unharmonized color schemes.
3. **No Mock or Fake Completion**: Code must be genuinely wired to active services, database tables, or robust fallback adapters.
4. **Verification Gate**: Any frontend change must compile cleanly via `npm run build`. Any backend change must pass Python syntax and service unit tests.
