"""Inbound customer messages from every channel, normalised into one path.

webhook → ``handle_inbound`` → save message (duplicates dropped) → lead + conversation → follow-ups adjusted →
agent turn queued (2 s debounce, one turn per chat at a time).
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.sales import agent_settings, followups, leads, messaging
from app.sales.db import as_utc, session_scope
from app.sales.db import lazy_jobs as jobs
from app.sales.models import CHANNELS

logger = logging.getLogger(__name__)


@dataclass
class InboundMessage:
    tenant_id: str
    channel: str
    external_id: str
    text: str
    channel_message_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    email: Optional[str] = None
    # False for shadow comparisons: recording a message must not start automatic follow-ups
    enroll_followups: bool = True


async def handle_inbound(msg: InboundMessage, *, queue_turn: bool = True) -> dict:
    """Record a customer message. ``queue_turn=False`` leaves the reply to the caller (the old entry points run the
    turn inline so their HTTP response can carry it)."""
    if msg.channel not in CHANNELS:
        return {"status": "rejected", "reason": f"unknown channel {msg.channel}"}
    text = (msg.text or "").strip()
    if not text:
        return {"status": "ignored", "reason": "empty message"}
    phone = msg.phone or (msg.external_id if msg.channel == "whatsapp" else None)
    async with session_scope() as session:
        lead, created = await leads.get_or_create_lead(
            session, msg.tenant_id, msg.channel, msg.external_id, name=msg.name, phone=phone, source=msg.source
        )
        if msg.email and not lead.email:
            lead.email = msg.email[:256]
        conv = await messaging.get_or_create_conversation(session, lead)
        stored = await messaging.record_inbound(session, conv, text[:4000], msg.channel_message_id)
        if stored is None:
            return {"status": "duplicate", "conversation_id": conv.conversation_id}
        leads.touch_contact(lead)
        enrollment = None
        if created and msg.enroll_followups:
            enrollment = await followups.enroll(session, lead, "new_lead")
        else:
            # They're talking to us: pause nurture messages; the hourly sweep re-engages them if they go quiet.
            await followups.stop_enrollments(session, lead, "customer replied", triggers=("new_lead", "reengage", "post_visit", "no_show"))
        settings = await agent_settings.get_settings(session, msg.tenant_id)
        channel_mode = agent_settings.effective_mode(settings, msg.channel)
        run_agent = channel_mode != "off" and conv.mode == "AI"
        result = {
            "status": "accepted", "conversation_id": conv.conversation_id, "lead_id": lead.lead_id,
            "new_lead": created, "conversation_mode": conv.mode, "assistant_mode": channel_mode,
        }
        enrollment_info = (enrollment.enrollment_id, as_utc(enrollment.next_run_at)) if enrollment else None
    if enrollment_info:
        await jobs.defer(jobs.followup_step, schedule_at=enrollment_info[1], enrollment_id=enrollment_info[0])
    if run_agent and not queue_turn:
        result["agent_turn"] = "caller"
    elif run_agent:
        job_id = await jobs.defer_agent_turn(result["conversation_id"])
        # None means a turn for this chat is already waiting and will read this message too, or the queue is down.
        result["agent_turn"] = "queued" if job_id else "already_queued_or_unavailable"
    else:
        result["agent_turn"] = "not_run"
    return result
