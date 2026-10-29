# GLG sales engine — setup and rollout

The sales engine replaces the n8n lead, booking and follow-up workflows with code in this repo:

- **`backend/app/sales/`** — lead pipeline, unit inventory, site visits, follow-ups, approvals, the AI sales assistant (LangGraph) and its governed tools, and the routing that moves the old chatbot's entry points onto it (`entry.py`).
- **`backend/app/worker.py`** — the job worker (Procrastinate on Postgres): agent turns, visit reminders, no-show checks, follow-ups, unit-match alerts, the 08:00 daily digest, the stale-lead sweep and hold expiry.
- **Dashboard** — Pipeline, Sales Inbox (with assistant settings and follow-up sequences), Inventory, Approvals and AI Quality.

The n8n workflows have been removed from the repository; the legacy LangGraph pipeline remains as the fallback (`ai_route_via_sales = legacy`).

## 1. Database

The web app creates the sales tables on startup (`init_db`). For Alembic users, migration `0008_sales_pipeline` creates them too.
Then create the job-queue and checkpoint tables once:

```bash
cd backend
python -m app.worker --setup
```

> The pre-existing migration `0003_knowledge_chunks` uses `sa.TSVECTOR`, which doesn't exist, so `alembic upgrade head` fails on a fresh database. Production currently relies on `init_db`.

## 2. Starting data

```bash
python scripts/seed_sales_data.py                                  # projects + default follow-up sequences
python scripts/seed_sales_data.py --units-csv units.csv            # unit inventory (template: docs/sales/units_template.csv)
python scripts/seed_sales_data.py --slots "5,6,0,1,2,3@11:00,15:00"   # visit slots Sat–Thu 11:00 and 15:00 for every project
```

Units and slots are never invented: they come only from the CSV, the `--slots` option or the Inventory page.

## 3. Run the worker

| Where | How |
| --- | --- |
| Docker Compose | `sales-worker` service (runs `--setup`, then the worker) |
| Render | `glg-sales-worker` background worker in `render.yaml` |
| Single instance | set `SALES_WORKER_IN_PROCESS=true` on the web service |
| Local | `python -m app.worker` |

## 4. Environment variables

| Variable | Needed for |
| --- | --- |
| `DATABASE_URL` | Everything (Postgres; the same value for web and worker) |
| `DEFAULT_TENANT_ID` | The tenant all channels and staff work in (one company per deployment) |
| `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` | The assistant's model (any OpenAI-compatible provider with tool calling). Without it every turn hands off to staff. |
| `FACEBOOK_APP_SECRET` | Verifying Meta webhooks. Without it Meta deliveries are refused (503). |
| `WHATSAPP_VERIFY_TOKEN` | Meta webhook verification handshake |
| `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` | Sending WhatsApp messages |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Sending Messenger and Instagram messages |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` | Telegram bot in and out |
| `DEFAULT_TELEGRAM_CHAT_ID` | Staff notifications and the daily digest (can also be set on the Sales Inbox settings) |

A channel without credentials is recorded as **not sent** with the reason; nothing is shown as delivered when it wasn't.

## 5. Point the channels at the backend

| Channel | Webhook URL | Notes |
| --- | --- | --- |
| WhatsApp Cloud API, Messenger, Instagram | `https://<backend>/api/v1/sales/webhooks/meta` | Verify token = `WHATSAPP_VERIFY_TOKEN`; subscribe to `messages` |
| Telegram | `https://<backend>/api/v1/sales/webhooks/telegram` | `setWebhook` with `secret_token = TELEGRAM_WEBHOOK_SECRET` |
| Website chat widget | `POST /api/v1/sales/webhooks/website`, poll `GET /api/v1/sales/webhooks/website/{session_id}/messages` | Called by the site's backend with `X-Automation-Secret` |

Move one channel at a time and keep the legacy pipeline (`ai_route_via_sales = legacy`) ready to switch back (plan risk table).

## 6. Rollout

New tenants start in **shadow** mode: the assistant writes drafts, staff rate them in the Sales Inbox, nothing is sent.

