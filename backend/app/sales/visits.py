"""Site-visit slots and bookings. The assistant may only book a real, free slot from ``visit_slots``."""

from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProjectRecord
from app.sales.db import DHAKA, as_utc, format_dhaka, now_utc
from app.sales.errors import Conflict, NotFound, SalesError
from app.sales.leads import add_event, change_stage, iso
from app.sales.models import ACTIVE_VISIT_STATUSES, VISIT_STATUSES, SalesLead, SiteVisit, VisitSlot

MIN_LEAD_TIME = timedelta(hours=2)
BOOKING_HORIZON_DAYS = 21


def slot_to_dict(slot: VisitSlot) -> dict:
    return {
        "slot_id": slot.slot_id,
        "project_id": slot.project_id,
        "weekday": slot.weekday,
        "start_time": slot.start_time,
        "duration_minutes": slot.duration_minutes,
        "capacity": slot.capacity,
        "active": slot.active,
    }


def visit_to_dict(visit: SiteVisit, project: Optional[ProjectRecord] = None, lead: Optional[SalesLead] = None) -> dict:
    return {
        "visit_id": visit.visit_id,
        "lead_id": visit.lead_id,
        "lead_name": lead.name if lead else None,
        "lead_phone": lead.phone if lead else None,
        "project_id": visit.project_id,
        "project_name": project.name if project else None,
        "slot_start": iso(visit.slot_start),
        "slot_end": iso(visit.slot_end),
        "slot_label": format_dhaka(visit.slot_start),
        "status": visit.status,
        "assigned_user_id": visit.assigned_user_id,
        "booked_by": visit.booked_by,
        "outcome_notes": visit.outcome_notes,
        "version": visit.version,
    }


def _parse_hhmm(value: str) -> time:
    try:
        hours, minutes = value.split(":")
        return time(int(hours), int(minutes))
    except (ValueError, AttributeError):
        raise SalesError("INVALID_TIME", "Start time must be HH:MM (24-hour)")


async def create_slot(session: AsyncSession, tenant_id: str, fields: dict) -> dict:
    project = await session.get(ProjectRecord, fields["project_id"])
    if not project:
        raise NotFound("PROJECT_NOT_FOUND", f"Project '{fields['project_id']}' does not exist")
    weekday = int(fields["weekday"])
    if not 0 <= weekday <= 6:
        raise SalesError("INVALID_WEEKDAY", "Weekday must be 0 (Monday) to 6 (Sunday)")
    _parse_hhmm(fields["start_time"])
    slot = VisitSlot(
        tenant_id=tenant_id,
        project_id=fields["project_id"],
        weekday=weekday,
        start_time=fields["start_time"],
        duration_minutes=int(fields.get("duration_minutes", 60)),
        capacity=max(1, int(fields.get("capacity", 1))),
        active=bool(fields.get("active", True)),
    )
    session.add(slot)
    await session.flush()
    return slot_to_dict(slot)


async def list_slots(session: AsyncSession, tenant_id: str, project_id: Optional[str] = None) -> list[dict]:
    stmt = select(VisitSlot).where(VisitSlot.tenant_id == tenant_id)
    if project_id:
        stmt = stmt.where(VisitSlot.project_id == project_id)
    rows = (await session.execute(stmt.order_by(VisitSlot.weekday, VisitSlot.start_time))).scalars().all()
    return [slot_to_dict(s) for s in rows]


async def delete_slot(session: AsyncSession, tenant_id: str, slot_id: str) -> None:
    slot = await session.get(VisitSlot, slot_id)
    if not slot or slot.tenant_id != tenant_id:
        raise NotFound("SLOT_NOT_FOUND", "Slot does not exist")
    slot.active = False
    await session.flush()


def _occurrence(day: date, slot: VisitSlot) -> tuple[datetime, datetime]:
    start_local = datetime.combine(day, _parse_hhmm(slot.start_time), tzinfo=DHAKA)
    start = start_local.astimezone(as_utc(now_utc()).tzinfo)
    return start, start + timedelta(minutes=slot.duration_minutes)


