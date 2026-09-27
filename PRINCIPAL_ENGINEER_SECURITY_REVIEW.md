# Principal Engineer Review — GLG Assets Social AI OS (backend)

**Scope reviewed:** `backend/` FastAPI service — auth & trust boundaries, the 200+ API
endpoints, the AI Control Plane, RAG/knowledge ingestion, rate limiting, and the
config/deploy surface (`render.yaml`, `docker-compose.yml`, frontend secret handling).
Language/runtime: Python 3.11/3.12, FastAPI 0.11x, SQLAlchemy 2 async. Deploy target:
Render (public internet) + Supabase Postgres/pgvector + n8n Cloud.
`platform-api/` and `frontend/` were spot-checked, not fully audited.

**Method:** static trace + live reproduction. All CRITICAL/HIGH findings below were
executed against the real app with `fastapi.testclient` (see "Reproduction"). Findings
are labelled **[PROVEN]** (I ran the exploit) or **[SUSPECTED]** (needs runtime/prod
confirmation).

---

## 1. Executive Summary

The authentication system has a **structural single-key failure**: the same
`AUTOMATION_SHARED_SECRET` is (a) the JWT signing key, (b) a master API bearer that
resolves to `role=admin`, and (c) shipped to every browser in the frontend JS bundle
(hardcoded fallback `3322af28…`, also committed in `automation/setup_credentials.py`).
Anyone who loads the SPA — or reads the public git repo — obtains a value that lets them
**forge admin JWTs and call any endpoint as admin**. That secret then unlocks an
**`eval()`-based remote code execution** primitive in the AI Control Plane policy
simulator. This is a full remote compromise reachable by an unauthenticated internet user.

Independently, a large set of state-changing endpoints (conversations CRUD, manual agent
replies, conversation deletion, Telegram webhook registration, n8n workflow toggle) have
**no authentication at all**.

The 5 things to fix first:
1. **Split the secrets** — separate random `JWT_SECRET`; stop reusing the automation
   secret as the JWT key; remove the hardcoded frontend fallback secret and rotate it. (F1)
2. **Remove `eval()`** from `simulate_policy` — it is RCE. (F2)
3. **Add auth** to the unauthenticated conversation/social/automation endpoints. (F4)
4. **Reject refresh tokens used as access tokens**, and enforce revocation on the access
   path. (F3)
5. **Rotate every credential committed to git** (n8n JWT, Telegram bot token, shared
   secret) and purge from history. (F5)

Honest one-liner: what breaks first in production is not load — it is the first person
who opens DevTools, copies the shared secret out of the JS bundle, and POSTs one `eval`
expression to `/api/v1/ai-control/policies/simulate`.

---

## 2. Findings Table

| ID | Severity | Status | Category | Location | Summary |
|----|----------|--------|----------|----------|---------|
| F1 | CRITICAL | PROVEN | Auth / Secrets (CWE-798, CWE-522) | `core/security.py:11`, `config.py:30-31`, `frontend/src/services/api.js:85` | Automation secret == JWT key == admin bearer, and it's shipped to the browser → forge admin JWTs |
| F2 | CRITICAL | PROVEN | Injection / RCE (CWE-95) | `services/ai_control_plane/control_plane_service.py:1478` | `eval()` on user expression; sandbox escape → arbitrary code execution |
| F3 | HIGH | PROVEN | Broken auth (CWE-287, CWE-613) | `dependencies.py:30-46`, `core/security.py:52-77` | Refresh token accepted as access token; revocation/logout not enforced on access path |
| F4 | HIGH | PROVEN | Missing authz (OWASP A01) | `conversations/endpoints.py:284,406,563,603`; `social/endpoints.py:343,443`; `automation/endpoints.py:351` | State-changing endpoints have no auth dependency |
| F5 | HIGH | PROVEN | Secrets in VCS (CWE-798) | `mcp-config.json:7`, `automation/*.py`, `automation/update_and_publish_active_wf.py:109` | Live n8n JWT, Telegram bot token, shared secret committed to git |
| F6 | HIGH | SUSPECTED | Meta webhook forgery (CWE-345) | `social/endpoints.py:217,244` | FB/IG webhooks process events with no `X-Hub-Signature-256` verification |
| F7 | MEDIUM | PROVEN | Weak password storage (CWE-916/759) | `core/security.py:20-23` | Unsalted single-round HMAC-SHA256; global static salt; non-constant-time compare |
| F8 | MEDIUM | PROVEN | Multi-tenant isolation (CWE-282) | `auth/endpoints.py:137-144`, `security.py:88-115`, `dependencies.py:32` | `tenant_id` dropped on token refresh → tenant becomes default |
| F9 | MEDIUM | PROVEN | DoS / auth (CWE-307, CWE-400) | `auth/endpoints.py:117-119`, `account_lockout.py:29` | In-request `asyncio.sleep` delay; lockout keyed only by email → account-lockout DoS of victims |
| F10 | MEDIUM | PROVEN | CORS misconfig (CWE-942) | `main.py:130-131`, `render.yaml` `CORS_ORIGINS:"*"` | `allow_origins=["*"]` + `allow_credentials=True` |
| F11 | MEDIUM | PROVEN | Auth state not durable (CWE-613) | `core/security.py:16-17` | Refresh-token registry is in-process dict → lost on restart / not shared across workers |
| F12 | LOW | PROVEN | Correctness / data (—) | `conversations/endpoints.py:22,378` | Conversations served from a process-global list → wrong data with >1 worker |
| F13 | LOW | PROVEN | Observability (CWE-532) | `main.py:60-63` | Global `warnings.simplefilter("ignore")` + broad swallowed excepts hide failures |