| Step | Move on when |
| --- | --- |
| Shadow, all channels | ≥ 50 drafts rated, ≥ 85% usable, 0 invented facts |
| Live pilot: one project, two agents | 2 weeks with 0 invented facts, p95 reply ≤ 8 s, handoff ≤ 15 min in office hours |
| Live, all projects | Weekly review of rated samples |

Switch modes and channels on the Sales Inbox → Settings & follow-ups. **Emergency stop** halts every automatic reply within one request.

## How a message flows

1. Webhook verified → message saved (repeat deliveries dropped) → lead and conversation created or found.
2. A follow-up sequence starts for new leads; any customer reply pauses nurture messages.
3. One agent turn is queued per chat (2 s debounce, never two at once).
4. The turn checks switches and limits (20 turns per chat per 10 minutes, daily token budget), then runs: prompt-injection guard → model with tools (≤ 6 model calls, ≤ 8 tool calls, 25 s) → grounding gate.
5. The grounding gate blocks any reply stating a price, unit code, year or time that wasn't in this turn's tool results, any discount promise, and availability claims without a unit lookup. A blocked reply becomes a handoff.
6. Live mode sends the reply; shadow mode stores a draft. Every turn is recorded in `sales_agent_turns`.

## Moving the old chatbot onto the sales pipeline

The old LangGraph pipeline (`app/agents/graph.py`) still answers `/api/v1/ai/chat`, the conversations AI reply and the
automation hook until the sales assistant has proved itself. One environment variable moves them:

| `AI_ROUTE_VIA_SALES` | What happens |
| --- | --- |
| `legacy` (default) | The old pipeline answers. Booking requests and hot leads it sees are still written to the sales pipeline as lead events. |
| `shadow` | The old pipeline answers; the sales assistant drafts a reply to the same message. Each pair appears on **AI Quality** for staff to rate better / same / worse. |
| `sales` | The sales assistant answers wherever it is live for that channel. Where it isn't live yet, the old pipeline answers and a comparison is stored. |

Other switches:

| Variable | Effect |
| --- | --- |
| `EMAIL_VIA_SALES=true` | Inbound email (`/api/v1/email/incoming`) becomes a lead message; the assistant drafts replies (email is **draft only** unless a manager sets it live under Sales Inbox → Settings). Sending uses `GMAIL_USER_EMAIL` / `GMAIL_APP_PASSWORD`. |
| `SOCIAL_VIA_SALES=true` | A public comment gets a fixed thank-you (never prices in public) and a DM invite; the commenter becomes a lead whose DMs go to the assistant. |
| `LEGACY_LLM_SAFETY_CHECKS=true` | Re-enables the old pipeline's extra AI moderation and safety calls. They fail closed: an error or timeout hands the chat to staff. Off by default; the rule-based policy engine runs either way. |
| `LLM_TIMEOUT_S`, `LLM_MAX_ATTEMPTS` | Chat completion timeout (10 s) and attempts (2). |

**AI Quality** (`/ai-quality`) shows who answers customers, the side-by-side replies to rate, and the retirement checks:
at least 50 rated comparisons, sales reply worse in under 10%, better or the same in at least 85%, and over at least
1,000 assistant turns a median of ≤ 2 AI calls per message, ≤ 3 for 95%, a reply within 8 s for 95%, and fewer than 10
grounding blocks per 100 replies. The old pipeline and its agents are deleted only when every check is met.

Assistant evals with known inventory (run as their own process):

```bash
python -m app.evals.sales_evals                  # grounding, multi_intent, profile_revision, language, adversarial
python -m app.evals.sales_evals --suite grounding --json report.json
```

Marketing posts: every Sunday 10:00 the worker drafts one post per project with new units, built from inventory facts
(an AI rewrite is kept only if it adds no fact). Each is a **Marketing post** on Approvals; approving marks it ready to
publish, nothing is posted automatically. "Draft posts now" on Approvals runs it on demand.

## Tests

```bash
pytest backend/tests/test_sales_services.py backend/tests/test_sales_agent.py backend/tests/test_sales_api.py \
       backend/tests/test_ai_workflow_fixes.py backend/tests/test_ai_workflow_migration.py
```

They run on SQLite with an in-memory job queue and a scripted model — no Postgres, network or API key needed.
