"""Channel webhooks for the sales engine. Each one verifies its sender before anything is stored.

- Meta (WhatsApp Cloud API, Messenger, Instagram DMs): ``X-Hub-Signature-256`` HMAC of the raw body with the app
  secret. Without ``FACEBOOK_APP_SECRET`` configured the endpoint refuses every delivery.
- Telegram: ``X-Telegram-Bot-Api-Secret-Token`` must equal ``TELEGRAM_WEBHOOK_SECRET`` (set when registering).
- Website chat: called by the site's widget backend with the automation secret.
Repeated deliveries are dropped by message id.
"""

import hashlib
import hmac
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.config import settings
from app.dependencies import require_automation_secret
from app.sales.db import session_scope
from app.sales.inbound import InboundMessage, handle_inbound
from app.sales.messaging import message_to_dict
from app.sales.models import SalesConversation, SalesMessage

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_meta_signature(raw_body: bytes, signature_header: Optional[str]) -> None:
    secret = settings.facebook_app_secret
    if not secret:
        raise HTTPException(status_code=503, detail="FACEBOOK_APP_SECRET is not configured; webhook deliveries are refused")
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256")
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header.split("=", 1)[1]):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


def parse_meta_payload(body: dict) -> list[InboundMessage]:
    """Text messages from a Meta webhook body; everything else (statuses, echoes, reactions) is skipped."""
    tenant = settings.default_tenant_id
    out: list[InboundMessage] = []
    obj = body.get("object")
    for entry in body.get("entry", []) or []:
        if obj == "whatsapp_business_account":
            for change in entry.get("changes", []) or []:
                value = change.get("value", {}) or {}
                names = {c.get("wa_id"): (c.get("profile") or {}).get("name") for c in value.get("contacts", []) or []}
                for m in value.get("messages", []) or []:
                    text = (m.get("text") or {}).get("body") if m.get("type") == "text" else None
                    if m.get("type") == "button":
                        text = (m.get("button") or {}).get("text")
                    if m.get("type") == "interactive":
                        inter = m.get("interactive") or {}
                        text = (inter.get("button_reply") or inter.get("list_reply") or {}).get("title")
                    if not text or not m.get("from"):
                        continue
                    out.append(InboundMessage(
                        tenant_id=tenant, channel="whatsapp", external_id=m["from"], text=text,
                        channel_message_id=m.get("id"), name=names.get(m["from"]), phone=f"+{m['from']}",
                        source="whatsapp",
                    ))
        elif obj in ("page", "instagram"):
            channel = "messenger" if obj == "page" else "instagram"
            for event in entry.get("messaging", []) or []:
                message = event.get("message") or {}
                if message.get("is_echo") or not message.get("text"):
                    continue
                sender = (event.get("sender") or {}).get("id")
                if not sender:
                    continue
                out.append(InboundMessage(
                    tenant_id=tenant, channel=channel, external_id=sender, text=message["text"],
                    channel_message_id=message.get("mid"), source=channel,
                ))
    return out


@router.get("/meta", summary="Meta webhook verification (WhatsApp, Messenger, Instagram)")
async def verify_meta(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    expected = settings.whatsapp_verify_token
    if not expected:
        return Response(content="WHATSAPP_VERIFY_TOKEN is not configured", status_code=503)
    if hub_mode == "subscribe" and hmac.compare_digest(hub_verify_token or "", expected):
        return Response(content=str(hub_challenge or ""), media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


@router.post("/meta", summary="Meta webhook deliveries: customer messages into the sales engine")
async def receive_meta(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    raw = await request.body()
    verify_meta_signature(raw, x_hub_signature_256)
    try:
        body = json.loads(raw or b"{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Body is not JSON")
    results = [await handle_inbound(m) for m in parse_meta_payload(body)]
    # Meta retries anything that isn't a 200, so failures are logged, not returned as errors.
    return {"received": len(results), "results": results}


@router.post("/telegram", summary="Telegram bot webhook: private messages into the sales engine")
async def receive_telegram(request: Request, x_telegram_bot_api_secret_token: Optional[str] = Header(None)):
    expected = settings.telegram_webhook_secret
    if not expected:
        raise HTTPException(status_code=503, detail="TELEGRAM_WEBHOOK_SECRET is not configured; deliveries are refused")
    if not x_telegram_bot_api_secret_token or not hmac.compare_digest(x_telegram_bot_api_secret_token, expected):
        raise HTTPException(status_code=401, detail="Invalid Telegram secret token")
    update = await request.json()
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    if chat.get("type") != "private" or not message.get("text"):
        return {"received": 0}
    sender = message.get("from") or {}
    name = " ".join(p for p in (sender.get("first_name"), sender.get("last_name")) if p) or None
    result = await handle_inbound(InboundMessage(
        tenant_id=settings.default_tenant_id, channel="telegram", external_id=str(chat["id"]), text=message["text"],
        channel_message_id=str(message.get("message_id")), name=name, source="telegram",
    ))
    return {"received": 1, "result": result}


class WebsiteMessage(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=128, description="The widget's visitor session id")
    text: str = Field(..., min_length=1, max_length=4000)
    message_id: Optional[str] = Field(None, max_length=128)
    name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)


@router.post("/website", summary="Website chat widget: a visitor message")
async def receive_website(body: WebsiteMessage, auth: dict = Depends(require_automation_secret)):
    return await handle_inbound(InboundMessage(
        tenant_id=auth["tenant_id"], channel="website", external_id=body.session_id, text=body.text,
        channel_message_id=body.message_id, name=body.name, phone=body.phone, source="website",
    ))


@router.get("/website/{session_id}/messages", summary="Website chat widget: replies for a visitor")
async def website_messages(session_id: str, after: Optional[str] = None, auth: dict = Depends(require_automation_secret)):
    async with session_scope() as session:
        conv = (
            await session.execute(
                select(SalesConversation).where(
                    SalesConversation.tenant_id == auth["tenant_id"], SalesConversation.channel == "website",
                    SalesConversation.external_id == session_id,
                )
            )
        ).scalar_one_or_none()
        if conv is None:
            return {"messages": []}
        stmt = select(SalesMessage).where(
            SalesMessage.conversation_id == conv.conversation_id, SalesMessage.direction == "out",
            SalesMessage.status == "stored",
        )
        if after:
            anchor = await session.get(SalesMessage, after)
            if anchor is not None:
                stmt = stmt.where(SalesMessage.created_at > anchor.created_at)
        rows = (await session.execute(stmt.order_by(SalesMessage.created_at))).scalars().all()
        return {"messages": [message_to_dict(m) for m in rows]}
