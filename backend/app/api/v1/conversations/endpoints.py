"""Conversations API & SSE Event Stream Endpoints."""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.services.event_broadcaster import broadcaster
from app.services.telegram import telegram_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Runtime conversation cache (hydrated from database on first API call)
IN_MEMORY_CONVERSATIONS = []


def get_or_create_conversation(conv_id: str, channel: str = "website", name: str = None, phone: str = None):
    """Retrieve existing or create new conversation in memory."""
    for conv in IN_MEMORY_CONVERSATIONS:
        if conv["id"] == conv_id:
            if name and conv.get("name") in [None, "Prospective Buyer", f"Lead {conv_id[-6:] if len(conv_id)>=6 else conv_id}"]:
                conv["name"] = name
            if phone and conv.get("phone") in [None, "+880 1700-000000"]:
                conv["phone"] = phone
            return conv
    
    new_conv = {
        "id": conv_id,
        "name": name or f"Lead {conv_id[-6:] if len(conv_id)>=6 else conv_id}",
        "phone": phone or "+880 1700-000000",
        "channel": channel or "website",
        "lastMessage": "New conversation initialized",
        "time": "Just now",
        "status": "active",
        "aiPaused": False,
        "confidence": 0.90,
        "intent": "general_inquiry",
        "beliefs": {},
        "messages": []
    }
    IN_MEMORY_CONVERSATIONS.insert(0, new_conv)
    return new_conv


async def async_get_or_create_conversation(conv_id: str, channel: str = "website", name: str = None, phone: str = None):
    """Retrieve existing conversation from memory cache or database, or create a new one."""
    for conv in IN_MEMORY_CONVERSATIONS:
        if conv["id"] == conv_id:
            if name and conv.get("name") in [None, "Prospective Buyer", f"Lead {conv_id[-6:] if len(conv_id)>=6 else conv_id}"]:
                conv["name"] = name
            if phone and conv.get("phone") in [None, "+880 1700-000000"]:
                conv["phone"] = phone
            return conv

    # Hydrate from database if present
    try:
        from sqlalchemy import select
        from app.database import async_session_factory
        from app.models.models import ConversationRecord, UserRecord

        async with async_session_factory() as session:
            stmt = (
                select(ConversationRecord, UserRecord)
                .join(UserRecord, ConversationRecord.user_id == UserRecord.user_id, isouter=True)
                .where(ConversationRecord.conversation_id == conv_id)
            )
            res = await session.execute(stmt)
            row = res.first()
            if row:
                db_c, db_u = row
                beliefs = db_c.beliefs if isinstance(db_c.beliefs, dict) else {}
                conv = {
                    "id": db_c.conversation_id,
                    "name": (db_u.name if db_u and db_u.name else None) or name or f"Lead {conv_id[-6:] if len(conv_id)>=6 else conv_id}",
                    "phone": (db_u.phone if db_u and db_u.phone else None) or phone or "+880 1700-000000",
                    "channel": db_c.channel or channel or "website",
                    "lastMessage": "Conversation resumed",
                    "time": db_c.last_message_at.strftime("%I:%M %p") if db_c.last_message_at else "Just now",
                    "status": db_c.status or "active",
                    "aiPaused": db_c.ai_paused or False,
                    "confidence": beliefs.get("confidence", 0.90),
                    "intent": beliefs.get("intent", "property_inquiry"),
                    "beliefs": beliefs,
                    "createdAt": db_c.created_at.isoformat() if db_c.created_at else None,
                    "messages": []
                }
                IN_MEMORY_CONVERSATIONS.insert(0, conv)
                return conv
    except Exception as e:
        logger.error(f"Error fetching conversation {conv_id} from DB: {e}")

    # Fallback to in-memory creation
    return get_or_create_conversation(conv_id, channel, name, phone)


