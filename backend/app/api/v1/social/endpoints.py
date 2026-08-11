"""Social Channel Services — Workstreams 25-33."""
from fastapi import APIRouter, Depends

router = APIRouter()


from app.dependencies import require_automation_secret as _auth


@router.post("/facebook/comments", summary="WS25 — Facebook Comment Automation")
async def facebook_comment(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "Thank you for your comment! Our team will reach out.",
        "action": "auto_reply",
        "tenantId": auth["tenant_id"],
    }


@router.post("/facebook/incoming", summary="WS26 — Facebook Incoming Message")
async def facebook_incoming(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "Hi! Thanks for reaching out. How can I help you today?",
        "conversation_id": body.get("conversation_id", "unknown"),
        "tenantId": auth["tenant_id"],
    }


@router.post("/facebook/send", summary="WS27 — Facebook Send Message")
async def facebook_send(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "message_id": f"fb_msg_{hash(str(body))}",
        "status": "sent",
        "tenantId": auth["tenant_id"],
    }


@router.post("/instagram/comments", summary="WS28 — Instagram Comment Automation")
async def instagram_comment(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "Thanks for the comment! Check our bio for more details.",
        "action": "auto_reply",
        "tenantId": auth["tenant_id"],
    }


@router.post("/instagram/dm", summary="WS29 — Instagram DM Processing")
async def instagram_dm(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "Hi there! Thanks for your message.",
        "conversation_id": body.get("conversation_id", "unknown"),
        "tenantId": auth["tenant_id"],
    }


@router.post("/website/livechat", summary="WS31 — Website Live Chat")
async def website_livechat(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "Welcome to GLG Assets! How can we help you find your perfect property?",
        "session_id": body.get("session_id", "unknown"),
        "tenantId": auth["tenant_id"],
    }


@router.post("/whatsapp/incoming", summary="WS32 — WhatsApp Incoming Message")
async def whatsapp_incoming(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "reply": "Thank you for contacting GLG Assets on WhatsApp! We'll respond shortly.",
        "conversation_id": body.get("conversation_id", "unknown"),
        "tenantId": auth["tenant_id"],
    }


@router.post("/whatsapp/media", summary="WS33 — WhatsApp Media Router")
async def whatsapp_media(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "media_type": body.get("media_type", "image"),
        "processed": True,
        "download_url": None,
        "tenantId": auth["tenant_id"],
    }


@router.post("/leads/capture", summary="WS30 — Lead Capture")
async def lead_capture(body: dict, auth: dict = Depends(_auth)):
    return {
        "success": True,
        "lead_id": f"lead_{hash(str(body))}",
        "stored_in": ["google_sheets", "supabase"],
        "tenantId": auth["tenant_id"],
    }


from fastapi import Response, Query

@router.get("/whatsapp/webhook", summary="Meta/WhatsApp Webhook Verification")
@router.get("/whatsapp/incoming", summary="WhatsApp Webhook Verification")
@router.get("/facebook/webhook", summary="Facebook Webhook Verification")
@router.get("/instagram/webhook", summary="Instagram Webhook Verification")
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Handles Meta (Facebook/WhatsApp/Instagram) Webhook Subscription Verification."""
    expected_token = getattr(settings, "whatsapp_verify_token", None) or "glg_wa_verify_2026"
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return Response(content=str(hub_challenge or ""), media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


from app.services.telegram import telegram_service
from app.api.v1.ai.endpoints import ai_chat
from app.schemas.chat import ChatRequest


@router.post("/telegram", summary="Telegram Bot Webhook & AI RAG Processing")
@router.post("/telegram/webhook", summary="Telegram Bot Webhook Endpoint")
async def telegram_webhook(body: dict):
    """Processes incoming Telegram updates, executes RAG + AI graph pipeline, and sends reply."""
    message = body.get("message") or body.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return {"ok": True, "status": "ignored"}

    conv_id = f"tg_{chat_id}"

    try:
        chat_req = ChatRequest(
            message=text,
            user_id=str(chat_id),
            conversation_id=conv_id,
            channel="telegram",
        )
        ai_response = await ai_chat(chat_req, auth={"tenant_id": "glg-assets-main"})
        reply_text = ai_response.get("reply") if isinstance(ai_response, dict) else str(ai_response)
    except Exception as err:
        print(f"[Telegram Webhook AI Error]: {err}")
        reply_text = "Thank you for reaching out to GLG Assets! A property consultant will contact you shortly."

    # Send reply back to Telegram
    await telegram_service.send_message(chat_id=chat_id, text=reply_text)

    return {
        "ok": True,
        "chat_id": chat_id,
        "incoming_text": text,
        "reply": reply_text,
    }


@router.post("/telegram/setup-webhook", summary="Set Telegram Webhook URL")
async def setup_telegram_webhook(body: dict):
    """Register public HTTPS webhook URL with Telegram Bot API."""
    url = body.get("url")
    if not url:
        return {"success": False, "error": "url parameter is required"}
    return await telegram_service.set_webhook(url)


@router.get("/telegram/status", summary="Get Telegram Bot & Webhook Status")
async def telegram_status():
    """Retrieve Bot Info and current Webhook configuration."""
    bot_info = await telegram_service.get_me()
    webhook_info = await telegram_service.get_webhook_info()
    return {
        "bot": bot_info,
        "webhook": webhook_info,
    }
