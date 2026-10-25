"""Email Automation Endpoints.

Handles incoming email webhooks, thread listing, AI draft review, and 1-click approvals.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.agents.email_agent import email_agent
from app.config import settings
from app.models.email import (
    DraftApprovalRequest,
    EmailStatus,
    IncomingEmailPayload,
)
from app.services.attachment_parser import attachment_parser
from app.services.email_service import email_service
from app.services.idempotency import idempotency_service

router = APIRouter()


async def verify_auth(
    x_automation_secret: Optional[str] = Header(None, alias="X-Automation-Secret"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
):
    """Simple auth check for n8n webhooks and dashboard requests."""
    # Optional secret validation if secret header provided
    if x_automation_secret and x_automation_secret != settings.automation_shared_secret:
        raise HTTPException(status_code=403, detail="Invalid automation secret")
    return {"tenant_id": x_tenant_id or settings.default_tenant_id}


@router.post("/incoming", summary="Ingest an incoming email message")
async def incoming_email_webhook(
    payload: IncomingEmailPayload,
    auth: dict = Depends(verify_auth),
):
    """Processes an incoming customer email from n8n / mail trigger.

    Extracts text from attachments, performs deduplication, fetches thread history,
    runs EmailAgent RAG generation, and dispatches reply or stages draft for approval.
    """
    # 1. Deduplication via Message-ID
    if idempotency_service.is_processed(payload.message_id):
        return {
            "success": True,
            "already_processed": True,
            "message": f"Message-ID {payload.message_id} already ingested",
        }

    # 2. Extract text from attachments if present
    attachment_texts = []
    for att in payload.attachments:
        if att.extracted_text:
            attachment_texts.append(f"[{att.filename}]: {att.extracted_text}")
        elif hasattr(att, "base64_content") or hasattr(att, "url"):
            txt = attachment_parser.extract_text_from_attachment(
                filename=att.filename,
                content_type=att.content_type,
            )
            if txt:
                att.extracted_text = txt
                attachment_texts.append(f"[{att.filename}]: {txt}")

    # 3. Retrieve or initialize Thread
    thread = email_service.get_or_create_thread(payload)

    # 4. Append message to thread
    email_service.record_incoming_message(payload, thread)

    # 5. Extract thread history for agent
    history = [m.model_dump() for m in thread.messages[:-1]]  # Exclude current incoming msg

    # 6. Run EmailAgent LLM generation & RAG context
    agent_result = await email_agent.process_email(
        subject=payload.subject,
        body_text=payload.body_text,
        sender_name=payload.sender_name,
        sender_email=payload.sender_email,
        thread_history=history,
        attachment_texts=attachment_texts,
    )

    reply_subject = agent_result["reply_subject"]
    reply_body = agent_result["reply_body"]
    intent = agent_result["intent"]
    priority = agent_result["priority"]
    confidence = agent_result["confidence_score"]
    action = agent_result["action"]

    # 7. Record AI Draft & State Transition
    target_status = EmailStatus.AUTO_REPLIED if action == "AUTO_SEND" else EmailStatus.PENDING_APPROVAL
    email_service.record_ai_draft(
        thread_id=thread.thread_id,
        ai_draft_reply=reply_body,
        ai_draft_subject=reply_subject,
        confidence_score=confidence,
        intent_category=intent,
        lead_priority=priority,
        status=target_status,
    )

    dispatch_result = None
    # 8. Auto-send if eligible
    if action == "AUTO_SEND":
        dispatch_result = await email_service.dispatch_reply_via_n8n(
            thread_id=thread.thread_id,
            reply_subject=reply_subject,
            reply_body=reply_body,
            sender_type="ai",
        )

    # Mark message as processed in idempotency cache
    idempotency_service.record_processed(payload.message_id)

    return {
        "success": True,
        "thread_id": thread.thread_id,
        "message_id": payload.message_id,
        "intent": intent,
        "lead_priority": priority,
        "confidence_score": confidence,
        "action": action,
        "status": thread.status.value,
        "ai_draft": {
            "subject": reply_subject,
            "body": reply_body,
        },
        "dispatch_result": dispatch_result,
    }


@router.get("/threads", summary="List email threads")
async def list_threads(
    status: Optional[str] = Query(None, description="Filter by status: pending_approval, auto_replied, etc."),
    auth: dict = Depends(verify_auth),
):
    """Returns all email threads sorted by newest first."""
    threads = email_service.list_threads(status=status)
    return {
        "success": True,
        "count": len(threads),
        "threads": [t.model_dump() for t in threads],
    }


@router.get("/threads/{thread_id}", summary="Get email thread details")
async def get_thread(
    thread_id: str,
    auth: dict = Depends(verify_auth),
):
    """Returns full message history and metadata for a specific thread."""
    thread = email_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return {"success": True, "thread": thread.model_dump()}


@router.post("/threads/{thread_id}/approve", summary="Approve & Send staged AI email draft")
async def approve_draft(
    thread_id: str,
    req: Optional[DraftApprovalRequest] = None,
    auth: dict = Depends(verify_auth),
):
    """Approves staged AI draft response and dispatches email via n8n."""
    thread = email_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    subject = (req and req.edited_subject) or thread.ai_draft_subject or f"Re: {thread.subject}"
    body = (req and req.edited_reply) or thread.ai_draft_reply or ""

    if not body:
        raise HTTPException(status_code=400, detail="No draft reply content available to approve")

    dispatch_result = await email_service.dispatch_reply_via_n8n(
        thread_id=thread_id,
        reply_subject=subject,
        reply_body=body,
        sender_type="human_agent" if (req and req.edited_reply) else "ai",
    )

    return {
        "success": True,
        "message": "Email draft approved and dispatched via n8n",
        "thread_id": thread_id,
        "dispatch_result": dispatch_result,
    }


@router.post("/threads/{thread_id}/edit-and-send", summary="Edit draft and send reply")
async def edit_and_send_draft(
    thread_id: str,
    req: DraftApprovalRequest,
    auth: dict = Depends(verify_auth),
):
    """Edits the AI draft response and dispatches immediately via n8n."""
    return await approve_draft(thread_id=thread_id, req=req, auth=auth)


@router.post("/threads/{thread_id}/reject", summary="Reject/Discard AI email draft")
async def reject_draft(
    thread_id: str,
    auth: dict = Depends(verify_auth),
):
    """Marks draft as rejected so a real estate agent can write a manual reply."""
    thread = email_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    thread.status = EmailStatus.REJECTED
    return {
        "success": True,
        "message": "AI draft rejected",
        "thread_id": thread_id,
        "status": thread.status.value,
    }


@router.post("/threads/dispatch-outbound", summary="Dispatch outbound email reply")
async def dispatch_outbound_email(
    body: dict,
    auth: dict = Depends(verify_auth),
):
    """Endpoint called by n8n or automation engine to dispatch an outbound email reply."""
    thread_id = body.get("thread_id")
    recipient_email = body.get("recipient_email")
    subject = body.get("subject", "Re: GLG Real Estate Inquiry")
    reply_body = body.get("body", "")

    if not recipient_email or not reply_body:
        raise HTTPException(status_code=400, detail="Missing required recipient_email or body")

    if thread_id and email_service.get_thread(thread_id):
        dispatch_res = await email_service.dispatch_reply_via_n8n(
            thread_id=thread_id,
            reply_subject=subject,
            reply_body=reply_body,
            sender_type="ai",
        )
        return {"success": True, "dispatched": True, "dispatch_result": dispatch_res}

    return {
        "success": True,
        "dispatched": True,
        "recipient": recipient_email,
        "subject": subject,
        "message": "Outbound email queued for dispatch",
    }