async def _persist_message_to_db(
    conv_id: str,
    sender: str | None = None,
    text: str | None = None,
    channel: str = "website",
    name: str | None = None,
    phone: str | None = None,
    status: str | None = None,
    ai_paused: bool | None = None,
    beliefs: dict | None = None,
):
    """Persists conversation and message into Supabase/PostgreSQL. Returns the created MessageRecord or None."""
    msg_record = None
    try:
        from sqlalchemy import select

        from app.database import async_session_factory
        from app.models.models import ConversationRecord, MessageRecord, UserRecord, utc_now
        async with async_session_factory() as session:
            user_id = f"usr_{conv_id}"
            user_stmt = select(UserRecord).where(UserRecord.user_id == user_id)
            u_res = await session.execute(user_stmt)
            db_user = u_res.scalar_one_or_none()
            if not db_user:
                db_user = UserRecord(user_id=user_id, name=name, phone=phone, channel=channel)
                session.add(db_user)
                await session.flush()
            else:
                if name and (not db_user.name or db_user.name == "Prospective Buyer"):
                    db_user.name = name
                if phone and (not db_user.phone or db_user.phone == "+880 1700-000000"):
                    db_user.phone = phone

            conv_stmt = select(ConversationRecord).where(ConversationRecord.conversation_id == conv_id)
            conv_res = await session.execute(conv_stmt)
            db_conv = conv_res.scalar_one_or_none()
            now = utc_now()
            if not db_conv:
                db_conv = ConversationRecord(
                    conversation_id=conv_id,
                    user_id=user_id,
                    channel=channel,
                    status=status or "active",
                    ai_paused=ai_paused if ai_paused is not None else False,
                    beliefs=beliefs or {},
                    last_message_at=now,
                    created_at=now
                )
                session.add(db_conv)
                await session.flush()
            else:
                db_conv.last_message_at = now
                if status is not None:
                    db_conv.status = status
                if ai_paused is not None:
                    db_conv.ai_paused = ai_paused
                if beliefs is not None:
                    merged = dict(db_conv.beliefs) if isinstance(db_conv.beliefs, dict) else {}
                    merged.update(beliefs)
                    db_conv.beliefs = merged

            if text and sender:
                msg_record = MessageRecord(conversation_id=conv_id, sender=sender, text=text, created_at=now)
                session.add(msg_record)
            await session.commit()
    except Exception as e:
        logger.error(f"Error persisting message to db: {e}")
    return msg_record


async def add_message_to_conversation(
    conv_id: str, 
    sender: str, 
    text: str, 
    channel: str = "website",
    confidence: float = None,
    intent: str = None,
    requires_escalation: bool = False
):
    """Append message to conversation state, persist to database, and broadcast via SSE."""
    conv = await async_get_or_create_conversation(conv_id, channel)
    
    # Deduplication Guard: Do not append if the exact same message was just added
    if conv["messages"]:
        last_msg = conv["messages"][-1]
        if last_msg.get("sender") == sender and last_msg.get("text", "").strip() == text.strip():
            return conv, last_msg

    now = datetime.now()
    now_time = now.strftime("%I:%M %p")
    
    if confidence is not None:
        conv["confidence"] = confidence
    if intent:
        conv["intent"] = intent
    if requires_escalation:
        conv["status"] = "escalated"
        conv["aiPaused"] = True

    beliefs_update = {}
    if confidence is not None:
        beliefs_update["confidence"] = confidence
    if intent:
        beliefs_update["intent"] = intent

    # 1. DB-first persistence: Write to database first and await commit
    persisted_record = await _persist_message_to_db(
        conv_id=conv_id,
        sender=sender,
        text=text,
        channel=conv.get("channel", channel),
        name=conv.get("name"),
        phone=conv.get("phone"),
        status=conv.get("status"),
        ai_paused=conv.get("aiPaused"),
        beliefs=beliefs_update or None,
    )

    msg_id = getattr(persisted_record, "message_id", None)
    if persisted_record and hasattr(persisted_record, "created_at") and persisted_record.created_at:
        now_time = persisted_record.created_at.strftime("%I:%M %p")

    msg_obj = {
        "id": msg_id,
        "sender": sender,
        "text": text,
        "time": now_time,
        "createdAt": persisted_record.created_at.isoformat() if persisted_record and hasattr(persisted_record, "created_at") and persisted_record.created_at else now.isoformat()
    }
    conv["messages"].append(msg_obj)
    conv["lastMessage"] = text
    conv["time"] = now_time

    # 2. Broadcast via SSE
    event_type = "new_lead" if (sender == "user" and len(conv["messages"]) == 1) else "message_received"
    await broadcaster.broadcast(event_type, {
        "conversation_id": conv_id,
        "message": msg_obj,
        "channel": conv["channel"],
        "name": conv["name"],
        "requires_escalation": requires_escalation
    })
    
    if requires_escalation:
        await broadcaster.broadcast("escalation_required", {
            "conversation_id": conv_id,
            "channel": conv["channel"],
            "reason": "AI confidence low or escalation requested"
        })

    # Trigger background sync to n8n Google Sheets webhook
    asyncio.create_task(_sync_lead_to_n8n_sheets(conv))
        
    return conv, msg_obj


