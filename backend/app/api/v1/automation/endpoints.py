"""Automation endpoints consumed by n8n workflows.

All endpoints require X-Automation-Secret and X-Tenant-Id headers.
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header

from app.config import settings

router = APIRouter()


# ---------- Dependency ----------

async def verify_auth(
    x_automation_secret: str = Header(..., alias="X-Automation-Secret"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
):
    if x_automation_secret != settings.automation_shared_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
    return {"tenant_id": x_tenant_id or settings.default_tenant_id}


# ==========================================================
#  BOOKING
# ==========================================================

@router.post("/booking", summary="Create a property tour booking")
async def create_booking(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Receives a booking request from the Booking Calendar n8n workflow.

    Expected body fields: name, email, phone, propertyId, tourDate, tourTime, message, source, tenantId
    """
    tenant_id = auth["tenant_id"]

    # TODO: Replace with actual DB insert — this is a stub
    booking = {
        "bookingId": f"book-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "status": "PENDING",
        "name": body.get("name"),
        "email": body.get("email"),
        "phone": body.get("phone"),
        "propertyId": body.get("propertyId"),
        "tourDate": body.get("tourDate"),
        "tourTime": body.get("tourTime"),
        "message": body.get("message", ""),
        "source": body.get("source", "website"),
        "tenantId": tenant_id,
        "createdAt": datetime.utcnow().isoformat(),
    }

    # TODO: Send confirmation to customer
    # TODO: Notify sales agent

    return {
        "success": True,
        "bookingId": booking["bookingId"],
        "status": booking["status"],
    }


# ==========================================================
#  NOTIFICATION
# ==========================================================

