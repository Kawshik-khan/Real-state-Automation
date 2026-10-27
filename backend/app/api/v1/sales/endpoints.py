"""Sales pipeline API for the dashboard (staff) and the website chat widget.

Roles: everyone signed in can read; agents work leads, visits and chats; managers and admins also edit inventory,
slots, plans, sequences and assistant settings, and decide approvals.
"""

from datetime import date, datetime, time, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import require_roles
from app.models.user import UserRole
from app.sales import (
    agent_settings,
    approvals,
    followups,
    leads,
    messaging,
    shadow,
    units,
    visits,
    workflows,
)
from app.sales.db import DHAKA, get_sales_session
from app.sales.errors import SalesError

router = APIRouter()

READERS = [UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT, UserRole.DEVELOPER, UserRole.VIEWER, UserRole.SERVICE]
AGENTS = [UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT, UserRole.SERVICE]
MANAGERS = [UserRole.ADMIN, UserRole.MANAGER, UserRole.SERVICE]

can_read = require_roles(READERS)
can_work = require_roles(AGENTS)
can_manage = require_roles(MANAGERS)


def _tenant(user: dict) -> str:
    """GLG runs one company per deployment. Channel webhooks can only know DEFAULT_TENANT_ID, while staff accounts
    are seeded with their own tenant label, so staff always work in the deployment's tenant."""
    from app.config import settings

    return settings.default_tenant_id


def _actor(user: dict) -> str:
    return str(user.get("sub") or user.get("email") or "staff")


# ── Overview ──────────────────────────────────────────────────────────

