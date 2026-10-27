"""One door for the old AI entry points: /api/v1/ai/chat, the conversations AI reply and the automation hook.

``settings.ai_route_via_sales`` picks who answers:

- ``legacy``: the old LangGraph pipeline, as before.
- ``shadow``: the old pipeline answers; the sales assistant drafts a reply to the same message beside it, and the
  pair is stored in ``ai_shadow_pairs`` for staff to rate (better / same / worse).
- ``sales``: the sales pipeline answers wherever the assistant is live for that channel. Where it isn't live yet
  (assistant in shadow mode, channel in draft-only), the old pipeline still answers and the pair is stored as in
  ``shadow``, so turning the route on never leaves a customer without a reply.

Every path returns the same dict shape as ``ai_graph.ainvoke``, so the endpoints' response builders don't change.
"""

import asyncio
import logging
from dataclasses import replace
from typing import Optional

from app.config import settings
from app.sales import agent, agent_settings
from app.sales.db import now_utc, session_scope
from app.sales.inbound import InboundMessage, handle_inbound
from app.sales.legacy_bridge import sales_channel
from app.sales.models import AIShadowPair, SalesConversation

logger = logging.getLogger(__name__)

ROUTES = ("legacy", "shadow", "sales")
REPLIED = ("replied", "handoff", "blocked", "grounding_failed", "error")
_background: set = set()


def route() -> str:
    value = (settings.ai_route_via_sales or "legacy").strip().lower()
    return value if value in ROUTES else "legacy"


async def _legacy(state) -> dict:
    from app.agents.graph import ai_graph

    return await ai_graph.ainvoke(state)


async def _channel_mode(channel: str) -> str:
    async with session_scope() as session:
        return agent_settings.effective_mode(await agent_settings.get_settings(session, settings.default_tenant_id), channel)


def _as_graph_output(state, reply: str, *, escalate: bool, reason: Optional[str], extra: dict) -> dict:
    from app.agents.state import Action

    return {
        "agent_reply": reply,
        "agent_used": "sales_assistant",
        "agent_actions": [Action(type="escalate", payload={"reason": reason or "handoff"})] if escalate else [],
        "requires_escalation": escalate,
        "escalation_reason": reason or "",
        "confidence": 0.9 if not escalate else 0.5,
        "conversation_id": state.conversation_id,
        "channel": state.channel,
        "language": state.language,
        "moderated": True,
        "intent_classified": True,
        "agent_done": True,
        "safety_checked": True,
        **extra,
    }


async def _sales_answer(state, inbound: dict) -> Optional[dict]:
    """Run the sales turn inline. None when the sales assistant didn't answer (the caller falls back)."""
    if inbound.get("status") == "duplicate":
        return _as_graph_output(state, "", escalate=False, reason=None, extra={"duplicate": True})
    if inbound.get("status") != "accepted":
        return None
    conversation_id = inbound["conversation_id"]
    if inbound.get("conversation_mode") != "AI":
        # A person owns this chat: they reply from the Sales Inbox, nothing is answered automatically.
        return _as_graph_output(state, "", escalate=True, reason="a consultant is handling this chat",
                                extra={"sales_conversation_id": conversation_id, "pending_staff_reply": True})
    result = await agent.run_turn(conversation_id)
    if result.status not in REPLIED:
        logger.info("[sales.entry] sales turn did not answer (%s: %s); old pipeline answers", result.status, result.reason)
        return None
    escalate = result.status != "replied"
    return _as_graph_output(state, result.reply or "", escalate=escalate, reason=result.reason,
                            extra={"sales_conversation_id": conversation_id, "sales_outcome": result.status})


async def answer_message(state, *, name: Optional[str] = None, channel_message_id: Optional[str] = None) -> dict:
    """Answer one customer message through whichever pipeline the route says."""
    current = route()
    if current == "legacy" or not (state.message or "").strip():
        return await _legacy(state)
    channel = sales_channel(state.channel)
    message = InboundMessage(
        tenant_id=settings.default_tenant_id, channel=channel, external_id=state.conversation_id,
        text=state.message, channel_message_id=channel_message_id, name=name, source="legacy_ai",
    )
    inbound = None
    try:
        if current == "sales" and await _channel_mode(channel) == "live":
            inbound = await handle_inbound(message, queue_turn=False)
            answer = await _sales_answer(state, inbound)
            if answer is not None:
                return answer
    except Exception:
        # The sales side failing must never leave the customer without an answer.
        logger.exception("[sales.entry] sales route failed for %s; old pipeline answers", state.conversation_id)
    raw = await _legacy(state)
    if inbound is not None:
        try:
            await record_legacy_reply(inbound.get("conversation_id"), raw.get("agent_reply") or "")
        except Exception:
            logger.exception("[sales.entry] could not record the old pipeline's reply")
    elif state.persist_leads:
        _spawn(shadow_compare(replace(message, enroll_followups=False), raw))
    return raw


def _spawn(coro) -> None:
    task = asyncio.create_task(coro)
    _background.add(task)
    task.add_done_callback(_background.discard)


async def record_legacy_reply(conversation_id: Optional[str], reply: str) -> None:
    """Keep the sales conversation complete: what the old pipeline told the customer becomes part of its history."""
    if not conversation_id or not reply.strip():
        return
    from app.sales.models import SalesMessage

    async with session_scope() as session:
        conv = await session.get(SalesConversation, conversation_id)
        if conv is None:
            return
        session.add(SalesMessage(
            tenant_id=conv.tenant_id, conversation_id=conversation_id, direction="out", sender="legacy_ai",
            text=reply[:4000], status="sent",
        ))
        conv.last_outbound_at = now_utc()


async def shadow_compare(message: InboundMessage, raw: dict) -> Optional[str]:
    """Record the message, let the sales assistant draft a reply to it, and store both replies as a pair.

    Order matters: the draft is made before the old reply is added to the conversation, so the assistant answers the
    customer's message rather than seeing it as already answered. Never raises.
    """
    legacy_reply = raw.get("agent_reply") or ""
    try:
        inbound = await handle_inbound(message, queue_turn=False)
        conversation_id = inbound.get("conversation_id")
        sales_reply = outcome = reason = None
        if inbound.get("status") == "accepted":
            result = await agent.run_turn(conversation_id, force_shadow=True)
            outcome, reason, sales_reply = result.status, result.reason, result.reply
        else:
            outcome, reason = inbound.get("status"), inbound.get("reason")
        await record_legacy_reply(conversation_id, legacy_reply)
        async with session_scope() as session:
            pair = AIShadowPair(
                tenant_id=message.tenant_id, conversation_id=conversation_id,
                legacy_conversation_id=message.external_id, channel=message.channel, customer_text=message.text[:4000],
                legacy_reply=legacy_reply[:4000], legacy_agent=str(raw.get("agent_used") or "")[:64] or None,
                legacy_escalated=bool(raw.get("requires_escalation")), sales_reply=sales_reply,
                sales_outcome=(outcome or "")[:32] or None, sales_reason=(reason or "")[:256] or None,
            )
            session.add(pair)
            await session.flush()
            return pair.pair_id
    except Exception:
        logger.exception("[sales.entry] shadow comparison failed for %s", message.external_id)
        return None
