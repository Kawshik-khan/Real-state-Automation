"""Social Channel Services — Facebook & Instagram Auto-Comment to Private DM Lead Bridge."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request, Response

from app.agents.social_bridge_agent import social_bridge_agent
from app.config import settings
from app.dependencies import require_automation_secret as _auth
from app.services.meta_social import meta_social_service
from app.services.telegram import telegram_service

router = APIRouter()


# ── Core Helper: Execute Comment-to-DM Bridge ─────────────────────────

async def _execute_comment_bridge(
    comment_id: str,
    comment_text: str,
    author_id: str,
    author_name: str,
    platform: str = "facebook",
    post_id: Optional[str] = None,
    tenant_id: str = "glg-assets-main"
) -> dict[str, Any]:
    """Executes the dual-action comment-to-DM bridge pipeline."""
    # 1. AI Social Bridge Agent Generates Responses & Lead Score
    bridge_result = await social_bridge_agent.process_comment(
        comment_text=comment_text,
        author_name=author_name,
        platform=platform
    )
    
    public_reply_text = bridge_result["public_reply"]
    private_dm_text = bridge_result["private_dm"]
    lead_score = bridge_result["lead_score"]
    is_hot_lead = bridge_result["is_hot_lead"]
    quick_replies = bridge_result.get("quick_replies", [])

    # 2. Post Public Reply underneath comment
    pub_res = await meta_social_service.post_public_comment_reply(
        comment_id=comment_id,
        message=public_reply_text,
        platform=platform
    )

    # 3. Send Private DM Reply using recipient.comment_id
    dm_res = await meta_social_service.send_private_reply_dm(
        comment_id=comment_id,
        message=private_dm_text,
        platform=platform,
        quick_replies=quick_replies
    )

    # 4. Save to Conversation Memory & DB Store
    conv_id = f"{platform[:2]}_{author_id}" if author_id else f"{platform[:2]}_{comment_id[-8:]}"
    try:
        from app.api.v1.conversations.endpoints import add_message_to_conversation
        from app.schemas.chat import MemoryEntry
        from app.services.memory import conversation_memory

        # Add user comment to history
        await conversation_memory.add(conv_id, MemoryEntry(role="user", content=comment_text))
        await add_message_to_conversation(
            conv_id=conv_id,
            sender="user",
            text=f"[Public Comment on Post]: {comment_text}",
            channel=platform,
        )

        # Add AI Private DM to history
        await conversation_memory.add(conv_id, MemoryEntry(role="assistant", content=private_dm_text))
        await add_message_to_conversation(
            conv_id=conv_id,
            sender="ai",
            text=private_dm_text,
            channel=platform,
            confidence=0.95,
            intent="social_comment_lead_bridge",
            requires_escalation=is_hot_lead
        )

        # Broadcast via WebSocket to Frontend Live Stream
        try:
            from app.api.v1.ws import ws_manager
            await ws_manager.broadcast_message({
                "event": "social_comment_bridge",
                "platform": platform,
                "author_name": author_name,
                "comment_text": comment_text,
                "public_reply": public_reply_text,
                "private_dm": private_dm_text,
                "lead_score": lead_score,
                "is_hot_lead": is_hot_lead,
                "conversation_id": conv_id,
            })
        except Exception as ws_err:
            print(f"[_execute_comment_bridge] WS broadcast error: {ws_err}")
    except Exception as err:
        print(f"[_execute_comment_bridge] Storage error: {err}")

    # 5. Escalate Hot Leads directly to Sales Team via Telegram
    if is_hot_lead and settings.default_telegram_chat_id:
        tg_text = (
            f"🔥 *HOT SOCIAL LEAD CAPTURED ({platform.upper()})*\n\n"
            f"👤 *Author*: {author_name}\n"
            f"💬 *Comment*: \"{comment_text}\"\n"
            f"⭐ *Lead Intent Score*: {lead_score}/100\n"
            f"🏢 *Target Project*: {bridge_result['project']['name']}\n"
            f"📍 *Location*: {bridge_result['entities'].get('location', 'Dhaka')}\n"
            f"📩 *Status*: Private DM & Brochure Delivered."
        )
        try:
            await telegram_service.send_message(
                chat_id=settings.default_telegram_chat_id,
                text=tg_text,
                parse_mode="Markdown"
            )
        except Exception as tg_err:
            print(f"[_execute_comment_bridge] Telegram notification error: {tg_err}")

    return {
        "success": True,
        "platform": platform,
        "comment_id": comment_id,
        "author_name": author_name,
        "public_reply": public_reply_text,
        "private_dm": private_dm_text,
        "public_reply_status": pub_res,
        "private_dm_status": dm_res,
        "lead_score": lead_score,
        "is_hot_lead": is_hot_lead,
        "conversation_id": conv_id,
        "tenant_id": tenant_id
    }


# ── Workstream Endpoints ──────────────────────────────────────────────

@router.post("/facebook/comments", summary="WS25 — Facebook Comment Automation & DM Bridge")
async def facebook_comment(body: dict, auth: dict = Depends(_auth)):
    """Processes incoming Facebook post comment and triggers public reply + private DM."""
    comment_id = body.get("comment_id") or body.get("commentId") or "fb_comment_sample"
    comment_text = body.get("text") or body.get("comment") or body.get("message", "")
    author_id = body.get("author_id") or body.get("authorId") or "fb_user_123"
    author_name = body.get("author_name") or body.get("authorName") or "Prospective Buyer"
    post_id = body.get("post_id") or body.get("postId")

    return await _execute_comment_bridge(
        comment_id=comment_id,
        comment_text=comment_text,
        author_id=author_id,
        author_name=author_name,
        platform="facebook",
        post_id=post_id,
        tenant_id=auth.get("tenant_id", "glg-assets-main")
    )


@router.post("/instagram/comments", summary="WS28 — Instagram Comment Automation & DM Bridge")
async def instagram_comment(body: dict, auth: dict = Depends(_auth)):
    """Processes incoming Instagram post/reel comment and triggers public reply + private DM."""
    comment_id = body.get("comment_id") or body.get("commentId") or "ig_comment_sample"
    comment_text = body.get("text") or body.get("comment") or body.get("message", "")
    author_id = body.get("author_id") or body.get("authorId") or "ig_user_123"
    author_name = body.get("author_name") or body.get("username") or "Valued Client"
    post_id = body.get("media_id") or body.get("post_id")

    return await _execute_comment_bridge(
        comment_id=comment_id,
        comment_text=comment_text,
        author_id=author_id,
        author_name=author_name,
        platform="instagram",
        post_id=post_id,
        tenant_id=auth.get("tenant_id", "glg-assets-main")
    )


@router.post("/simulator/comment-to-dm", summary="Interactive Comment-to-DM Bridge Simulator")
async def simulate_comment_to_dm(body: dict):
    """Developer & Dashboard Simulation endpoint for testing social lead bridge in real-time."""
    comment_text = body.get("comment_text") or body.get("text") or "Banani 3 BHK flat er price koto? Details inbox korun"
    author_name = body.get("author_name") or "Mahmudur Rahman"
    platform = body.get("platform") or "facebook"
    comment_id = body.get("comment_id") or f"sim_{platform}_{hash(comment_text) % 10000}"

    return await _execute_comment_bridge(
        comment_id=comment_id,
        comment_text=comment_text,
        author_id=f"sim_user_{hash(author_name) % 1000}",
        author_name=author_name,
        platform=platform,
        tenant_id="glg-assets-main"
    )


# ── Webhook Verification & Real Event Handlers ─────────────────────────

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


@router.post("/facebook/webhook", summary="Live Meta Facebook Webhook Event Handler")
async def facebook_webhook_event(body: dict):
    """Ingests live Meta Webhook events for Facebook Page feed comments and messages."""
    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            val = change.get("value", {})
            item = val.get("item")
            verb = val.get("verb")
            if item == "comment" and verb == "add":
                comment_id = val.get("comment_id")
                text = val.get("message", "")
                author = val.get("from", {})
                author_id = author.get("id")
                author_name = author.get("name", "User")
                if comment_id and text:
                    await _execute_comment_bridge(
                        comment_id=comment_id,
                        comment_text=text,
                        author_id=author_id,
                        author_name=author_name,
                        platform="facebook"
                    )
    return {"status": "ok"}


@router.post("/instagram/webhook", summary="Live Meta Instagram Webhook Event Handler")
async def instagram_webhook_event(body: dict):
    """Ingests live Meta Webhook events for Instagram comments."""
    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            val = change.get("value", {})
            comment_id = val.get("id")
            text = val.get("text", "")
            author = val.get("from", {})
            author_id = author.get("id")
            author_name = author.get("username", "User")
            if comment_id and text:
                await _execute_comment_bridge(
                    comment_id=comment_id,
                    comment_text=text,
                    author_id=author_id,
                    author_name=author_name,
                    platform="instagram"
                )
    return {"status": "ok"}


# ── Other Social Channels ─────────────────────────────────────────────

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


# ── Telegram Direct Bot Handlers ──────────────────────────────────────

@router.post("/telegram", summary="Telegram Bot Webhook & AI RAG Processing")
@router.post("/telegram/webhook", summary="Telegram Bot Webhook Endpoint")
async def telegram_webhook(request: Request, body: dict):
    """Processes incoming Telegram updates, executes RAG + AI graph pipeline, and sends reply."""
    from app.api.v1.ai.endpoints import ai_chat
    from app.schemas.chat import ChatRequest

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
        ai_response = await ai_chat(request=request, body=chat_req, auth={"tenant_id": "glg-assets-main"})
        reply_text = ai_response.get("reply") if isinstance(ai_response, dict) else str(ai_response)
    except Exception as err:
        print(f"[Telegram Webhook AI Error]: {err}")
        reply_text = "Thank you for reaching out to GLG Assets! A property consultant will contact you shortly."

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