async def _sync_lead_to_n8n_sheets(conv: dict):
    """Asynchronously post lead/message update to n8n Google Sheets Sync webhook."""
    try:
        n8n_base = (
            getattr(settings, "n8n_webhook_base_url", None)
            or os.getenv("N8N_WEBHOOK_BASE_URL")
            or getattr(settings, "n8n_api_url", "https://glg-ai.app.n8n.cloud/api/v1").replace("/api/v1", "")
        ).rstrip("/")
        url = f"{n8n_base}/webhook/google-sheets-leads"
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(url, json={
                "conversation_id": conv["id"],
                "name": conv["name"],
                "phone": conv["phone"],
                "channel": conv["channel"],
                "lastMessage": conv["lastMessage"],
                "intent": conv.get("intent", "property_inquiry"),
                "confidence": conv.get("confidence", 0.90),
                "status": conv.get("status", "active")
            })
    except Exception:
        pass  # Non-blocking background sync


@router.get("", summary="List active conversations")
@router.get("/", summary="List active conversations")
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    channel: str = "all",
    status: str = "all"
):
    """Returns active customer conversations from database or cache."""
    try:
        from sqlalchemy import and_, desc, select

        from app.database import async_session_factory
        from app.models.models import ConversationRecord, MessageRecord, UserRecord

        async with async_session_factory() as session:
            stmt = select(ConversationRecord, UserRecord).join(
                UserRecord, ConversationRecord.user_id == UserRecord.user_id, isouter=True
            )
            filters = []
            if channel != "all":
                filters.append(ConversationRecord.channel == channel)
            if status != "all":
                filters.append(ConversationRecord.status == status)

            if filters:
                stmt = stmt.where(and_(*filters))

            stmt = stmt.order_by(desc(ConversationRecord.last_message_at)).offset(offset).limit(limit)
            res = await session.execute(stmt)
            rows = res.all()

            formatted = []
            for conv, usr in rows:
                msg_stmt = (
                    select(MessageRecord)
                    .where(MessageRecord.conversation_id == conv.conversation_id)
                    .order_by(desc(MessageRecord.created_at))
                    .limit(1)
                )
                msg_res = await session.execute(msg_stmt)
                last_msg = msg_res.scalar_one_or_none()

                last_msg_time = conv.last_message_at or (last_msg.created_at if last_msg else None)
                time_display = last_msg_time.strftime("%I:%M %p") if last_msg_time else "Just now"

                beliefs = conv.beliefs if isinstance(conv.beliefs, dict) else {}
                formatted.append({
                    "id": conv.conversation_id,
                    "name": usr.name if usr and usr.name else "Prospective Buyer",
                    "phone": usr.phone if usr and usr.phone else "+880 1700-000000",
                    "channel": conv.channel,
                    "status": conv.status,
                    "aiPaused": conv.ai_paused,
                    "lastMessage": last_msg.text if last_msg and hasattr(last_msg, 'text') else "Inquiry initiated",
                    "time": time_display,
                    "unread": 0,
                    "avatar": (usr.name[0].upper() if (usr and usr.name) else "C"),
                    "beliefs": beliefs,
                    "createdAt": conv.created_at.isoformat() if conv.created_at else None,
                    "confidence": beliefs.get("confidence", 0.90),
                    "intent": beliefs.get("intent", "property_inquiry"),
                    "messages": []
                })

            # Hydrate in-memory cache with DB data
            for f_conv in formatted:
                existing = next((c for c in IN_MEMORY_CONVERSATIONS if c["id"] == f_conv["id"]), None)
                if not existing:
                    IN_MEMORY_CONVERSATIONS.append(dict(f_conv))
                else:
                    existing["name"] = f_conv["name"]
                    existing["phone"] = f_conv["phone"]
                    existing["channel"] = f_conv["channel"]
                    existing["aiPaused"] = f_conv["aiPaused"]
                    existing["status"] = f_conv["status"]
                    existing["lastMessage"] = f_conv["lastMessage"]
                    existing["time"] = f_conv["time"]
                    existing["confidence"] = f_conv["confidence"]
                    existing["intent"] = f_conv["intent"]

            # If there are any in-memory conversations created recently not yet fetched in rows
            formatted_ids = {f["id"] for f in formatted}
            for mem_conv in IN_MEMORY_CONVERSATIONS:
                if mem_conv["id"] not in formatted_ids:
                    formatted.insert(0, mem_conv)

            return {"success": True, "conversations": formatted, "count": len(formatted)}
    except Exception as e:
        logger.error(f"Error listing conversations from DB: {e}")
        return {"success": True, "conversations": IN_MEMORY_CONVERSATIONS, "count": len(IN_MEMORY_CONVERSATIONS)}