---

## 3. Detailed Findings

### [F1] Single shared secret is the JWT key, an admin bearer, AND shipped to browsers — CRITICAL | PROVEN | CWE-798, CWE-522, CWE-321
**Location:** `backend/app/core/security.py:11`; `backend/app/config.py:30-31`;
`backend/app/dependencies.py:32-46`; `frontend/src/services/api.js:85` &
`frontend/src/services/aiControlPlaneApi.js:3`; `render.yaml` (`JWT_SECRET` not set).

**What's wrong:** Three trust roles collapse onto one value:
- `SECRET_KEY = settings.jwt_secret or settings.automation_shared_secret` — `JWT_SECRET`
  is unset in `render.yaml`, so the HS256 signing key **is** the automation secret.
- `require_automation_secret` treats a raw `X-Automation-Secret`/Bearer equal to that
  secret as `role=ADMIN` (`dependencies.py:44-46`), and `get_current_user` does the same
  (`dependencies.py:56-63`).
- The frontend hardcodes that secret as a build fallback
  (`3322af28…[redacted]`) and even when
  `VITE_AUTOMATION_SECRET` is injected at build time, Vite **bakes it into the public JS
  bundle**. The same value is committed in `automation/setup_credentials.py:35`.

**Impact / exploit:** Any internet user who loads the dashboard (or reads the repo)
extracts the secret, then either sends it as `X-Automation-Secret` (instant admin) or
signs a JWT with any `role`/`tenant_id` they like. Total auth bypass and cross-tenant
takeover; it is also the key that unlocks F2 (RCE).

**Reproduction (executed):**
```
[forged-JWT -> /auth/users] HTTP 200 :: [{"email":"admin@glgassets.com",...}]   # JWT signed with the shared secret
[X-Automation-Secret -> /ai-control/policies/simulate] HTTP 200                  # secret alone = admin
```

**Fix (minimal):**
- Generate an independent `JWT_SECRET` (32+ random bytes) and set it in Render; never fall
  back to the automation secret for signing.
- Remove the hardcoded fallback in `api.js`/`aiControlPlaneApi.js`. The browser must not
  hold a service secret at all — the SPA should authenticate as a *user* (login → JWT) and
  send only that JWT. Reserve `X-Automation-Secret` for server-to-server callers (n8n).
- Rotate the shared secret after purging it from git (F5).

---

### [F2] `eval()` in policy simulator → remote code execution — CRITICAL | PROVEN | CWE-95
**Location:** `backend/app/services/ai_control_plane/control_plane_service.py:1478`,
reached via `POST /api/v1/ai-control/policies/simulate`
(`ai_control_plane/endpoints.py:834-839`).

**What's wrong:**
```python
triggered = bool(eval(expression, {"__builtins__": None}, safe_names))
```
`{"__builtins__": None}` is **not** a sandbox. The classic object-graph walk
(`().__class__.__base__.__subclasses__()[…]`) reaches OS-level callables and yields
arbitrary code execution from a fully attacker-controlled `condition_expression`.

**Impact / exploit:** RCE on the backend host — read `DATABASE_URL`/service-role keys,
pivot to Supabase and n8n, exfiltrate all tenant data. The endpoint is nominally
DEVELOPER/ADMIN-gated, but F1 hands any anonymous user that role, so this is
**remote, unauthenticated RCE** in practice.

