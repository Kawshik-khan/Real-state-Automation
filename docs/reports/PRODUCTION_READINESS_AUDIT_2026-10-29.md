# Production-Readiness Audit: GLG Assets Realstate Automation

- **Date:** 2026-10-29
- **Branch audited:** `main` @ 66dfcc4
- **Method:** read-only. Code reading, git history scan, AST scans of all backend routes and imports, and the project's own linter (oxlint). No source file was changed.
- **Secrets:** token and password values are deliberately not reproduced in this report. Each one is referenced by file and line only.

---

## Step 1: Project overview

- **Backend:** FastAPI on Python 3.11+. The entry point is `backend/app/main.py`. It uses async SQLAlchemy with Postgres/pgvector (Supabase), LangGraph agents, Pinecone, and Groq through the OpenAI SDK. 23 routers are mounted under `/api/v1/*` (main.py:352-375), and 7 "MVP" routes are defined directly under `/api/*` (main.py:290-347).
- **Background workers** start in `lifespan` (main.py:64-124): Gmail poller, report scheduler and ads sync. Every startup also seeds default users.
- **Frontend:** React 19 + Vite 8 + react-router 7, routed by a config object in `frontend/src/App.jsx`:242-278. There's no file-based routing. All API calls go through `frontend/src/services/api.js` and `aiControlPlaneApi.js`.
- **Secondary service:** `platform-api/` is a separate FastAPI app on port 8001. Only docker-compose uses it.
- **Config:** pydantic-settings in `backend/app/config.py` reads `backend/.env`, which is git-ignored. **`.env.example` is also ignored** (`.gitignore` has `.env.*`), so the repo ships no env template.
- **Deploy targets:**
  - `render.yaml` runs uvicorn directly (single worker).
  - `docker-compose.yml` uses `backend/entrypoint.sh` (2 workers, runs Alembic).
  - There's also `frontend/vercel.json`, a root `Dockerfile` and a k8s manifest.
- **CI** (`.github/workflows/ci.yml`): ruff, pytest, eval gate, Vite build, Docker health check. Frontend tests and lint are not run.
- **Context:** two unmerged branches already address part of this report:
  - `origin/claude/principal-engineer-review-t4qi8f` (531cf11, "Security remediation")
  - `chore/remove-n8n-remnants` (a795cc1)

  Neither is on `main`.

---

## A. Summary

| Category | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| 1. Hardcoded data / secrets | 4 | 3 | 1 | 1 | 9 |
| 2. Demo / placeholder / orphan pages | 0 | 5 | 3 | 0 | 8 |
| 3. Dead / unused code | 0 | 0 | 2 | 3 | 5 (+ safe-delete list) |
| 4. Function quality (stubs, fake success, swallowed errors) | 0 | 5 | 2 | 2 | 9 |
| 5. Dev artifacts | 0 | 0 | 0 | 4 | 4 |
| 6. Auth / other risks | 3 | 7 | 7 | 1 | 18 |
| **Total** | **7** | **20** | **15** | **11** | **53** |

---

## B. Findings

### Critical

