# GLG Assets — Gap Map & Build Plan

> Generated: 2026-07-26
> Maps Social AI OS v1 workflow (45 workstreams) to the current FastAPI backend (41 endpoints) and Platform API (6 endpoints).

---

## 1. Legend

| Icon | Meaning |
|------|---------|
| ✅ | Endpoint exists, same path & name — no work needed (but still stub) |
| 🟡 | Path mismatch — Social AI OS calls `/api/v1/automation/…` but backend has it under `/api/v1/ai/…` etc. |
| 🟠 | Name mismatch — similar route exists but with different signature |
| 🔴 | Does not exist in backend at all |
| ⚫ | External API dependency (Google, Meta, WhatsApp, Supabase, etc.) |
| 💎 | Placeholder URL (crm-system, erp-system) — needs real service |
| 🔵 | Platform API (port 8001) — separate service |

**Status notes:**
- **Stub** = endpoint exists but returns static/placeholder data
- **Partial** = some logic exists but not production-ready (no DB/LLM/external API)

---

## 2. Complete Endpoint Gap Map

### 2.1 AI Services (Workstreams 01-08) → `/api/v1/ai/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 01 | WS01 | `POST /automation/ai/respond` | `POST /ai/ask` | 🟡 Path + name mismatch | Stub |
| 02 | WS02 | `POST /automation/translate` | `POST /ai/translate` | 🟡 Path mismatch | Stub |
| 03 | WS03 | `POST /automation/knowledge/embed` | `POST /ai/embeddings` | 🟡 Path + name mismatch | Stub |
| 04 | WS04 | `POST /automation/media/image` | `POST /ai/image` | 🟡 Path mismatch | Stub |
| 05 | WS06 | `POST /automation/memory/update` | `POST /ai/memory` | 🟡 Path + name mismatch | Stub |
| 06 | WS07 | `POST /automation/rag/query` | `POST /ai/rag` | 🟡 Path + name mismatch | Stub |
| 07 | WS08 | `POST /automation/media/voice` | `POST /ai/voice` | 🟡 Path mismatch | Stub |
| - | WS05 | `POST /automation/knowledge/ingest` | `POST /knowledge/upload` | 🟡 Path + name mismatch | Stub |

### 2.2 Automation (Core Business Logic)

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 08 | - | `POST /automation/booking` | `POST /automation/booking` | ✅ Same | Stub |
| 09 | - | `POST /automation/notify` | `POST /automation/notify` | ✅ Same | Stub |
| 10 | - | `POST /automation/classify` | `POST /automation/classify` | ✅ Same | Partial |
| 11 | - | `GET /automation/daily-digest` | `GET /automation/daily-digest` | ✅ Same | Stub |
| 12 | - | `POST /automation/logs` | `POST /automation/logs` | ✅ Same | Stub |
| 13 | - | `POST /automation/chat` | `POST /automation/chat` | ✅ Same | Stub |
| 14 | - | `POST /automation/inbound` | **MISSING** | 🔴 | - |
| 15 | - | `POST /automation/outbound` | **MISSING** | 🔴 | - |
| 16 | - | `POST /automation/outbound/facebook` | **MISSING** | 🔴 | - |

### 2.3 Content Services (Workstreams 12-18) → `/api/v1/content/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 17 | WS13 | `POST /automation/content/captions` | `POST /content/captions` | 🟡 Path mismatch | Stub |
| 18 | WS14 | `POST /automation/content/publish/facebook` | `POST /content/facebook/publish` | 🟡 Path + order mismatch | Stub |
| 19 | WS15 | `POST /automation/content/hashtags` | `POST /content/hashtags` | 🟡 Path mismatch | Stub |
| 20 | WS16 | `POST /automation/content/publish/instagram` | `POST /content/instagram/publish` | 🟡 Path + order mismatch | Stub |
| 21 | WS17 | `POST /automation/content/publish/linkedin` | `POST /content/linkedin/publish` | 🟡 Path + order mismatch | Stub |
| 22 | - | `POST /automation/content/publish` | **MISSING** | 🔴 Generic publish | - |
| 23 | - | `POST /automation/content/generate` | **MISSING** | 🔴 AI content gen | - |
| 24 | - | `POST /automation/content/approval` | **MISSING** | 🔴 Approval flow | - |
| 25 | WS12 | `POST /automation/brochure/send` | `POST /media/brochure` | 🟡 Path mismatch | Stub |

