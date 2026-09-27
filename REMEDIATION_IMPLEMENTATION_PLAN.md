# GLG Assets — Security Remediation Implementation Plan

Pairs with `PRINCIPAL_ENGINEER_SECURITY_REVIEW.md` (backend F1–F13) and
`FRONTEND_SECURITY_REVIEW.md` (frontend W1–W9). This plan sequences the fixes by
**dependency and blast radius**, not by severity alone, because several fixes must land
together (the auth-key refactor spans backend + frontend + n8n + Render config).

**Legend:** effort **S** ≤0.5d · **M** 0.5–2d · **L** 2–5d. Each task lists *Files*,
*Change*, *Verify*, *Depends on*. Code blocks are **sketches**, not drop-in patches.

**Golden rules for this work** (`AGENTS.md`): no MEDIUM+ change is self-certified — a second
reviewer signs off (§3.1); backend changes must pass Python syntax + service unit tests,
frontend must pass `npm run build` (§3.4); leave changes uncommitted for review unless told
otherwise (§3.5).

---

## Target auth model (the decision everything else depends on)

Today one value (`AUTOMATION_SHARED_SECRET`) is the JWT signing key **and** an admin bearer
**and** shipped to browsers. We split it into three distinct concerns:

| Concern | After the fix | Who holds it |
|---|---|---|
| Sign/verify user JWTs | new random `JWT_SECRET` | backend only |
| Server-to-server auth (n8n, webhooks) | rotated `AUTOMATION_SHARED_SECRET`, maps to a **service principal**, not auto-admin unless the caller is n8n | backend + n8n only |
| Dashboard API auth | the logged-in user's **Bearer JWT**; role comes from the JWT | browser (JWT only, never the secret) |

**Access/refresh token handling (recommended):** access JWT in memory (React context),
refresh token in the backend's existing **httpOnly cookie only**. Alternative (lower effort,
weaker): keep access token in `sessionStorage` (cleared on tab close) — still better than
`localStorage`. Plan assumes the recommended option; note the fallback if timeline is tight.

---

## Phase 0 — Emergency containment (do first, no code dependency) — ~0.5d

These credentials are already public (git + browser bundle). Rotating code without rotating
secrets fixes nothing.

### T0.1 Rotate every exposed credential — **M** — [F5, F1, W1]
- **Rotate:** n8n API JWT (`mcp-config.json:7` and `automation/*.py`), Telegram bot token
  (`automation/update_and_publish_active_wf.py:109`), `AUTOMATION_SHARED_SECRET`, Supabase
  service-role key, Pinecone/OpenAI/Groq keys if they ever transited git.
- **Where:** n8n Cloud (revoke old API key — it has no `exp`), BotFather (`/revoke`), Render
  dashboard env vars (`sync:false` values), Supabase project settings.
- **Verify:** old n8n JWT returns 401 against `N8N_API_URL`; old Telegram token
  `getMe` returns 401.
- **Depends on:** nothing. Start immediately.

### T0.2 Purge secrets from git history — **M** — [F5]
- **Change:** `git filter-repo --replace-text` (or BFG) over `mcp-config.json`,
  `automation/setup_credentials.*`, `automation/publish_all.py`,
  `automation/update_and_publish_active_wf.py`, `automation/upload_email_wf_json.py`,
  `automation/upload_all_workflows.py`, `automation/update_backend_url.py`. Replace hardcoded
  values with `os.environ[...]` reads.
- **Verify:** `git log -S'3322af281a2b' --all` and `-S'8098076051:'` return nothing;
  re-scan with `gitleaks detect`.
- **Note:** history rewrite is disruptive (force-push, everyone re-clones) — coordinate with
  the team; do it once, right after T0.1.

---

## Phase 1 — Kill remote code execution (isolated, highest severity) — ~0.5d