| # | Sev | Cat | File:line | What's wrong | Evidence | Suggested action | Conf. |
|---|---|---|---|---|---|---|---|
| C1 | Critical | 1 | `mcp-config.json`:7 | A live n8n MCP bearer JWT is committed. It has no `exp` claim, so it never expires. | `"Authorization": "Bearer eyJhbGciOi…"` against `glg-ai.app.n8n.cloud/mcp-server/http` | Revoke the token in n8n now, delete the file, then purge it from history. | High |
| C2 | Critical | 1 | git history: `automation/update_and_publish_active_wf.py`, `automation/upload_email_wf_json.py` | A Telegram bot token (`8098076051:AA…`) and an n8n API JWT (`AUTH_TOKEN = "eyJ…"`) were committed. | Commits d5f9ba1 and f6fe996 are ancestors of `main`. The files were deleted later, but the history is still pushed. | Revoke the bot token via BotFather and rotate the n8n API key. Deleting the files doesn't remove the secrets. | High |
| C3 | Critical | 1 | `backend/scripts/test_pooler.py`:14-22 | A hardcoded list of what look like personal passwords (including name/email variants), looped against Supabase pooler hosts. | `candidate_passwords = [...]`, committed in aed8106 | Change any real account that uses one of these passwords, delete the script, and purge history. | High |
| C4 | Critical | 1/6 | `backend/app/config.py`:30-32; `backend/app/core/crypto.py`:18-25; `render.yaml` | Default `automation_shared_secret`, `jwt_secret` and `password_hash_salt` are public in source, and nothing checks at startup that they were overridden. `render.yaml` never sets `JWT_SECRET` or `PASSWORD_HASH_SALT`. With the defaults, anyone can sign an admin JWT. The integration-credential vault key is derived from the same three values, so stored third-party API keys can be decrypted too. | `jwt_secret: str = "glg_assets_default_jwt_secret_key_2026_minimum_32_chars"`; `_get_master_key()` concatenates those settings. | Fail startup when a default is in use. Add `JWT_SECRET` to render.yaml with `sync: false`. Use a separate vault key. **Unverified:** whether the Render dashboard sets `JWT_SECRET`. | High (code) |
| C5 | Critical | 6 | `backend/app/services/user_service.py`:23-69, 79, 102-135, 167-169; `main.py`:77; `SUPABASE_SCHEMA_LATEST.sql`:1092-1098 | Five accounts (admin, manager, agent, developer, viewer) with passwords like `admin123` are re-seeded on every startup and also live in an in-memory fallback. `get_user_by_email` falls back to the in-memory copy when the DB has no row, so deleting `admin@glgassets.com` in the DB still leaves `admin123` working. | `"password": "admin123"` … `return self._in_memory.get(email_clean)` | Remove the hardcoded seed and the fallback. Bootstrap the first admin from env or a CLI, one time only. | High |
| C6 | Critical | 6 | `backend/app/services/ai_control_plane/control_plane_service.py`:1478 via `backend/app/api/v1/ai_control_plane/endpoints.py`:834 | `eval()` runs a user-supplied expression. `{"__builtins__": None}` can be escaped through `().__class__.__base__.__subclasses__()`, so this is server code execution for developer/admin users, and for anyone once combined with C4 or C5. The route is mounted twice (`/api/ai` and `/api/v1/ai-control`). | `triggered = bool(eval(expression, {"__builtins__": None}, safe_names))` | Replace it with an AST allow-list evaluator. The security branch has `safe_expression.py` for this. | High |
| C7 | Critical | 6 | `backend/app/api/v1/social/endpoints.py`:465, 474 | `POST /api/v1/social/telegram/setup-webhook` has no auth. Anyone can repoint the bot's webhook and receive every customer message. `GET /telegram/status` is also unauthenticated. | `async def setup_telegram_webhook(body: dict):` has no `Depends` (confirmed by an AST scan of all routes). | Require the admin/developer role, or remove the route. | High |

### High

