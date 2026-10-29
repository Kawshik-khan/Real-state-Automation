"""Follow-up sequences: enroll a lead, advance one step at a time, stop on reply or stage change."""

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales.db import now_utc
from app.sales.errors import NotFound, SalesError
from app.sales.leads import add_event, iso
from app.sales.models import (
    OPEN_LEAD_STAGES,
    SEQUENCE_TRIGGERS,
    FollowupEnrollment,
    FollowupSequence,
    FollowupStep,
    SalesLead,
)

DAY = 24 * 60

# Starting sequences a manager can edit. Bangla first line, English second, matching how GLG customers write.
DEFAULT_SEQUENCES: dict[str, dict] = {
    "new_lead": {
        "name": "New inquiry nurture",
        "steps": [
            (DAY, "Assalamu alaikum {name}! GLG Assets theke bolchi. Apnar pochonder flat khuje dite pari — "
                  "kon area ar budget-e dekhchen?\nHi {name}, GLG Assets here. Shall I shortlist flats for your area and budget?"),
            (2 * DAY, "{name}, apni chaile ei shoptahe ekta site visit book kore dite pari.\n"
                      "{name}, would you like to visit a project this week? I can book a slot for you."),
            (4 * DAY, "Notun unit ar payment plan-er update pete chaile janaben.\n"
                      "Let me know if you'd like updates on new units and payment plans."),
        ],
    },
    "post_visit": {
        "name": "After site visit",
        "steps": [
            (DAY, "{name}, {project} dekhe kemon laglo? Kono proshno thakle bolun.\n"
                  "{name}, how did you find {project}? Happy to answer any questions."),
        ],
    },
    "no_show": {
        "name": "Missed visit",
        "steps": [
            (60, "{name}, ajker visit-e apnake pai ni. Onno somoy book kore dibo?\n"
                 "{name}, we missed you at today's visit. Shall I book another time?"),
        ],
    },
    "reengage": {
        "name": "Re-engage quiet leads",
        "steps": [
            (0, "{name}, apnar flat khoja kemon cholche? Notun kichu unit eseche.\n"
                "{name}, how is your flat search going? New units have come in since we last spoke."),
        ],
    },
}


def sequence_to_dict(seq: FollowupSequence, steps: list[FollowupStep]) -> dict:
    return {
        "sequence_id": seq.sequence_id,
        "name": seq.name,
        "trigger": seq.trigger,
        "active": seq.active,
        "steps": [
            {
                "step_id": s.step_id, "position": s.position, "delay_minutes": s.delay_minutes,
                "message_template": s.message_template, "whatsapp_template": s.whatsapp_template,
            }
            for s in sorted(steps, key=lambda s: s.position)
        ],
    }


async def _steps(session: AsyncSession, sequence_id: str) -> list[FollowupStep]:
    return list(
        (
            await session.execute(
                select(FollowupStep).where(FollowupStep.sequence_id == sequence_id).order_by(FollowupStep.position)
            )
        ).scalars().all()
    )


async def list_sequences(session: AsyncSession, tenant_id: str) -> list[dict]:
    seqs = (
        await session.execute(select(FollowupSequence).where(FollowupSequence.tenant_id == tenant_id))
    ).scalars().all()
    return [sequence_to_dict(s, await _steps(session, s.sequence_id)) for s in seqs]


async def save_sequence(
    session: AsyncSession, tenant_id: str, trigger: str, name: str, steps: list[dict], active: bool = True
) -> dict:
    """Create or replace the sequence for a trigger."""
    if trigger not in SEQUENCE_TRIGGERS:
        raise SalesError("INVALID_TRIGGER", f"Trigger must be one of {', '.join(SEQUENCE_TRIGGERS)}")
    if not steps:
        raise SalesError("NO_STEPS", "A sequence needs at least one step")
    seq = (
        await session.execute(
            select(FollowupSequence).where(FollowupSequence.tenant_id == tenant_id, FollowupSequence.trigger == trigger)
        )
    ).scalar_one_or_none()
    if seq is None:
        seq = FollowupSequence(tenant_id=tenant_id, trigger=trigger, name=name, active=active)
        session.add(seq)
        await session.flush()
    else:
        seq.name, seq.active = name, active
        for old in await _steps(session, seq.sequence_id):
            await session.delete(old)
        await session.flush()
    for position, step in enumerate(steps):
        if int(step["delay_minutes"]) < 0 or not str(step["message_template"]).strip():
            raise SalesError("INVALID_STEP", "Each step needs a delay of 0 or more minutes and a message")
        session.add(FollowupStep(
            sequence_id=seq.sequence_id, position=position, delay_minutes=int(step["delay_minutes"]),
            message_template=str(step["message_template"]).strip(), whatsapp_template=step.get("whatsapp_template"),
        ))
    await session.flush()
    return sequence_to_dict(seq, await _steps(session, seq.sequence_id))


async def install_default_sequences(session: AsyncSession, tenant_id: str) -> list[dict]:
    """Create any default sequence that doesn't exist yet; existing ones are left as managers edited them."""
    existing = {s["trigger"] for s in await list_sequences(session, tenant_id)}
    created = []
    for trigger, spec in DEFAULT_SEQUENCES.items():
        if trigger in existing:
            continue
        created.append(await save_sequence(
            session, tenant_id, trigger, spec["name"],
            [{"delay_minutes": delay, "message_template": text} for delay, text in spec["steps"]],
        ))
    return created


