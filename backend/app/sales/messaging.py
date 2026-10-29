"""Sales conversations: inbound recording, AI / human handoff state, and sending with channel rules.

Channel rules enforced here:
- WhatsApp, Messenger and Instagram only allow free text within 24 hours of the customer's last message. Outside it
  a proactive WhatsApp message needs an approved template; Messenger and Instagram proactive messages are skipped.
- At most one proactive (AI-initiated) message per conversation every 48 hours.
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales import outbound
from app.sales.db import as_utc, now_utc
from app.sales.errors import NotFound, SalesError
from app.sales.leads import add_event, iso
from app.sales.models import SalesConversation, SalesLead, SalesMessage

SESSION_WINDOW = timedelta(hours=24)
PROACTIVE_GAP = timedelta(hours=48)
WINDOWED_CHANNELS = ("whatsapp", "messenger", "instagram")


def conversation_to_dict(conv: SalesConversation, lead: Optional[SalesLead] = None) -> dict:
    return {
        "conversation_id": conv.conversation_id,
        "lead_id": conv.lead_id,
        "lead_name": lead.name if lead else None,
        "lead_stage": lead.stage if lead else None,
        "channel": conv.channel,
        "external_id": conv.external_id,
        "mode": conv.mode,
        "assigned_user_id": conv.assigned_user_id,
        "handoff_reason": conv.handoff_reason,
        "last_customer_message_at": iso(conv.last_customer_message_at),
        "last_outbound_at": iso(conv.last_outbound_at),
        "updated_at": iso(conv.updated_at),
    }


def message_to_dict(msg: SalesMessage) -> dict:
    return {
        "message_id": msg.message_id,
        "direction": msg.direction,
        "sender": msg.sender,
        "text": msg.text,
        "status": msg.status,
        "error": msg.error,
        "staff_user_id": msg.staff_user_id,
        "draft_rating": msg.draft_rating,
        "created_at": iso(msg.created_at),
    }


async def find_conversation(session: AsyncSession, lead: SalesLead) -> Optional[SalesConversation]:
    return (
        await session.execute(
            select(SalesConversation).where(
                SalesConversation.tenant_id == lead.tenant_id,
                SalesConversation.channel == lead.channel,
                SalesConversation.external_id == lead.external_id,
            )
        )
    ).scalar_one_or_none()


async def get_or_create_conversation(session: AsyncSession, lead: SalesLead) -> SalesConversation:
    conv = (
        await session.execute(
            select(SalesConversation).where(
                SalesConversation.tenant_id == lead.tenant_id,
                SalesConversation.channel == lead.channel,
                SalesConversation.external_id == lead.external_id,
            )
        )
    ).scalar_one_or_none()
    if conv:
        return conv
    conv = SalesConversation(
        tenant_id=lead.tenant_id, lead_id=lead.lead_id, channel=lead.channel, external_id=lead.external_id,
        mode="AI", assigned_user_id=lead.owner_user_id,
    )
    session.add(conv)
    await session.flush()
    return conv


async def get_conversation(session: AsyncSession, tenant_id: str, conversation_id: str) -> SalesConversation:
    conv = await session.get(SalesConversation, conversation_id)
    if not conv or conv.tenant_id != tenant_id:
        raise NotFound("CONVERSATION_NOT_FOUND", "Conversation does not exist")
    return conv


async def record_inbound(
    session: AsyncSession, conv: SalesConversation, text: str, channel_message_id: Optional[str]
) -> Optional[SalesMessage]:
    """Store a customer message. Returns None when this channel message id was already stored (a webhook retry)."""
    if channel_message_id:
        seen = await session.scalar(
            select(func.count()).select_from(SalesMessage).where(
                SalesMessage.conversation_id == conv.conversation_id,
                SalesMessage.channel_message_id == channel_message_id,
            )
        )
        if seen:
            return None
    msg = SalesMessage(
        tenant_id=conv.tenant_id, conversation_id=conv.conversation_id, direction="in", sender="customer",
        text=text, channel_message_id=channel_message_id, status="received",
    )
    session.add(msg)
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError:  # a concurrent delivery of the same webhook won the race
        return None
    conv.last_customer_message_at = now_utc()
    return msg


def window_open(conv: SalesConversation) -> bool:
    last = as_utc(conv.last_customer_message_at)
    return bool(last and now_utc() - last < SESSION_WINDOW)


async def send_text(
    session: AsyncSession, conv: SalesConversation, text: str, *, sender: str, proactive: bool = False,
    whatsapp_template: Optional[str] = None, staff_user_id: Optional[str] = None,
) -> SalesMessage:
    """Send and record a message with its real delivery status."""
    if not text.strip():
        raise SalesError("EMPTY_MESSAGE", "Message text is empty")
    template = None
    skip_reason = None
    if conv.channel in WINDOWED_CHANNELS and not window_open(conv):
        if conv.channel == "whatsapp" and whatsapp_template:
            template = whatsapp_template
        else:
            skip_reason = "OUTSIDE_24H_WINDOW"
    if proactive and not skip_reason:
        last = as_utc(conv.last_proactive_at)
        if last and now_utc() - last < PROACTIVE_GAP:
            skip_reason = "PROACTIVE_LIMIT_48H"
    msg = SalesMessage(
        tenant_id=conv.tenant_id, conversation_id=conv.conversation_id, direction="out", sender=sender, text=text,
        staff_user_id=staff_user_id,
    )
    if skip_reason:
        msg.status, msg.error = "skipped", skip_reason
    else:
        result = await outbound.send(conv.channel, conv.external_id, text, template)
        msg.status, msg.error, msg.channel_message_id = result.status, result.error, result.provider_message_id
        if result.delivered:
            conv.last_outbound_at = now_utc()
            if proactive:
                conv.last_proactive_at = now_utc()
    session.add(msg)
    await session.flush()
    return msg


async def save_draft(session: AsyncSession, conv: SalesConversation, text: str) -> SalesMessage:
    msg = SalesMessage(
        tenant_id=conv.tenant_id, conversation_id=conv.conversation_id, direction="out", sender="ai", text=text,
        status="draft",
    )
    session.add(msg)
    await session.flush()
    return msg


async def staff_reply(session: AsyncSession, conv: SalesConversation, text: str, staff_user_id: str) -> SalesMessage:
    """A person replies: the chat becomes theirs until handed back."""
    msg = await send_text(session, conv, text, sender="staff", staff_user_id=staff_user_id)
    await set_mode(session, conv, "HUMAN", staff_user_id, reason="staff replied")
    return msg


async def set_mode(
    session: AsyncSession, conv: SalesConversation, mode: str, actor: str, reason: Optional[str] = None
) -> None:
    if mode not in ("AI", "HUMAN"):
        raise SalesError("INVALID_MODE", "Mode must be AI or HUMAN")
    if conv.mode == mode:
        return
    conv.mode = mode
    conv.handoff_reason = reason if mode == "HUMAN" else None
    if mode == "HUMAN" and actor not in ("ai", "system"):
        conv.assigned_user_id = actor
    lead = await session.get(SalesLead, conv.lead_id)
    await add_event(session, lead, "handoff" if mode == "HUMAN" else "handback", actor, {"reason": reason})
    await session.flush()


async def recent_history(session: AsyncSession, conv: SalesConversation, limit: int = 12) -> list[SalesMessage]:
    """Last messages the customer actually saw or sent (drafts and skipped sends excluded), oldest first."""
    rows = (
        await session.execute(
            select(SalesMessage)
            .where(
                SalesMessage.conversation_id == conv.conversation_id,
                SalesMessage.status.in_(("received", "sent", "stored")),
            )
            .order_by(SalesMessage.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return list(reversed(rows))


async def list_conversations(
    session: AsyncSession, tenant_id: str, *, mode: Optional[str] = None, limit: int = 100
) -> list[dict]:
    stmt = (
        select(SalesConversation, SalesLead)
        .join(SalesLead, SalesLead.lead_id == SalesConversation.lead_id)
        .where(SalesConversation.tenant_id == tenant_id)
    )
    if mode:
        stmt = stmt.where(SalesConversation.mode == mode)
    rows = (await session.execute(stmt.order_by(SalesConversation.updated_at.desc()).limit(limit))).all()
    return [conversation_to_dict(c, lead) for c, lead in rows]


async def conversation_messages(session: AsyncSession, conversation_id: str, limit: int = 200) -> list[dict]:
    rows = (
        await session.execute(
            select(SalesMessage)
            .where(SalesMessage.conversation_id == conversation_id)
            .order_by(SalesMessage.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [message_to_dict(m) for m in reversed(rows)]


async def rate_draft(session: AsyncSession, tenant_id: str, message_id: str, rating: str, actor: str) -> dict:
    if rating not in ("usable", "not_usable"):
        raise SalesError("INVALID_RATING", "Rating must be usable or not_usable")
    msg = await session.get(SalesMessage, message_id)
    if not msg or msg.tenant_id != tenant_id or msg.status != "draft":
        raise NotFound("DRAFT_NOT_FOUND", "Draft does not exist")
    msg.draft_rating, msg.rated_by = rating, actor
    await session.flush()
    return message_to_dict(msg)


async def draft_stats(session: AsyncSession, tenant_id: str) -> dict:
    rows = dict(
        (
            await session.execute(
                select(SalesMessage.draft_rating, func.count())
                .where(SalesMessage.tenant_id == tenant_id, SalesMessage.status == "draft")
                .group_by(SalesMessage.draft_rating)
            )
        ).all()
    )
    usable, not_usable = rows.get("usable", 0), rows.get("not_usable", 0)
    rated = usable + not_usable
    return {
        "drafts": sum(rows.values()),
        "rated": rated,
        "usable": usable,
        "usable_pct": round(100 * usable / rated, 1) if rated else None,
    }