**Reproduction (executed, benign):** I confirmed `eval` reaches the arbitrary object
graph without spawning a shell:
```
POST /api/v1/ai-control/policies/simulate
  {"condition_expression":"().__class__.__base__.__subclasses__()[0].__name__ == ...","context":{}}
-> HTTP 200 {"success":true,"triggered":true,...}     # arbitrary object access succeeds
```
The same reachability is what an attacker uses to reach OS calls; I deliberately did not
run the shell payload.

**Fix (minimal):** Do not `eval`. Parse the condition with `ast.parse(expr, mode="eval")`
and walk an allow-list of node types (`BoolOp/Compare/Name/Constant/comparators`), or
replace the "pythonic expression" feature with a small structured rule schema
(`{field, op, value}`). Reject anything else.

---

### [F3] Refresh tokens accepted as access tokens; revocation not enforced on access — HIGH | PROVEN | CWE-287, CWE-613
**Location:** `backend/app/dependencies.py:30-46` & `85-101`;
`backend/app/core/security.py:52-77`.

**What's wrong:** `decode_access_token` never checks the `type` claim, and the auth
dependencies accept **any** validly-signed JWT that carries a `role`. A 7-day refresh
token therefore works as a bearer on every protected endpoint. Worse, access-token
validation is pure signature+exp — it does not consult the revocation set — so `logout`
and replay-revocation (which only touch the refresh registry) do not stop a stolen token.

**Impact / exploit:** A leaked/rotated refresh token grants 7 days of full API access;
logging out does not actually end the session for the access path.

**Reproduction (executed):**
```
[refresh-as-bearer -> /auth/users]              HTTP 200   # refresh token used as access
[AFTER logout, refresh-as-bearer -> /auth/users] HTTP 200  # revocation not enforced
```

**Fix:** In `decode_access_token`/the dependency, require `payload["type"] == "access"`.
Add a `jti` to access tokens and check it against a revocation store (Redis) on each
request, or keep access-token TTL very short (already 15m) and document that logout only
kills the refresh chain — but at minimum reject `type=refresh` on protected routes.

---

### [F4] State-changing endpoints with no authentication — HIGH | PROVEN | OWASP A01 (Broken Access Control)
**Location (no auth dependency):**
`conversations/endpoints.py:284` (list), `:406` (**delete**), `:459` (messages),
`:563` (takeover), `:603` (**manual agent reply**); `social/endpoints.py:343`
(**telegram webhook → AI pipeline**), `:443` (**setup-webhook**), `:452` (status),
`:181` (comment-to-DM simulator); `automation/endpoints.py:351` (**n8n toggle**),
`:362` (n8n test), `:344` (n8n health).

**What's wrong:** These handlers take no `Depends(_auth)`/`require_roles`. Anyone can read
and delete conversations, **post messages that are delivered to real customers as the
human agent**, flip AI-takeover, register an attacker-controlled Telegram webhook, and
disable n8n workflows. `/telegram` also drives the LLM pipeline with no shared secret,
enabling cost-burn/abuse.

**Impact / exploit:** Customer-data disclosure and destruction, brand/impersonation
(fraudulent replies telling leads to wire deposits), automation sabotage, LLM cost abuse.

**Reproduction (executed):**
```
[GET /conversations]                    HTTP 200
[POST /conversations/{id}/reply]        HTTP 200   # message accepted, delivery attempted
[DELETE /conversations/{id}]            HTTP 200
[POST /social/telegram/setup-webhook]   HTTP 200   # only fails later on missing bot token
```

**Fix:** Add `auth: dict = Depends(require_automation_secret)` (or `require_roles(...)`
for dashboard-only ops) to each handler, or attach a router-level dependency:
`APIRouter(dependencies=[Depends(require_automation_secret)])`. Real inbound webhooks
(Telegram/Meta) must instead verify a provider signature / secret path token.

---

### [F5] Live credentials committed to the repository — HIGH | PROVEN | CWE-798
**Location:** `mcp-config.json:7` (n8n API JWT `Bearer eyJ…`), same token in
`automation/publish_all.py:7`, `upload_all_workflows.py`, `update_backend_url.py`,
`upload_email_wf_json.py`, etc.; Telegram bot token
`8098076051:…[redacted]` in `automation/update_and_publish_active_wf.py:109` &
`upload_email_wf_json.py:109`; shared secret in `automation/setup_credentials.py:35`.

**What's wrong:** Real tokens are hardcoded in tracked files (the n8n JWT has no `exp`
claim — it does not expire). They live in git history even if deleted from HEAD.