### T1.1 Remove `eval()` from policy simulator — **S** — [F2] CRITICAL
- **Files:** `backend/app/services/ai_control_plane/control_plane_service.py:1474-1495`.
- **Change:** replace `eval(...)` with a safe evaluator. Minimal — AST allow-list:
  ```python
  import ast, operator
  _OPS = {ast.And: all, ast.Or: any}
  _CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
          ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}
  def _safe_eval(node, ctx):
      if isinstance(node, ast.Expression): return _safe_eval(node.body, ctx)
      if isinstance(node, ast.BoolOp):
          vals = [_safe_eval(v, ctx) for v in node.values]
          return _OPS[type(node.op)](vals)
      if isinstance(node, ast.Compare):
          left = _safe_eval(node.left, ctx)
          for op, comp in zip(node.ops, node.comparators):
              if not _CMP[type(op)](left, _safe_eval(comp, ctx)): return False
              left = _safe_eval(comp, ctx)
          return True
      if isinstance(node, ast.Name): return ctx.get(node.id)
      if isinstance(node, ast.Constant): return node.value
      raise ValueError(f"disallowed expression node: {type(node).__name__}")
  # simulate_policy:
  tree = ast.parse(expression, mode="eval")
  triggered = bool(_safe_eval(tree, safe_names))
  ```
  Reject `Attribute`, `Call`, `Subscript`, comprehensions, etc. by omission.
- **Verify:** `().__class__.__base__.__subclasses__()` → 400/handled error, not 200;
  `price_bdt > 50000000 and location == "Banani"` still evaluates correctly.
- **Depends on:** nothing. Ship independently of the auth refactor.

---

## Phase 2 — Auth key separation (the linchpin; backend + frontend deploy together) — ~2–3d

Order within the phase matters: backend must accept JWT-only auth **before** the browser
stops sending the secret.

### T2.1 Separate JWT signing key from automation secret — **S** — [F1]
- **Files:** `backend/app/core/security.py:11`, `backend/app/config.py:31`, `render.yaml`.
- **Change:** require a real `JWT_SECRET`; stop falling back to the automation secret:
  ```python
  SECRET_KEY = settings.jwt_secret or _fail("JWT_SECRET must be set")
  ```
  Add `JWT_SECRET` (`sync:false`) to `render.yaml`; generate `openssl rand -hex 32`.
- **Verify:** a JWT signed with the automation secret is rejected once `JWT_SECRET` differs
  (re-run the backend PoC — forged-JWT test should now 401).
- **Depends on:** T0.1 (new secrets exist).

### T2.2 Make the automation secret a service principal, not auto-admin for browsers — **M** — [F1]
- **Files:** `backend/app/dependencies.py:44-46` & `56-63`, `backend/app/main.py`
  `verify_automation_secret`.
- **Change:** keep `X-Automation-Secret` acceptance for server-to-server routes, but return a
  **service** identity (`role="service"`, or a dedicated tenant), not `UserRole.ADMIN`.
  Endpoints that must stay admin-only should use `require_roles([...])` against a JWT.
  Decide per-endpoint: webhooks/automation ingestion → service principal OK; control-plane
  mutation → JWT role required.
- **Verify:** the secret alone can hit `/api/v1/automation/*` (n8n) but **cannot** reach
  `/api/v1/ai-control/policies` mutation without a DEVELOPER/ADMIN JWT.
- **Depends on:** T2.1.

### T2.3 Remove the hardcoded secret from the frontend; send JWT only — **M** — [W1]
- **Files:** `frontend/src/services/api.js:85`, `frontend/src/services/aiControlPlaneApi.js:3`
  and its `getAuthHeaders` (used by 66 calls), plus `sendChatMessage`/`generateContent`/etc.
  in `api.js` that set `X-Automation-Secret`.
- **Change:** delete the literal; route **all** browser calls through one `fetchWithAuth`
  that attaches only `Authorization: Bearer <accessToken>`. Drop `X-Automation-Secret` from
  every browser request.
  ```js
  // getAuthHeaders(isJson) -> { 'Content-Type'?, 'Authorization': `Bearer ${accessToken}` }
  ```
- **Verify:** built bundle contains no `X-Automation-Secret` (see T7.2 CI grep); dashboard
  still works when logged in as `developer@…`; a `viewer` gets 403 from control-plane calls.
- **Depends on:** T2.2 (backend must authorize by JWT first), and demo users having correct
  roles (already seeded, `auth/endpoints.py:32-83`).

### T2.4 Update n8n + server callers to use the rotated secret from env — **S** — [F1, F5]
- **Files:** `automation/*.py`, `automation/*/workflow.json` (`X-Automation-Secret` values),
  n8n Cloud credentials.
- **Change:** replace inline secret literals with env references; set the rotated value in n8n.
- **Verify:** an n8n test execution against `/api/v1/automation/*` returns 200.
- **Depends on:** T0.1, T2.2.

