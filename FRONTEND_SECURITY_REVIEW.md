# Principal Engineer Review — GLG Assets Dashboard (frontend/)

**Scope:** `frontend/` — React 19 + Vite SPA (`src/`), `vite.config.js`, `nginx.conf`,
`package.json`. Trust boundary: this is a **public, unauthenticated-download** static
bundle served to any browser; everything in it (including build-time env values) is
attacker-readable. Backend was reviewed separately (`PRINCIPAL_ENGINEER_SECURITY_REVIEW.md`).

**Method:** static trace of auth flow, routing, API layer, and render sinks. Findings
labelled **[PROVEN]** (traced in source) or **[SUSPECTED]** (needs runtime/prod confirm).
I did not run the SPA; "PROVEN" here means the code path is unambiguous in source.

---

## 1. Executive Summary

The SPA's security model is **"hide the menu item"** — and nothing else. Role separation is
enforced only by filtering sidebar links (`Sidebar.jsx:111-127`); the router itself
(`App.jsx:262-282`) has **no per-route role guard**, so any authenticated user can type
`/developer`, `/ai-studio`, or `/n8n` and load the privileged console. Worse, **every
AI-Control-Plane API call attaches a hardcoded `X-Automation-Secret`**
(`aiControlPlaneApi.js:3`, used by 66 calls) that the backend treats as `role=admin`. So a
`viewer` account, or anyone who reads the JS bundle, performs admin actions — including the
`eval`-backed policy simulator (backend RCE). The 5-tier RBAC is cosmetic on this client.

Fix first:
1. **Remove the hardcoded `AUTOMATION_SECRET` from the bundle** (`api.js:85`,
   `aiControlPlaneApi.js:3`) — the browser must never carry a service/admin secret. (W1)
2. **Add role-based route guards** in `App.jsx`; don't rely on sidebar filtering. (W2)
3. **Stop storing tokens (esp. the 7-day refresh token) in `localStorage`** — it defeats the
   httpOnly cookie the backend sets. (W3)
4. **Constrain the dynamic backend/candidate resolver** so a poisoned `localStorage` value
   can't redirect the Bearer token + secret to an attacker host. (W4)

Honest one-liner: what breaks first is trust, not uptime — a `viewer` (or a curious
customer) opens DevTools, reads the admin secret from `assets/index-*.js`, and drives the
whole control plane.

---

## 2. Findings Table

| ID | Severity | Status | Category | Location | Summary |
|----|----------|--------|----------|----------|---------|
| W1 | CRITICAL | PROVEN | Hardcoded secret / privilege (CWE-798, CWE-522) | `api.js:85`, `aiControlPlaneApi.js:3` | Admin-equivalent `X-Automation-Secret` baked into public bundle; attached to 66 calls |
| W2 | HIGH | PROVEN | Broken access control (OWASP A01, CWE-284) | `App.jsx:262-282` vs `Sidebar.jsx:111-127` | No route-level RBAC; privileged consoles reachable by URL for any role |
| W3 | HIGH | PROVEN | Token storage (CWE-522, CWE-539) | `auth.js` (`glg_token`/`glg_refresh_token` in localStorage) | 7-day refresh token in JS-readable storage defeats backend httpOnly cookie |
| W4 | MEDIUM | PROVEN | Credential redirection / SSRF-ish (CWE-601, CWE-522) | `api.js:32-42,110-125`, `auth.js:getCandidateBases` | Backend URL from localStorage/`window.__GLG_API_BASE_URL__`; token+secret sent to attacker-set host, and fanned out to multiple candidates |
| W5 | MEDIUM | SUSPECTED | CORS + credentials (CWE-942) | `api.js:229,243,304` (`credentials:'include'`) + backend CORS `*` | Cross-origin credentialed requests; refresh/logout have no CSRF token |
| W6 | LOW | PROVEN | Session validation gap (CWE-613) | `AuthContext.jsx:14-31` | `isAuthenticated` trusts localStorage before backend `getMe` resolves; validation runs once, deps `[]` |
| W7 | LOW | PROVEN | Private-range check too broad (CWE-183) | `api.js:53` | `hostname.startsWith('172.')` matches public 172.x, not just 172.16–31 |
| W8 | LOW | SUSPECTED | Supply chain (CWE-1104) | `package.json` | Dependency versions unverifiable here; no lockfile audit run |
| W9 | INFO | PROVEN | Static innerHTML (not user data) | `Header.jsx:416` | `innerHTML` assigns a constant fallback avatar; no injection, but avoid the pattern |