@router.post("", summary="Create a new conversation / lead")
@router.post("/", summary="Create a new conversation / lead")
async def create_conversation(body: dict):
    """Create a new conversation lead manually or via simulation."""
    conv_id = body.get("id") or f"lead_{int(asyncio.get_event_loop().time() * 1000)}"
    name = body.get("name", "New Visitor")
    phone = body.get("phone", "+880 1700-000000")
    channel = body.get("channel", "website")
    initial_message = body.get("message", "Hello, I am interested in GLG properties.")

    conv = await async_get_or_create_conversation(conv_id, channel, name, phone)
    
    # Persist lead immediately to database
    await _persist_message_to_db(
        conv_id=conv_id,
        channel=channel,
        name=name,
        phone=phone,
        status="active",
        ai_paused=False
    )

    if initial_message:
        conv, _ = await add_message_to_conversation(conv_id, "user", initial_message, channel)
        
    return {"success": True, "conversation": conv}


@router.delete("/{conv_id}", summary="Delete or clear a conversation")
async def delete_conversation(conv_id: str):
    """Delete a conversation from memory and database."""
    global IN_MEMORY_CONVERSATIONS
    IN_MEMORY_CONVERSATIONS = [c for c in IN_MEMORY_CONVERSATIONS if c["id"] != conv_id]

    try:
        from sqlalchemy import delete
        from app.database import async_session_factory
        from app.models.models import ConversationRecord, MessageRecord
        async with async_session_factory() as session:
            await session.execute(delete(MessageRecord).where(MessageRecord.conversation_id == conv_id))
            await session.execute(delete(ConversationRecord).where(ConversationRecord.conversation_id == conv_id))
            await session.commit()
    except Exception as e:
        logger.error(f"Error deleting conversation {conv_id} from DB: {e}")

    await broadcaster.broadcast("conversation_deleted", {"conversation_id": conv_id})
    return {"success": True, "conversation_id": conv_id}