### 2.4 Social Channels (Workstreams 25-33) → `/api/v1/social/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 26 | WS25 | `POST /automation/…/facebook/comments` | `POST /social/facebook/comments` | 🟡 Path mismatch | Stub |
| 27 | WS26 | `POST /automation/…/facebook/incoming` | `POST /social/facebook/incoming` | 🟡 Path mismatch | Stub |
| 28 | WS27 | `POST /automation/…/facebook/send` | `POST /social/facebook/send` | 🟡 Path mismatch | Stub |
| 29 | WS28 | `POST /automation/…/instagram/comments` | `POST /social/instagram/comments` | 🟡 Path mismatch | Stub |
| 30 | WS29 | `POST /automation/…/instagram/dm` | `POST /social/instagram/dm` | 🟡 Path mismatch | Stub |
| 31 | WS30 | `POST /automation/…/leads/capture` | `POST /social/leads/capture` | 🟡 Path mismatch | Stub |
| 32 | WS31 | `POST /automation/…/website/livechat` | `POST /social/website/livechat` | 🟡 Path mismatch | Stub |
| 33 | WS32 | `POST /automation/…/whatsapp/incoming` | `POST /social/whatsapp/incoming` | 🟡 Path mismatch | Stub |
| 34 | WS33 | `POST /automation/…/whatsapp/media` | `POST /social/whatsapp/media` | 🟡 Path mismatch | Stub |

### 2.5 Moderation (Workstreams 20-21) → `/api/v1/moderation/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 35 | WS20 | `POST /automation/moderate/spam` | `POST /moderation/spam` | 🟡 Path mismatch | Partial |
| 36 | WS21 | `POST /automation/moderate/toxicity` | `POST /moderation/toxicity` | 🟡 Path mismatch | Partial |
| 37 | - | `POST /automation/moderate` | **MISSING** | 🔴 Generic moderation | - |

### 2.6 Notifications (Workstreams 22-24) → `/api/v1/notifications/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 38 | WS22 | `POST /automation/notify/email` | `POST /notifications/email` | 🟡 Path mismatch | Stub |
| 39 | WS23 | `POST /automation/notify/slack` | `POST /notifications/slack` | 🟡 Path mismatch | Stub |
| 40 | WS24 | `POST /automation/notify/telegram` | `POST /notifications/telegram` | 🟡 Path mismatch | Stub |
| 41 | - | `POST /automation/notify/whatsapp` | **MISSING** | 🔴 WhatsApp notify | - |

### 2.7 Analytics (Workstreams 09-11) → `/api/v1/analytics/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 42 | WS09 | `POST /automation/analytics/daily` | `POST /analytics/daily` | 🟡 Path mismatch | Stub |
| 43 | WS10 | `POST /automation/analytics/engagement` | `POST /analytics/engagement` | 🟡 Path mismatch | Stub |
| 44 | WS11 | `POST /automation/analytics/failed-replies` | `POST /analytics/failed-replies` | 🟡 Path mismatch | Stub |

### 2.8 Escalations (Workstream 19) → `/api/v1/escalations/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 45 | WS19 | `POST /automation/handoffs` | `POST /escalations/create` | 🟡 Path + name mismatch | Stub |

### 2.9 Knowledge (Workstream 05) → `/api/v1/knowledge/`

| # | WS | Social AI OS Expected | Backend Actual | Gap | Status |
|---|----|----------------------|----------------|-----|--------|
| 46 | WS05 | `POST /automation/knowledge/ingest` | `POST /knowledge/upload` | 🟡 Path + name mismatch | Stub |

### 2.10 Platform API (port 8001) — Workstreams 34-45

