# GLG Assets — Modular vs Monolith Architecture Comparison

## Overview

This document compares the **old monolith approach** (single massive Master Integration Hub + standalone workflows) with the **new modular architecture** (22 specialized workflows organized in a 3-layer hierarchy). All 22 modular workflows have been validated and imported into the n8n cloud instance at [shown.app.n8n.cloud](https://shown.app.n8n.cloud).

---

## The Two Approaches

### Old Monolith (5 workflows)

| Workflow | Purpose | Nodes | Design |
|----------|---------|-------|--------|
| Master Integration Hub | Central hub connecting 8+ backend endpoints | Large single-path | Switch node routing |
| Lead Capture Webhook | Landing page lead capture | Medium | Self-contained |
| Lead Qualification & Routing | Classify & route leads | Medium | Self-contained |
| Platform Automation Main | Legacy monolith | Large | Unstructured |
| Message Processing | AI message processing | Medium | Self-contained |

**Problems:**
- Hub has single point of failure — one broken node blocks all channels
- No separation of concerns (WhatsApp + FB + IG + analytics all in one graph)
- Hard to debug: 50+ nodes in a single canvas
- Every change requires re-testing the entire workflow
- Cannot reuse logic (e.g., AI API call duplicated across workflows)
- No standardized error handling or logging
- Credentials mixed inline without proper abstraction

### New Modular Architecture (22 workflows)

```
automation/02-modular/
├── subworkflows/                     # 7 reusable utility workflows
│   ├── swf-ai-api-caller.js          # Calls FastAPI /api/v1/automation/chat
│   ├── swf-whatsapp-send.js          # Sends WhatsApp via Meta API
│   ├── swf-facebook-send.js          # Sends FB Messenger via Graph API
│   ├── swf-instagram-send.js         # Sends IG DM via Graph API
│   ├── swf-notification.js           # Multi-channel alerts (Slack/Telegram/Email)
│   ├── swf-error-handler.js          # Catches errors, logs, alerts
│   └── swf-log.js                    # Standardized API logging
│
├── channel-workflows/                # 6 channel-specific entry points
│   ├── wf-incoming-whatsapp.js       # Meta webhook → AI → reply → log
│   ├── wf-facebook-messenger.js      # FB page messages
│   ├── wf-instagram-dm.js            # Instagram DMs
│   ├── wf-facebook-comments.js       # FB post comments
│   ├── wf-instagram-comments.js      # IG post comments
│   └── wf-website-live-chat.js       # Website live chat widget
│
└── admin-workflows/                  # 9 admin & support workflows
    ├── wf-brochure-sender.js         # Automated brochure delivery
    ├── wf-project-images.js          # Project image carousel sending
    ├── wf-human-escalation.js        # Escalation to human agents
    ├── wf-knowledge-upload.js        # Knowledge base document ingestion
    ├── wf-content-generator.js       # AI content generation (social posts)
    ├── wf-scheduled-posts.js         # Scheduled social media publishing
    ├── wf-analytics.js               # Daily analytics report generation
    ├── wf-failed-ai-replies.js       # Retry/review failed AI responses
    └── wf-moderation.js              # Content moderation
```

---

## Comparison Table

| Criterion | Old Monolith | Modular (New) | Impact |
|-----------|-------------|---------------|--------|
| **Total workflows** | 5 | 22 | More focused, easier to maintain |
| **Avg. nodes per workflow** | ~30-50 | ~5-7 | Smaller = easier to debug |
| **Reusability** | None (duplicated logic) | 7 shared subworkflows | Changes propagate automatically |
| **Error handling** | Basic per-workflow | Dedicated error handler + alerts | Faster incident response |
| **Logging** | None standardized | SWF-Log subworkflow | Full audit trail |
| **Multi-channel** | Single hub | 6 dedicated channel workflows | Isolated failures |
| **Admin functions** | Mixed into hub | 9 dedicated admin workflows | Clear ownership |
| **Onboarding speed** | Weeks (big graph) | Hours (small focused workflows) | Faster team scaling |
| **Credential use** | Inline/hardcoded | newCredential() references | Centralized management |
| **Testing** | Manual full regression | Test each subworkflow independently | Safer deployments |
| **Scalability** | Limited | Parallel channel processing | Linearly scalable |

---

## What Makes This Modular

### 1. Subworkflow Reusability
Channel workflows **call** subworkflows via **Execute Workflow Trigger** nodes. The subworkflow pattern uses:
- `ExecuteWorkflowTrigger` — receives standardized inputs
- `Set` nodes to normalize payloads
- Business logic (API calls, formatting)
- `Set` nodes to return standardized output shapes
- `ifElse` for branching (success vs error paths)

All subworkflows return a consistent `{success, ...}` shape so callers can handle errors uniformly.

### 2. Stable Output Contracts

**SWF-AI-API-Caller output:**
```json
{
  "success": true|false,
  "reply": "string",
  "action": "inquire|schedule|escalate|complete|error",
  "confidence": 0.95,
  "project_ids": ["proj_001"],
  "error_message": ""|"description"
}
```

**SWF-WhatsApp-Send output:**
```json
{
  "success": true|false,
  "messageId": "wamid.ABC123" | null,
  "error": "" | "description"
}
```

### 3. Environment-Based Configuration
All workflows use `$env.*` variables instead of hardcoded URLs/tokens:
- `$env.FASTAPI_BASE_URL` — Backend API base URL
- `$env.WHATSAPP_PHONE_NUMBER_ID` — WhatsApp Business API phone ID
- `$env.TELEGRAM_BOT_TOKEN` — Telegram notification bot
- `$env.SLACK_WEBHOOK_URL` — Slack alert webhook
- `$env.EMAIL_API_KEY` / `$env.EMAIL_API_URL` — Email notifications
- `$env.TENANT_ID` — Multi-tenant support

### 4. Layered Error Handling
```
Channel Workflow → calls SWF-AI-API-Caller → if error:
  → SWF-AI-API-Caller returns {success: false, error_message: "..."}
  → Channel workflow calls SWF-Error-Handler
  → SWF-Error-Handler logs to API + sends Slack alert
  → Channel workflow returns graceful error response
```

---

## n8n Cloud Workflow IDs

### Subworkflows (7)
| Name | ID | URL |
|------|----|-----|
| SWF-AI-API-Caller (Modular) | `YsV5tnnvrKAcI1Zk` | [Open](https://shown.app.n8n.cloud/workflow/YsV5tnnvrKAcI1Zk) |
| SWF-WhatsApp-Send (Modular) | `ZQjSYg2NUYNKvuIl` | [Open](https://shown.app.n8n.cloud/workflow/ZQjSYg2NUYNKvuIl) |
| SWF-Facebook-Send (Modular) | `xc4RpXER4BDYBU7Q` | [Open](https://shown.app.n8n.cloud/workflow/xc4RpXER4BDYBU7Q) |
| SWF-Instagram-Send (Modular) | `cT0VAAcyAAOBKTOY` | [Open](https://shown.app.n8n.cloud/workflow/cT0VAAcyAAOBKTOY) |
| SWF-Notification (Modular) | `9iCG6dJJH36G8qJS` | [Open](https://shown.app.n8n.cloud/workflow/9iCG6dJJH36G8qJS) |
| SWF-Error-Handler (Modular) | `d18Lu3sZxMB7zlZC` | [Open](https://shown.app.n8n.cloud/workflow/d18Lu3sZxMB7zlZC) |
| SWF-Log (Modular) | `vXp6fZHjhETnjVMp` | [Open](https://shown.app.n8n.cloud/workflow/vXp6fZHjhETnjVMp) |

### Channel Workflows (6)
| Name | ID | URL |
|------|----|-----|
| WF-Incoming-WhatsApp (Modular) | `oQeG9zA0BL0y3lz0` | [Open](https://shown.app.n8n.cloud/workflow/oQeG9zA0BL0y3lz0) |
| WF-Facebook-Messenger (Modular) | `jEVquEG367goIp2b` | [Open](https://shown.app.n8n.cloud/workflow/jEVquEG367goIp2b) |
| WF-Instagram-DM (Modular) | `Wkw9vub5g9x5CufS` | [Open](https://shown.app.n8n.cloud/workflow/Wkw9vub5g9x5CufS) |
| WF-Facebook-Comments (Modular) | `qRdOcS5eQibaoOcK` | [Open](https://shown.app.n8n.cloud/workflow/qRdOcS5eQibaoOcK) |
| WF-Instagram-Comments (Modular) | `5KBucoA5JWPUhNEK` | [Open](https://shown.app.n8n.cloud/workflow/5KBucoA5JWPUhNEK) |
| WF-Website-Live-Chat (Modular) | `BM2t1Q7AaRMAXL9T` | [Open](https://shown.app.n8n.cloud/workflow/BM2t1Q7AaRMAXL9T) |

### Admin Workflows (9)
| Name | ID | URL |
|------|----|-----|
| WF-Brochure-Sender (Modular) | `267yYbMpxCUzfnHL` | [Open](https://shown.app.n8n.cloud/workflow/267yYbMpxCUzfnHL) |
| WF-Project-Images (Modular) | `UyiGamDJHsVWVs2T` | [Open](https://shown.app.n8n.cloud/workflow/UyiGamDJHsVWVs2T) |
| WF-Human-Escalation (Modular) | `fQiorEA13H57aeiK` | [Open](https://shown.app.n8n.cloud/workflow/fQiorEA13H57aeiK) |
| WF-Knowledge-Upload (Modular) | `EE90hGJOtahLYsIB` | [Open](https://shown.app.n8n.cloud/workflow/EE90hGJOtahLYsIB) |
| WF-Content-Generator (Modular) | `DOgNzsVn9MLJVT7J` | [Open](https://shown.app.n8n.cloud/workflow/DOgNzsVn9MLJVT7J) |
| WF-Scheduled-Posts (Modular) | `JocUw5TOJfQl4OEv` | [Open](https://shown.app.n8n.cloud/workflow/JocUw5TOJfQl4OEv) |
| WF-Analytics (Modular) | `OIHFV70DO4c9B928` | [Open](https://shown.app.n8n.cloud/workflow/OIHFV70DO4c9B928) |
| WF-Failed-AI-Replies (Modular) | `XnElXJROEXl9nm8A` | [Open](https://shown.app.n8n.cloud/workflow/XnElXJROEXl9nm8A) |
| WF-Moderation (Modular) | `4tioJTsiNa2xoqK1` | [Open](https://shown.app.n8n.cloud/workflow/4tioJTsiNa2xoqK1) |

---

## Remaining Steps to Production

### Credential Setup (in n8n UI)
These credentials need to be created manually in the n8n UI before any workflow can execute:

1. **Backend API Key** (httpHeaderAuth) — X-Automation-Secret header for FastAPI auth
2. **WhatsApp Business** (whatsAppApi) — Meta WhatsApp Cloud API credentials
3. **Facebook Graph** (oAuth2) — For FB Messenger / Instagram Graph API
4. **Slack Webhook** — For error alerts and notifications

### Environment Variables (set in n8n)
```
FASTAPI_BASE_URL=https://host.docker.internal:8000
WHATSAPP_PHONE_NUMBER_ID=your_meta_phone_id
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TELEGRAM_BOT_TOKEN=your_bot_token
EMAIL_API_KEY=your_sendgrid_key
EMAIL_API_URL=https://api.sendgrid.com/v3/mail/send
FROM_EMAIL=noreply@glgassets.com
TENANT_ID=glg-assets
```

### Architecture Diagram

```
                     ┌─────────────────────────┐
                     │    Client Channels       │
                     │ WhatsApp │ FB │ IG │ Web │
                     └─────────┬──┬──┬──┬──────┘
                               │  │  │  │
                    ┌──────────▼──▼──▼──▼──────────┐
                    │    Channel Workflows (6)     │
                    │  Receive → Parse → Normalize  │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │    Subworkflows (7)          │
                    │  AI API │ Send │ Log │ Error │
                    │  Notify │ FB   │ IG  │ Alert │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │    FastAPI Backend           │
                    │  /api/v1/automation/chat     │
                    │  /api/v1/automation/logs     │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │    Admin Workflows (9)       │
                    │  Brochure │ Images │ Execute │
                    │  Content  │ Escalate │ Report│
                    └──────────────────────────────┘
```
