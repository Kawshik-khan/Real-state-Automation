"""Conversations API & SSE Event Stream Endpoints."""

import asyncio
import json

from app.services.event_broadcaster import broadcaster
from app.services.telegram import telegram_service
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

# In-memory mock conversation database store
IN_MEMORY_CONVERSATIONS = [
    {
        "id": "wa_8801711122233",
        "name": "Tanvir Hossain",
        "phone": "+880 1711-122233",
        "channel": "whatsapp",
        "lastMessage": "I want 3 BHK in Gulshan under 1 crore",
        "time": "2 mins ago",
        "status": "active",
        "aiPaused": False,
        "confidence": 0.92,
        "intent": "property_search",
        "messages": [
            {"sender": "user", "text": "Hi, looking for apartments in Gulshan", "time": "10:14 AM"},
            {"sender": "ai", "text": "Hello Tanvir! Welcome to GLG Assets. What is your preferred budget?", "time": "10:14 AM"},
            {"sender": "user", "text": "I want 3 BHK in Gulshan under 1 crore", "time": "10:16 AM"},
            {"sender": "ai", "text": "Great choice! GLG Gulshan Heights features 3 BHK priced at ৳95 Lakhs.", "time": "10:16 AM"}
        ]
    },
    {
        "id": "tg_88018998877",
        "name": "Mahmudur Rahman",
        "phone": "+880 1899-887766",
        "channel": "telegram",
        "lastMessage": "Send me the brochure and price list for Uttara project",
        "time": "5 mins ago",
        "status": "active",
        "aiPaused": False,
        "confidence": 0.94,
        "intent": "brochure_request",
        "messages": [
            {"sender": "user", "text": "Hi, I am interested in your Uttara project on Telegram", "time": "10:20 AM"},
            {"sender": "ai", "text": "Hello Mahmudur! Welcome to GLG Assets Telegram Bot. How can I assist you?", "time": "10:20 AM"},
            {"sender": "user", "text": "Send me the brochure and price list for Uttara project", "time": "10:22 AM"}
        ]
    },
    {
        "id": "fb_1029384756",
        "name": "Sarah Khan",
        "phone": "+880 1822-334455",
        "channel": "facebook",
        "lastMessage": "Can I visit the site tomorrow at 3 PM?",
        "time": "15 mins ago",
        "status": "escalated",
        "aiPaused": True,
        "confidence": 0.68,
        "intent": "booking",
        "messages": [
            {"sender": "user", "text": "Is Banani Crest project open for site visit?", "time": "09:45 AM"},
            {"sender": "ai", "text": "Yes Sarah! Site visits are available daily 10 AM to 5 PM.", "time": "09:45 AM"},
            {"sender": "user", "text": "Can I visit the site tomorrow at 3 PM?", "time": "10:01 AM"}
        ]
    },
    {
        "id": "ig_99887766",
        "name": "Anisur Rahman",
        "phone": "+880 1911-556677",
        "channel": "instagram",
        "lastMessage": "Is payment schedule flexible over 3 years?",
        "time": "1 hour ago",
        "status": "active",
        "aiPaused": False,
        "confidence": 0.88,
        "intent": "faq",
        "messages": [
            {"sender": "user", "text": "Is payment schedule flexible over 3 years?", "time": "09:12 AM"}
        ]
    }
]


def get_or_create_conversation(conv_id: str, channel: str = "website", name: str = None, phone: str = None):
    """Retrieve existing or create new conversation in memory."""
    for conv in IN_MEMORY_CONVERSATIONS:
        if conv["id"] == conv_id:
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
        "messages": []
    }
    IN_MEMORY_CONVERSATIONS.insert(0, new_conv)
    return new_conv


async def add_message_to_conversation(
    conv_id: str, 
    sender: str, 
    text: str, 
    channel: str = "website",
    confidence: float = None,
    intent: str = None,
    requires_escalation: bool = False
):
    """Append message to conversation state and broadcast via SSE."""
    conv = get_or_create_conversation(conv_id, channel)
    
    # Deduplication Guard: Do not append if the exact same message was just added
    if conv["messages"]:
        last_msg = conv["messages"][-1]
        if last_msg.get("sender") == sender and last_msg.get("text", "").strip() == text.strip():
            return conv, last_msg

    msg_obj = {"sender": sender, "text": text, "time": "Just now"}
    conv["messages"].append(msg_obj)
    conv["lastMessage"] = text
    conv["time"] = "Just now"
    
    if confidence is not None:
        conv["confidence"] = confidence
    if intent:
        conv["intent"] = intent
    if requires_escalation:
        conv["status"] = "escalated"
        conv["aiPaused"] = True

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

    # Trigger background sync to n8n Google Sheets webhook and database persistence
    asyncio.create_task(_sync_lead_to_n8n_sheets(conv))
    asyncio.create_task(_persist_message_to_db(conv_id, sender, text, conv["channel"], conv["name"], conv["phone"]))
        
    return conv, msg_obj