@router.get("/overview", summary="Pipeline counts, today's visits, approvals and assistant health")
async def overview(user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    tenant = _tenant(user)
    today = datetime.combine(datetime.now(DHAKA).date(), time(0), tzinfo=DHAKA)
    settings_row = await agent_settings.get_settings(session, tenant)
    return {
        "pipeline": await leads.pipeline_counts(session, tenant),
        "visits_today": await visits.list_visits(session, tenant, start=today, end=today + timedelta(days=1)),
        "pending_approvals": len(await approvals.list_approvals(session, tenant)),
        "drafts": await messaging.draft_stats(session, tenant),
        "assistant": agent_settings.settings_to_dict(settings_row),
        "tokens_used_today": await agent_settings.tokens_used_today(session, tenant),
    }


# ── Projects, units, plans, slots ─────────────────────────────────────

@router.get("/projects")
async def get_projects(user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    return {"projects": await units.list_projects(session)}


@router.get("/units")
async def get_units(
    project_id: Optional[str] = None, status: Optional[str] = None,
    user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session),
):
    return {"units": await units.list_units(session, _tenant(user), project_id=project_id, status=status)}


class UnitCreate(BaseModel):
    project_id: str = Field(..., max_length=128)
    unit_code: str = Field(..., min_length=1, max_length=64)
    list_price_bdt: int = Field(..., gt=0)
    floor: Optional[int] = None
    bedrooms: Optional[int] = Field(None, ge=0, le=20)
    bathrooms: Optional[int] = Field(None, ge=0, le=20)
    size_sqft: Optional[int] = Field(None, gt=0)
    facing: Optional[str] = Field(None, max_length=32)
    status: Literal["AVAILABLE", "HELD", "BOOKED", "SOLD"] = "AVAILABLE"
    notes: Optional[str] = Field(None, max_length=1000)


@router.post("/units", status_code=201)
async def post_unit(body: UnitCreate, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    unit = await units.create_unit(session, _tenant(user), body.model_dump(exclude_none=True), _actor(user))
    await session.commit()
    if unit["status"] == "AVAILABLE":
        await workflows.unit_changed(_tenant(user), units.UnitChange(unit=unit, became_available=True))
    return {"unit": unit}


class UnitUpdate(BaseModel):
    version: Optional[int] = Field(None, description="The version you loaded; a newer edit makes this fail with 409")
    unit_code: Optional[str] = Field(None, min_length=1, max_length=64)
    list_price_bdt: Optional[int] = Field(None, gt=0)
    floor: Optional[int] = None
    bedrooms: Optional[int] = Field(None, ge=0, le=20)
    bathrooms: Optional[int] = Field(None, ge=0, le=20)
    size_sqft: Optional[int] = Field(None, gt=0)
    facing: Optional[str] = Field(None, max_length=32)
    status: Optional[Literal["AVAILABLE", "HELD", "BOOKED", "SOLD"]] = None
    notes: Optional[str] = Field(None, max_length=1000)


@router.patch("/units/{unit_id}")
async def patch_unit(
    unit_id: str, body: UnitUpdate, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)
):
    fields = body.model_dump(exclude_none=True, exclude={"version"})
    change = await units.update_unit(session, _tenant(user), unit_id, fields, _actor(user), expected_version=body.version)
    await session.commit()
    alert_job = await workflows.unit_changed(_tenant(user), change)
    return {"unit": change.unit, "changed": change.changed, "unit_match_alert_queued": bool(alert_job)}


@router.get("/payment-plans")
async def get_plans(project_id: Optional[str] = None, user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    return {"plans": await units.list_plans(session, _tenant(user), project_id)}


class PlanCreate(BaseModel):
    project_id: str = Field(..., max_length=128)
    name: str = Field(..., min_length=2, max_length=128)
    booking_money_bdt: int = Field(0, ge=0)
    down_payment_pct: float = Field(0, ge=0, le=100)
    installment_months: int = Field(0, ge=0, le=240)
    active: bool = True


@router.post("/payment-plans", status_code=201)
async def post_plan(body: PlanCreate, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    return {"plan": await units.create_plan(session, _tenant(user), body.model_dump())}


@router.get("/visit-slots")
async def get_slots(project_id: Optional[str] = None, user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    return {"slots": await visits.list_slots(session, _tenant(user), project_id)}


class SlotCreate(BaseModel):
    project_id: str = Field(..., max_length=128)
    weekday: int = Field(..., ge=0, le=6, description="0 = Monday … 6 = Sunday")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    duration_minutes: int = Field(60, ge=15, le=480)
    capacity: int = Field(1, ge=1, le=50)


@router.post("/visit-slots", status_code=201)
async def post_slot(body: SlotCreate, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    return {"slot": await visits.create_slot(session, _tenant(user), body.model_dump())}


@router.delete("/visit-slots/{slot_id}")
async def remove_slot(slot_id: str, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    await visits.delete_slot(session, _tenant(user), slot_id)
    return {"deactivated": slot_id}


@router.get("/visit-slots/free")
async def get_free_slots(
    project_id: str, from_date: Optional[date] = None, user: dict = Depends(can_read),
    session: AsyncSession = Depends(get_sales_session),
):
    return {"slots": await visits.free_slots(session, _tenant(user), project_id, from_date=from_date, limit=20)}


# ── Leads ─────────────────────────────────────────────────────────────

@router.get("/leads")
async def get_leads(
    stage: Optional[str] = None, owner_user_id: Optional[str] = None, search: Optional[str] = Query(None, max_length=80),
    mine: bool = False, user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session),
):
    owner = _actor(user) if mine else owner_user_id
    return {"leads": await leads.list_leads(session, _tenant(user), stage=stage, owner_user_id=owner, search=search)}


@router.get("/leads/{lead_id}")
async def get_lead_detail(lead_id: str, user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    tenant = _tenant(user)
    lead = await leads.get_lead(session, tenant, lead_id)
    conv = await messaging.find_conversation(session, lead)
    return {
        "lead": leads.lead_to_dict(lead),
        "events": await leads.lead_events(session, lead_id),
        "visits": await visits.list_visits(session, tenant, lead_id=lead_id),
        "followups": await followups.active_enrollments(session, lead_id),
        "conversation": messaging.conversation_to_dict(conv, lead) if conv else None,
        "messages": await messaging.conversation_messages(session, conv.conversation_id, limit=50) if conv else [],
    }


class LeadCreate(BaseModel):
    """A lead staff add by hand (walk-in, phone call, referral). WhatsApp is used as the contact channel."""

    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=6, max_length=32)
    source: str = Field("walk_in", max_length=64)
    budget_max_bdt: Optional[int] = Field(None, ge=0)
    preferred_areas: Optional[list[str]] = None
    bedrooms: Optional[int] = Field(None, ge=1, le=10)
    timeline: Optional[str] = Field(None, max_length=60)


@router.post("/leads", status_code=201)
async def post_lead(body: LeadCreate, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    from app.services.whatsapp_dispatcher import clean_phone_number

    phone = clean_phone_number(body.phone)
    lead, created = await leads.get_or_create_lead(
        session, _tenant(user), "whatsapp", phone.lstrip("+"), name=body.name, phone=phone, source=body.source
    )
    await leads.update_profile(session, lead, body.model_dump(exclude_none=True, exclude={"name", "phone", "source"}), _actor(user))
    await messaging.get_or_create_conversation(session, lead)
    return {"lead": leads.lead_to_dict(lead), "created": created}


class StageChange(BaseModel):
    stage: Literal["NEW", "QUALIFIED", "VISIT_BOOKED", "VISITED", "NEGOTIATING", "BOOKING_MONEY", "WON", "LOST"]
    lost_reason: Optional[str] = Field(None, max_length=256)


@router.post("/leads/{lead_id}/stage")
async def post_stage(lead_id: str, body: StageChange, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    lead = await leads.get_lead(session, _tenant(user), lead_id)
    await leads.change_stage(session, lead, body.stage, _actor(user), by_ai=False, lost_reason=body.lost_reason)
    return {"lead": leads.lead_to_dict(lead)}


class OwnerChange(BaseModel):
    owner_user_id: Optional[str] = Field(None, max_length=128)


@router.post("/leads/{lead_id}/owner")
async def post_owner(lead_id: str, body: OwnerChange, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    lead = await leads.get_lead(session, _tenant(user), lead_id)
    await leads.assign_owner(session, lead, body.owner_user_id, _actor(user))
    return {"lead": leads.lead_to_dict(lead)}


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=200)
    budget_min_bdt: Optional[int] = Field(None, ge=0)
    budget_max_bdt: Optional[int] = Field(None, ge=0)
    preferred_areas: Optional[list[str]] = None
    excluded_areas: Optional[list[str]] = None
    must_have: Optional[list[str]] = None
    deal_breakers: Optional[list[str]] = None
    bedrooms: Optional[int] = Field(None, ge=1, le=10)
    timeline: Optional[str] = Field(None, max_length=60)
    purpose: Optional[str] = Field(None, max_length=64)
    financing: Optional[Literal["cash", "home_loan", "installments", "undecided"]] = None


@router.patch("/leads/{lead_id}")
async def patch_lead(lead_id: str, body: ProfileUpdate, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    lead = await leads.get_lead(session, _tenant(user), lead_id)
    result = await leads.update_profile(session, lead, body.model_dump(exclude_none=True), _actor(user))
    return {"lead": leads.lead_to_dict(lead), **result}


class NoteCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.post("/leads/{lead_id}/notes", status_code=201)
async def post_note(lead_id: str, body: NoteCreate, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    lead = await leads.get_lead(session, _tenant(user), lead_id)
    await leads.add_note(session, lead, body.text, _actor(user))
    return {"ok": True}


class StaffVisitCreate(BaseModel):
    project_id: str = Field(..., max_length=128)
    slot_start: datetime


@router.post("/leads/{lead_id}/visits", status_code=201)
async def post_visit(lead_id: str, body: StaffVisitCreate, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    if body.slot_start.tzinfo is None:
        raise SalesError("INVALID_TIME", "slot_start must include a timezone offset")
    lead = await leads.get_lead(session, _tenant(user), lead_id)
    visit, _ = await visits.book_visit(session, lead, body.project_id, body.slot_start, booked_by=_actor(user))
    await followups.stop_enrollments(session, lead, "visit booked", triggers=("new_lead", "reengage"))
    await session.commit()
    await workflows.schedule_visit_jobs(visit)
    return {"visit": visit}


# ── Visits ────────────────────────────────────────────────────────────

@router.get("/visits")
async def get_visits(
    start: Optional[date] = None, days: int = Query(7, ge=1, le=62), status: Optional[str] = None,
    user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session),
):
    first = datetime.combine(start or datetime.now(DHAKA).date(), time(0), tzinfo=DHAKA)
    return {"visits": await visits.list_visits(session, _tenant(user), start=first, end=first + timedelta(days=days), status=status)}


class VisitUpdate(BaseModel):
    status: Optional[Literal["CONFIRMED", "DONE", "NO_SHOW", "CANCELLED"]] = None
    new_slot_start: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2000)


@router.patch("/visits/{visit_id}")
async def patch_visit(visit_id: str, body: VisitUpdate, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    visit = await visits.get_visit(session, _tenant(user), visit_id)
    if body.new_slot_start:
        if body.new_slot_start.tzinfo is None:
            raise SalesError("INVALID_TIME", "new_slot_start must include a timezone offset")
        result = await visits.reschedule_visit(session, visit, body.new_slot_start, _actor(user))
        await session.commit()
        await workflows.schedule_visit_jobs(result)
        return {"visit": result}
    if not body.status:
        raise SalesError("NOTHING_TO_DO", "Give a status or a new_slot_start")
    result = await visits.set_visit_status(session, visit, body.status, _actor(user), body.notes)
    await session.commit()
    if body.status == "DONE":
        await workflows.after_visit_done(result["lead_id"], result["project_name"] or "")
    return {"visit": result}


# ── Approvals ─────────────────────────────────────────────────────────

@router.get("/approvals")
async def get_approvals(
    status: Optional[str] = "PENDING", user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)
):
    return {"approvals": await approvals.list_approvals(session, _tenant(user), status or None)}


class Decision(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    reason: Optional[str] = Field(None, max_length=1000)


@router.post("/approvals/{approval_id}/decision")
async def post_decision(
    approval_id: str, body: Decision, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)
):
    tenant = _tenant(user)
    hold_hours = (await agent_settings.get_settings(session, tenant)).hold_hours
    try:
        result = await approvals.decide(session, tenant, approval_id, body.decision, _actor(user), body.reason, hold_hours)
    except SalesError as err:
        if err.code == "APPROVAL_STALE":
            await session.commit()  # keep the STALE status and its audit event
        raise
    return {"approval": result}


# ── Conversations ─────────────────────────────────────────────────────

@router.get("/conversations")
async def get_conversations(
    mode: Optional[Literal["AI", "HUMAN"]] = None, user: dict = Depends(can_read),
    session: AsyncSession = Depends(get_sales_session),
):
    return {"conversations": await messaging.list_conversations(session, _tenant(user), mode=mode)}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    conv = await messaging.get_conversation(session, _tenant(user), conversation_id)
    return {"conversation": messaging.conversation_to_dict(conv), "messages": await messaging.conversation_messages(session, conv.conversation_id)}


class StaffReply(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


@router.post("/conversations/{conversation_id}/reply")
async def post_reply(conversation_id: str, body: StaffReply, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    conv = await messaging.get_conversation(session, _tenant(user), conversation_id)
    msg = await messaging.staff_reply(session, conv, body.text, _actor(user))
    return {"message": messaging.message_to_dict(msg), "conversation": messaging.conversation_to_dict(conv)}


class ModeChange(BaseModel):
    mode: Literal["AI", "HUMAN"]
    reason: Optional[str] = Field(None, max_length=256)


@router.post("/conversations/{conversation_id}/mode")
async def post_mode(conversation_id: str, body: ModeChange, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    conv = await messaging.get_conversation(session, _tenant(user), conversation_id)
    await messaging.set_mode(session, conv, body.mode, _actor(user), reason=body.reason or ("taken over" if body.mode == "HUMAN" else None))
    return {"conversation": messaging.conversation_to_dict(conv)}


class DraftRating(BaseModel):
    rating: Literal["usable", "not_usable"]


@router.post("/drafts/{message_id}/rating")
async def post_rating(message_id: str, body: DraftRating, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    return {"message": await messaging.rate_draft(session, _tenant(user), message_id, body.rating, _actor(user))}


# ── Follow-up sequences ───────────────────────────────────────────────

@router.get("/sequences")
async def get_sequences(user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    return {"sequences": await followups.list_sequences(session, _tenant(user))}


class StepIn(BaseModel):
    delay_minutes: int = Field(..., ge=0, le=60 * 24 * 60)
    message_template: str = Field(..., min_length=1, max_length=1500)
    whatsapp_template: Optional[str] = Field(None, max_length=128)


class SequenceIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    active: bool = True
    steps: list[StepIn] = Field(..., min_length=1, max_length=10)


@router.put("/sequences/{trigger}")
async def put_sequence(
    trigger: Literal["new_lead", "post_visit", "no_show", "reengage"], body: SequenceIn,
    user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session),
):
    seq = await followups.save_sequence(
        session, _tenant(user), trigger, body.name, [s.model_dump() for s in body.steps], body.active
    )
    return {"sequence": seq}


@router.post("/sequences/install-defaults")
async def install_defaults(user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    return {"created": await followups.install_default_sequences(session, _tenant(user))}


# ── Assistant settings ────────────────────────────────────────────────

@router.get("/settings")
async def get_assistant_settings(user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    tenant = _tenant(user)
    return {
        "settings": agent_settings.settings_to_dict(await agent_settings.get_settings(session, tenant)),
        "tokens_used_today": await agent_settings.tokens_used_today(session, tenant),
    }


class SettingsUpdate(BaseModel):
    mode: Optional[Literal["off", "shadow", "live"]] = None
    enabled_channels: Optional[list[str]] = None
    channel_modes: Optional[dict[str, Literal["live", "draft_only"]]] = None
    kill_switch: Optional[bool] = None
    daily_token_budget: Optional[int] = Field(None, ge=0)
    hold_hours: Optional[int] = Field(None, ge=1, le=168)
    digest_chat_id: Optional[str] = Field(None, max_length=128)


@router.patch("/settings")
async def patch_assistant_settings(body: SettingsUpdate, user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    fields = body.model_dump(exclude_unset=True)
    return {"settings": await agent_settings.update_settings(session, _tenant(user), fields, _actor(user))}


@router.post("/digest/preview")
async def digest_preview(user: dict = Depends(can_manage), session: AsyncSession = Depends(get_sales_session)):
    return {"text": await workflows.build_digest(_tenant(user))}


# ── Shadow comparison and AI quality (retiring the old pipeline) ──────

@router.get("/shadow/pairs")
async def get_shadow_pairs(
    rated: Optional[bool] = Query(None), limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session),
):
    return {"pairs": await shadow.list_pairs(session, _tenant(user), rated=rated, limit=limit)}


class PairRating(BaseModel):
    rating: Literal["better", "same", "worse"]
    note: Optional[str] = Field(None, max_length=500)


@router.post("/shadow/pairs/{pair_id}/rating")
async def post_shadow_rating(pair_id: str, body: PairRating, user: dict = Depends(can_work), session: AsyncSession = Depends(get_sales_session)):
    return {"pair": await shadow.rate_pair(session, _tenant(user), pair_id, body.rating, _actor(user), body.note)}


@router.get("/ai-quality")
async def get_ai_quality(days: int = Query(14, ge=1, le=90), user: dict = Depends(can_read), session: AsyncSession = Depends(get_sales_session)):
    from app.config import settings as app_settings
    from app.sales import entry

    report = await shadow.quality_report(session, _tenant(user), days=days)
    report["routing"] = {
        "ai_route_via_sales": entry.route(),
        "email_via_sales": app_settings.email_via_sales,
        "social_via_sales": app_settings.social_via_sales,
        "legacy_llm_safety_checks": app_settings.legacy_llm_safety_checks,
    }
    return report


@router.post("/content/drafts/run")
async def run_content_drafts(days: int = Query(7, ge=1, le=60), user: dict = Depends(can_manage)):
    """Draft marketing posts for projects with new units now (the weekly job does the same every Sunday)."""
    from app.sales.content import draft_weekly_posts

    return await draft_weekly_posts(_tenant(user), days=days)