| # | WS | URL | Backend Actual | Gap | Status |
|---|----|-----|----------------|-----|--------|
| 47 | WS34 | `POST /api/v1/n8n/events/…` | `POST /api/v1/platform-events` | 🟡 Path + name mismatch | Stub |
| 48 | WS35 | `POST /api/v1/n8n/events/lead-created` | **MISSING** in Platform API | 🔴 | - |
| 49 | WS36 | `POST /api/v1/n8n/events/booking-created` | **MISSING** in Platform API | 🔴 | - |
| 50 | WS37 | `POST /api/v1/n8n/events/payment-completed` | **MISSING** in Platform API | 🔴 | - |
| 51 | WS34 | `POST /api/v1/n8n/events/conversation-started` | **MISSING** in Platform API | 🔴 | - |
| 52 | WS45 | `POST /api/v1/conversations` | `POST /api/v1/conversations` | ✅ Same | Stub |
| 53 | WS45 | `POST /api/v1/conversations/{id}/messages` | `POST /api/v1/conversations/{id}/messages` | ✅ Same | Stub |
| 54 | WS44 | `POST /api/v1/analytics/social-media` | `POST /api/v1/analytics/social-media` | ✅ Same | Stub |
| 55 | WS41 | `POST /api/v1/social-media-post` | `POST /api/v1/social-media-post` | ✅ Same | Stub |
| 56 | WS42 | `POST /api/v1/content-distribute` | `POST /api/v1/content-distribute` | ✅ Same | Stub |
| 57 | WS43 | `POST /api/v1/campaign-execute` | `POST /api/v1/campaign-execute` | ✅ Same | Stub |

### 2.11 External APIs & Placeholders

| # | Expected URL | Type | Gap |
|---|-------------|------|-----|
| 58 | `POST http://localhost:8000/api/v1/leads` | 🔴 Missing | CRM leads endpoint (different from /social/leads/capture) |
| 59 | `POST http://localhost:8000/api/v1/bookings` | 🔴 Missing | CRM bookings endpoint (different from /automation/booking) |
| 60 | `POST http://localhost:8000/api/v1/inventory` | 🔴 Missing | Property inventory endpoint |
| 61 | `POST http://localhost:8000/api/v1/analytics/content` | 🔴 Missing | Content analytics endpoint |
| 62 | `POST http://crm-system/api/leads` | 💎 Placeholder | Needs CRM service |
| 63 | `POST http://crm-system/api/bookings` | 💎 Placeholder | Needs CRM service |
| 64 | `POST http://crm-system/api/payments` | 💎 Placeholder | Needs payment service |
| 65 | `POST http://erp-system/api/transactions` | 💎 Placeholder | Needs ERP service |
| 66 | `https://www.googleapis.com/calendar/v3/…` | ⚫ External | Needs Google Calendar OAuth |
| 67 | `SUPABASE_URL/rest/v1/leads` | ⚫ External | Needs Supabase project + API key |
| 68 | `GOOGLE_SHEETS_WEBHOOK_URL` | ⚫ External | Needs Google Sheets webhook setup |

---

## 3. Gap Summary

### 3.1 By the Numbers

| Category | Count |
|----------|-------|
| **Total unique endpoints referenced** | 68 |
| **✅ Exact match (same path)** | 10 |
| **🟡 Path mismatch (move under /automation/ or alias)** | 31 |
| **🔴 Missing entirely** | 17 |
| **⚫ External API dependency** | 3 |
| **💎 Placeholder (crm/erp)** | 5 |
| **🟠 Name mismatch** | 2 |

### 3.2 Biggest Wins — Path Normalization

31 of 41 existing backend endpoints need **path aliasing** or the Social AI OS workflow paths need updating. The workflow hits everything under `/api/v1/automation/*` but the backend has them under `/api/v1/ai/*`, `/api/v1/analytics/*`, `/api/v1/content/*`, etc.

**Two options:**
1. **Add FastAPI aliases** (recommended) — mount the same router function at both paths
2. **Update the n8n workflow** — change all URLs in the Social AI OS workflow to match actual backend paths (much more work, ~80 URL changes)

### 3.3 All Endpoints Are Stubs

100% of the 47 existing endpoints (41 main + 6 platform) return **static/placeholder data**. None have:
- PostgreSQL database queries
- LangGraph/AI integration
- Real external API calls (Meta, WhatsApp, Slack, etc.)
- File storage for media
- Email/SMS delivery