| # | Sev | Cat | File:line | What's wrong | Evidence | Suggested action | Conf. |
|---|---|---|---|---|---|---|---|
| H1 | High | 6 | `backend/app/config.py`:39; `backend/app/main.py`:138-145; `render.yaml`:19 | The default `cors_origin_regex` is `^https?://.*` and credentials are allowed, so any website can make credentialed requests. render.yaml also sets `CORS_ORIGINS: "*"`. | `allow_origin_regex=settings.cors_origin_regex, allow_credentials=True` | Default the regex to `None` and set explicit origins. | High |
| H2 | High | 6 | `backend/app/api/v1/social/endpoints.py`:366 | The Telegram webhook doesn't check `X-Telegram-Bot-Api-Secret-Token`. Forged updates with any `chat_id` make the bot send LLM replies to arbitrary chats and burn LLM credits. | No header check before `telegram_service.send_message(chat_id=…)` | Set `secret_token` on `setWebhook` and verify it, failing closed. | High |
| H3 | High | 6 | `backend/app/api/v1/social/endpoints.py`:266 | The Instagram webhook POST doesn't verify the signature, although the Facebook handler does (:228). Forged comments trigger public replies and DMs. | `async def instagram_webhook_event(body: dict):` | Reuse `verify_signature` as in `facebook_webhook_event`. | High |
| H4 | High | 2/6 | `backend/app/api/v1/social/endpoints.py`:185-199 | `/simulator/comment-to-dm` is an unauthenticated demo endpoint in production. It runs the LLM, calls the Meta reply/DM APIs, writes conversations and sends Telegram alerts. Demo text and name are hardcoded. | Default `"Banani 3 BHK flat er price koto?…"`, `"Mahmudur Rahman"` | Delete it, or require the developer role and hard-disable outbound calls. | High |
| H5 | High | 1 | `backend/app/api/v1/social/endpoints.py`:214 | A hardcoded Meta webhook verify-token fallback. | `or "glg_wa_verify_2026"` | Fail when `WHATSAPP_VERIFY_TOKEN` is unset. | High |
| H6 | High | 6 | `backend/app/api/v1/ws/websocket.py`:40-58 | `/api/v1/ws/chat` has no auth, yet broadcasts lead PII: names, comment text, DMs and lead scores (sent from social/endpoints.py:89-99). | `await manager.connect(websocket)` with no token check | Require a short-lived ticket or JWT before `accept()`. | High |
| H7 | High | 6 | `backend/app/dependencies.py`:15-47; `backend/app/core/security.py`:63-69 | `require_automation_secret` accepts any JWT that has a `role`, including the **viewer** role and **refresh tokens** (`decode_access_token` never checks `type`). About 120 of 229 routes use only this check. So a viewer can delete conversations (conversations/endpoints.py:462), send agent replies (:696), toggle takeover (:655) and trigger report delivery (reports/endpoints.py:104). | `if payload and "role" in payload: return {...}` | Enforce `type == "access"` and add `require_roles` to mutating routes. | High |
| H8 | High | 6 | `backend/app/api/v1/knowledge/endpoints.py`:86, 92, 123-124 | Path traversal: a form-supplied `doc_id` like `../../x` writes a `.txt` file outside the knowledge directory. Uploads are read with no size cap. Admin/developer only. | `save_path = base_dir / f"{final_doc_id}.txt"` | Validate `doc_id` against `[A-Za-z0-9_-]+`, check the resolved path stays inside `base_dir`, and cap upload size. | High |
| H9 | High | 6/1 | `backend/app/api/v1/conversations/endpoints.py`:286-313; `backend/app/config.py`:70-72; `render.yaml`:52-57 | Every message POSTs lead name, phone and last message to `https://glg-ai.app.n8n.cloud/webhook/google-sheets-leads`, even though n8n was removed from the repo (6e6ae0d). PII goes to an external endpoint you may no longer control. | `url = f"{n8n_base}/webhook/google-sheets-leads"`, with the hardcoded default URL | Remove it (branch `chore/remove-n8n-remnants` does). **Unverified:** who controls that n8n tenant now. | High |
| H10 | High | 4 | `backend/app/services/email_service.py`:132-252 | `dispatch_reply_via_n8n` returns `success: True, dispatched: True` even when both n8n and SMTP failed (failures are only logged). Threads live only in memory (:27), so they're lost on restart and not shared across workers. | Hardcoded return at :244-252 | Return the real delivery status and persist threads. | High |
| H11 | High | 4 | `backend/app/api/v1/automation/endpoints.py`:49-83, 106-116, 228-229 | Fake completions:<br>• Booking swallows DB errors (`except Exception: pass`, :72) yet returns `"CONFIRMED"` with hardcoded agent "Sarah Connor" and phone `+880 1700-000000`.<br>• `/notify` returns `sent: True` for email, Slack and Telegram without sending anything (TODOs).<br>• `/logs` discards input. | See lines | Implement these or delete them (they were n8n consumers). | High |
| H12 | High | 1/4 | `backend/app/api/v1/analytics/endpoints.py`:81-160, 177-228; `backend/app/api/v1/developer/endpoints.py`:98-112 | Fabricated metrics:<br>• `cross-role-summary` is entirely hardcoded (e.g. `"n8n_workflows_active": "6/6 (Healthy)"`).<br>• `total_leads = conversations * 3` (:132) and `unique_users = max(x*0.57, 89)` (:103).<br>• Invented fallback numbers (42, 156, 142…).<br>• System-health reports n8n `"CONNECTED"` and a DB pool of 8. | See lines | Compute from the DB, or return an "empty" state as `/social-kpis` already does. | High |
| H13 | High | 4 | `backend/app/api/v1/social/endpoints.py`:291-360 | Seven stub endpoints return fake success: `facebook/send` (`"status": "sent"`), `instagram/dm`, `website/livechat`, `whatsapp/incoming` (POST), `whatsapp/media`, `leads/capture` (`"stored_in": ["google_sheets","supabase"]`), `facebook/incoming`. | Hardcoded dicts | Delete them (n8n-era), or implement them. | High |
| H14 | High | 2 | `frontend/src/pages/AnalyticsPage.jsx`:32-53, 60, 76, 110-340 | The whole page is static: charts, KPIs ("94.2%") and "insights". `liveReport` is fetched but never rendered (oxlint confirms). It shows hardcoded lead names and phone numbers. | `const HOT_LEADS = [{ name: 'John Doe', phone: '+880 1711-998877', …` | Wire it to the analytics API, or remove the route. | High |
| H15 | High | 2 | `frontend/src/pages/EmailInboxPage.jsx`:23, 114-115, 138 | Mock threads are the initial state and the silent fallback, so real-looking customer emails (with a gmail address) appear as genuine inbox items. | `useState(MOCK_EMAIL_THREADS)`; `console.log('Using local mock threads fallback'…)` | Start empty and show an error state. | High |
| H16 | High | 2 | `frontend/src/pages/PropertiesPage.jsx`:50, 127-155 | When an API field is missing, fake price, location, coordinates, amenities and brochure are merged into real projects field by field. Every project without a brochure links to one hardcoded Supabase PDF. | `price: … (p.price \|\| fallback.price)`; brochure URL at :154 | Show "—" for missing fields and drop `MOCK_PROJECTS`. | High |
| H17 | High | 2/6 | `frontend/src/pages/N8nMonitoringPage.jsx`:26; `frontend/src/App.jsx`:15, 62, 82-83, 99, 272-273; `frontend/src/services/api.js`:645-680 | **Broken page:** it calls `/api/v1/automation/n8n/*`, but those backend routes were deleted (grep finds none in backend/app). The page is still routed and linked. | `resilientFetch('/api/v1/automation/n8n/health', …)` | Remove the page, route and helpers (done on `chore/remove-n8n-remnants`). | High |
| H18 | High | 4 | `frontend/src/pages/DeveloperConsolePage.jsx`:260-370, 527-535, 711-745; `frontend/src/services/api.js`:940-945, 993-998 | When the backend is unreachable, the eval quality gate "runs" in the browser using `simulate_fail` flags from bundled JSON and displays PASSED/FAILED scorecards. The latest-report fallback returns the bundled baseline as `success: true`. | `runClientSimulation`, `execution_mode: 'client_simulation'` | Remove the client simulation. Show "backend offline" instead of results. | High |
| H19 | High | 2 | `frontend/src/components/ai-control-plane/IncidentManagementView.jsx`:15, 41 | The incident list is static (`SAMPLE_INCIDENTS`). `getAiIncidents`, `createAiIncident` and `updateAiIncident` exist in aiControlPlaneApi.js but are never imported. | `useState(SAMPLE_INCIDENTS)` | Wire it to the API, or hide it. | High |
| H20 | High | 6 | `frontend/src/services/auth.js`:63, 92, 111; `frontend/src/services/aiControlPlaneApi.js`:625-626 | The 7-day refresh token is stored in localStorage, which defeats the HttpOnly cookie: any XSS steals a 7-day session. The access JWT is also sent in an SSE query string, so it ends up in access logs. | `localStorage.setItem('glg_refresh_token', …)`; `?token=${…}` | Keep the refresh token in the cookie only. Use short-lived stream tickets. | High |