@router.get("/stream", summary="SSE Real-time Conversation Event Stream")
async def event_stream(request: Request):
    """Server-Sent Events (SSE) endpoint pushing live lead & chat events to dashboard clients."""
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            # Send initial ping event
            yield f"data: {json.dumps({'event': 'connected', 'message': 'SSE live stream established'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment
                    yield ": heartbeat\n\n"
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/{conv_id}/messages", summary="Get full message history for conversation")
async def get_conversation_messages(conv_id: str, limit: int = 60):
    """Fetch chronological message history for a specific conversation from DB or memory cache."""
    messages = []
    try:
        from sqlalchemy import desc, select

        from app.database import async_session_factory
        from app.models.models import MessageRecord

        async with async_session_factory() as session:
            stmt = (
                select(MessageRecord)
                .where(MessageRecord.conversation_id == conv_id)
                .order_by(desc(MessageRecord.created_at))
                .limit(limit)
            )
            res = await session.execute(stmt)
            records = res.scalars().all()
            if records:
                for r in reversed(records):
                    messages.append({
                        "id": r.message_id,
                        "sender": r.sender,
                        "text": r.text,
                        "time": r.created_at.strftime("%I:%M %p") if r.created_at else "Just now",
                        "createdAt": r.created_at.isoformat() if r.created_at else None
                    })
                return {"success": True, "conversation_id": conv_id, "messages": messages, "count": len(messages)}
    except Exception as e:
        logger.error(f"Error fetching messages for conversation {conv_id}: {e}")

    # Fallback to in-memory conversation messages
    conv = next((c for c in IN_MEMORY_CONVERSATIONS if c["id"] == conv_id), None)
    if conv and conv.get("messages"):
        messages = conv["messages"][-limit:]
        return {"success": True, "conversation_id": conv_id, "messages": messages, "count": len(messages)}

    return {"success": True, "conversation_id": conv_id, "messages": [], "count": 0}


@router.post("/{conv_id}/message", summary="Process customer message (triggers AI pipeline if active)")
async def send_customer_message(conv_id: str, body: dict):
    """Process incoming customer message. If AI is active, run through LangGraph pipeline."""
    text = body.get("text") or body.get("message", "")
    channel = body.get("channel", "website")
    if not text:
        raise HTTPException(status_code=400, detail="Text or message required")

    conv = await async_get_or_create_conversation(conv_id, channel)
    
    # 1. Add user message
    conv, user_msg = await add_message_to_conversation(conv_id, "user", text, channel)
    
    ai_reply_msg = None
    # 2. If AI is active (not paused), trigger LangGraph AI pipeline
    if not conv.get("aiPaused", False):
        try:
            from app.agents.graph import ai_graph
            from app.agents.state import AIState
            from app.utils.chat_response_builder import ChatResponseBuilder

            initial_state = AIState(
                message=text,
                conversation_id=conv_id,
                channel=channel,
                language="en",
            )
            raw = await ai_graph.ainvoke(initial_state)
            extracted = ChatResponseBuilder.extract_workflow_data(raw)
            reply_text = extracted.get("agent_reply") or "Thank you for reaching out! How else can GLG Assets assist you?"
            confidence = extracted.get("confidence", 0.90)
            intent = str(extracted.get("agent_used", extracted.get("intent", "property_inquiry")))
            requires_esc = bool(extracted.get("requires_escalation", False))

            # Add AI message to conversation
            conv, ai_reply_msg = await add_message_to_conversation(
                conv_id=conv_id,
                sender="ai",
                text=reply_text,
                channel=channel,
                confidence=confidence,
                intent=intent,
                requires_escalation=requires_esc
            )
        except Exception:
            # Fallback if graph fails or API key missing
            fallback_text = "Thank you for your message! Our GLG Assets team has received your inquiry."
            conv, ai_reply_msg = await add_message_to_conversation(
                conv_id=conv_id,
                sender="ai",
                text=fallback_text,
                channel=channel
            )

    return {
        "success": True,
        "conversation_id": conv_id,
        "user_message": user_msg,
        "ai_reply": ai_reply_msg,
        "conversation": conv
    }