---

## 4. Prioritized Build Plan

### Phase 0: Infrastructure & Production Readiness (Do First — 2-3 days)

| # | Task | Why | Files |
|---|------|-----|-------|
| P0.1 | Generate production secrets | Security — `openssl rand -hex 32` for both `.env` files | `backend/.env`, `platform-api/.env` |
| P0.2 | Set up PostgreSQL + pgvector | All endpoints depend on DB | `docker-compose.yml`, `backend/app/database.py` |
| P0.3 | Create httpHeaderAuth credential in n8n | Unblocks all 19 workflows | n8n UI, name: "Backend API Key" |
| P0.4 | Set up ngrok/Cloudflare Tunnel or self-host n8n | n8n cloud blocks localhost (SSRF) | `docker-compose.yml` |
| P0.5 | Fix alembic.ini for PostgreSQL | DB migrations won't work with SQLite target | `alembic.ini` |
| P0.6 | Resolve dual app/ vs backend/app/ structure | Confusion in imports and deployments | Project root |

### Phase 1: Core Real Estate Automation (Week 1-2)

| # | Task | Endpoints | Effort | Priority |
|---|------|-----------|--------|----------|
| **1.1** | **Lead capture → DB** | `POST /social/leads/capture` | 1d | 🥇 Critical |
| | Create `leads` table; store lead data; return lead_id | | | |
| **1.2** | **Lead classification with LLM** | `POST /automation/classify` | 1d | 🥇 Critical |
| | Replace rule-based with LangGraph/LLM classification | | | |
| **1.3** | **Booking creation → DB** | `POST /automation/booking` | 1d | 🥇 Critical |
| | Create `bookings` table; store tour requests; conflict detection | | | |
| **1.4** | **Chat endpoint with LangGraph** | `POST /automation/chat` | 2d | 🥇 Critical |
| | Integrate LangGraph agent for real estate Q&A; conversation memory | | | |
| **1.5** | **Daily digest from real data** | `GET /automation/daily-digest` | 0.5d | 🥈 High |
| | Query actual lead/booking/conversation counts from DB | | | |

### Phase 2: Path Normalization & Workflow Alignment (Week 2)

| # | Task | Effort | Priority |
|---|------|--------|----------|
| **2.1** | Add FastAPI path aliases → mount endpoints under both `/ai/…` AND `/automation/…` | 0.5d | 🥇 Critical |
| **2.2** | Create `POST /automation/inbound` — generic webhook receiver | 0.5d | 🥈 High |
| **2.3** | Create `POST /automation/outbound` — generic webhook dispatcher | 0.5d | 🥈 High |
| **2.4** | Create `POST /automation/moderate` — generic moderation endpoint | 0.25d | 🥉 Medium |
| **2.5** | Create `POST /automation/notify/whatsapp` — WhatsApp notification adapter | 0.5d | 🥉 Medium |
| **2.6** | Update all Social AI OS workflow URLs (or add FastAPI route aliases) | 1d | 🥇 Critical |

### Phase 3: Notification & Channel Integration (Week 2-3)

| # | Task | Endpoints | Effort | Priority |
|---|------|-----------|--------|----------|
| **3.1** | Email notifications (SendGrid/SMTP) | `POST /notifications/email`, `POST /automation/notify` | 1d | 🥈 High |
| **3.2** | Slack webhook integration | `POST /notifications/slack` | 0.5d | 🥈 High |
| **3.3** | Telegram bot integration | `POST /notifications/telegram` | 0.5d | 🥈 High |
| **3.4** | WhatsApp Cloud API integration | `POST /social/whatsapp/incoming`, `POST /social/whatsapp/media` | 2d | 🥇 Critical |

### Phase 4: Social Media & Content (Week 3-4)

