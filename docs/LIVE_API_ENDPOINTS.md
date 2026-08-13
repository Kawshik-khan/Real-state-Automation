# GLG Real Estate Automation — Live API & Webhook Endpoints Directory

This document details all live API endpoints, webhook listeners, n8n Cloud triggers, authentication headers, and request/response specifications across the platform.

---

## 🔒 Authentication & Headers

Unless otherwise noted, all automation and internal API endpoints require the following headers:

| Header | Type | Description |
| :--- | :--- | :--- |
| `X-Automation-Secret` | `string` | Shared secret key for verifying incoming requests (`3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8`). |
| `X-Tenant-Id` | `string` | *(Optional)* Tenant scoping identifier (Default: `glg-assets-main`). |
| `Authorization` | `string` | *(Optional)* `Bearer <token>` for user dashboard authentication (`/api/v1/auth/*`). |

---

## 🌐 1. System Health & Probes

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | Root service health check & OpenAPI documentation link | ❌ |
| `GET` | `/health` | Core backend health probe | ❌ |
| `GET` | `/health/ready` | Kubernetes / Render readiness probe | ❌ |
| `GET` | `/health/live` | Kubernetes / Render liveness probe | ❌ |

---

## ⚡ 2. Core MVP API (`/api/...`)

| Method | Endpoint | Description | Request Body / Parameters |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/chat` | Main AI conversational pipeline (LangGraph + RAG) | `{ message, userId, channel, sessionId }` |
| `POST` | `/api/content` | Social media post generator (FB, IG, LinkedIn) | `{ topic, platform, target_audience }` |
| `POST` | `/api/knowledge/upload` | Ingest PDF/DOCX/OCR file into vector index | `multipart/form-data` (`file`, `doc_id`, `project`) |
| `POST` | `/api/moderation` | AI content safety & policy moderation check | `{ text, channel }` |
| `GET` | `/api/projects` | List all real-estate property projects | None |
| `GET` | `/api/project/{id}` | Get property project details by ID or slug | `{id}` (Path Parameter) |
| `POST` | `/api/search` | Hybrid property & knowledge base vector search | `{ query, top_k, project_filter }` |

---

## ✉️ 3. Email Reply Automation (`/api/v1/email/...`)

| Method | Endpoint | Description | Key Payload Fields |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/email/incoming` | Ingest incoming email, trigger AI RAG, evaluate `AUTO_SEND` vs `REQUIRES_APPROVAL` | `{ message_id, thread_id, sender_email, subject, body_text, attachments }` |
| `GET` | `/api/v1/email/threads` | List all email threads sorted by last activity | `?status=pending_approval` (Optional Query) |
| `GET` | `/api/v1/email/threads/{thread_id}` | Get complete message history and AI draft details | `{thread_id}` (Path Parameter) |
| `POST` | `/api/v1/email/threads/{thread_id}/approve` | Approve & dispatch staged AI draft via n8n | `{ edited_subject, edited_reply }` (Optional) |
| `POST` | `/api/v1/email/threads/{thread_id}/edit-and-send` | Edit draft content and dispatch immediately | `{ edited_subject, edited_reply }` |
| `POST` | `/api/v1/email/threads/{thread_id}/reject` | Reject/discard AI draft for manual agent handling | None |
| `POST` | `/api/v1/email/threads/dispatch-outbound` | Endpoint called by n8n relays to dispatch outbound email | `{ thread_id, recipient_email, subject, body }` |

---

## ⚙️ 4. n8n Automation & System Telemetry (`/api/v1/automation/...`)

| Method | Endpoint | Description | Notes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/automation/n8n/health` | Real-time workflow state, node latency, and system health status | Consumed by Dashboard (`/monitoring`) |
| `POST` | `/api/v1/automation/n8n/workflows/{workflow_id}/toggle` | Enable or disable specific n8n workflow | `{ active: boolean }` |
| `POST` | `/api/v1/automation/n8n/workflows/{workflow_id}/test` | Execute real-time latency ping test across workflow nodes | Returns node-by-node execution time breakdown |
| `POST` | `/api/v1/automation/booking` | Property tour booking ingress | `{ name, email, phone, propertyId, tourDate }` |
| `POST` | `/api/v1/automation/notify` | Dispatch notifications across channels (Slack, Email, Telegram) | `{ channels: ["slack", "telegram"], message }` |
| `POST` | `/api/v1/automation/classify` | Lead classification & priority scoring engine | `{ lead_email, message, source }` |
| `GET` | `/api/v1/automation/daily-digest` | Fetch executive daily automation summary | Returns daily lead counts & AI metrics |
| `POST` | `/api/v1/automation/logs` | Centralized log ingestion endpoint from n8n workflows | `{ workflow_id, execution_id, level, data }` |
| `POST` | `/api/v1/automation/idempotency/check` | Check if message ID has been processed | `{ message_id }` |
| `POST` | `/api/v1/automation/idempotency/record` | Record message ID to prevent duplicate processing | `{ message_id }` |

---

## ☁️ 5. Cloud n8n Active Webhook Triggers (`https://glg-ai.app.n8n.cloud`)