async def enroll(
    session: AsyncSession, lead: SalesLead, trigger: str, context: Optional[dict] = None
) -> Optional[FollowupEnrollment]:
    """Start a sequence for a lead. Returns None when there is no active sequence or the lead is already in it."""
    if lead.stage not in OPEN_LEAD_STAGES:
        return None
    seq = (
        await session.execute(
            select(FollowupSequence).where(
                FollowupSequence.tenant_id == lead.tenant_id, FollowupSequence.trigger == trigger,
                FollowupSequence.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not seq:
        return None
    steps = await _steps(session, seq.sequence_id)
    if not steps:
        return None
    already = (
        await session.execute(
            select(FollowupEnrollment).where(
                FollowupEnrollment.lead_id == lead.lead_id, FollowupEnrollment.sequence_id == seq.sequence_id,
                FollowupEnrollment.status == "ACTIVE",
            )
        )
    ).scalar_one_or_none()
    if already:
        return None
    enrollment = FollowupEnrollment(
        tenant_id=lead.tenant_id, lead_id=lead.lead_id, sequence_id=seq.sequence_id, next_position=0,
        next_run_at=now_utc() + timedelta(minutes=steps[0].delay_minutes), status="ACTIVE", context=context or {},
    )
    session.add(enrollment)
    await session.flush()
    await add_event(session, lead, "followup_enrolled", "system", {"sequence": seq.name, "trigger": trigger})
    await refresh_next_followup(session, lead)
    return enrollment


async def stop_enrollments(
    session: AsyncSession, lead: SalesLead, reason: str, triggers: Optional[tuple[str, ...]] = None
) -> int:
    stmt = select(FollowupEnrollment).where(
        FollowupEnrollment.lead_id == lead.lead_id, FollowupEnrollment.status == "ACTIVE"
    )
    if triggers:
        stmt = stmt.join(FollowupSequence, FollowupSequence.sequence_id == FollowupEnrollment.sequence_id).where(
            FollowupSequence.trigger.in_(triggers)
        )
    rows = (await session.execute(stmt)).scalars().all()
    for enrollment in rows:
        enrollment.status, enrollment.stop_reason, enrollment.next_run_at = "STOPPED", reason, None
    await session.flush()
    if rows:
        await refresh_next_followup(session, lead)
    return len(rows)


async def refresh_next_followup(session: AsyncSession, lead: SalesLead) -> None:
    upcoming = (
        await session.execute(
            select(FollowupEnrollment.next_run_at).where(
                FollowupEnrollment.lead_id == lead.lead_id, FollowupEnrollment.status == "ACTIVE",
                FollowupEnrollment.next_run_at.is_not(None),
            )
        )
    ).scalars().all()
    lead.next_followup_at = min(upcoming) if upcoming else None


async def due_step(session: AsyncSession, enrollment_id: str) -> Optional[tuple[FollowupEnrollment, FollowupStep]]:
    """The step to send now, or None when the enrollment ended or isn't due yet."""
    enrollment = await session.get(FollowupEnrollment, enrollment_id)
    if not enrollment or enrollment.status != "ACTIVE" or enrollment.next_run_at is None:
        return None
    from app.sales.db import as_utc

    if as_utc(enrollment.next_run_at) > now_utc() + timedelta(seconds=30):
        return None
    steps = await _steps(session, enrollment.sequence_id)
    if enrollment.next_position >= len(steps):
        enrollment.status, enrollment.next_run_at = "DONE", None
        return None
    return enrollment, steps[enrollment.next_position]


async def advance(session: AsyncSession, enrollment: FollowupEnrollment, lead: SalesLead) -> None:
    """Mark the current step sent and schedule the next one (or finish)."""
    steps = await _steps(session, enrollment.sequence_id)
    enrollment.next_position += 1
    if enrollment.next_position >= len(steps):
        enrollment.status, enrollment.next_run_at = "DONE", None
    else:
        enrollment.next_run_at = now_utc() + timedelta(minutes=steps[enrollment.next_position].delay_minutes)
    await session.flush()
    await refresh_next_followup(session, lead)


def render(template: str, *, name: Optional[str], project: Optional[str]) -> str:
    return template.replace("{name}", name or "").replace("{project}", project or "the project").replace("  ", " ").strip()


async def active_enrollments(session: AsyncSession, lead_id: str) -> list[dict]:
    rows = (
        await session.execute(
            select(FollowupEnrollment, FollowupSequence)
            .join(FollowupSequence, FollowupSequence.sequence_id == FollowupEnrollment.sequence_id)
            .where(FollowupEnrollment.lead_id == lead_id, FollowupEnrollment.status == "ACTIVE")
        )
    ).all()
    return [
        {"enrollment_id": e.enrollment_id, "sequence": s.name, "trigger": s.trigger, "next_run_at": iso(e.next_run_at)}
        for e, s in rows
    ]


async def get_enrollment(session: AsyncSession, enrollment_id: str) -> FollowupEnrollment:
    enrollment = await session.get(FollowupEnrollment, enrollment_id)
    if not enrollment:
        raise NotFound("ENROLLMENT_NOT_FOUND", "Enrollment does not exist")
    return enrollment
