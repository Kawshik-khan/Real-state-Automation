"""What the jobs do: reminders, visit outcomes, follow-ups, unit-match alerts, digests and sweeps.

Each function opens its own session, is safe to run twice (it re-checks state first), and returns a small dict
describing what actually happened, which Procrastinate stores as the job result.
"""

import logging
from datetime import timedelta
from typing import Optional

from sqlalchemy import func, select

from app.config import settings
from app.models.models import ProjectRecord
from app.sales import agent_settings, followups, leads, messaging, units
from app.sales.db import as_utc, format_dhaka, now_utc, session_scope
from app.sales.db import lazy_jobs as jobs
from app.sales.models import (
    ACTIVE_VISIT_STATUSES,
    OPEN_LEAD_STAGES,
    FollowupEnrollment,
    LeadEvent,
    PropertyUnit,
    SalesApproval,
    SalesLead,
    SiteVisit,
)

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(days=5)
UNIT_ALERT_GAP = timedelta(days=7)
OUTCOME_CHECK_DELAY = timedelta(hours=1)


# ── Staff notifications ───────────────────────────────────────────────

async def notify_staff(tenant_id: str, text: str) -> dict:
    """Message the sales team's Telegram chat. Never raises; returns what happened."""
    try:
        async with session_scope() as session:
            chat_id = (await agent_settings.get_settings(session, tenant_id)).digest_chat_id
    except Exception:
        chat_id = None
    chat_id = chat_id or settings.default_telegram_chat_id
    if not chat_id:
        logger.info("[sales.notify] no staff chat configured; not sent: %s", text)
        return {"status": "not_sent", "error": "NO_STAFF_CHAT_CONFIGURED"}
    from app.sales import outbound

    result = await outbound.send("telegram", str(chat_id), text)
    return {"status": result.status, "error": result.error}


# ── Visits ────────────────────────────────────────────────────────────

async def schedule_visit_jobs(visit: dict) -> dict:
    """Queue the 24 h and 2 h reminders and the outcome check for a booked visit."""
    from datetime import datetime

    start = datetime.fromisoformat(visit["slot_start"])
    end = datetime.fromisoformat(visit["slot_end"])
    queued = {}
    for kind, before in (("24h", timedelta(hours=24)), ("2h", timedelta(hours=2))):
        at = start - before
        if at > now_utc():
            queued[kind] = await jobs.defer(jobs.visit_reminder, schedule_at=at, visit_id=visit["visit_id"], kind=kind)
    queued["outcome"] = await jobs.defer(
        jobs.visit_outcome_check, schedule_at=end + OUTCOME_CHECK_DELAY, visit_id=visit["visit_id"]
    )
    return queued


async def send_visit_reminder(visit_id: str, kind: str) -> dict:
    async with session_scope() as session:
        visit = await session.get(SiteVisit, visit_id)
        if not visit or visit.status not in ACTIVE_VISIT_STATUSES:
            return {"status": "skipped", "reason": "visit no longer active"}
        if as_utc(visit.slot_start) <= now_utc():
            return {"status": "skipped", "reason": "visit already started"}
        lead = await session.get(SalesLead, visit.lead_id)
        project = await session.get(ProjectRecord, visit.project_id)
        conv = await messaging.get_or_create_conversation(session, lead)
        when = format_dhaka(visit.slot_start)
        name = f" {lead.name}" if lead.name else ""
        text = (
            f"Reminder{name}: apnar {project.name} site visit {when}-e. Asben to? Somoy bodlate chaile janaben.\n"
            f"Reminder{name}: your site visit to {project.name} is on {when}. Reply here if you need to change it."
        )
        msg = await messaging.send_text(session, conv, text, sender="system")
        await leads.add_event(session, lead, f"reminder_{kind}", "system", {"visit_id": visit_id, "status": msg.status, "error": msg.error})
        return {"status": msg.status, "error": msg.error}