@router.post("/notify", summary="Send a notification via one or more channels")
async def send_notification(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Sends a notification across specified channels.

    Expected body: { channels: ["email"|"slack"|"telegram"], type, title, message, recipient, tenantId }
    """
    channels = body.get("channels", ["email"])
    notif_type = body.get("type", "info")
    title = body.get("title", "")
    message = body.get("message", "")
    recipient = body.get("recipient", "")
    tenant_id = auth["tenant_id"]

    results = {}

    for channel in channels:
        try:
            if channel == "email":
                # TODO: Integrate with SendGrid / SMTP
                results[channel] = {"sent": True, "recipient": recipient or settings.default_email_recipient}
            elif channel == "slack":
                # TODO: Integrate with Slack Webhook API
                results[channel] = {"sent": True, "channel": recipient or settings.default_slack_channel}
            elif channel == "telegram":
                # TODO: Integrate with Telegram Bot API
                results[channel] = {"sent": True, "chatId": recipient or settings.default_telegram_chat_id}
            else:
                results[channel] = {"sent": False, "error": f"Unknown channel: {channel}"}
        except Exception as e:
            results[channel] = {"sent": False, "error": str(e)}

    all_success = all(r.get("sent") for r in results.values())
    return {
        "success": all_success,
        "results": results,
        "tenantId": tenant_id,
    }


# ==========================================================
#  LEAD CLASSIFICATION
# ==========================================================

@router.post("/classify", summary="Classify and qualify a lead")
async def classify_lead(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Classifies a lead's intent, priority, and assigns an agent.

    Expected body fields: leadId, name, email, phone, message, source, tenantId
    Returns: priority (high/normal/low), category, assignedAgent
    """
    tenant_id = auth["tenant_id"]
    message = body.get("message", "").lower()
    source = body.get("source", "unknown")

    # Simple rule-based classification (replace with AI/LLM for production)
    high_value_keywords = [
        "buying", "purchase", "investment", "interested in", "urgent",
        "looking for", "budget", "price", "cost", "want to see",
        "schedule", "tour", "visit", "available",
    ]
    low_value_keywords = [
        "just browsing", "maybe", "not sure", "researching",
        "compare", "information", "brochure",
    ]

    priority = "normal"
    category = "inquiry"

    if any(kw in message for kw in high_value_keywords):
        priority = "high"
        if any(kw in message for kw in ["tour", "visit", "schedule", "see"]):
            category = "tour_request"
        elif any(kw in message for kw in ["price", "cost", "budget", "investment"]):
            category = "pricing_inquiry"
        else:
            category = "hot_lead"
    elif any(kw in message for kw in low_value_keywords):
        priority = "low"
        category = "research"
    elif not message.strip():
        priority = "low"
        category = "unknown"

    # TODO: Replace with real LLM classification
    return {
        "success": True,
        "leadId": body.get("leadId"),
        "priority": priority,
        "category": category,
        "assignedAgent": "default-team",
        "tenantId": tenant_id,
    }


# ==========================================================
#  DAILY DIGEST
# ==========================================================

@router.get("/daily-digest", summary="Get daily summary for reporting")
async def daily_digest(
    auth: dict = Depends(verify_auth),
):
    """Returns a daily summary of system activity for the Daily Digest n8n workflow.

    Replace with real DB aggregation queries in production.
    """
    today = date.today().isoformat()

    # TODO: Query actual metrics from DB
    summary = {
        "summary": (
            f"GLG Assets Daily Report for {today}\n"
            "All systems operating normally."
        ),
        "newLeads": 0,
        "newBookings": 0,
        "messagesProcessed": 0,
        "escalations": 0,
        "date": today,
        "tenantId": auth["tenant_id"],
    }

    return summary


# ==========================================================
#  LOGS
# ==========================================================

@router.post("/logs", summary="Ingest workflow execution logs")
async def ingest_logs(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Accepts log entries from n8n workflows for centralized logging."""
    # TODO: Write to structured log store / DB
    return {"success": True, "logged": True, "tenantId": auth["tenant_id"]}


# ==========================================================
#  CHAT (existing AI API Caller compatibility)
# ==========================================================

@router.post("/chat", summary="Process a chat message with AI")
async def chat_message(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Processes incoming chat messages via LLM.

    Expected: { channel, userId, sessionId, message, messageId, metadata }
    Returns: { success, reply, action, confidence }
    """
    tenant_id = auth["tenant_id"]
    message = body.get("message", "")
    channel = body.get("channel", "unknown")
    user_id = body.get("userId", "unknown")
    session_id = body.get("sessionId", f"session-{datetime.utcnow().timestamp()}")

    # TODO: Integrate with LangGraph / LLM for real response
    return {
        "success": True,
        "reply": f"Thanks for your message! Our team will get back to you shortly.",
        "action": "escalate_to_human",
        "confidence": 0.5,
        "project_ids": [],
        "error_message": None,
        "tenantId": tenant_id,
    }


# ==========================================================
#  IDEMPOTENCY & DE-DUPLICATION
# ==========================================================

@router.post("/idempotency/check", summary="Check if webhook message_id has been processed")
async def check_idempotency(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Checks if incoming message_id has already been processed within TTL window."""
    from app.services.idempotency import idempotency_service

    message_id = body.get("message_id") or body.get("key")
    if not message_id:
        return {"success": True, "already_processed": False, "reason": "No message_id supplied", "tenantId": auth["tenant_id"]}

    already_processed = idempotency_service.is_processed(message_id)
    return {
        "success": True,
        "already_processed": already_processed,
        "message_id": message_id,
        "tenantId": auth["tenant_id"],
    }


@router.post("/idempotency/record", summary="Record webhook message_id as processed")
async def record_idempotency(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Records message_id in the idempotency cache with expiration TTL."""
    from app.services.idempotency import idempotency_service

    message_id = body.get("message_id") or body.get("key")
    ttl = body.get("ttl_seconds", 86400)

    if message_id:
        idempotency_service.record_processed(message_id, ttl_seconds=ttl)

    return {
        "success": True,
        "recorded": True,
        "message_id": message_id,
        "tenantId": auth["tenant_id"],
    }
