# GLG Assets Real Estate Automation
# n8n Workflow Index
# Generated: 2026-07-26

This directory contains n8n workflow JSON exports organized by domain.

## Directory Structure

automation/
  social/           - Social media integrations (WhatsApp, Facebook, Instagram, website)
  ai/               - AI/LLM workflows (ask-ai, rag, embeddings, agents)
  notifications/    - Notification channels (email, slack, telegram)
  analytics/        - Reporting and analytics (daily-report, engagement, failed-replies)
  moderation/       - Content moderation (toxicity, spam, escalation)
  content/          - Content generation (social posts, captions, brochures)
  glg-assets/       - GLG Assets-specific workflows (NEW)

## GLG Assets Workflows (MCP-enabled)

These workflows are created and managed via the n8n MCP SDK.
They connect to the FastAPI backend at /api/v1/automation/*.

| ID  | Name                          | Webhook/Trigger Path          | Status     |
|-----|-------------------------------|-------------------------------|------------|
| WF1 | Lead Capture                  | POST /leads/capture           | ✅ Imported|
| WF2 | Booking Calendar              | POST /bookings/create         | ✅ Created |
| WF3 | Lead Qualification & Routing  | POST /leads/qualify           | ✅ Created |
| WF4 | Notification Hub              | POST /notifications/send      | ✅ Created |
| WF5 | Daily Digest                  | Schedule (0 8 * * 1-5)        | ✅ Created |
| WF6 | AI API Caller (Subworkflow)   | (called by other workflows)   | ✅ Existing|
| WF7 | Incoming WhatsApp Message     | Meta webhook                  | ✅ Existing|

## Setup

1. Copy `backend/.env.example` to `.env` and fill in your values
2. Start FastAPI: `cd backend && uvicorn app.main:app --reload`
3. In n8n, go to Settings > Environment Variables and set:
   - FASTAPI_BASE_URL
   - AUTOMATION_SHARED_SECRET
   - DEFAULT_TENANT_ID
4. Create HTTP Header Auth credentials in n8n for the FastAPI backend
5. Test each workflow manually in the n8n editor

## Required n8n Credentials

For the HTTP Request nodes to reach your FastAPI backend, create a credential:
- Type: **Header Auth**
- Name: `FastAPI Backend`
- Header Name: `X-Automation-Secret`
- Header Value: (same as AUTOMATION_SHARED_SECRET)

Then assign this credential to all HTTP Request nodes in the workflows.