async def _persist_message_to_db(conv_id: str, sender: str, text: str, channel: str = "website", name: str = None, phone: str = None):
    """Persists conversation and message into Supabase/PostgreSQL."""
    try:
        from app.database import async_session_factory
        from app.models.models import ConversationRecord, MessageRecord, UserRecord
        from sqlalchemy import select
        async with async_session_factory() as session:
            user_id = f"usr_{conv_id}"
            user_stmt = select(UserRecord).where(UserRecord.user_id == user_id)
            u_res = await session.execute(user_stmt)
            db_user = u_res.scalar_one_or_none()
            if not db_user:
                db_user = UserRecord(user_id=user_id, name=name, phone=phone, channel=channel)
                session.add(db_user)
                await session.flush()

            conv_stmt = select(ConversationRecord).where(ConversationRecord.conversation_id == conv_id)
            conv_res = await session.execute(conv_stmt)
            db_conv = conv_res.scalar_one_or_none()
            if not db_conv:
                db_conv = ConversationRecord(conversation_id=conv_id, user_id=user_id, channel=channel, status="active")
                session.add(db_conv)
                await session.flush()

            new_msg = MessageRecord(conversation_id=conv_id, sender=sender, text=text)
            session.add(new_msg)
            await session.commit()
    except Exception:
        pass  # Non-blocking async persistence


async def _sync_lead_to_n8n_sheets(conv: dict):
    """Asynchronously post lead/message update to n8n Google Sheets Sync webhook."""
    try:
        import httpx
        url = "http://localhost:5678/webhook/google-sheets-leads"
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
        from app.database import async_session_factory
        from app.models.models import ConversationRecord, MessageRecord, UserRecord
        from sqlalchemy import and_, desc, select

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

            if rows:
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

                    formatted.append({
                        "id": conv.conversation_id,
                        "name": usr.name if usr and usr.name else "Prospective Buyer",
                        "phone": usr.phone if usr and usr.phone else "+880 1700-000000",
                        "channel": conv.channel,
                        "status": conv.status,
                        "aiPaused": conv.ai_paused,
                        "lastMessage": last_msg.text if last_msg and hasattr(last_msg, 'text') else "Inquiry initiated",
                        "time": conv.last_message_at.strftime("%I:%M %p") if conv.last_message_at else "Just now",
                        "unread": 0,
                        "avatar": (usr.name[0].upper() if (usr and usr.name) else "C"),
                        "beliefs": conv.beliefs or {},
                        "createdAt": conv.created_at.isoformat() if conv.created_at else None
                    })
                return {"success": True, "conversations": formatted, "count": len(formatted)}
    except Exception:
        pass
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

    conv = get_or_create_conversation(conv_id, channel, name, phone)
    if initial_message:
        await add_message_to_conversation(conv_id, "user", initial_message, channel)
        
    return {"success": True, "conversation": conv}


@router.delete("/{conv_id}", summary="Delete or clear a conversation")
async def delete_conversation(conv_id: str):
    """Delete a conversation from memory."""
    global IN_MEMORY_CONVERSATIONS
    IN_MEMORY_CONVERSATIONS = [c for c in IN_MEMORY_CONVERSATIONS if c["id"] != conv_id]
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


@router.post("/{conv_id}/message", summary="Process customer message (triggers AI pipeline if active)")
async def send_customer_message(conv_id: str, body: dict):
    """Process incoming customer message. If AI is active, run through LangGraph pipeline."""
    text = body.get("text") or body.get("message", "")
    channel = body.get("channel", "website")
    if not text:
        raise HTTPException(status_code=400, detail="Text or message required")

    conv = get_or_create_conversation(conv_id, channel)
    
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
    for conv in IN_MEMORY_CONVERSATIONS:
        if conv["id"] == conv_id:
            conv["aiPaused"] = not conv["aiPaused"]
            conv["status"] = "human_takeover" if conv["aiPaused"] else "active"
            
            # Persist to database
            try:
                from app.database import async_session_factory
                from app.models.models import ConversationRecord
                from sqlalchemy import update

                async with async_session_factory() as session:
                    stmt = update(ConversationRecord).where(
                        ConversationRecord.conversation_id == conv_id
                    ).values(ai_paused=conv["aiPaused"], status=conv["status"])
                    await session.execute(stmt)
                    await session.commit()
            except Exception:
                pass

            # Broadcast state change
            await broadcaster.broadcast("agent_takeover", {
                "conversation_id": conv_id,
                "aiPaused": conv["aiPaused"],
                "status": conv["status"],
                "name": conv["name"],
                "channel": conv["channel"]
            })
            
            return {
                "success": True,
                "conversation_id": conv_id,
                "aiPaused": conv["aiPaused"],
                "status": conv["status"]
            }
    raise HTTPException(status_code=404, detail="Conversation not found")





@router.post("/{conv_id}/reply", summary="Post manual human agent reply")
async def send_agent_reply(conv_id: str, body: dict):
    """Post manual agent reply, broadcast message_received event, and dispatch to real social channel."""
    reply_text = body.get("text", "")
    if not reply_text:
        raise HTTPException(status_code=400, detail="Text required")

    conv = None
    for c in IN_MEMORY_CONVERSATIONS:
        if c["id"] == conv_id:
            conv = c
            break

    if not conv:
        conv = get_or_create_conversation(conv_id)

    msg_obj = {"sender": "human_agent", "text": reply_text, "time": "Just now"}
    conv["messages"].append(msg_obj)
    conv["lastMessage"] = reply_text
    conv["time"] = "Just now"

    channel = conv.get("channel", "website")
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