async def check_visit_outcome(visit_id: str) -> dict:
    """An hour after the slot: if nobody recorded an outcome, mark it a no-show and start the missed-visit sequence.

    The no-show sequence's first message waits another hour, so staff can still mark the visit DONE (which stops it).
    """
    async with session_scope() as session:
        visit = await session.get(SiteVisit, visit_id)
        if not visit or visit.status not in ACTIVE_VISIT_STATUSES:
            return {"status": "skipped", "reason": f"outcome already recorded ({visit.status if visit else 'missing'})"}
        if as_utc(visit.slot_end) + OUTCOME_CHECK_DELAY > now_utc() + timedelta(minutes=1):
            return {"status": "skipped", "reason": "too early"}
        from app.sales.visits import set_visit_status

        await set_visit_status(session, visit, "NO_SHOW", "system", notes="No outcome recorded an hour after the slot")
        lead = await session.get(SalesLead, visit.lead_id)
        project = await session.get(ProjectRecord, visit.project_id)
        enrollment = await followups.enroll(session, lead, "no_show", {"project": project.name})
        tenant_id, lead_id = lead.tenant_id, lead.lead_id
        next_at = as_utc(enrollment.next_run_at) if enrollment else None
        enrollment_id = enrollment.enrollment_id if enrollment else None
    if enrollment_id:
        await jobs.defer(jobs.followup_step, schedule_at=next_at, enrollment_id=enrollment_id)
    await notify_staff(tenant_id, f"No outcome recorded for visit {visit_id} (lead {lead_id}); marked no-show. Mark it DONE if they came.")
    return {"status": "no_show", "enrolled": bool(enrollment_id)}


async def after_visit_done(lead_id: str, project_name: str) -> Optional[str]:
    """Start the post-visit sequence and stop the missed-visit one."""
    async with session_scope() as session:
        lead = await session.get(SalesLead, lead_id)
        await followups.stop_enrollments(session, lead, "visit done", triggers=("no_show",))
        enrollment = await followups.enroll(session, lead, "post_visit", {"project": project_name})
        info = (enrollment.enrollment_id, as_utc(enrollment.next_run_at)) if enrollment else None
    if info:
        await jobs.defer(jobs.followup_step, schedule_at=info[1], enrollment_id=info[0])
        return info[0]
    return None


# ── Follow-ups ────────────────────────────────────────────────────────

async def schedule_enrollment(enrollment: FollowupEnrollment) -> Optional[int]:
    return await jobs.defer(jobs.followup_step, schedule_at=as_utc(enrollment.next_run_at), enrollment_id=enrollment.enrollment_id)


async def run_followup_step(enrollment_id: str) -> dict:
    async with session_scope() as session:
        due = await followups.due_step(session, enrollment_id)
        if due is None:
            return {"status": "skipped", "reason": "enrollment ended or not due"}
        enrollment, step = due
        lead = await session.get(SalesLead, enrollment.lead_id)
        if lead.stage not in OPEN_LEAD_STAGES:
            await followups.stop_enrollments(session, lead, f"stage {lead.stage}")
            return {"status": "stopped", "reason": f"stage {lead.stage}"}
        conv = await messaging.get_or_create_conversation(session, lead)
        assistant = await agent_settings.get_settings(session, lead.tenant_id)
        if agent_settings.channel_modes(assistant).get(conv.channel) == "draft_only":
            # Draft-only channels (email by default) never get automatic messages; staff write to them.
            await followups.stop_enrollments(session, lead, f"{conv.channel} is draft only")
            return {"status": "stopped", "reason": f"{conv.channel} is draft only"}
        if conv.mode == "HUMAN":
            # A person owns the chat: they decide what to send. Push the step back a day instead.
            enrollment.next_run_at = now_utc() + timedelta(days=1)
            await followups.refresh_next_followup(session, lead)
            next_at, result = as_utc(enrollment.next_run_at), {"status": "deferred", "reason": "chat owned by staff"}
        else:
            text = followups.render(step.message_template, name=lead.name, project=(enrollment.context or {}).get("project"))
            msg = await messaging.send_text(session, conv, text, sender="ai", proactive=True, whatsapp_template=step.whatsapp_template)
            await leads.add_event(session, lead, "followup_sent", "system", {
                "enrollment_id": enrollment_id, "position": step.position, "status": msg.status, "error": msg.error,
            })
            await followups.advance(session, enrollment, lead)
            next_at = as_utc(enrollment.next_run_at) if enrollment.status == "ACTIVE" else None
            result = {"status": msg.status, "error": msg.error}
    if next_at:
        await jobs.defer(jobs.followup_step, schedule_at=next_at, enrollment_id=enrollment_id)
    return result