| # | Task | Endpoints | Effort | Priority |
|---|------|-----------|--------|----------|
| **4.1** | Facebook Graph API — auto-comment reply | `POST /social/facebook/comments` | 1d | 🥉 Medium |
| **4.2** | Facebook Messenger integration | `POST /social/facebook/incoming`, `POST /social/facebook/send` | 1d | 🥉 Medium |
| **4.3** | Instagram comments + DM | `POST /social/instagram/comments`, `POST /social/instagram/dm` | 1d | 🥉 Medium |
| **4.4** | Content generation (LLM) | `POST /content/captions`, `POST /content/hashtags` | 1d | 🥉 Medium |
| **4.5** | Social media publisher | `POST /content/facebook/publish`, `POST /content/instagram/publish`, `POST /content/linkedin/publish` | 1.5d | 🥉 Medium |
| **4.6** | Content approval workflow | `POST /automation/content/approval` (MISSING) | 1d | 🥉 Medium |

### Phase 5: AI Services (Week 4-5)

| # | Task | Endpoints | Effort | Priority |
|---|------|-----------|--------|----------|
| **5.1** | AI Q&A with LangGraph + RAG | `POST /ai/ask`, `POST /ai/rag` | 2d | 🥈 High |
| **5.2** | Translation service (DeepL/Google Translate) | `POST /ai/translate` | 0.5d | 🥉 Medium |
| **5.3** | Image understanding (vision model) | `POST /ai/image` | 1d | 🥉 Medium |
| **5.4** | Voice processing (Whisper) | `POST /ai/voice` | 1d | 🥉 Medium |
| **5.5** | Knowledge base ingestion + embeddings (pgvector) | `POST /knowledge/upload`, `POST /ai/embeddings` | 1d | 🥈 High |
| **5.6** | Conversation memory (pgvector) | `POST /ai/memory` | 1d | 🥈 High |

### Phase 6: Platform API Events (Week 5)

| # | Task | Effort | Priority |
|---|------|--------|----------|
| **6.1** | Event bus — lead.created, booking.created, payment.completed | 1d | 🥉 Medium |
| **6.2** | Social media posting queue (platform-api) | 1d | 🥉 Medium |
| **6.3** | Content distribution pipeline | 0.5d | 🥉 Medium |
| **6.4** | Campaign execution engine | 1d | 🥉 Medium |
| **6.5** | Conversation management API | 0.5d | 🥉 Medium |

### Phase 7: External Integrations (Week 5-6)

| # | Task | Effort | Priority |
|---|------|--------|----------|
| **7.1** | CRM system — leads, bookings, payments CRUD | 2d | 🥈 High |
| **7.2** | ERP system — transaction sync | 2d | 🥉 Medium |
| **7.3** | Google Calendar sync — tour bookings → calendar events | 1d | 🥉 Medium |
| **7.4** | Supabase — lead storage fallback | 0.5d | 🥉 Medium |
| **7.5** | Google Sheets — lead export webhook | 0.5d | 🥉 Medium |

### Phase 8: Analytics & Monitoring (Week 6)

| # | Task | Endpoints | Effort | Priority |
|---|------|-----------|--------|----------|
| **8.1** | Daily social AI report from real data | `POST /analytics/daily` | 0.5d | 🥉 Medium |
| **8.2** | Engagement analytics dashboard | `POST /analytics/engagement` | 1d | 🥉 Medium |
| **8.3** | Failed reply monitoring + retry | `POST /analytics/failed-replies` | 0.5d | 🥉 Medium |
| **8.4** | Escalation tracking | `POST /escalations/create` | 0.5d | 🥉 Medium |
| **8.5** | Centralized logging (DB-backed) | `POST /automation/logs` | 0.5d | 🥉 Medium |

---

## 5. Quick Wins (Do This Week)

These are the highest-impact items that can be done in 1-2 days:

1. **Generate prod secrets** — `openssl rand -hex 32` for both `.env` files
2. **Create n8n httpHeaderAuth credential** — Name: "Backend API Key", Header: `X-Automation-Secret`
3. **Set up ngrok tunnel** — `ngrok http 8000` so n8n cloud can reach the backend
4. **Start backend + test** — `uvicorn app.main:app --reload --port 8000` and run the 23 tests
5. **Activate the Backend Integration Hub workflow** — After tunnel + credential are in place
6. **Add FastAPI path aliases** — Mount `/api/v1/automation/…` endpoints alongside existing paths