async def _booked_count(session: AsyncSession, project_id: str, start: datetime) -> int:
    return await session.scalar(
        select(func.count()).select_from(SiteVisit).where(
            SiteVisit.project_id == project_id,
            SiteVisit.slot_start == start,
            SiteVisit.status.in_(ACTIVE_VISIT_STATUSES),
        )
    ) or 0


async def free_slots(
    session: AsyncSession, tenant_id: str, project_id: str, *, from_date: Optional[date] = None, days: int = 14,
    limit: int = 6,
) -> list[dict]:
    """Upcoming slot occurrences with seats left, soonest first."""
    slots = (
        await session.execute(
            select(VisitSlot).where(
                VisitSlot.tenant_id == tenant_id, VisitSlot.project_id == project_id, VisitSlot.active.is_(True)
            )
        )
    ).scalars().all()
    if not slots:
        return []
    earliest = now_utc() + MIN_LEAD_TIME
    first_day = max(from_date or earliest.astimezone(DHAKA).date(), earliest.astimezone(DHAKA).date())
    results = []
    for offset in range(min(days, BOOKING_HORIZON_DAYS)):
        day = first_day + timedelta(days=offset)
        for slot in sorted((s for s in slots if s.weekday == day.weekday()), key=lambda s: s.start_time):
            start, end = _occurrence(day, slot)
            if start < earliest:
                continue
            seats_left = slot.capacity - await _booked_count(session, project_id, start)
            if seats_left > 0:
                results.append({
                    "slot_start": start.isoformat(),
                    "slot_end": end.isoformat(),
                    "label": format_dhaka(start),
                    "seats_left": seats_left,
                })
            if len(results) >= limit:
                return results
    return results


async def _matching_slot(session: AsyncSession, tenant_id: str, project_id: str, start: datetime) -> VisitSlot:
    local = start.astimezone(DHAKA)
    hhmm = local.strftime("%H:%M")
    slot = (
        await session.execute(
            select(VisitSlot)
            .where(
                VisitSlot.tenant_id == tenant_id, VisitSlot.project_id == project_id, VisitSlot.active.is_(True),
                VisitSlot.weekday == local.weekday(), VisitSlot.start_time == hhmm,
            )
            .with_for_update()
        )
    ).scalars().first()
    if not slot:
        raise Conflict("SLOT_NOT_OFFERED", "That time is not a visit slot for this project; offer one from free_slots")
    return slot


async def book_visit(
    session: AsyncSession, lead: SalesLead, project_id: str, slot_start: datetime, *, booked_by: str,
    idempotency_key: Optional[str] = None,
) -> tuple[dict, bool]:
    """Book a visit. Returns (visit, created). A repeated idempotency key returns the first booking."""
    if idempotency_key:
        existing = (
            await session.execute(select(SiteVisit).where(SiteVisit.idempotency_key == idempotency_key))
        ).scalar_one_or_none()
        if existing:
            return visit_to_dict(existing, await session.get(ProjectRecord, existing.project_id), lead), False
    project = await session.get(ProjectRecord, project_id)
    if not project:
        raise NotFound("PROJECT_NOT_FOUND", f"Project '{project_id}' does not exist")
    start = as_utc(slot_start)
    if start < now_utc() + MIN_LEAD_TIME:
        raise SalesError("SLOT_TOO_SOON", "Visits must be booked at least 2 hours ahead")
    if start > now_utc() + timedelta(days=BOOKING_HORIZON_DAYS):
        raise SalesError("SLOT_TOO_FAR", f"Visits can be booked up to {BOOKING_HORIZON_DAYS} days ahead")
    slot = await _matching_slot(session, lead.tenant_id, project_id, start)
    active = (
        await session.execute(
            select(SiteVisit).where(
                SiteVisit.lead_id == lead.lead_id, SiteVisit.project_id == project_id,
                SiteVisit.status.in_(ACTIVE_VISIT_STATUSES),
            )
        )
    ).scalars().first()
    if active:
        raise Conflict(
            "VISIT_ALREADY_BOOKED",
            f"This customer already has a visit to {project.name} on {format_dhaka(active.slot_start)}; reschedule it instead",
        )
    if await _booked_count(session, project_id, start) >= slot.capacity:
        raise Conflict("SLOT_FULL", "That slot is full; offer another from free_slots")
    visit = SiteVisit(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        project_id=project_id,
        slot_start=start,
        slot_end=start + timedelta(minutes=slot.duration_minutes),
        status="BOOKED",
        assigned_user_id=lead.owner_user_id,
        idempotency_key=idempotency_key,
        booked_by=booked_by,
    )
    session.add(visit)
    await session.flush()
    await add_event(session, lead, "visit_booked", booked_by, {
        "visit_id": visit.visit_id, "project_id": project_id, "slot_start": start.isoformat(),
    })
    if lead.stage in ("NEW", "QUALIFIED"):
        await change_stage(session, lead, "VISIT_BOOKED", booked_by, by_ai=booked_by == "ai")
    from app.sales.leads import _rescore

    await _rescore(session, lead)
    await session.flush()
    return visit_to_dict(visit, project, lead), True