async def sweep_stale_leads() -> dict:
    """Re-engage open leads nobody has heard from in 5 days and who have nothing scheduled."""
    cutoff = now_utc() - STALE_AFTER
    scheduled = []
    async with session_scope() as session:
        active_leads = select(FollowupEnrollment.lead_id).where(FollowupEnrollment.status == "ACTIVE")
        rows = (
            await session.execute(
                select(SalesLead).where(
                    SalesLead.stage.in_(("NEW", "QUALIFIED", "VISITED")),
                    SalesLead.last_contact_at.is_not(None),
                    SalesLead.last_contact_at < cutoff,
                    SalesLead.lead_id.not_in(active_leads),
                    leads.sales_may_message_first(),
                ).limit(200)
            )
        ).scalars().all()
        for lead in rows:
            enrollment = await followups.enroll(session, lead, "reengage")
            if enrollment:
                scheduled.append((enrollment.enrollment_id, as_utc(enrollment.next_run_at)))
    for enrollment_id, at in scheduled:
        await jobs.defer(jobs.followup_step, schedule_at=at, enrollment_id=enrollment_id)
    return {"status": "ok", "reengaged": len(scheduled)}


# ── Unit-match alerts ─────────────────────────────────────────────────

async def send_unit_match_alerts(tenant_id: str, unit_id: str) -> dict:
    """A unit came back on sale or got cheaper: tell open leads it fits (once a week per lead at most)."""
    sent, skipped = 0, 0
    async with session_scope() as session:
        unit = await session.get(PropertyUnit, unit_id)
        if not unit or unit.status != "AVAILABLE":
            return {"status": "skipped", "reason": "unit not available"}
        project = await session.get(ProjectRecord, unit.project_id)
        candidates = (
            await session.execute(
                select(SalesLead).where(
                    SalesLead.tenant_id == tenant_id,
                    SalesLead.stage.in_(OPEN_LEAD_STAGES),
                    SalesLead.budget_max_bdt.is_not(None),
                    SalesLead.budget_max_bdt >= unit.list_price_bdt,
                    leads.sales_may_message_first(),
                )
            )
        ).scalars().all()
        since = now_utc() - UNIT_ALERT_GAP
        assistant = await agent_settings.get_settings(session, tenant_id)
        for lead in candidates:
            if lead.bedrooms and unit.bedrooms and lead.bedrooms != unit.bedrooms:
                continue
            areas = [a.lower() for a in (lead.preferred_areas or [])]
            place = f"{project.name} {project.location}".lower()
            if areas and not any(a in place for a in areas):
                continue
            recent = await session.scalar(
                select(func.count()).select_from(LeadEvent).where(
                    LeadEvent.lead_id == lead.lead_id, LeadEvent.type == "unit_alert", LeadEvent.created_at >= since
                )
            )
            if recent:
                skipped += 1
                continue
            conv = await messaging.get_or_create_conversation(session, lead)
            if conv.mode == "HUMAN" or agent_settings.channel_modes(assistant).get(conv.channel) == "draft_only":
                skipped += 1
                continue
            beds = f"{unit.bedrooms}-bed " if unit.bedrooms else ""
            text = (
                f"{lead.name or ''} apnar budget-er moddhe {project.name}-e ekta {beds}unit ({unit.unit_code}) "
                f"available hoyeche: ৳{unit.list_price_bdt:,}. Dekhte chaile visit book kore dibo.\n"
                f"A {beds}unit ({unit.unit_code}) in {project.name} within your budget is now available at "
                f"৳{unit.list_price_bdt:,}. Shall I book you a visit?"
            ).strip()
            msg = await messaging.send_text(session, conv, text, sender="ai", proactive=True)
            await leads.add_event(session, lead, "unit_alert", "system", {"unit_id": unit_id, "status": msg.status, "error": msg.error})
            if msg.status in ("sent", "stored"):
                sent += 1
            else:
                skipped += 1
    return {"status": "ok", "sent": sent, "skipped": skipped}


