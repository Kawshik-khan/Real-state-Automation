# GLG Assets — n8n Integration Setup Guide

## Overview

This project uses **n8n Cloud** (shown.app.n8n.cloud) as the workflow automation engine, connected to a **FastAPI backend** running locally.

## Architecture

```
[Social Media / WhatsApp / Web / Email / Form]
        │
        ▼
┌─────────────────────────────────────┐
│      n8n Cloud                       │  ← https://shown.app.n8n.cloud
│  (Workflow Automation)               │
│                                      │
│  GLG Assets - Backend Integration Hub  │  NEW! 11 nodes — 7 endpoints + lead routing
│  GLG Assets - Lead Capture Webhook     │  NEW! 7 nodes — webhook → classify → route
│  GLG Assets - Master Integration Hub   │  Updated! 8 nodes — legacy hub
│  GLG Assets wf2-5                      │  Per-service workflows (booking, notify, daily, lead)
│  Social AI OS v1                       │  All-in-one social orchestration
│  10 standalone workflows               │  WhatsApp, error handling, etc.
└──────────┬──────────────────────────┘
           │ HTTP (X-Automation-Secret header auth)
           ▼
┌─────────────────────────────┐
│  FastAPI Backend             │  ← localhost:8000
│  (ports 8000 + 8001)        │
│  routers: automation, ai,   │
│  content, social, moderation,│
│  knowledge, analytics,      │
│  escalations, media,        │
│  notifications              │
└─────────────────────────────┘
```

## ☐ Prerequisites

Create these **Environment Variables** in **n8n → Settings → Environment**:

| Variable | Value | Purpose |
|----------|-------|---------|
| `FASTAPI_BASE_URL` | `http://localhost:8000` (local) or deployed URL | Backend API base |
| `DEFAULT_TENANT_ID` | `glg-assets-main` | Default tenant ID |

> ⚠️ **n8n Cloud blocks localhost (SSRF protection)**
> For local dev, use one of:
> - **ngrok tunnel:** `npx ngrok http 8000` → set `FASTAPI_BASE_URL` to the ngrok URL
> - **Self-host n8n** via Docker: `docker compose up n8n` (see `docker-compose.yml` in root)
> - **Deploy the backend** to a public cloud endpoint (Render, Railway, etc.)

## ☐ Step 1: Create the Header Auth Credential (CRITICAL)

This is the **#1 missing piece** — all HTTP Request nodes reference this credential but it doesn't exist yet.

1. Go to **n8n → Credentials → Add Credential**
2. Type: **Header Auth**
3. Name: `Backend API Key` (must match what workflows expect)
4. **Header Name**: `X-Automation-Secret`
5. **Header Value**: `change-me-in-production` (or the value in your `backend/.env` `AUTOMATION_SHARED_SECRET`)
6. **Save**

Then for **each workflow** with HTTP Request nodes:
- Open the workflow
- Click each HTTP Request node → go to **Credential** dropdown
- Select `Backend API Key`
- Save workflow

## ☐ Step 2: Workflow Overview

### 1. GLG Assets — Backend Integration Hub (NEW)
**ID:** `IQwnA2cudSWCo5wv`
**Purpose:** Comprehensive integration hub with 11 nodes connecting to ALL backend endpoints.
**Nodes:**
| # | Node | Endpoint | Method |
|---|------|----------|--------|
| 1 | Health Check | `{BASE}/health` | GET |
| 2 | Daily Digest | `{BASE}/api/v1/automation/daily-digest` | GET |
| 3 | Create Booking | `{BASE}/api/v1/automation/booking` | POST |
| 4 | Send Notification | `{BASE}/api/v1/automation/notify` | POST |
| 5 | Classify Lead | `{BASE}/api/v1/automation/classify` | POST |
| 6 | AI Chat | `{BASE}/api/v1/automation/chat` | POST |
| 7 | Ingest Logs | `{BASE}/api/v1/automation/logs` | POST |
| 8A | High Priority Lead? | IF node — checks if `$json.priority == "high"` |
| 8B | Notify Urgent Lead | `{BASE}/api/v1/automation/notify` | POST |
| 8C | Log Normal Lead | `{BASE}/api/v1/automation/logs` | POST |

**Features:** Lead classification with priority routing (high-priority leads trigger urgent Slack+email notification, normal leads are logged). Retry logic on classify + chat nodes (3 tries, 2s apart). Error handling via `continueErrorOutput` on all critical nodes.