---

## Phase 3 — Close authn/authz holes — ~2d

### T3.1 Reject refresh tokens as access tokens; enforce revocation on access path — **S** — [F3]
- **Files:** `backend/app/dependencies.py:30-46` & `85-101`; `backend/app/core/security.py`.
- **Change:** in the protected-route path require `payload.get("type") == "access"`. Add a
  `jti` to access tokens; check a revocation set (Redis, see T4.3) on each request, or accept
  the 15-min TTL window and document that logout kills only the refresh chain — but **always**
  reject `type == "refresh"` on protected routes.
- **Verify:** refresh-token-as-bearer → 401; after logout, access path denied (re-run backend
  PoC P3).
- **Depends on:** none (Redis check optional until T4.3).

### T3.2 Add auth to unauthenticated endpoints — **M** — [F4]
- **Files:** `backend/app/api/v1/conversations/endpoints.py` (`:284,406,459,563,603`),
  `backend/app/api/v1/social/endpoints.py` (`:181,443,452`),
  `backend/app/api/v1/automation/endpoints.py` (`:344,351,362`).
- **Change:** dashboard-facing routes → `Depends(require_roles([...]))`; internal ops → 
  `Depends(require_automation_secret)`. Consider a router-level dependency:
  `APIRouter(dependencies=[Depends(require_automation_secret)])` for conversations/automation.
- **Verify:** each route returns 401/403 without creds (table-driven test T7.1).
- **Depends on:** T2.2.

### T3.3 Real webhooks: verify provider signatures instead of app auth — **M** — [F4, F6]
- **Files:** `backend/app/api/v1/social/endpoints.py:217,244` (Meta), `:343` (Telegram).
- **Change (Meta):** verify `X-Hub-Signature-256` HMAC over the **raw body** with
  `facebook_app_secret`, constant-time compare; reject on mismatch. Read raw bytes
  (`await request.body()`), then parse.
  ```python
  sig = request.headers.get("X-Hub-Signature-256","").removeprefix("sha256=")
  mac = hmac.new(app_secret.encode(), raw, hashlib.sha256).hexdigest()
  if not hmac.compare_digest(sig, mac): raise HTTPException(403)
  ```
  **Telegram:** set a secret path token or `X-Telegram-Bot-Api-Secret-Token` (configured via
  `setWebhook`) and verify it; also protect `/telegram/setup-webhook` with admin auth.
- **Verify:** forged Meta POST without valid signature → 403; legitimate signed payload → 200.
- **Depends on:** T0.1 (rotated tokens).

### T3.4 Frontend route-level RBAC — **S** — [W2]
- **Files:** `frontend/src/App.jsx:262-282`; new `components/common/RequireRole.jsx`.
- **Change:**
  ```jsx
  function RequireRole({ roles, children }) {
    const { user } = useAuth();
    return roles.includes(user?.role) ? children
      : <Navigate to={TAB_TO_PATH[getDefaultTabForRole(user?.role)]} replace />;
  }
  // wrap: <Route path="/developer" element={<RequireRole roles={['developer','admin']}><DeveloperConsolePage/></RequireRole>} />
  ```
  Mirror `Sidebar.jsx:111-120` role sets.