---

## 6. Architecture Decision Record

### ADR-1: Path aliases vs workflow URL updates

**Decision**: Add FastAPI aliases rather than updating 80+ URLs in the Social AI OS workflow.
**Rationale**: FastAPI can mount the same router at multiple prefixes with zero code duplication. Updating the n8n workflow URLs is manual, fragile, and would need re-doing each time the workflow template is updated.
**Implementation**: In `main.py`, add a second `app.include_router(ai_router, prefix="/api/v1/automation")` for relevant routers — or create a single `automation_alias_router` that re-exports all endpoints under `/api/v1/automation/`.

### ADR-2: Monorepo services vs single backend

**Decision**: Keep Main Backend (port 8000) + Platform API (port 8001) as separate services.
**Rationale**: The platform-api handles event-driven workstreams (34-45) with different scaling needs than the request-response main backend. Docker Compose manages both.
**Implementation**: Both services share the same `X-Automation-Secret` for auth. They can later merge if the separation proves unnecessary.

### ADR-3: n8n cloud vs self-hosted

**Decision (pending)**: Currently using n8n cloud (shown.app.n8n.cloud) but blocked by SSRF (localhost unreachable).
**Options**:
- **ngrok tunnel** (quickest): `ngrok http 8000`, set FASTAPI_BASE_URL to ngrok URL
- **Self-hosted Docker**: `docker compose up n8n` — full localhost access, but needs maintenance
- **Deploy backend publicly**: Render/Railway/Fly.io — fastest for production

### ADR-4: Factual Grounding & Prompt Behavior Separation (Bangladesh Localization Blueprint)

**Audit Source**: `docs/prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md`
**Decision**: Prompts define behavior; canonical repositories (`PropertyRepository`, `PolicyRepository`, `ContactRepository`) and approved RAG tools define business facts.
**Rationale**:
1. Business facts embedded in system prompts lead to cross-agent drift (e.g. 95 Lakhs BDT vs $250k / 3.5 Cr contradiction in email vs chat).
2. Indian real estate metadata contamination (Mumbai, Bandra, Goa, PAN card, Aadhaar, +91 phone numbers) severely violated operating geography requirements.
3. RAG short-circuiting in property agent discarded knowledge chunks when SQL returned records.
4. Banglish requires multi-signal classification (script ratio + lexical scoring + suffix patterns), not brittle keyword checks.
**Implementation**:
- Canonical data layer in `backend/app/repositories/`.
- Modular, versioned prompt registry in `backend/app/prompts/` rooted in `SYSTEM_CORE_POLICY`.
- Strict 5-tier evidence hierarchy (Live tool/DB > Approved policy > RAG docs > Conversation context > Model knowledge).
- Pre-send response validation via `GroundingValidator`.
- Complete removal of legacy foreign tokens.

---

## 7. Dependency Graph

```
Phase 0 (Infra)
  ├── P0.1 Generate secrets
  ├── P0.2 PostgreSQL + pgvector
  ├── P0.3 n8n credential
  ├── P0.4 ngrok/tunnel
  ├── P0.5 Alembic fix
  └── P0.6 Dual-app resolution
        │
Phase 1 (Core Automation) ── depends on P0.1-P0.5
  ├── 1.1 Lead capture → DB ── depends on P0.2
  ├── 1.2 LLM classification   ── depends on P0.2
  ├── 1.3 Booking → DB         ── depends on P0.2
  ├── 1.4 LangGraph chat       ── depends on P0.2
  └── 1.5 Daily digest         ── depends on 1.1-1.3
        │
Phase 2 (Path Alias) ── can run in parallel with Phase 1
  ├── 2.1 FastAPI aliases
  ├── 2.2-2.5 Missing endpoints
  └── 2.6 Workflow URL update
        │
Phase 3 (Notifications) ── depends on Phase 0
        │
Phase 4 (Social Media) ── depends on Phase 2
        │
Phase 5 (AI Services) ── depends on Phase 0, can parallel Phase 1
        │
Phase 6-8 ── depends on earlier phases
```