@router.post("/{conv_id}/takeover", summary="Toggle AI vs Human Agent takeover")
async def toggle_takeover(conv_id: str):
    """Toggle human takeover state for a conversation and broadcast state update."""
    conv = await async_get_or_create_conversation(conv_id)

    conv["aiPaused"] = not conv.get("aiPaused", False)
    conv["status"] = "human_takeover" if conv["aiPaused"] else "active"

    # Persist to database
    try:
        from sqlalchemy import update
        from app.database import async_session_factory
        from app.models.models import ConversationRecord

        async with async_session_factory() as session:
            stmt = update(ConversationRecord).where(
                ConversationRecord.conversation_id == conv_id
            ).values(ai_paused=conv["aiPaused"], status=conv["status"])
            await session.execute(stmt)
            await session.commit()
    except Exception as e:
        logger.error(f"Error persisting takeover update to DB: {e}")

    # Broadcast state change
    await broadcaster.broadcast("agent_takeover", {
        "conversation_id": conv_id,
        "aiPaused": conv["aiPaused"],
        "status": conv["status"],
        "name": conv.get("name", "Prospective Buyer"),
        "channel": conv.get("channel", "website")
    })

    return {
        "success": True,
        "conversation_id": conv_id,
        "aiPaused": conv["aiPaused"],
        "status": conv["status"]
    }


@router.post("/{conv_id}/reply", summary="Post manual human agent reply")
async def send_agent_reply(conv_id: str, body: dict):
    """Post manual agent reply, broadcast message_received event, and dispatch to real social channel."""
    reply_text = body.get("text", "")
    if not reply_text:
        raise HTTPException(status_code=400, detail="Text required")

    conv = await async_get_or_create_conversation(conv_id)

    now = datetime.now()
    now_time = now.strftime("%I:%M %p")
    channel = conv.get("channel", "website")

    # Persist agent reply to DB first
    persisted_record = await _persist_message_to_db(
        conv_id=conv_id,
        sender="human_agent",
        text=reply_text,
        channel=channel,
        name=conv.get("name"),
        phone=conv.get("phone")
    )

    msg_id = getattr(persisted_record, "message_id", None)
    if persisted_record and hasattr(persisted_record, "created_at") and persisted_record.created_at:
        now_time = persisted_record.created_at.strftime("%I:%M %p")

    msg_obj = {
        "id": msg_id,
        "sender": "human_agent",
        "text": reply_text,
        "time": now_time,
        "createdAt": persisted_record.created_at.isoformat() if persisted_record and hasattr(persisted_record, "created_at") and persisted_record.created_at else now.isoformat()
    }
    conv["messages"].append(msg_obj)
    conv["lastMessage"] = reply_text
    conv["time"] = now_time

    delivery_status = "internal_dashboard"

    # Dispatch reply to real Telegram user if channel is Telegram
    if channel == "telegram" or conv_id.startswith("tg_"):
        chat_id = conv_id.replace("tg_", "").strip()
        if chat_id:
            tg_res = await telegram_service.send_message(chat_id=chat_id, text=reply_text)
            delivery_status = "sent_to_telegram" if tg_res.get("success") else f"telegram_error: {tg_res.get('error')}"

    # Broadcast message event to dashboard SSE stream
    await broadcaster.broadcast("message_received", {
        "conversation_id": conv_id,
        "message": msg_obj,
        "channel": channel,
        "name": conv["name"],
        "delivery_status": delivery_status,
    })

    return {
        "success": True,
        "conversation_id": conv_id,
        "channel": channel,
        "delivery_status": delivery_status,
        "message": msg_obj
    }

