"""AI Services -- Main chat endpoint using LangGraph orchestration.

n8n calls POST /api/chat for every incoming message.
MVP specification: {"reply":"...", "actions":["send_images","send_brochure"]}
Backward compatible: Full format with confidence, intent, metadata
"""
from fastapi import APIRouter, Depends, Header, Request

from app.agents.graph import ai_graph
from app.agents.state import AIState
from app.core.rate_limiter import AI_CHAT_LIMIT, limiter
from app.dependencies import require_automation_secret as _auth
from app.schemas.chat import Action, ChatRequest, ChatResponse
from app.utils.chat_response_builder import ChatResponseBuilder

router = APIRouter()

@router.post("/chat", summary="Main chat endpoint -- full AI pipeline (LangGraph)")
@router.post("/ask", summary="Main chat endpoint alias -- full AI pipeline (LangGraph)")
@limiter.limit(AI_CHAT_LIMIT)
async def ai_chat(
    request: Request,
    body: ChatRequest, 
    auth: dict = Depends(_auth),
    format_version: str = Header("full", alias="X-Format-Version")  # "full" or "structured"
):
    """Process a chat message through the LangGraph AI pipeline.

    n8n calls this endpoint when it receives a message from any channel.
    Supports both full format (backward compatible) and structured format (MVP spec).
    """
    # 1. Semantic Vector Cache Lookup: Intercept repeated real estate queries
    from app.core.semantic_cache import semantic_cache

    cached_entry = await semantic_cache.lookup(
        query=body.message,
        tenant_id=body.tenant_id,
        language=body.language or "en",
    )

    is_cache_hit = False
    if cached_entry:
        extracted_data, sim_score = cached_entry
        is_cache_hit = True
    else:
        # Build initial state
        initial_state = AIState(
            message=body.message,
            conversation_id=body.conversation_id,
            channel=body.channel,
            user_id=body.user_id,
            tenant_id=body.tenant_id,
            language=body.language or "en",
        )

        # Run the graph -- LangGraph returns state dict
        raw: dict = await ai_graph.ainvoke(initial_state)

        # Extract LangGraph output for both formats
        extracted_data = ChatResponseBuilder.extract_workflow_data(raw)

        # Store in semantic cache if not an escalation
        if not extracted_data.get("requires_escalation"):
            import asyncio
            asyncio.create_task(
                semantic_cache.store(
                    query=body.message,
                    response_data=extracted_data,
                    tenant_id=body.tenant_id,
                    language=body.language or "en",
                    intent=str(extracted_data.get("agent_used", "property_inquiry")),
                )
            )
    
    # Broadcast live SSE message events & update conversations store
    try:
        from app.api.v1.conversations.endpoints import add_message_to_conversation
        from app.schemas.chat import MemoryEntry
        from app.services.llm_guardrails import llm_guardrails
        from app.services.memory import conversation_memory
        requires_esc = bool(extracted_data.get("requires_escalation", False))
        reply_text = extracted_data.get("agent_reply", "")
        confidence = extracted_data.get("confidence", 0.90)
        intent = str(extracted_data.get("agent_used", "property_inquiry"))

        # Redact sensitive PII before persistence in chat history & memory stores
        persisted_user_msg, _ = llm_guardrails.redact_pii(body.message)

        # Save user message to memory store & DB
        await conversation_memory.add(
            body.conversation_id,
            MemoryEntry(role="user", content=persisted_user_msg)
        )
        await add_message_to_conversation(
            conv_id=body.conversation_id,
            sender="user",
            text=persisted_user_msg,
            channel=body.channel,
        )

        # Save AI reply message to memory store & DB if present
        if reply_text:
            await conversation_memory.add(
                body.conversation_id,
                MemoryEntry(role="assistant", content=reply_text)
            )
            await add_message_to_conversation(
                conv_id=body.conversation_id,
                sender="ai",
                text=reply_text,
                channel=body.channel,
                confidence=confidence,
                intent=intent,
                requires_escalation=requires_esc,
            )

        # Broadcast real-time message event via WebSocket
        try:
            from app.api.v1.ws import ws_manager
            await ws_manager.broadcast_message({
                "event": "new_message",
                "conversation_id": body.conversation_id,
                "user_message": body.message,
                "ai_reply": reply_text,
                "channel": body.channel,
                "requires_escalation": requires_esc,
            })
        except Exception as ws_err:
            print(f"[ai_chat] WebSocket broadcast error: {ws_err}")
    except Exception as err:
        print(f"[ai_chat] Sync error: {err}")

    # Build response based on requested format
    if format_version == "structured":
        # MVP structured format: {"reply": "...", "actions": ["send_images", ...]}
        response_data = ChatResponseBuilder.build_structured(extracted_data)
        if is_cache_hit:
            response_data["cached"] = True
            response_data["cache_similarity"] = round(sim_score, 4)
        return ChatResponseBuilder.create_json_response(response_data, format_version)
    else:
        # Full format for backward compatibility
        res = await _build_full_chat_response(extracted_data, body, auth)
        if is_cache_hit and isinstance(res, dict):
            res["cached"] = True
            res["cache_similarity"] = round(sim_score, 4)
        return res