async def get_visit(session: AsyncSession, tenant_id: str, visit_id: str) -> SiteVisit:
    visit = await session.get(SiteVisit, visit_id)
    if not visit or visit.tenant_id != tenant_id:
        raise NotFound("VISIT_NOT_FOUND", "Visit does not exist")
    return visit


async def set_visit_status(
    session: AsyncSession, visit: SiteVisit, status: str, actor: str, notes: Optional[str] = None
) -> dict:
    if status not in VISIT_STATUSES:
        raise SalesError("INVALID_STATUS", f"Status must be one of {', '.join(VISIT_STATUSES)}")
    lead = await session.get(SalesLead, visit.lead_id)
    previous = visit.status
    visit.status = status
    if notes:
        visit.outcome_notes = notes
    await add_event(session, lead, f"visit_{status.lower()}", actor, {"visit_id": visit.visit_id, "from": previous})
    if status == "DONE" and lead.stage in ("NEW", "QUALIFIED", "VISIT_BOOKED"):
        await change_stage(session, lead, "VISITED", actor, by_ai=False)
    await session.flush()
    return visit_to_dict(visit, await session.get(ProjectRecord, visit.project_id), lead)


async def reschedule_visit(
    session: AsyncSession, visit: SiteVisit, new_start: datetime, actor: str
) -> dict:
    if visit.status not in ACTIVE_VISIT_STATUSES:
        raise Conflict("VISIT_NOT_ACTIVE", f"This visit is {visit.status} and can't be moved")
    lead = await session.get(SalesLead, visit.lead_id)
    visit.status = "CANCELLED"
    await session.flush()
    try:
        new_visit, _ = await book_visit(session, lead, visit.project_id, new_start, booked_by=actor)
    except SalesError:
        visit.status = "BOOKED"
        await session.flush()
        raise
    await add_event(session, lead, "visit_rescheduled", actor, {"from_visit": visit.visit_id, "to_visit": new_visit["visit_id"]})
    return new_visit


async def list_visits(
    session: AsyncSession, tenant_id: str, *, start: Optional[datetime] = None, end: Optional[datetime] = None,
    status: Optional[str] = None, lead_id: Optional[str] = None,
) -> list[dict]:
    stmt = (
        select(SiteVisit, ProjectRecord, SalesLead)
        .join(ProjectRecord, ProjectRecord.project_id == SiteVisit.project_id)
        .join(SalesLead, SalesLead.lead_id == SiteVisit.lead_id)
        .where(SiteVisit.tenant_id == tenant_id)
    )
    if start:
        stmt = stmt.where(SiteVisit.slot_start >= start)
    if end:
        stmt = stmt.where(SiteVisit.slot_start < end)
    if status:
        stmt = stmt.where(SiteVisit.status == status)
    if lead_id:
        stmt = stmt.where(SiteVisit.lead_id == lead_id)
    rows = (await session.execute(stmt.order_by(SiteVisit.slot_start))).all()
    return [visit_to_dict(v, p, lead) for v, p, lead in rows]