---

## 3. Detailed Findings

### [W1] Admin-equivalent automation secret is hardcoded in the public bundle — CRITICAL | PROVEN | CWE-798, CWE-522
**Location:** `src/services/api.js:85`, `src/services/aiControlPlaneApi.js:3`:
```js
const AUTOMATION_SECRET = import.meta.env.VITE_AUTOMATION_SECRET
  || '3322af28…[redacted]';
```
Attached to requests via `getAuthHeaders()` (`aiControlPlaneApi.js:5-16`, referenced by
**66** call sites) and directly in `api.js` (`sendChatMessage`, `generateContent`, etc.).

**What's wrong:** Vite inlines `import.meta.env.VITE_*` into the built JS at build time, and
the hardcoded fallback is shipped verbatim regardless. On the backend, this secret is
accepted by `get_current_user`/`require_automation_secret` as `role=ADMIN` (see backend F1),
so this string is an **admin bearer available to anyone who opens the bundle** — every
dashboard visitor, and anyone who reads the git repo (same value in
`automation/setup_credentials.py`).

**Impact / exploit:** Open the site → DevTools → Sources → search `X-Automation-Secret` →
copy the secret → call any endpoint as admin, including
`POST /api/v1/ai-control/policies/simulate` which `eval`s attacker input (backend F2 = RCE).
No account needed.

**Reproduction / trace:** `aiControlPlaneApi.js:3` → `getAuthHeaders()` sets
`'X-Automation-Secret': AUTOMATION_SECRET` → e.g. `simulateAiPolicy()` (`:608-615`) →
`POST /api/v1/ai-control/policies/simulate`. Backend `dependencies.py:56-63` returns admin.

**Fix (minimal):**
- Delete the fallback literal and **do not send `X-Automation-Secret` from the browser at
  all**. Dashboard calls should carry only the user's `Bearer` JWT; the backend must
  authorize by that JWT's role. Reserve the automation secret for server-to-server callers
  (n8n).
- Rotate the secret (it is burned) and, on the backend, stop mapping it to admin for
  browser-originated routes.

---

### [W2] No route-level RBAC — privileged consoles reachable by URL — HIGH | PROVEN | OWASP A01, CWE-284
**Location:** `src/App.jsx:262-282` (route table) vs `src/components/layout/Sidebar.jsx:111-127`.

**What's wrong:** Roles are enforced only by filtering which links render in the sidebar
(`universalNavItems.filter(item => item.roles.includes(userRole))`, `Sidebar.jsx:127`). The
`<Routes>` in `App.jsx` gate nothing by role: `/developer`, `/ai-studio`, `/n8n`,
`/reports`, `/inbox`, `/analytics` render for **any** authenticated user who navigates there
directly. Only `/overview` has role redirects, and those are UX, not authorization.

**Impact / exploit:** A `viewer` or `agent` types `/ai-studio` and gets the full AI Control
Plane UI. Because every control-plane call also ships the admin secret (W1), the backend
executes those actions as admin. Net effect: **the 5-tier RBAC advertised in `AGENTS.md`
does not exist on the client** — menu hiding is trivially bypassed.

**Reproduction / trace:** Log in as `viewer@glgassets.com` → browser bar `/developer` →
`App.jsx:274` renders `<DeveloperConsolePage/>` with no guard → its API calls use
`getAuthHeaders()` (secret) → succeed.