async def _build_full_chat_response(extracted_data: dict, body: ChatRequest, auth: dict):
    """Build full ChatResponse format (backward compatible)"""
    
    # Convert actions to Pydantic Action objects  
    actions_raw = extracted_data.get("agent_actions", [])
    if actions_raw:
        actions_raw = [
            a.model_dump() if hasattr(a, "model_dump") else a.dict() if hasattr(a, "dict") else a
            for a in actions_raw
        ]

    actions = [
        Action(type=a["type"], payload=a.get("payload", {}))
        if isinstance(a, dict) else a
        for a in (actions_raw if isinstance(actions_raw, list) else [])
    ]

    # Handle intent safely
    intent_value = extracted_data.get("agent_used", extracted_data.get("intent", ""))
    if hasattr(intent_value, "model_dump"):
        intent_value = intent_value.model_dump()
    elif hasattr(intent_value, "dict"):
        intent_value = intent_value.dict()

    resp = ChatResponse(
        reply=extracted_data.get("agent_reply", ""),
        confidence=extracted_data.get("confidence", 0.5),
        actions=actions,
        intent=str(intent_value) if intent_value else "",
        conversation_id=body.conversation_id,
        requires_escalation=bool(extracted_data.get("requires_escalation", False)),
        metadata=extracted_data.get("metadata", {}),
    )

    res = resp.model_dump()
    res["success"] = True
    return res


# ── Auxiliary endpoints (unchanged) ─────────────────────────

@router.post("/translate", summary="Auto Translate")
async def ai_translate(body: dict, auth: dict = Depends(_auth)):
    """Translate text using LLM."""
    from app.services.llm import llm_service

    text = body.get("text", "")
    target = body.get("target_language", "en")
    source = body.get("source_language", "auto")

    messages = [
        {"role": "system", "content": f"You are a translator. Translate the following text to {target}. Respond with ONLY the translated text, no explanations."},
        {"role": "user", "content": text}
    ]
    try:
        translated = await llm_service.chat(messages, temperature=0.1)
    except Exception:
        translated = text

    return {
        "success": True,
        "translated_text": translated,
        "source_language": source,
        "target_language": target,
        "tenantId": auth["tenant_id"],
    }


@router.post("/embeddings", summary="Generate embeddings for text")
async def ai_embeddings(body: dict, auth: dict = Depends(_auth)):
    """Generate embeddings for the given text."""
    from app.services.llm import llm_service

    text = body.get("text", "")
    if not text:
        return {"success": False, "error": "text is required", "tenantId": auth["tenant_id"]}

    embedding = await llm_service.embed(text)
    return {
        "success": True,
        "embedding_preview": embedding[:8],
        "dimension": len(embedding),
        "tenantId": auth["tenant_id"],
    }


@router.post("/rag", summary="RAG retrieval")
async def ai_rag(body: dict, auth: dict = Depends(_auth)):
    """Run RAG retrieval pipeline."""
    from app.rag.pipeline import rag

    query = body.get("query", "")
    top_k = min(int(body.get("top_k", 3)), 20)

    if not query:
        return {"success": False, "error": "query is required", "tenantId": auth["tenant_id"]}

    chunks = await rag.query(query, top_k=top_k)
    context = await rag.build_context(chunks)

    return {
        "success": True,
        "results": chunks,
        "context": context,
        "query": query,
        "tenantId": auth["tenant_id"],
    }


@router.post("/memory", summary="Conversation Memory operations")
async def ai_memory(body: dict, auth: dict = Depends(_auth)):
    """Manage conversation memory."""
    from app.services.memory import conversation_memory

    action = body.get("action", "get")
    conversation_id = body.get("conversation_id", "")

    if action == "clear":
        await conversation_memory.clear(conversation_id)
        return {"success": True, "memory_stored": True, "action": "cleared", "tenantId": auth["tenant_id"]}

    history = await conversation_memory.get_history(conversation_id)
    return {
        "success": True,
        "memory_stored": True,
        "conversation_id": conversation_id,
        "history": [e.dict() for e in history],
        "turn_count": len(history),
        "tenantId": auth["tenant_id"],
    }