| Workflow Name | Webhook URL | Method | Status |
| :--- | :--- | :---: | :---: |
| **GLG Email Reply Automation** | `https://glg-ai.app.n8n.cloud/webhook/glg-email-webhook` | `POST` | **Active / Published** (`sPdLa6ogi2pJifJg`) |
| **Social AI OS Master** | `https://glg-ai.app.n8n.cloud/webhook/lead-capture` | `POST` | **Active / Published** |
| **Telegram Ingress Webhook** | `https://glg-ai.app.n8n.cloud/webhook/telegram-ingress` | `POST` | **Active / Published** |
| **WhatsApp Ingress Webhook** | `https://glg-ai.app.n8n.cloud/webhook/whatsapp-ingress` | `POST` | **Active / Published** |

---

## 📱 6. Social Media & Multi-Channel Messaging (`/api/v1/social/...`)

| Method | Endpoint | Description | Target Channel |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/social/telegram` | Telegram Bot Webhook & AI RAG conversation processing | Telegram |
| `POST` | `/api/v1/social/telegram/setup-webhook` | Programmatically register Telegram Bot webhook URL | Telegram |
| `GET` | `/api/v1/social/telegram/status` | Get Telegram Bot connectivity and webhook status | Telegram |
| `POST` | `/api/v1/social/facebook/comments` | Facebook post comment auto-reply pipeline | Facebook |
| `POST` | `/api/v1/social/facebook/incoming` | Facebook Page Messenger incoming message ingress | Facebook |
| `POST` | `/api/v1/social/facebook/send` | Facebook Messenger outbound message dispatcher | Facebook |
| `POST` | `/api/v1/social/instagram/comments` | Instagram media comment auto-reply pipeline | Instagram |
| `POST` | `/api/v1/social/instagram/dm` | Instagram Direct Message (DM) AI assistant | Instagram |
| `POST` | `/api/v1/social/website/livechat` | Website Live Chat widget backend endpoint | Web Chat |
| `POST` | `/api/v1/social/whatsapp/incoming` | WhatsApp Business API incoming message handler | WhatsApp |
| `POST` | `/api/v1/social/whatsapp/media` | WhatsApp image / document media attachment parser | WhatsApp |
| `POST` | `/api/v1/social/leads/capture` | Social Lead Ads (Meta Lead Forms) payload capture | Social Ads |

---

## 📚 7. Knowledge Base & Vector Indexing (`/api/v1/knowledge/...`)

| Method | Endpoint | Description | Parameters |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/knowledge/upload` | Multipart document parser, text chunker & vector upsert | `file`, `doc_id`, `project`, `location` |
| `POST` | `/api/v1/knowledge/text` | Plain text knowledge ingestion and embedding | `{ text, title, tags }` |
| `GET` | `/api/v1/knowledge/documents` | List all ingested knowledge base documents | None |
| `DELETE` | `/api/v1/knowledge/documents/{doc_id}` | Delete a document and purge vector embeddings | `{doc_id}` (Path Parameter) |

---

## 💬 8. Live Customer Conversations & Agent Takeover (`/api/v1/conversations/...`)

| Method | Endpoint | Description | Response / Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/conversations` | List active leads and customer conversations | Returns array of thread objects |
| `POST` | `/api/v1/conversations` | Create a new conversation / lead thread | `{ customer_name, channel, phone, email }` |
| `GET` | `/api/v1/conversations/stream` | **SSE Event Stream** for real-time dashboard UI updates | `text/event-stream` stream |
| `POST` | `/api/v1/conversations/{conv_id}/message` | Ingest customer message and trigger AI response | `{ message, sender_type }` |
| `POST` | `/api/v1/conversations/{conv_id}/takeover` | Toggle between **AI Auto-Pilot** and **Human Agent Control** | `{ is_human_agent_active: boolean }` |
| `POST` | `/api/v1/conversations/{conv_id}/reply` | Post manual human agent reply to customer channel | `{ message, agent_name }` |

---

## 📊 9. Analytics & Reporting (`/api/v1/analytics/...`)

| Method | Endpoint | Description | Key Output |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/analytics/daily` | Generate daily Social AI Performance Report | Lead stats, response times, channel split |
| `POST` | `/api/v1/analytics/engagement` | Fetch engagement rates across FB, IG, WhatsApp, Email | Click-through rates & conversation depth |
| `POST` | `/api/v1/analytics/failed-replies` | Monitor failed AI replies & low confidence fallbacks | Escalation audit log |
| `POST` | `/api/v1/analytics/weekly-digest` | Generate executive weekly summary digest | Conversion stats & lead velocity |

---

## 🔑 10. User Auth & Identity (`/api/v1/auth/...`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/login` | Authenticate user and issue JWT Access Token | ❌ |
| `POST` | `/api/v1/auth/register` | Register new team user / sales agent | ❌ |
| `GET` | `/api/v1/auth/me` | Fetch current user profile metadata | Bearer JWT |
| `GET` | `/api/v1/auth/users` | List all system users (Admin) | Bearer JWT |

---

## 🔌 11. Real-Time WebSockets (`/api/v1/ws/...`)

| Method / Protocol | Endpoint | Description |
| :--- | :--- | :--- |
| `WebSocket` | `ws://localhost:8000/api/v1/ws/chat` | Full-duplex WebSocket connection for real-time chat & live status streaming |