async def unit_changed(tenant_id: str, change: units.UnitChange) -> Optional[int]:
    if change.became_available or change.price_dropped:
        return await jobs.defer(jobs.unit_match_alert, tenant_id=tenant_id, unit_id=change.unit["unit_id"])
    return None


async def release_expired_holds() -> dict:
    async with session_scope() as session:
        released = await units.release_expired_holds(session)
        tenant_of = {}
        if released:
            rows = (await session.execute(select(PropertyUnit).where(PropertyUnit.unit_id.in_(released)))).scalars().all()
            tenant_of = {u.unit_id: u.tenant_id for u in rows}
    for unit_id, tenant_id in tenant_of.items():
        await jobs.defer(jobs.unit_match_alert, tenant_id=tenant_id, unit_id=unit_id)
    return {"status": "ok", "released": len(released)}


# ── Daily digest ──────────────────────────────────────────────────────

async def build_digest(tenant_id: str) -> str:
    async with session_scope() as session:
        day_start = agent_settings.start_of_today_utc()
        yesterday = day_start - timedelta(days=1)
        new_leads = await session.scalar(
            select(func.count()).select_from(SalesLead).where(
                SalesLead.tenant_id == tenant_id, SalesLead.created_at >= yesterday, SalesLead.created_at < day_start
            )
        )
        visits_today = await session.scalar(
            select(func.count()).select_from(SiteVisit).where(
                SiteVisit.tenant_id == tenant_id, SiteVisit.status.in_(ACTIVE_VISIT_STATUSES),
                SiteVisit.slot_start >= day_start, SiteVisit.slot_start < day_start + timedelta(days=1),
            )
        )
        pending_approvals = await session.scalar(
            select(func.count()).select_from(SalesApproval).where(
                SalesApproval.tenant_id == tenant_id, SalesApproval.status == "PENDING"
            )
        )
        no_followup = await session.scalar(
            select(func.count()).select_from(SalesLead).where(
                SalesLead.tenant_id == tenant_id, SalesLead.stage.in_(OPEN_LEAD_STAGES),
                SalesLead.next_followup_at.is_(None),
            )
        )
        counts = await leads.pipeline_counts(session, tenant_id)
    pipeline = ", ".join(f"{stage.title().replace('_', ' ')} {n}" for stage, n in counts.items() if n)
    return (
        "GLG sales digest\n"
        f"New leads yesterday: {new_leads}\n"
        f"Site visits today: {visits_today}\n"
        f"Approvals waiting: {pending_approvals}\n"
        f"Open leads with no follow-up scheduled: {no_followup}\n"
        f"Pipeline: {pipeline or 'empty'}"
    )


async def send_daily_digests() -> dict:
    async with session_scope() as session:
        tenants = set((await session.execute(select(SalesLead.tenant_id).distinct())).scalars().all())
    results = {}
    for tenant_id in sorted(tenants):
        results[tenant_id] = await notify_staff(tenant_id, await build_digest(tenant_id))
    return {"status": "ok", "tenants": results}