**Fix:** Add a `<RequireRole roles={[...]}>` wrapper (reads `useAuth().hasRole`) around each
privileged `<Route>`, redirecting unauthorized roles to their default tab. This is
defense-in-depth; the authoritative check must remain server-side (and W1 must be fixed so
the client can't self-elevate).

---

### [W3] Access + 7-day refresh tokens stored in localStorage — HIGH | PROVEN | CWE-522, CWE-539
**Location:** `src/services/auth.js` — `login()` writes `localStorage.setItem('glg_token', …)`
and `localStorage.setItem('glg_refresh_token', …)`; `getToken()/getRefreshToken()` read them;
`api.js` reads `glg_token` at 40+ sites.

**What's wrong:** The backend deliberately also sets the refresh token as an **httpOnly,
SameSite=lax cookie** (`auth/endpoints.py:148-156`) to keep it out of JS reach — but the
frontend then stores the same 7-day refresh token in `localStorage`, which is fully readable
by any script running on the origin. This throws away the httpOnly protection.

**Impact / exploit:** Any script-execution foothold (a future XSS, a compromised npm
dependency, a malicious browser extension on a shared kiosk) exfiltrates a 7-day refresh
token and a live access token in one `localStorage.getItem` — full account takeover that
survives the victim closing the tab.

**Fix:** Keep the refresh token **only** in the httpOnly cookie (the refresh call already
sends `credentials:'include'`, so the body copy is redundant — `auth.js:refreshToken`).
Hold the short-lived access token in memory (module/context state), not `localStorage`. If a
reload-persistence UX is required, accept re-auth via the refresh cookie on load rather than
persisting bearer tokens in JS storage.

---

### [W4] Backend URL is attacker-influenceable; credentials fan out to candidates — MEDIUM | PROVEN | CWE-601, CWE-522
**Location:** `src/services/api.js:32-42` (`localStorage.getItem('glg_api_base_url')`),
`:33-36` (`window.__GLG_API_BASE_URL__`), `:110-125` (`glg_working_backend`);
`src/services/auth.js:getCandidateBases()` and the login/refresh/getMe loops that POST
credentials to **each** candidate base until one answers.

**What's wrong:** The API base URL is taken from `localStorage`/a global window var with no
allow-list, and `resolveDynamicHost` (`api.js:13-22`) rewrites the host to
`window.location.hostname`. The auth service then iterates candidate bases and sends the
login body / `Authorization: Bearer` / `X-Automation-Secret` to whichever responds first,
caching it in `glg_working_backend`.

**Impact / exploit:** An attacker who can write one `localStorage` key (via XSS, a shared
machine, or a stored-value poisoning bug) sets `glg_working_backend` /
`glg_api_base_url` to `https://evil.tld` and the app happily ships the user's bearer token
and the admin secret there on the next call. Even absent an attacker, credentials being
tried against multiple hosts widens exposure (any misconfigured candidate logs the secret).

**Fix:** Resolve the API base from build config only; validate any stored/dynamic base
against an explicit allow-list of known origins before use; never send `Authorization` or
`X-Automation-Secret` to a non-allow-listed host. Remove the multi-candidate credential
fan-out in `auth.js` (probe health unauthenticated, then send credentials only to the chosen
origin).

---

### [W5] Credentialed cross-origin requests + no CSRF token on cookie routes — MEDIUM | SUSPECTED | CWE-942, CWE-352
**Location:** `api.js:229,243,304` etc. (`fetch(..., { credentials:'include' })`);
`auth.js:refreshToken/logout` (`credentials:'include'`, no CSRF token). Pairs with backend
`main.py:130-131` (`allow_origins=["*"]`, `allow_credentials=True`).

**What's wrong:** `credentials:'include'` sends the refresh cookie cross-origin. `/refresh`
and `/logout` are driven by the cookie alone with no anti-CSRF token, and backend CORS is
wildcard. Whether the browser actually honors credentialed `*` varies (modern browsers
reject `ACAO:*` with credentials), so I mark this SUSPECTED pending a runtime check of the
exact `Access-Control-Allow-Origin` the backend emits.

**Impact:** If the backend reflects the origin (or a proxy does), a malicious site could ride
the victim's refresh cookie to rotate/deny their session (CSRF). Bounded because the primary
API auth is a custom header (not cookie), which is CSRF-resistant.

**Fix:** Lock backend CORS to explicit origins (backend F10); add a CSRF token or
`SameSite=strict` for `/refresh` and `/logout`; drop `credentials:'include'` on calls that
authenticate via the bearer header.

---

### [W6] `isAuthenticated` trusts localStorage before server validation — LOW | PROVEN | CWE-613
**Location:** `src/context/AuthContext.jsx:8-31`.

**What's wrong:** Initial state is seeded from `localStorage` (`getUser()/getToken()`), so
`isAuthenticated` is true before `getMe()` confirms the token, and the validation effect runs
once (`[]` deps). A stale/forged `glg_user` object renders the authed shell (with the role it
claims) until/unless `getMe` fails. Combined with W2, a hand-edited `glg_user`
`{"role":"admin"}` shows admin UI locally.

**Impact:** Client-side role spoofing for UI; no server impact by itself (backend still
authorizes) — but misleads and, with W1, becomes real. 

**Fix:** Treat the app as unauthenticated until `getMe()` resolves (gate on a `verified`
flag); re-validate on route changes to privileged areas.

---

### [W7] Over-broad private-range detection — LOW | PROVEN | CWE-183
**Location:** `src/services/api.js:53` — `hostname.startsWith('172.')`.

**What's wrong:** RFC1918 covers only `172.16.0.0/12` (172.16–172.31), but `startsWith('172.')`
also matches public addresses like `172.0.x` / `172.100.x`, classifying them as LAN and
routing API traffic to `:8000` on that host.

**Impact:** Edge-case misrouting for users on public 172.x networks. Minor.

**Fix:** Match `172.(1[6-9]|2\d|3[01])\.` or parse the octet range.

---

### [W8] Dependency versions not audited — LOW | SUSPECTED | CWE-1104
**Location:** `package.json`. No lockfile scan performed in this environment.

**What's wrong / fix:** Versions listed (React 19.2.x, Vite 8.x, react-router 7.x,
recharts 3.x, leaflet 1.9.4) could not be checked against an advisory DB here. Run
`npm audit --production` in CI and pin via a committed lockfile; I make **no CVE claim**.