### 2. GLG Assets — Lead Capture Webhook (NEW)
**ID:** `aI09BIthIt5hst9S`
**Purpose:** External HTTP endpoint that accepts lead data from any source (forms, APIs, websites).
**Flow:** Webhook (`POST /leads/capture`) → Normalize fields → Backend classify → Route priority → Respond to caller
**Webhook URL:** `https://shown.app.n8n.cloud/webhook/leads/capture`
**Input format:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "propertyId": "prop-001",
  "message": "Interested in 3BR apartment",
  "source": "website"
}
```
**Response:** `{ "success": true, "leadId": "...", "priority": "high|normal", "category": "...", "assignedAgent": "..." }`

### 3. GLG Assets — Master Integration Hub (UPDATED)
**ID:** `VMVAiXhYYk9vQuIM`
**Purpose:** Original integration hub (8 nodes). Now updated — logs endpoint uses correct POST method.
**Features:** Manual trigger → 7 parallel HTTP nodes connecting all backend endpoints.

### 4. GLG Assets — Booking Calendar (wf2)
**ID:** `oizj8jYoRuDncbz4`
**Purpose:** Property tour booking via webhook trigger.

### 5. GLG Assets — Lead Qualification & Routing (wf3)
**ID:** `3fQ6NHCqt7YI03bp`
**Purpose:** Classifies and routes incoming leads.

### 6. GLG Assets — Notification Hub (wf4)
**ID:** `UvY3HQgVljNCJAxe`
**Purpose:** Multi-channel notification dispatch.

### 7. GLG Assets — Daily Digest (wf5)
**ID:** `MFmQm0Pwdnd8mfWL`
**Purpose:** Scheduled daily email digest (Mon-Fri 8AM).
**Cron:** `0 8 * * 1-5`

### 8. WhatsApp Inbound (WF1)
**ID:** `vWmB3DbB9guaI7Kp`
**Purpose:** Receives incoming WhatsApp messages and routes them.
**Note:** Needs Meta WhatsApp Webhook verified — requires deployed public HTTPS endpoint.

### 9. WhatsApp Send Sub-workflow (SWF)
**ID:** `1q5rGvyvI0EUIrKe`
**Purpose:** Callable sub-workflow for sending WhatsApp messages via Meta API.

### 10. Error Handler + Idempotency Guard
**IDs:** `RNwUuF4i2agoX8St`, `ApSyRPYcnnejCieS`
**Purpose:** Reusable sub-workflows for error handling and deduplication.

## ☐ Step 3: Test the Connection

1. Start your backend: `cd backend && uvicorn app.main:app --port 8000`
2. If using n8n cloud + localhost: use **ngrok**:
   ```bash
   npx ngrok http 8000
   # Copy the https://xxxx.ngrok.io URL → set as FASTAPI_BASE_URL in n8n env
   ```
3. Or self-host n8n: `docker compose up -d` (see root docker-compose.yml)
4. Open **GLG Assets - Backend Integration Hub** in n8n
5. Click **"Test Workflow"** → for the **"1. Health Check"** node click **"Test Step"**
6. Expected response:
   ```json
   { "status": "ok", "service": "GLG Assets Automation API" }
   ```

## ☐ Step 4: Activate Production Workflows

Once tested, toggle workflows to **Active**:

| Workflow | When to Activate |
|----------|-----------------|
| GLG Assets - Daily Digest | After backend deployed (cron) |
| GLG Assets - Lead Capture Webhook | When external forms/websites need to submit leads |
| GLG Assets - Master Integration Hub | For manual testing |
| WhatsApp workflows | After Meta Webhook verified + deployed publicly |
| Error Handler / Idempotency | Enable as sub-workflows when other workflows active |

## Project Files

All workflow SDK source and exports live in `D:\Softwear Project\Realstate Automation\automotion\`:

| File | Description |
|------|-------------|
| `automation/glg-backend-hub.js` | Backend Integration Hub SDK source (11 nodes) |
| `automation/glg-lead-capture.js` | Lead Capture Webhook SDK source (7 nodes) |
| `automation/glg-master-integration.js` | Master Integration Hub SDK source (8 nodes) |
| `automation/glg-assets/` | JSON exports of 4 per-service workflows |
| `automation/social-ai-os-v1-all-in-one.json` | Social AI OS workflow |

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| "401 Unauthorized" | No credential assigned to HTTP node | Assign "Backend API Key" credential to node |
| "Connection refused" | Backend not running | Start `uvicorn app.main:app --port 8000` |
| "Failed to fetch" or "ERR_NAME_NOT_RESOLVED" | n8n cloud blocks localhost | Use ngrok tunnel or self-host n8n |
| "Workflow execution failed: credentials not found" | Credential name mismatch | Create credential named "Backend API Key" |
| Webhook not responding | Workflow not activated | Toggle workflow to Active |
| Daily digest not firing | Cron timezone mismatch | Check n8n instance timezone in Settings |
