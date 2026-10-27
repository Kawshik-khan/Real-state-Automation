"""Lead pipeline: identity, profile, stages, owners, notes and history."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuthUserRecord
from app.sales.db import as_utc, now_utc
from app.sales.errors import NotFound, SalesError
from app.sales.models import (
    ACTIVE_VISIT_STATUSES,
    AI_SETTABLE_STAGES,
    LEAD_STAGES,
    OPEN_LEAD_STAGES,
    LeadEvent,
    SalesLead,
    SiteVisit,
)
from app.sales.scoring import compute_score, is_qualified


def iso(value) -> Optional[str]:
    value = as_utc(value)
    return value.isoformat() if value else None


def lead_to_dict(lead: SalesLead) -> dict:
    return {
        "lead_id": lead.lead_id,
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "channel": lead.channel,
        "source": lead.source,
        "stage": lead.stage,
        "score": lead.score,
        "budget_min_bdt": lead.budget_min_bdt,
        "budget_max_bdt": lead.budget_max_bdt,
        "preferred_areas": lead.preferred_areas or [],
        "bedrooms": lead.bedrooms,
        "timeline": lead.timeline,
        "purpose": lead.purpose,
        "owner_user_id": lead.owner_user_id,
        "next_followup_at": iso(lead.next_followup_at),
        "last_contact_at": iso(lead.last_contact_at),
        "lost_reason": lead.lost_reason,
        "version": lead.version,
        "created_at": iso(lead.created_at),
        "updated_at": iso(lead.updated_at),
    }


def event_to_dict(event: LeadEvent) -> dict:
    return {
        "event_id": event.event_id,
        "type": event.type,
        "actor": event.actor,
        "payload": event.payload or {},
        "created_at": iso(event.created_at),
    }


async def add_event(session: AsyncSession, lead: SalesLead, type_: str, actor: str, payload: Optional[dict] = None) -> None:
    session.add(LeadEvent(tenant_id=lead.tenant_id, lead_id=lead.lead_id, type=type_, actor=actor, payload=payload or {}))


async def get_lead(session: AsyncSession, tenant_id: str, lead_id: str) -> SalesLead:
    lead = await session.get(SalesLead, lead_id)
    if not lead or lead.tenant_id != tenant_id:
        raise NotFound("LEAD_NOT_FOUND", f"Lead '{lead_id}' does not exist")
    return lead


async def get_or_create_lead(
    session: AsyncSession, tenant_id: str, channel: str, external_id: str, *, name: Optional[str] = None,
    phone: Optional[str] = None, source: Optional[str] = None,
) -> tuple[SalesLead, bool]:
    lead = (
        await session.execute(
            select(SalesLead).where(
                SalesLead.tenant_id == tenant_id, SalesLead.channel == channel, SalesLead.external_id == external_id
            )
        )
    ).scalar_one_or_none()
    if lead:
        changed = False
        if name and not lead.name:
            lead.name, changed = name, True
        if phone and not lead.phone:
            lead.phone, changed = phone, True
        if changed:
            await _rescore(session, lead)
        return lead, False
    lead = SalesLead(
        tenant_id=tenant_id, channel=channel, external_id=external_id, name=name, phone=phone,
        source=source or channel, stage="NEW", preferred_areas=[],
    )
    session.add(lead)
    await session.flush()
    await _rescore(session, lead)
    await add_event(session, lead, "created", "system", {"channel": channel, "source": lead.source})
    await auto_assign_owner(session, lead)
    return lead, True


async def _has_active_visit(session: AsyncSession, lead: SalesLead) -> bool:
    count = await session.scalar(
        select(func.count()).select_from(SiteVisit).where(
            SiteVisit.lead_id == lead.lead_id, SiteVisit.status.in_(ACTIVE_VISIT_STATUSES)
        )
    )
    return bool(count)


async def _rescore(session: AsyncSession, lead: SalesLead) -> None:
    lead.score = compute_score(
        budget_max_bdt=lead.budget_max_bdt,
        preferred_areas=lead.preferred_areas,
        bedrooms=lead.bedrooms,
        timeline=lead.timeline,
        phone=lead.phone,
        has_active_visit=await _has_active_visit(session, lead),
    )


PROFILE_FIELDS = {"name", "phone", "email", "budget_min_bdt", "budget_max_bdt", "preferred_areas", "bedrooms", "timeline", "purpose"}


async def update_profile(session: AsyncSession, lead: SalesLead, fields: dict, actor: str) -> dict:
    """Update what we know about the buyer; rescore; move NEW → QUALIFIED when enough is known."""
    changes = {}
    for key, value in fields.items():
        if key not in PROFILE_FIELDS or value is None:
            continue
        if key == "preferred_areas":
            value = sorted({str(a).strip() for a in value if str(a).strip()})
        if getattr(lead, key) != value:
            setattr(lead, key, value)
            changes[key] = value
    if lead.budget_min_bdt and lead.budget_max_bdt and lead.budget_min_bdt > lead.budget_max_bdt:
        raise SalesError("INVALID_BUDGET", "Minimum budget is above the maximum")
    await _rescore(session, lead)
    if changes:
        await add_event(session, lead, "profile_updated", actor, changes)
    if lead.stage == "NEW" and is_qualified(
        budget_max_bdt=lead.budget_max_bdt, preferred_areas=lead.preferred_areas, bedrooms=lead.bedrooms
    ):
        await change_stage(session, lead, "QUALIFIED", actor, by_ai=actor == "ai")
    await session.flush()
    return {"changed": changes, "score": lead.score, "stage": lead.stage}


async def change_stage(
    session: AsyncSession, lead: SalesLead, stage: str, actor: str, *, by_ai: bool, lost_reason: Optional[str] = None
) -> None:
    if stage not in LEAD_STAGES:
        raise SalesError("INVALID_STAGE", f"Stage must be one of {', '.join(LEAD_STAGES)}")
    if stage == lead.stage:
        return
    if by_ai:
        # The assistant only moves a lead forward through the early stages; people own everything after.
        if stage not in AI_SETTABLE_STAGES or lead.stage not in AI_SETTABLE_STAGES:
            raise SalesError("STAGE_NOT_ALLOWED", "Only a sales agent can move a lead to this stage", 403)
        if AI_SETTABLE_STAGES.index(stage) < AI_SETTABLE_STAGES.index(lead.stage):
            return
    if stage == "LOST" and not (lost_reason or "").strip():
        raise SalesError("LOST_REASON_REQUIRED", "Give a reason when marking a lead lost")
    previous = lead.stage
    lead.stage = stage
    lead.lost_reason = lost_reason.strip() if stage == "LOST" and lost_reason else None
    await add_event(session, lead, "stage_change", actor, {"from": previous, "to": stage, "lost_reason": lead.lost_reason})
    if stage not in OPEN_LEAD_STAGES:
        lead.next_followup_at = None
        from app.sales.followups import stop_enrollments

        await stop_enrollments(session, lead, f"stage {stage}")
    await session.flush()


async def auto_assign_owner(session: AsyncSession, lead: SalesLead) -> Optional[str]:
    """Give the lead to the active sales agent with the fewest open leads (round robin by load).

    Staff accounts carry their own tenant label (one company per deployment), so every active agent is eligible.
    """
    if lead.owner_user_id:
        return lead.owner_user_id
    agents = (
        await session.execute(
            select(AuthUserRecord.id).where(AuthUserRecord.role == "agent", AuthUserRecord.is_active.is_(True))
        )
    ).scalars().all()
    if not agents:
        return None
    loads = dict(
        (
            await session.execute(
                select(SalesLead.owner_user_id, func.count())
                .where(SalesLead.owner_user_id.in_(agents), SalesLead.stage.in_(OPEN_LEAD_STAGES))
                .group_by(SalesLead.owner_user_id)
            )
        ).all()
    )
    owner = min(sorted(agents), key=lambda a: loads.get(a, 0))
    lead.owner_user_id = owner
    await add_event(session, lead, "owner_assigned", "system", {"owner_user_id": owner})
    return owner


async def assign_owner(session: AsyncSession, lead: SalesLead, owner_user_id: Optional[str], actor: str) -> None:
    lead.owner_user_id = owner_user_id
    await add_event(session, lead, "owner_assigned", actor, {"owner_user_id": owner_user_id})
    await session.flush()


async def add_note(session: AsyncSession, lead: SalesLead, text: str, actor: str) -> None:
    if not text.strip():
        raise SalesError("EMPTY_NOTE", "Note text is empty")
    await add_event(session, lead, "note", actor, {"text": text.strip()})
    await session.flush()


def touch_contact(lead: SalesLead) -> None:
    lead.last_contact_at = now_utc()


async def list_leads(
    session: AsyncSession, tenant_id: str, *, stage: Optional[str] = None, owner_user_id: Optional[str] = None,
    search: Optional[str] = None, limit: int = 200,
) -> list[dict]:
    stmt = select(SalesLead).where(SalesLead.tenant_id == tenant_id)
    if stage:
        stmt = stmt.where(SalesLead.stage == stage)
    if owner_user_id:
        stmt = stmt.where(SalesLead.owner_user_id == owner_user_id)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(func.lower(func.coalesce(SalesLead.name, "") + " " + func.coalesce(SalesLead.phone, "")).like(like))
    stmt = stmt.order_by(SalesLead.updated_at.desc()).limit(min(limit, 500))
    return [lead_to_dict(lead) for lead in (await session.execute(stmt)).scalars().all()]


async def lead_events(session: AsyncSession, lead_id: str, limit: int = 100) -> list[dict]:
    rows = (
        await session.execute(
            select(LeadEvent).where(LeadEvent.lead_id == lead_id).order_by(LeadEvent.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [event_to_dict(e) for e in rows]


async def pipeline_counts(session: AsyncSession, tenant_id: str) -> dict:
    rows = (
        await session.execute(
            select(SalesLead.stage, func.count()).where(SalesLead.tenant_id == tenant_id).group_by(SalesLead.stage)
        )
    ).all()
    counts = {stage: 0 for stage in LEAD_STAGES}
    counts.update(dict(rows))
    return counts
