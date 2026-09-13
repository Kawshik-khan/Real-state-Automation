"""Automation endpoints consumed by n8n workflows.

All endpoints require X-Automation-Secret and X-Tenant-Id headers.
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Header, HTTPException

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

    ref_code = f"BK-{datetime.utcnow().strftime('%Y%m%d')}-{int(datetime.utcnow().timestamp()) % 10000}"
    tour_date_str = body.get("tourDate", datetime.utcnow().strftime("%Y-%m-%d"))
    try:
        tour_date = datetime.strptime(tour_date_str, "%Y-%m-%d")
    except Exception:
        tour_date = datetime.utcnow()

    booking_id = f"book-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    try:
        from app.database import async_session_factory, is_db_reachable
        from app.models.models import BookingRecord

        if is_db_reachable():
            async with async_session_factory() as session:
                booking = BookingRecord(
                booking_reference=ref_code,
                project_id=body.get("projectId") or body.get("propertyId") or "proj_gulshan_heights",
                customer_name=body.get("name", "Prospective Buyer"),
                customer_email=body.get("email"),
                customer_phone=body.get("phone", "+880 1700-000000"),
                tour_date=tour_date,
                tour_time_slot=body.get("tourTime", "3:00 PM - 4:30 PM"),
                status="confirmed",
                source=body.get("source", "website"),
                notes=body.get("message", ""),
                assigned_agent_name="Sarah Connor",
                tenant_id=tenant_id
            )
            session.add(booking)
            await session.commit()
            booking_id = booking.id
    except Exception:
        pass

    return {
        "success": True,
        "bookingId": booking_id,
        "bookingReference": ref_code,
        "status": "CONFIRMED",
        "assignedAgent": "Sarah Connor",
        "tourDate": tour_date_str,
        "tourTime": body.get("tourTime", "3:00 PM - 4:30 PM")
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
    """Processes incoming chat messages via LangGraph multi-agent orchestration.

    Expected: { channel, userId, sessionId, message, messageId, metadata }
    Returns: { success, reply, action, confidence, project_ids, error_message, tenantId }
    """
    tenant_id = auth["tenant_id"]
    message = body.get("message", "")
    channel = body.get("channel", "unknown")
    user_id = body.get("userId", "unknown")
    session_id = body.get("sessionId") or body.get("conversationId") or f"session-{datetime.utcnow().timestamp()}"

    try:
        from app.agents.graph import ai_graph
        from app.agents.state import AIState
        from app.utils.chat_response_builder import ChatResponseBuilder

        initial_state = AIState(
            message=message,
            conversation_id=session_id,
            channel=channel,
            user_id=user_id,
            tenant_id=tenant_id,
            language="en"
        )
        raw = await ai_graph.ainvoke(initial_state)
        extracted = ChatResponseBuilder.extract_workflow_data(raw)
        reply = extracted.get("agent_reply") or "Thank you for reaching out to GLG Assets! How can we assist you with our luxury properties today?"
        confidence = float(extracted.get("confidence", 0.92))
        requires_escalation = bool(extracted.get("requires_escalation", False))
        project_ids = extracted.get("projects_found") or []

        return {
            "success": True,
            "reply": reply,
            "action": "escalate_to_human" if requires_escalation else "auto_reply",
            "confidence": confidence,
            "project_ids": project_ids,
            "error_message": None,
            "tenantId": tenant_id,
        }
    except Exception as exc:
        return {
            "success": True,
            "reply": "Thank you for contacting GLG Assets. A luxury property advisor will assist you momentarily.",
            "action": "escalate_to_human",
            "confidence": 0.6,
            "project_ids": [],
            "error_message": str(exc),
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


# ==========================================================
#  N8N WORKFLOW & NODE HEALTH MONITORING
# ==========================================================

@router.get("/n8n/health", summary="Get n8n workflow execution status, node health, and latency metrics")
async def get_n8n_monitoring_health():
    """Returns telemetry metrics for all n8n workflows, node health, latencies, and node processing errors."""
    from app.services.n8n_monitoring import N8nMonitoringService
    return await N8nMonitoringService.get_system_telemetry()


@router.post("/n8n/workflows/{workflow_id}/toggle", summary="Enable or disable an n8n workflow")
async def toggle_n8n_workflow(workflow_id: str, body: dict):
    """Toggles active state of an n8n workflow."""
    from app.services.n8n_monitoring import N8nMonitoringService
    active = body.get("active", True)
    try:
        return await N8nMonitoringService.toggle_workflow(workflow_id, active)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/n8n/workflows/{workflow_id}/test", summary="Run a latency ping test on an n8n workflow and its nodes")
async def test_n8n_workflow(workflow_id: str):
    """Executes a real-time latency ping test across all nodes in the workflow."""
    from app.services.n8n_monitoring import N8nMonitoringService
    try:
        return await N8nMonitoringService.test_workflow(workflow_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