**Impact:** Anyone with repo access controls the n8n Cloud instance and the Telegram bot
(send/receive as the brand). The n8n JWT being non-expiring makes rotation the only
remedy.

**Fix:** Rotate all three now. Move to env vars / a secrets manager. Purge from history
(`git filter-repo`) and invalidate the old n8n key in n8n Cloud.

---

### [F6] Meta (Facebook/Instagram) webhooks unauthenticated & unverified — HIGH | SUSPECTED | CWE-345
**Location:** `social/endpoints.py:217` (`facebook_webhook_event`), `:244`
(`instagram_webhook_event`).

**What's wrong:** POST webhook handlers process `entry[].changes[]` and trigger the
comment-to-DM bridge (public replies + private DMs + hot-lead Telegram alerts) with no
`X-Hub-Signature-256` HMAC check against `facebook_app_secret` (which *is* configured).
GET verification exists; POST integrity does not.

**Impact:** Anyone can forge Meta events to make the Page post attacker-authored public
replies and DMs, and spam sales staff with fake "hot leads." Marked SUSPECTED pending
confirmation that no upstream proxy enforces the signature.

**Fix:** Compute `hmac.sha256(app_secret, raw_body)` and constant-time compare to
`X-Hub-Signature-256`; reject on mismatch. Read the raw body (not the parsed dict) for the
HMAC.

---

### [F7] Weak password hashing — MEDIUM | PROVEN | CWE-916, CWE-759, CWE-208
**Location:** `core/security.py:20-27`.

**What's wrong:** `hmac_sha256(global_static_salt, password)` — a single fast round, one
process-wide salt (`glg_assets_salt_2026`, `config.py`), and `verify_password` uses `==`
(not constant-time). `requirements.txt` already ships `bcrypt`/`passlib`, so this is a
regression, not a missing dependency.

**Impact:** A DB/hash leak is trivially cracked (no per-user salt → single rainbow table
for all users; GPU-fast). Timing side-channel on compare.

**Fix:** Use `passlib`'s bcrypt/argon2 (`CryptContext`) with per-hash salt; migrate on
next login. If kept temporarily, at least `hmac.compare_digest`.

---

### [F8] `tenant_id` dropped on token refresh — MEDIUM | PROVEN | CWE-282
**Location:** `auth/endpoints.py:137-144` (login embeds `tenant_id`) vs
`security.py:88-115` (`create_refresh_token` stores only sub/role/email) →
`refresh_access_token` reissues an access token **without** `tenant_id`;
`dependencies.py:32` then falls back to `settings.default_tenant_id`.

**What's wrong:** After the first 15-minute refresh, every user silently becomes
`glg-assets-main`. In a multi-tenant system this is a cross-tenant authorization defect.

**Impact:** Tenant-scoped reads/writes hit the default tenant's data after refresh.

**Reproduction (executed):**
```
tenant in login token: glg-default | after refresh: None   # → resolves to default tenant
```

**Fix:** Carry `tenant_id` (and `email`) through `create_refresh_token`/rotation and
re-embed it in the new access token.

---

### [F9] Login blocking-sleep + email-only lockout → DoS — MEDIUM | PROVEN | CWE-307, CWE-400
**Location:** `auth/endpoints.py:117-119`; `core/account_lockout.py:29,57-103`.

**What's wrong:** (a) On failed login the handler `await asyncio.sleep(delay)` **inside
the request** — an attacker can open many failing logins to pin the event loop and inflate
concurrency. (b) `_get_key` ignores IP and keys only on email, so an attacker who knows a
victim's email can deliberately trip 5 failures and **lock the real user out** for 15
minutes (targeted account-lockout DoS). The IP argument is threaded through but discarded.

**Fix:** Return 401 immediately without server-side sleep (rate-limiter already throttles);
track failures per (email, ip) and only lock the offending IP, not the account, or use an
exponential-backoff token the client must wait on.

---

### [F10] CORS `*` with credentials — MEDIUM | PROVEN | CWE-942
**Location:** `main.py:130-131`; `render.yaml` `CORS_ORIGINS: "*"`.

**What's wrong:** `allow_origins=["*"]` + `allow_credentials=True`. Combined with the
public shared secret (F1), any website can script authenticated calls from a victim's
browser. Even setting aside credentials, `*` in production is over-broad.

**Fix:** Set `CORS_ORIGINS` to the explicit dashboard origin(s); never pair `*` with
credentials.

---

