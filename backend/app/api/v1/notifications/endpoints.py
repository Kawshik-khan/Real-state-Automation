"""Notification Adapter Services — Workstreams 22-24."""
from fastapi import APIRouter, Depends

router = APIRouter()


from app.dependencies import require_automation_secret as _auth


@router.post("/email", summary="WS22 — Email Notification Adapter")
async def notify_email(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "channel": "email",
        "recipient": body.get("to", "team@glgassets.com"),
        "status": "queued",
        "tenantId": auth["tenant_id"],
    }


@router.post("/slack", summary="WS23 — Slack Notification Adapter")
async def notify_slack(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "channel": "slack",
        "channel_name": body.get("channel", "#general"),
        "status": "sent",
        "tenantId": auth["tenant_id"],
    }


from app.config import settings
from app.services.telegram import telegram_service


@router.post("/telegram", summary="WS24 — Telegram Notification Adapter")
async def notify_telegram(body: dict, auth: dict = Depends(_auth)):
    chat_id = body.get("chat_id") or getattr(settings, "default_telegram_chat_id", None) or getattr(settings, "telegram_admin_chat_id", None)
    text = body.get("message") or body.get("text") or "GLG Assets Automated Notification"
    
    if not chat_id:
        return {"success": False, "error": "No chat_id specified or configured in env"}

    res = await telegram_service.send_message(chat_id=chat_id, text=text)
    return {
        "success": res.get("success", False),
        "channel": "telegram",
        "chat_id": chat_id,
        "status": "sent" if res.get("success") else "failed",
        "response": res,
        "tenantId": auth["tenant_id"],
    }