---

### [W9] Static `innerHTML` fallback — INFO | PROVEN
**Location:** `src/components/layout/Header.jsx:416`.

**What's wrong:** On avatar image error it assigns a **constant** string via `innerHTML`. No
user data flows in, so it is not XSS today, but the pattern invites regression. React's
auto-escaping is otherwise used throughout (I found no `dangerouslySetInnerHTML` with
untrusted data). Replace with a rendered `<span>` fallback.

---

## 4. Prioritized Remediation Plan
1. **W1** Remove hardcoded secret from bundle; stop sending `X-Automation-Secret` from the
   browser; rotate the secret. — **S** (frontend) / coordinate with backend F1.
2. **W2** Add `RequireRole` route guards in `App.jsx`. — **S**
3. **W3** Move tokens out of `localStorage` (refresh → httpOnly cookie only; access → memory).
   — **M**
4. **W4** Allow-list API origins; stop credential fan-out across candidates. — **M**
5. **W5** Lock CORS (backend) + CSRF/SameSite on `/refresh` & `/logout`. — **S/M**
6. **W6** Gate `isAuthenticated` on server validation; re-validate on privileged routes. — **S**
7. **W7/W9** Fix 172.x check; replace `innerHTML` fallback. — **S**
8. **W8** Add `npm audit` to CI + commit lockfile. — **S**

## 5. Test Additions
- **Route-guard tests (Vitest + React Testing Library):** render `<App>` with a mocked
  `viewer` auth context, navigate to `/developer`, `/ai-studio`, `/n8n`; assert a redirect to
  the role's default tab and that `DeveloperConsolePage` does not mount.
- **Secret-absence test:** grep the built bundle in CI (`vite build` then
  `grep -R "X-Automation-Secret" dist/ && exit 1`) to fail the build if a service secret
  leaks into client output.
- **Token-storage test:** after `authService.login()`, assert `localStorage.getItem('glg_refresh_token')`
  is `null` (once W3 lands).
- **API-origin allow-list test:** set `localStorage['glg_working_backend']='https://evil.tld'`,
  call an authed API helper, assert no request is made to a non-allow-listed origin and no
  `Authorization` header leaves for it (mock `fetch`).
- **hostname classifier unit test:** `172.15.0.1` and `172.32.0.1` → not LAN; `172.16.0.1`
  and `172.31.255.1` → LAN.

## 6. Open Questions / Could Not Verify
- The exact `Access-Control-Allow-Origin` the deployed backend/proxy returns (decides W5).
- Whether production actually injects `VITE_AUTOMATION_SECRET` at build (irrelevant to W1's
  severity — the fallback ships regardless, and any injected value is equally public).
- Whether any reverse proxy strips `X-Automation-Secret` from browser-origin requests
  (would blunt W1/W2 — I saw no such config in `nginx.conf`, which does not touch it).
- Dependency advisory status (W8) — needs `npm audit` with network access.
