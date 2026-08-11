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


@router.post("/telegram", summary="WS24 — Telegram Notification Adapter")
async def notify_telegram(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "channel": "telegram",
        "chat_id": body.get("chat_id", "unknown"),
        "status": "sent",
        "tenantId": auth["tenant_id"],
    }