- **Verify:** T7.3 route-guard tests; a `viewer` hitting `/ai-studio` is redirected.
- **Depends on:** T2.3 (so a wrongly-loaded page can't self-elevate in the meantime).

---

## Phase 4 — Token handling, tenant integrity, durable state — ~2d

### T4.1 Move tokens out of localStorage — **M** — [W3]
- **Files:** `frontend/src/services/auth.js`, `AuthContext.jsx`, all `localStorage.getItem('glg_token')`
  sites in `api.js`/`aiControlPlaneApi.js` (~45).
- **Change:** hold access token in `AuthContext` state; expose `getAccessToken()` from a small
  module so `fetchWithAuth` can read it without `localStorage`. Stop writing
  `glg_refresh_token` to `localStorage` — rely on the httpOnly cookie (refresh call already
  sends `credentials:'include'`). On load, attempt `/refresh` (cookie) to rehydrate.
- **Verify:** after login, `localStorage.getItem('glg_refresh_token')` is `null` (T7.4); a
  full reload restores the session via cookie.
- **Depends on:** T2.3.

### T4.2 Preserve `tenant_id` through refresh — **S** — [F8]
- **Files:** `backend/app/core/security.py:88-115` (`create_refresh_token`),
  `backend/app/api/v1/auth/endpoints.py:201-241` (`refresh`).
- **Change:** carry `tenant_id` (and `email`) into the refresh token payload/registry and
  re-embed in the reissued access token.
- **Verify:** re-run backend PoC P4 — tenant is preserved, not `None`/default.
- **Depends on:** none.

### T4.3 Back token/lockout/conversation state with Redis — **M** — [F11, F12, F9-partial]
- **Files:** `backend/app/core/security.py:16-17` (token registries),
  `backend/app/api/v1/conversations/endpoints.py:22` (global list).
- **Change:** move `_active_refresh_tokens`/`_revoked_refresh_tokens` into `resilient_store`
  (Redis-backed) keyed by `jti`; treat the DB as source of truth for conversations and drop
  or Redis-back the in-process cache.
- **Verify:** revocation on worker A is visible on worker B (integration test with 2 workers).
- **Depends on:** `REDIS_URL` provisioned.

---

## Phase 5 — Hardening — ~2d

### T5.1 Lock CORS to explicit origins — **S** — [F10, W5]
- **Files:** `backend/app/main.py:130-131`, `render.yaml` `CORS_ORIGINS`, `platform-api` config.
- **Change:** set `CORS_ORIGINS` to the dashboard origin(s); never pair `*` with
  `allow_credentials=True`.
- **Verify:** preflight from a random origin is refused; dashboard origin works.

### T5.2 bcrypt/argon2 password hashing — **M** — [F7]
- **Files:** `backend/app/core/security.py:20-27` (+ `passlib`, already in requirements).
- **Change:** `CryptContext(schemes=["bcrypt"])`; migrate on next successful login (verify old
  HMAC, re-hash with bcrypt). Constant-time compare comes for free.
- **Verify:** identical passwords produce distinct hashes; login still works; migration path
  test.

### T5.3 Fix login DoS + lockout keying — **S** — [F9]
- **Files:** `backend/app/api/v1/auth/endpoints.py:117-119`,
  `backend/app/core/account_lockout.py:29`.
- **Change:** remove the in-request `asyncio.sleep`; key failures per `(email, ip)` and lock
  the offending IP, not the victim's account (rate limiter already throttles).
- **Verify:** attacker IP failures don't lock the victim from a different IP; no server-side
  delay on the request path.

### T5.4 Constrain frontend API-origin resolution — **M** — [W4]
- **Files:** `frontend/src/services/api.js:13-42,110-125`, `auth.js:getCandidateBases`.
- **Change:** resolve base from build config; validate any stored/dynamic base against an
  allow-list before use; never send `Authorization` to a non-allow-listed host; remove the
  credential fan-out (probe health unauthenticated, then send creds only to the chosen origin).
- **Verify:** T7.5 — poisoned `glg_working_backend` does not receive credentialed requests.

### T5.5 CSRF/SameSite on cookie routes — **S** — [W5]
- **Files:** `backend/app/api/v1/auth/endpoints.py` cookie set (`:148-156,211-219`).
- **Change:** `SameSite=strict` for the refresh cookie (or add a CSRF token for
  `/refresh`,`/logout`); drop `credentials:'include'` on bearer-authenticated calls.
- **Verify:** cross-site `/refresh` without token/same-site is rejected.

---

## Phase 6 — Reliability & minor correctness — ~1d

- **T6.1 [F13]** Scope `warnings.simplefilter("ignore")` narrowly; log swallowed excepts at
  `warning`/`error` (`main.py:59-60`, broad `except: pass` sites). — **S**
- **T6.2 [W6]** Gate `isAuthenticated` on server `getMe` (`verified` flag); re-validate on
  privileged routes (`AuthContext.jsx:8-31`). — **S**
- **T6.3 [W7]** Fix `172.` LAN check → `172.(1[6-9]|2\d|3[01])\.` (`api.js:53`). — **S**
- **T6.4 [W9]** Replace static `innerHTML` avatar fallback with a rendered `<span>`
  (`Header.jsx:416`). — **S**

---

## Phase 7 — Tests & CI gates (write alongside each phase) — ~2d

### T7.1 Backend authz matrix — table-driven test asserting every route in T3.2 returns
401/403 without creds, and the right role passes. — **M**
### T7.2 Bundle-secret CI gate — `vite build` then
`grep -rEq "X-Automation-Secret|VITE_AUTOMATION_SECRET" dist/ && exit 1`. — **S**
### T7.3 Frontend route-guard tests — mocked `viewer` context → `/developer` redirects,
console does not mount. — **S**
### T7.4 Token-storage test — post-login `glg_refresh_token` is `null`. — **S**
### T7.5 API-origin allow-list test — poisoned base gets no credentialed fetch. — **S**
### T7.6 Injection test — `simulate_policy` rejects object-graph/`Call`/`Attribute`. — **S**
### T7.7 Auth-regression suite — the backend PoC (P1–P4) as pytest: forged JWT rejected,
refresh-as-access rejected, revocation enforced, tenant preserved. — **M**
### T7.8 Webhook-integrity test — bad/absent `X-Hub-Signature-256` → 403. — **S**
### T7.9 `npm audit --production` + committed lockfile in CI. — **S** — [W8]

---

## Suggested execution order (critical path)

```
Day 0        Phase 0 (rotate + purge)      ── unblocks everything, no code risk
Day 0–1      Phase 1 (kill eval/RCE)       ── isolated, ship immediately
Day 1–4      Phase 2 (auth key split)      ── backend T2.1→T2.2, then frontend T2.3, n8n T2.4
                                              deploy backend+frontend TOGETHER
Day 4–6      Phase 3 (authz holes + guards)
Day 6–8      Phase 4 (tokens, tenant, Redis)
Day 8–10     Phase 5 (hardening)
Day 10–11    Phase 6 (reliability/minor)
throughout   Phase 7 (tests land with each phase; CI gates before merge)
```

**Hard ordering constraints:**
- T2.3 (frontend drops secret) must not deploy before T2.2 (backend authorizes by JWT) — else
  the dashboard 401s. Ship backend first, verify, then frontend.
- T0.1 before T2.4 (n8n needs the new secret) and before any "fixed" deploy (old secret is
  public).
- Phase 1 is independent — do not let the larger Phase 2 delay the RCE fix.

## Rollback & safety
- Each phase is a separate branch/PR; keep changes uncommitted for review per `AGENTS.md §3.5`
  until each is signed off by a second reviewer (§3.1, MEDIUM+).
- Phase 2 is the risky one: feature-flag the backend to accept **both** JWT and the (rotated)
  secret from browsers during a short bake, then flip off browser-secret acceptance once the
  new frontend is confirmed. Remove the flag after.
- Verify each backend change with `python -m pytest backend/tests` and each frontend change
  with `npm run build` before requesting review.

## Out of scope / still needed
- **`platform-api/` (port 8001)** was not reviewed; it shares the `change-me-in-production`
  secret default and `CORS "*"` and almost certainly needs T2.1/T2.2/T5.1 equivalents. Add a
  review pass and mirror the relevant tasks.
- Runtime confirmations still open (from both reviews): exact prod `Access-Control-Allow-Origin`,
  whether a proxy strips `X-Automation-Secret`, Gunicorn worker count, Supabase RLS status.

---

## Implementation status (this branch, uncommitted)

Verified: backend **253 passed** (was 172; +81 security tests), frontend **46 passed**
(was 23), `npm run build` clean, **0** secret references in `dist/`, ruff at the pre-existing
baseline (0 new findings). Security tests were mutation-checked: re-admitting the service
secret as admin, dropping the token-type check, or skipping revocation each turns them red.

| Task | Status | Notes |
|---|---|---|
| T0.1 rotate credentials | **YOU** | Cannot be done from code. See checklist below. |
| T0.2 purge git history | **YOU** | Destructive force-push; needs team coordination. HEAD is clean. |
| T0 strip secrets from tracked files | Done | n8n JWT, Telegram token, shared secret, local n8n admin password → env vars. |
| T1.1 remove `eval()` | Done | `app/core/safe_expression.py` (AST allow-list). |
| T2.1 independent `JWT_SECRET` | Done | App **refuses to start** without a ≥32-char key distinct from the automation secret. |
| T2.2 secret → service principal | Done | Service secret is `role=service`, rejected by `require_roles` unless `allow_service=True`. Known-leaked values are denylisted. Bearer JWT wins when both are sent. |
| T2.3 frontend JWT-only | Done | No secret in the bundle; all calls via `apiFetch`. |
| T2.4 n8n env references | Done | Workflows use `{{ $env.AUTOMATION_SHARED_SECRET }}`. |
| T3.1 token types + revocation | Done | `type` enforced; session `sid` revocation covers access tokens on logout/replay. |
| T3.2 auth on open routes | Done | 48 → 16 routes without dependency auth; the 16 are health, login/refresh/logout, and webhooks/WS that verify in-handler. Also fixed fail-open `email/verify_auth` (not in original review). |
| T3.3 webhook signatures | Done | Meta HMAC over raw body; Telegram secret token; both fail closed. |
| T3.4 route guards | Done | `src/auth/routeAccess.js` + `RequireRole`. |
| T4.1 tokens out of localStorage | Done | Access token in memory; refresh token httpOnly cookie only (path `/api/v1/auth`). Legacy stored tokens are purged. |
| T4.2 tenant through refresh | Done | |
| T4.3 shared revocation state | Done | Via `resilient_store` (Redis when `REDIS_URL` is set). |
| T5.1 CORS | Done | Explicit origins; credentials never with `*`. |
| T5.2 bcrypt | Done | Legacy HMAC hashes verify and are upgraded on next login; bcrypt runs off the event loop. |
| T5.3 lockout | Done | Per-(email, IP); no in-request sleep. Also fixed a pre-existing bug where Redis-backed lockout never persisted (`ttl=` vs `expire_seconds=`). |
| T5.4 API origin allow-list | Done | No base URL from storage; bearer only sent to allow-listed origins. |
| T5.5 CSRF on cookie routes | Done | Cookie refresh/logout require `X-GLG-Client` header (forces CORS preflight). |
| T6.1 warnings | Done | Only deprecation warnings silenced. |
| T6.2–T6.4 | Done | Session verified before auth UI; RFC1918 172.16/12 check; no `innerHTML`. |
| F12 conversation cache | **Not done** | In-process `IN_MEMORY_CONVERSATIONS` still diverges across workers; functional refactor, deferred. |
| Extra: knowledge path traversal | Done | `doc_id` validated; writes confined to base dir; 20 MB upload cap. |
| Extra: SSE/WS auth | Done | 60 s stream tickets (`POST /api/v1/auth/stream-ticket`). Also fixes AI-control SSE, which was always 401ing. |

## Deployment checklist (required — the new build fails closed without these)

Deploy **backend first**, verify, then frontend. n8n credentials must be updated at the same
time as the backend secret rotation.

1. **Rotate & set secrets** (Render dashboard → backend env):
   - `JWT_SECRET` = `openssl rand -hex 32` (new; app won't boot without it)
   - `AUTOMATION_SHARED_SECRET` = new random value. The old `3322af…` value is **denylisted in
     code** — n8n calls fail with 403 until n8n is updated to the new value.
   - Revoke the old n8n API key (n8n Cloud) and Telegram bot token (BotFather `/revoke`).
2. **n8n Cloud:** set env/credential `AUTOMATION_SHARED_SECRET` to the new value.
3. **Webhooks** (they fail closed until set): `FACEBOOK_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`
   (must match the Meta app dashboard), `TELEGRAM_WEBHOOK_SECRET` — then re-run
   `POST /api/v1/social/telegram/setup-webhook` so Telegram starts sending the secret.
4. **Verify client IP resolution — do not skip.** Log in as admin and call
   `GET /api/v1/auth/client-ip-diagnostics`. `resolved_client_ip` must be *your* public IP.
   If it shows a proxy/internal address, all users share one login rate-limit bucket
   (5/min) — adjust `TRUSTED_PROXY_HOPS` or set `CLIENT_IP_HEADER` (e.g. `CF-Connecting-IP`)
   and re-check. `render.yaml` sets hops=1 as a best guess; **UNVERIFIED** for Render.
5. **Recommended:** set `REDIS_URL` so revocation/lockout/rate-limit state is shared across
   instances.
6. **Frontend:** redeploy (no `VITE_AUTOMATION_SECRET` any more). All users re-login once
   (new JWT key invalidates existing sessions).
7. **Known limitation:** frontend and API are different sites on `onrender.com`, so the
   refresh cookie is `SameSite=None` (third-party). Safari blocks it → Safari users log in
   again after each reload. Fix by serving dashboard + API from one origin (reverse proxy),
   then set `REFRESH_COOKIE_SAMESITE=lax`.

## Follow-ups found while implementing
- **CI lint is already red at HEAD** (37 pre-existing ruff findings) — independent of this change.
- The existing test suite writes run history into tracked files
  (`backend/data/report_store.json`, `backend/data/knowledge/documents_registry.json`,
  ~3k lines per run). Tests should use a temp data dir.
- `platform-api/` still unreviewed; same `change-me-in-production` / `CORS *` defaults.
- n8n in `docker-compose.yml` runs with `N8N_AUTH_ENABLED=false` on a published port.

---

## Merge of `main` into PR #9

`main` gained a parallel auth redesign (durable PostgreSQL token store, database-backed users,
encrypted integration vault) while this branch was in review. Resolved by keeping all of
`main`'s features and this branch's security invariants on top:

| Area | Resolution |
|---|---|
| Token lifecycle | `main`'s memory → Redis → PostgreSQL `token_store` for refresh tokens; this branch's typed tokens, session (`sid`) revocation, tenant preservation and stream tickets on top. Session revocations are written to `revoked_tokens` (`token_type="session"`); per-request checks read memory/Redis only. |
| Bug fixed in `main` | `token_store.is_token_revoked` treated any revoke-all as permanent, so after a replay detection or password reset **every future session** of that user was rejected (until restart, or 7 days in Redis). The cut-off now applies only to tokens issued before it. |
| Passwords | `main`'s scheme (bcrypt of the raw password, 72-byte truncation) kept for compatibility with stored users; implemented on `bcrypt` directly. |
| Secrets | `main` added hardcoded defaults for `JWT_SECRET` / `AUTOMATION_SHARED_SECRET`. Removed; the app refuses to start with a missing or publicly known JWT key, and the old defaults are denylisted. |
| CORS | `main` defaulted to allowing every origin (`^https?://.*`) with credentials — any site could read a logged-in user's refreshed tokens. Now: explicit origins, no regex by default; `render.yaml` sets a pattern limited to this project's Vercel deployments. |
| Demo users | `main` created `admin@glgassets.com` / `admin123` etc. both in the database **and** as an in-memory fallback used whenever the database has no matching row. Both now only when `SEED_DEMO_USERS=true` (tests/dev). |
| Credential vault | Its key was derived from the JWT/automation secrets, so rotating them (required above) would silently make every stored integration credential unreadable. New `CREDENTIALS_ENCRYPTION_KEY`; decrypt failures are now logged. |
| Conversations | `main`'s bounded O(1) cache and bounded SSE queues kept (partly addresses F12); per-role access instead of "any authenticated caller". |
| Tests | `main`'s edge-case test asserting refresh tokens decode as access tokens (finding F3) updated to the fixed contract. 7 regression tests pin the decisions above. Backend 271 passed, frontend 46 passed, ruff 0 findings. |

### Additional deployment steps from the merge
- **`CREDENTIALS_ENCRYPTION_KEY`**: set it (`openssl rand -hex 32`). If integration credentials
  were already saved under `main`, they were encrypted with the legacy derived key: rotating
  `JWT_SECRET`/`AUTOMATION_SHARED_SECRET` or setting this key makes them unreadable (now logged
  as `[crypto] Failed to decrypt`). Re-enter them in Developer Console → Integrations after
  deploying.
- **Admin account**: with demo seeding off, production has no default users and `/auth/register`
  itself requires an admin. Bootstrap one **before** relying on the deploy:
  `cd backend && python -m scripts.create_admin --email you@company.com --name "Your Name"`
  (password prompted, or from `ADMIN_PASSWORD`; min 12 chars). Then delete the old demo rows if
  `main` already seeded them: `DELETE FROM auth_users WHERE email IN ('admin@glgassets.com', 'manager@glgassets.com', 'agent@glgassets.com', 'developer@glgassets.com', 'viewer@glgassets.com');` (exact demo addresses only; check none is a real account first)
- **CORS**: if the production dashboard is served from a domain the Vercel pattern does not
  cover (e.g. `real-state-automation.vercel.app` or a custom domain), add it to `CORS_ORIGINS`.
- **Residual risk (SUSPECTED):** any suffix pattern on `vercel.app` depends on nobody else being
  able to register a project name ending in `-kawshik-khans-projects`. A custom domain for the
  dashboard removes that dependency.