### [F11] Auth revocation state is in-process only — MEDIUM | PROVEN | CWE-613
**Location:** `core/security.py:16-17` (`_active_refresh_tokens`, `_revoked_refresh_tokens`
module dicts).

**What's wrong:** Render/Gunicorn runs multiple workers; each has its own dicts. A refresh
token issued by worker A is "unrecognized" on worker B, and revocation on one worker
doesn't apply to others. Restart wipes all sessions and the replay-detection set.

**Impact:** Inconsistent logout/rotation; replay detection is unreliable across workers.

**Fix:** Back the token registry with Redis (the `resilient_store` already exists) keyed by
`jti`.

---

### [F12] Conversations served from a process-global list — LOW | PROVEN
**Location:** `conversations/endpoints.py:22` (`IN_MEMORY_CONVERSATIONS = []`), mutated in
`create_conversation` (:378), `delete_conversation` (:406), etc.

**What's wrong:** Cross-request mutable global; with >1 worker, reads/writes are
worker-local and inconsistent, and the fallback path returns stale/empty data. Also a slow
memory grower.

**Fix:** Treat the DB as source of truth; drop the global cache or move it to Redis.

---

### [F13] Warnings globally silenced + broad excepts — LOW | PROVEN | CWE-532/CWE-703
**Location:** `main.py:59-60` (`warnings.simplefilter("ignore")`), plus many
`except Exception: pass` (e.g. `conversations/endpoints.py`, `event_broadcaster.py:33`).

**What's wrong:** Deprecations and runtime warnings are hidden platform-wide; swallowed
exceptions blind on-call to DB and delivery failures (the SSE broadcaster silently drops
events on a full queue).

**Fix:** Scope warning filters narrowly; log swallowed exceptions at `warning`/`error`
with context.

---

## 4. Prioritized Remediation Plan
1. **F2** Remove `eval` from `simulate_policy` (ast allow-list or structured rules). — **S**
2. **F1** Split `JWT_SECRET` from automation secret; strip the frontend hardcoded secret;
   SPA authenticates as user. — **M**
3. **F5** Rotate & purge committed n8n JWT / Telegram token / shared secret. — **M**
4. **F4** Add auth deps to conversation/social/automation endpoints; signature-verify real
   webhooks. — **M**
5. **F3** Reject `type=refresh` on protected routes; enforce revocation on access path. — **S**
6. **F6** HMAC-verify Meta webhooks. — **S**
7. **F8** Preserve `tenant_id` through refresh. — **S**
8. **F10** Lock CORS to explicit origins. — **S**
9. **F7** bcrypt/argon2 password hashing with migration. — **M**
10. **F9/F11/F12** Remove in-request sleep + per-IP lockout; move token/conversation state
    to Redis/DB. — **M**
11. **F13** Scope warning filters; log swallowed errors. — **S**

## 5. Test Additions
- **Auth contract tests:** (a) a `type=refresh` JWT is rejected on a protected route;
  (b) a revoked refresh token fails as bearer after logout; (c) a token signed with the
  automation secret is rejected once `JWT_SECRET` differs; (d) `tenant_id` survives refresh.
- **Authz tests:** each conversation/social/automation route returns 401/403 without
  credentials (table-driven over the route list in F4).
- **Injection test:** `simulate_policy` rejects `().__class__.__base__.__subclasses__()`
  and any name outside the allow-list; property/fuzz test over random expressions asserting
  no attribute access escapes.
- **Webhook integrity:** Meta POST with a bad/absent `X-Hub-Signature-256` → 403.
- **Lockout:** failed logins for victim email from attacker IP do not lock the victim's
  logins from a different IP; failed login path adds no server-side delay.
- **Password:** hashes are per-user unique for identical passwords; verify is
  constant-time.

## 6. Open Questions / Could Not Verify
- Is a reverse proxy / WAF in front of Render enforcing Meta webhook signatures or origin
  restrictions? (F6 severity depends on this.)
- Is the production `AUTOMATION_SHARED_SECRET` the committed `3322af…` value, or a distinct
  Render-dashboard value? Either way F1 holds (browser bundle exposure), but this decides
  whether the git-committed value is *also* live.
- Does production run multiple Gunicorn workers? (Confirms F11/F12 impact.)
- Are Supabase RLS policies enforced independently of the app's `tenant_id`? (Would bound
  F8's blast radius.)
- `platform-api/` (port 8001) was only spot-checked; it shares the same
  `automation_shared_secret` default `change-me-in-production` and `CORS "*"` and likely
  repeats F1/F10 — needs its own pass.