### Medium

| # | Sev | Cat | File:line | What's wrong | Evidence | Suggested action | Conf. |
|---|---|---|---|---|---|---|---|
| M1 | Medium | 6 | `backend/app/api/v1/auth/endpoints.py`:40-41; `backend/entrypoint.sh` (`--forwarded-allow-ips "*"`) | Login lockout keys on a client-supplied `X-Forwarded-For`, so rotating the header bypasses lockout. | `client_ip = request.headers["x-forwarded-for"].split(",")[0]` | Trust XFF only from known proxies. | High |
| M2 | Medium | 6 | `frontend/src/App.jsx`:243-277 | No role guards on routes. A viewer can open `/developer`, `/ai-studio` and `/reports` (the backend blocks some API calls, not all; see H7). | Only `/overview` branches on role | Add a `RequireRole` wrapper. | High |
| M3 | Medium | 4/6 | `frontend/src/services/api.js`:242-282, 284-297 | Silent token refresh is dead code. `fetchWithAuth` is never called (only imported, unused, in aiControlPlaneApi.js:1), and `handleResponse` has no 401 handling. Sessions should hard-fail after 15 minutes. | grep: no call sites | Route all calls through one client that handles 401. **Unverified at runtime.** | Medium |
| M4 | Medium | 6 | `frontend/src/services/api.js`:38, 131, 203-225 | `resilientFetch` replays any method, including POST and DELETE, against up to 5 candidate hosts after a network error, which can double-send replies. Base URLs can be overridden from localStorage (`glg_api_base_url`, `glg_working_backend`), so a planted value redirects bearer tokens. | `for (const url of candidates) { … fetch(url, options) }` | Retry only GETs and remove the storage overrides. | High |
| M5 | Medium | 6 | `backend/entrypoint.sh` (`WORKERS=${WEB_CONCURRENCY:-2}`); `backend/app/core/security.py`:19-20; `conversations/endpoints.py`:27; `email_service.py`:27; `report_scheduler.py`; `email_poller.py` | Docker runs 2 workers, but a lot of state is per-process: refresh registry, conversation cache, WebSocket clients, email threads, in-memory users. The report scheduler and email poller have no cross-worker lock, so reports and auto-replies would go out twice. | grep finds no lock or leader election in either worker | Run workers in one process, or add a DB advisory lock. **Unverified at runtime.** | Medium |
| M6 | Medium | 6 | `SUPABASE_SCHEMA_LATEST.sql`:1092 vs `backend/app/models/models.py`:450 and migration `0006_auth_users.py`:26 | Schema drift: the dump uses column `password_hash`, while the model and migration use `hashed_password`. If the DB was built from the dump, every auth lookup fails and silently falls back to the hardcoded users (C5). | Column names differ | Compare against the live DB. **Unverified.** | Medium |
| M7 | Medium | 3/6 | `backend/requirements.txt`; `pyproject.toml` | Imported packages are missing from requirements: `cryptography` (crypto.py:35, so it falls back to a homemade cipher at :46+), `redis` (redis_client.py:99, so it's silently disabled), `pdfplumber`, `PyPDF2`. pyproject lists `psycopg[binary]` (never imported) and omits `langchain-core`. Two dependency manifests plus uv.lock have drifted. | AST import scan | Add the missing packages and keep one source of truth. Whether `cryptography` arrives transitively is **unverified**. | High |
| M8 | Medium | 6 | `render.yaml`:9; `backend/entrypoint.sh`:25; root `alembic.ini` + `migrations/` | Render bypasses the entrypoint, so Alembic never runs there. The entrypoint swallows migration failures (`\|\| echo …`). The root `migrations/` is a stale copy with only 0001-0004 (backend has up to 0008). | `diff` of the versions dirs | Pick one migration path and make failures fatal. | High |
| M9 | Medium | 4 | `backend/app/api/v1/developer/endpoints.py`:269 | Production code imports an ops script at runtime. | `from scripts.sync_databases import sync_pinecone_and_supabase` | Move it into `app/services`. | High |
| M10 | Medium | 4 | `backend/app/api/v1/automation/endpoints.py`:281-290 | Returns `success: True` on exception and leaks `str(exc)` to the caller. | `"error_message": str(exc)` | Return 5xx and log internally. | High |
| M11 | Medium | 2 | `frontend/src/pages/ConversationsPage.jsx`:437-445, 856, 1195-1290 | A "Simulate New Lead" demo feature is in the production UI and defaults the phone to `+880 1711-998877`. | Button "Simulate New Lead" | Needs your decision (D). | High |
| M12 | Medium | 2 | `CriticalDatesTimeline.jsx`:8, 56; `ValuablePropertiesTable.jsx`:7, 55; `AIEngagementChart.jsx`:16, 27; `WorkflowBuilderView.jsx`:18-29 | Dashboard widgets start with, and fall back to, fake `DEFAULT_*` data. | `useState(DEFAULT_CRITICAL_DATES)` | Use loading and empty states. | High |
| M13 | Medium | 6 | `docker-compose.yml`:40, 100-140 | The n8n service is still defined (`N8N_AUTH_ENABLED: "false"`, port 5678 published, default encryption key). `AUTOMATION_SHARED_SECRET` defaults to `glg-secret-key`. | See lines | Remove n8n and require secrets with `${VAR:?}`. | High |
| M14 | Medium | 2/4 | `platform-api/` (all endpoints); `platform-api/app/config.py`:12-19; `platform-api/app/main.py`:18-24, 55-57 | The entire service is stubs returning fake "processed/queued/executed". Default secret `change-me-in-production`; CORS `*` with credentials; `print` at startup. Only docker-compose references it. | `"status": "distributed"` etc. | Needs your decision (D). | High |
| M15 | Medium | 6 | `backend/app/api/v1/conversations/endpoints.py` (whole file) | No tenant scoping: `tenant_id` is never used in queries, while the config talks about multi-tenancy. | grep `tenant_id` finds nothing relevant | Only matters if you go multi-tenant. Needs your decision. | High |

### Low

| # | Sev | Cat | File:line | What's wrong | Evidence | Suggested action | Conf. |
|---|---|---|---|---|---|---|---|
| L1 | Low | 1 | `render.yaml`:23, 51; `PropertiesPage.jsx`:154; `property_tool.py`:102; `api.js`:73, 169; `social/endpoints.py`:28, 198, 446 | Hardcoded identifiers: Supabase project URL, Pinecone host, onrender backend URL, the `"glg-assets-main"` tenant literal. These aren't secrets. | See lines | Move them to settings or env. | High |
| L2 | Low | 5 | backend/app: 44 `print()` calls. llm.py 17, vector_store.py 8, social/endpoints.py 4, evals/engine.py 4, telegram.py 3, ai/endpoints.py 2, meta_social.py 2, supabase_storage.py 2, developer/endpoints.py 1, knowledge/endpoints.py 1 | `print` instead of the logger. | grep | Replace with `logger`. | High |
| L3 | Low | 5 | `automation/endpoints.py`:109, 112, 115, 176, 201, 228 | All 6 TODOs in app code: SendGrid, Slack, Telegram integration, LLM classification, DB metrics, log store. | grep | Covered by H11. | High |
| L4 | Low | 5 | `redis_client.py`:99 `# type: ignore`; `database.py`:83 `# noqa: F401` | The only two lint suppressions. Both are justified (optional import; side-effect model registration). | grep | No action. | High |
| L5 | Low | 5 | Frontend: about 60 `console.*` calls across 33 files (DeveloperConsolePage 12, ConversationsPage 10). One `console.log` at `EmailInboxPage.jsx`:138. | grep | Strip or gate behind dev mode. | High |
| L6 | Low | 3 | Frontend: 338 oxlint warnings. Mostly unused lucide imports; unused `loading` state in 9 components; `App.jsx`:1 (`useEffect`), 180 (`isAdmin`), 183 (`isViewer`); empty blocks at `DeveloperConsolePage.jsx`:423, 469, 498. | oxlint output | Run `oxlint --fix`, then review. | High |
| L7 | Low | 4 | backend: 45 swallowed `except: pass/continue` blocks. The worst are `account_lockout.py` (52, 100, 114, 130), `two_tier_cache.py` (60, 78, 99), `belief_memory.py` (86, 111, 128), `automation/endpoints.py`:72. | AST scan | Log at least at warning level. Lockout failures should fail closed. | High |
| L8 | Low | 4 | 38 backend functions are over 80 lines. Top: `ensure_db_seeded` 264 (ai_control_plane_store.py:1109), `PropertyAgent.handle` 221 (property_agent.py:191), `generate_and_deliver` 207 (report_scheduler.py:33), `run_suite` 200 (evals/engine.py:107), `ai_chat` 127 (ai/endpoints.py:21). Frontend `DeveloperConsolePage.jsx` is 4,077 lines. | AST scan / wc | Split as you touch them. | High |
| L9 | Low | 4 | `main.py`:256; `automation/endpoints.py`:17; `dependencies.py`:15; `conversations/endpoints.py`:485-510; `platform-api/app/dependencies.py` | Five separate implementations of "check automation secret". Two HTTP clients in the frontend (`resilientFetch` used 38 times, `fetchWithAuth` never). 55 direct `localStorage.getItem('glg_token')` reads. | grep | Consolidate. | High |
| L10 | Low | 3 | `.benchmarks/datasets/*.json` and `backend/app/evals/datasets/*.json` | Byte-identical duplicates, and both are read (run_ci_evals.py:33; engine.py:22-23). Also `data/knowledge/documents_registry.json` vs `backend/data/...` (they differ), and root `Dockerfile` vs `backend/Dockerfile`. | `cmp` | Keep one copy of each. | High |
| L11 | Low | 6 | `.github/workflows/ci.yml` | Frontend `vitest` and `oxlint` never run in CI. | No such step | Add them. | High |

---

## C. Safe-to-delete list (High confidence only)

Each item was searched across the whole repo: Python and JS imports, config, Dockerfiles, CI, scripts, tests, and string references.

**Backend**
- `backend/app/api/v1/automation/compat.py`: whole file. n8n stub router, never imported or mounted.
- `backend/app/api/v1/social/compat.py`: whole file. Same.
- `backend/app/agents/supervisor.py`: whole file. Never imported; the graph uses `supervisor_node` in graph.py.
- `backend/app/persistence/models.py`: whole file. Re-export shim with no importers.
- `backend/app/services/supabase_storage.py`: whole file. `upload_to_supabase_storage` is never called.
- `backend/app/main.py`:256-264: `verify_automation_secret`, unused.
- `backend/app/api/v1/auth/endpoints.py`:31: `USERS_DB`, assigned and never read.
- `backend/test_invoke.py`: step-by-step `print` debug script.
- `backend/Dockerfile.override`: references a manual `docker cp` workflow; nothing builds it.
- `backend/n8n-workflows/` (2 `.ts` files): n8n leftovers. `incoming-whatsapp.ts` even starts with a Python docstring, so it isn't valid TypeScript.
- `backend/scripts/test_pooler.py`: see C3.

**Frontend**
- `frontend/src/components/dashboard/PropertyEstateMap.jsx`: imported nowhere (only docs mention it).
- `frontend/src/App.css`: leftover Vite template (`.counter`…), never imported.
- `frontend/src/assets/hero.png`, `frontend/src/assets/vite.svg`, `frontend/src/assets/react.svg`, `frontend/public/icons.svg`: never referenced (index.html uses only `favicon.svg`).
- Unused imports and variables from L6 (oxlint).

**Repo root**
- `mcp-config.json`: after revoking the token (C1).

---

## D. Needs your decision

1. **The unmerged security branch** `origin/claude/principal-engineer-review-t4qi8f` (531cf11). Its commit message says it fixes C4, C6, C7, H1-H3, H5-H8, H20, M1 and M2 (eval to AST, JWT/automation-secret split, token types, webhook signatures, stream tickets, CORS, path traversal, role guards). Merge or rebase it instead of redoing the work? It will conflict with later work on `main`.
2. **Branch `chore/remove-n8n-remnants`** (a795cc1): already removes H9, H17, M13, the compat routers, n8n-workflows/ and mcp-config.json. Merge it?
3. **`platform-api/`** (M14): 100% stubs, used only by docker-compose. Delete, or is it a planned service?
4. **Social/automation endpoints** (H11, H13: `/facebook/send`, `/leads/capture`, `/automation/booking`, `/notify`…): were these only for n8n? If no external caller remains, delete them; otherwise implement them.
5. **Demo features in the production UI:** "Simulate New Lead" (M11), the Developer Console webhook simulator and in-browser eval simulation (H18), `/simulator/comment-to-dm` (H4). Keep them behind a dev flag, or remove?
6. **Unused API client functions:** 22 in api.js (e.g. `getCalendarEvents`, `createSiteTourBooking`, `getAgentConfigs`, `getFineTuningJobs`, `unlockUserAccount`, `createReportSchedule`) and 18 in aiControlPlaneApi.js (e.g. `getAiIncidents`, `tripCircuitBreaker`, `rollbackAiAgent`, `getAiMemories`). The backend endpoints exist, so they may be planned UI work. Medium confidence that they're dead.
7. **Backend methods referenced nowhere else** (Medium confidence; something could call them via `getattr` or an external caller):
   - `rate_limiter.py`:99 `check_sliding_window_rate_limit`, `two_tier_cache.py`:33 `_purge_l1_expired`
   - `property_repository.py`:185, 238, 245; `location_service.py`:79, 94; `memory.py`:63 `to_openai_messages`; `meta_social.py`:117 `send_dm_by_psid`
   - `supabase_db.py`:102-165 (6 methods); `user_service.py`:171 `get_user_by_id`; `ads_repository.py`:328
   - `ai_control_plane_store.py`:1742, 1821, 1973, 2960; `models/report.py`:69, 80, 98; `schemas/ai_control_plane.py`:14, 204; `agents/state.py`:44
   - The SQLAlchemy record classes flagged by the same scan are **not** dead: `create_all`/metadata uses them.
8. **Committed runtime stores:** `backend/data/report_store.json`, `ai_control_plane_store.json`, `agent_configurations.json` are written at runtime as fallbacks and contain demo recipients and phones. Keep them as seed fixtures, or git-ignore them?
9. **`SUPABASE_SCHEMA_LATEST.sql`** (69 KB, includes bcrypt hashes of the default passwords): keep as documentation, or delete in favour of Alembic?
10. **Git history purge** (C1-C3): rewriting history (`git filter-repo`) needs a force-push and every clone to re-sync. Rotating the credentials is mandatory either way; the purge is your call.

---

## E. Recommended cleanup order

1. **Rotate and revoke now, outside the code:** the n8n MCP token (C1), the Telegram bot token and n8n API key (C2), any account using the passwords in C3. Confirm `JWT_SECRET`, `AUTOMATION_SHARED_SECRET` and `PASSWORD_HASH_SALT` are set to non-default values in Render (C4).
2. **Close remote-exploitable holes:** C6 (eval), C7 (Telegram setup), C5 (default users and fallback), C4 (fail on default secrets), H1 (CORS), H2/H3 (webhook verification), H4 (simulator), H6 (WebSocket), H7 (token type plus roles), H8 (path traversal). Decision 1 probably covers most of this in one merge.
3. **Stop data leaving the system and stop fake successes:** H9 (n8n lead sync), H10 (email status), H11/H13 (stub endpoints), M10.
4. **Fix broken things:** H17 (n8n page), M3 (token refresh), M6 (schema drift check), M7 (missing dependencies), M8 (migrations), M5 (multi-worker duplicates).
5. **Remove fake data from the UI and API:** H12, H14-H16, H18, H19, M11, M12.
6. **Dead code:** section C, then the section D items you approve.
7. **Quality:** L2/L5 logging, L7 swallowed errors, L9 consolidation, L6 lint, L10 duplicates, L11 CI, L8 long functions as you touch them.

No code changes will be made until this report is approved.
