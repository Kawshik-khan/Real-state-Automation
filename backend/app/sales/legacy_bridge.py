"""Writes what the old LangGraph pipeline learns into the sales pipeline, so staff see it.

Until every entry point runs through ``sales.inbound`` (the AI workflow fix plan, Phase B), chats answered by the old
graph would otherwise leave no lead behind: booking requests and intent scores lived only in graph state. Failures
here never break a customer reply; they are logged.
"""

import logging
from typing import Optional

from app.config import settings
from app.sales import leads
from app.sales.db import session_scope
from app.sales.models import CHANNELS

logger = logging.getLogger(__name__)


def sales_channel(channel: Optional[str]) -> str:
    channel = (channel or "").lower()
    return channel if channel in CHANNELS else "website"


async def record_lead_signal(
    *,
    conversation_id: str,
    channel: Optional[str],
    event_type: str,
    payload: dict,
    name: Optional[str] = None,
    notify: Optional[str] = None,
) -> Optional[str]:
    """Find or create the lead for this legacy conversation and append an event. Returns the lead id."""
    tenant_id = settings.default_tenant_id
    try:
        async with session_scope() as session:
            lead, _created = await leads.get_or_create_lead(
                session, tenant_id, sales_channel(channel), conversation_id, name=name, source="legacy_ai"
            )
            leads.touch_contact(lead)
            await leads.add_event(session, lead, event_type, "ai", payload)
            lead_id = lead.lead_id
    except Exception as exc:
        logger.warning("[sales.legacy_bridge] could not record %s for %s: %s", event_type, conversation_id, exc)
        return None
    if notify:
        from app.sales import workflows

        await workflows.notify_staff(tenant_id, f"{notify} — lead {lead_id}")
    return lead_id


async def record_intent_score(
    *, conversation_id: str, channel: Optional[str], score: int, hot: bool, payload: dict
) -> Optional[str]:
    """Record the old pipeline's intent score when it rises above the best one recorded for this lead.

    One event per new high, and one staff notification the first time the lead turns hot, so a long chat doesn't
    flood the lead's timeline or the sales team's chat.
    """
    from sqlalchemy import select

    from app.sales.models import LeadEvent

    tenant_id = settings.default_tenant_id
    try:
        async with session_scope() as session:
            lead, _created = await leads.get_or_create_lead(
                session, tenant_id, sales_channel(channel), conversation_id, source="legacy_ai"
            )
            leads.touch_contact(lead)
            earlier = (
                await session.execute(
                    select(LeadEvent.payload).where(LeadEvent.lead_id == lead.lead_id, LeadEvent.type == "intent_scored")
                )
            ).scalars().all()
            best = max((int((p or {}).get("score", 0)) for p in earlier), default=-1)
            was_hot = any((p or {}).get("hot") for p in earlier)
            if score <= best:
                return lead.lead_id
            await leads.add_event(session, lead, "intent_scored", "ai", {**payload, "score": score, "hot": hot})
            lead_id = lead.lead_id
    except Exception as exc:
        logger.warning("[sales.legacy_bridge] could not record intent score for %s: %s", conversation_id, exc)
        return None
    if hot and not was_hot:
        from app.sales import workflows

        await workflows.notify_staff(tenant_id, f"Hot lead by chat (intent score {score}/100) — lead {lead_id}")
    return lead_id
