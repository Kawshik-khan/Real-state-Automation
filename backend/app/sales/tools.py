"""Governed tools: the assistant's only way to read or change sales data.

Tenant, lead and conversation come from the turn context, never from model arguments. Each handler opens its own
session, so a refused or failed tool call changes nothing. Business refusals come back as data
(``{"refused": CODE, "message": ...}``) so the model can explain them and offer alternatives.

``request_unit_hold`` and ``request_price_exception`` are Tier 2: they only create a request row. The decision that
changes a unit or a price is made by a person through the approvals API.
"""

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.sales import approvals, followups, leads, messaging, units, visits
from app.sales.db import session_scope
from app.sales.errors import SalesError
from app.sales.models import PaymentPlan, SalesConversation
from app.tools.governance import GovernedTool, ToolAuthorityTier, ToolGovernanceService

sales_tools = ToolGovernanceService()


def _refused(err: SalesError) -> dict:
    return {"refused": err.code, "message": err.message}


async def _lead(session, ctx: dict):
    return await leads.get_lead(session, ctx["tenant_id"], ctx["lead_id"])


# ── Read-only ─────────────────────────────────────────────────────────

class SearchUnitsInput(BaseModel):
    area: Optional[str] = Field(None, max_length=80, description="Area or project name, e.g. 'Gulshan'")
    project_id: Optional[str] = Field(None, max_length=128)
    bedrooms: Optional[int] = Field(None, ge=1, le=10)
    budget_min_bdt: Optional[int] = Field(None, ge=0)
    budget_max_bdt: Optional[int] = Field(None, ge=0, description="Whole taka, e.g. 12000000 for 1.2 crore")
    min_size_sqft: Optional[int] = Field(None, ge=0)


async def _search_units(args: SearchUnitsInput, ctx: dict) -> dict:
    async with session_scope() as session:
        found = await units.search_units(session, ctx["tenant_id"], **args.model_dump(), limit=5)
    return {"units": found, "count": len(found), "note": "Only AVAILABLE units are listed; prices are list prices in BDT."}


class GetUnitInput(BaseModel):
    unit_id: Optional[str] = Field(None, max_length=36)
    project_id: Optional[str] = Field(None, max_length=128)
    unit_code: Optional[str] = Field(None, max_length=64)


async def _get_unit(args: GetUnitInput, ctx: dict) -> dict:
    try:
        async with session_scope() as session:
            unit = await units.find_unit(session, ctx["tenant_id"], **args.model_dump())
    except SalesError as err:
        return _refused(err)
    return {"unit": unit}


class ListProjectsInput(BaseModel):
    pass


async def _list_projects(args: ListProjectsInput, ctx: dict) -> dict:
    async with session_scope() as session:
        return {"projects": await units.list_projects(session)}


class CalcPlanInput(BaseModel):
    unit_id: str = Field(..., max_length=36)
    plan_id: Optional[str] = Field(None, max_length=36)


async def _calc_payment_plan(args: CalcPlanInput, ctx: dict) -> dict:
    from sqlalchemy import select

    try:
        async with session_scope() as session:
            unit = await units.get_unit_row(session, ctx["tenant_id"], args.unit_id)
            stmt = select(PaymentPlan).where(
                PaymentPlan.tenant_id == ctx["tenant_id"], PaymentPlan.project_id == unit.project_id,
                PaymentPlan.active.is_(True),
            )
            if args.plan_id:
                stmt = stmt.where(PaymentPlan.plan_id == args.plan_id)
            plans = (await session.execute(stmt)).scalars().all()
            if not plans:
                return {"refused": "NO_PUBLISHED_PLAN", "message": "No published payment plan for this project; a sales agent must advise."}
            return {
                "unit_code": unit.unit_code,
                "unit_status": unit.status,
                "plans": [{"plan_id": p.plan_id, **units.calculate_plan(unit.list_price_bdt, p)} for p in plans],
            }
    except SalesError as err:
        return _refused(err)


class ProjectDocsInput(BaseModel):
    query: str = Field(..., min_length=2, max_length=300)
    project: Optional[str] = Field(None, max_length=128)


async def _get_project_docs(args: ProjectDocsInput, ctx: dict) -> dict:
    from app.rag.pipeline import rag

    filters = {"project": args.project} if args.project else None
    try:
        chunks = await rag.query(args.query, top_k=3, filters=filters)
    except Exception as exc:
        return {"refused": "DOCS_UNAVAILABLE", "message": f"Document search failed: {type(exc).__name__}"}
    sources = [
        {"source": c.get("filename") or c.get("doc_id") or "document", "excerpt": (c.get("content") or "")[:700]}
        for c in chunks if c.get("content")
    ]
    return {"sources": sources, "note": "Answer only from these excerpts and name the source; if they don't answer it, say a consultant will confirm."}


class FreeSlotsInput(BaseModel):
    project_id: str = Field(..., max_length=128)
    from_date: Optional[date] = None


async def _free_visit_slots(args: FreeSlotsInput, ctx: dict) -> dict:
    async with session_scope() as session:
        slots = await visits.free_slots(session, ctx["tenant_id"], args.project_id, from_date=args.from_date)
    if not slots:
        return {"slots": [], "note": "No visit slots are set up or free for this project; hand off to a sales agent to arrange a visit."}
    return {"slots": slots, "note": "Times are Asia/Dhaka. Pass slot_start exactly as given to book_site_visit."}


# ── Safe writes ───────────────────────────────────────────────────────

class UpdateLeadInput(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=200)
    budget_min_bdt: Optional[int] = Field(None, ge=0)
    budget_max_bdt: Optional[int] = Field(None, ge=0)
    preferred_areas: Optional[list[str]] = Field(None, max_length=8)
    bedrooms: Optional[int] = Field(None, ge=1, le=10)
    timeline: Optional[str] = Field(None, max_length=60, description="When they want to buy, e.g. 'within 3 months'")
    purpose: Optional[Literal["own_use", "investment", "rental", "other"]] = None


async def _update_lead_profile(args: UpdateLeadInput, ctx: dict) -> dict:
    try:
        async with session_scope() as session:
            lead = await _lead(session, ctx)
            result = await leads.update_profile(session, lead, args.model_dump(exclude_none=True), "ai")
    except SalesError as err:
        return _refused(err)
    return result


class BookVisitInput(BaseModel):
    project_id: str = Field(..., max_length=128)
    slot_start: datetime = Field(..., description="Exactly a slot_start returned by free_visit_slots")

    @field_validator("slot_start")
    @classmethod
    def needs_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("slot_start must include a timezone offset; copy it from free_visit_slots")
        return value


async def _book_site_visit(args: BookVisitInput, ctx: dict) -> dict:
    key = f"{ctx['lead_id']}:{args.project_id}:{args.slot_start.isoformat()}"
    try:
        async with session_scope() as session:
            lead = await _lead(session, ctx)
            visit, created = await visits.book_visit(
                session, lead, args.project_id, args.slot_start, booked_by="ai", idempotency_key=key
            )
            if created:
                await followups.stop_enrollments(session, lead, "visit booked", triggers=("new_lead", "reengage"))
    except SalesError as err:
        return _refused(err)
    if created:
        from app.sales import workflows

        await workflows.schedule_visit_jobs(visit)
    return {"visit": visit, "already_booked": not created}


class ChangeVisitInput(BaseModel):
    visit_id: str = Field(..., max_length=36)
    action: Literal["reschedule", "cancel"]
    new_slot_start: Optional[datetime] = None

    @model_validator(mode="after")
    def slot_for_reschedule(self):
        if self.action == "reschedule" and (self.new_slot_start is None or self.new_slot_start.tzinfo is None):
            raise ValueError("reschedule needs new_slot_start with a timezone, from free_visit_slots")
        return self


async def _reschedule_or_cancel_visit(args: ChangeVisitInput, ctx: dict) -> dict:
    try:
        async with session_scope() as session:
            visit = await visits.get_visit(session, ctx["tenant_id"], args.visit_id)
            if visit.lead_id != ctx["lead_id"]:
                return {"refused": "NOT_THIS_CUSTOMER", "message": "That visit belongs to another customer"}
            if args.action == "cancel":
                result = await visits.set_visit_status(session, visit, "CANCELLED", "ai")
                return {"visit": result}
            result = await visits.reschedule_visit(session, visit, args.new_slot_start, "ai")
    except SalesError as err:
        return _refused(err)
    from app.sales import workflows

    await workflows.schedule_visit_jobs(result)
    return {"visit": result}


class HandoffInput(BaseModel):
    reason: str = Field(..., min_length=3, max_length=300)


async def _handoff_to_agent(args: HandoffInput, ctx: dict) -> dict:
    async with session_scope() as session:
        conv = await session.get(SalesConversation, ctx["conversation_id"])
        lead = await _lead(session, ctx)
        owner = await leads.auto_assign_owner(session, lead)
        await messaging.set_mode(session, conv, "HUMAN", "ai", reason=args.reason)
        conv.assigned_user_id = owner
    from app.sales import workflows

    await workflows.notify_staff(ctx["tenant_id"], f"Handoff: lead {ctx['lead_id']} needs a person — {args.reason}")
    return {"handed_off": True, "owner_user_id": owner, "note": "Tell the customer a consultant will reply; stop answering."}


class UnitHoldInput(BaseModel):
    unit_id: str = Field(..., max_length=36)
    note: str = Field("", max_length=300)


async def _request_unit_hold(args: UnitHoldInput, ctx: dict) -> dict:
    try:
        async with session_scope() as session:
            lead = await _lead(session, ctx)
            approval = await approvals.request_unit_hold(session, lead, args.unit_id, args.note, "ai")
    except SalesError as err:
        return _refused(err)
    from app.sales import workflows

    await workflows.notify_staff(ctx["tenant_id"], f"Approval needed: hold unit {approval['unit_code']} for lead {ctx['lead_id']}")
    return {"approval": approval, "note": "The hold is NOT granted yet. Tell the customer a manager will confirm."}


class PriceExceptionInput(BaseModel):
    unit_id: Optional[str] = Field(None, max_length=36)
    requested_price_bdt: Optional[int] = Field(None, ge=0)
    request: str = Field(..., min_length=3, max_length=500, description="What the customer asked for, in their words")


async def _request_price_exception(args: PriceExceptionInput, ctx: dict) -> dict:
    try:
        async with session_scope() as session:
            lead = await _lead(session, ctx)
            approval = await approvals.request_price_exception(
                session, lead, unit_id=args.unit_id, requested_price_bdt=args.requested_price_bdt,
                request=args.request, requested_by="ai",
            )
    except SalesError as err:
        return _refused(err)
    from app.sales import workflows

    await workflows.notify_staff(ctx["tenant_id"], f"Price request from lead {ctx['lead_id']}: {args.request[:120]}")
    return {"approval": approval, "note": "Nothing is approved. Do not mention any discount; say a manager will get back to them."}


TOOL_SPECS: list[tuple[str, str, ToolAuthorityTier, type[BaseModel], Any]] = [
    ("list_projects", "List GLG projects with their locations.", ToolAuthorityTier.TIER_1_READ_ONLY, ListProjectsInput, _list_projects),
    ("search_units", "Find AVAILABLE units by area, project, bedrooms, budget (BDT) or size. Use before naming any unit or price.", ToolAuthorityTier.TIER_1_READ_ONLY, SearchUnitsInput, _search_units),
    ("get_unit", "Live status and list price of one unit, by unit_id or project_id + unit_code.", ToolAuthorityTier.TIER_1_READ_ONLY, GetUnitInput, _get_unit),
    ("calc_payment_plan", "Split a unit's list price by the project's published payment plans.", ToolAuthorityTier.TIER_1_READ_ONLY, CalcPlanInput, _calc_payment_plan),
    ("get_project_docs", "Search approved project documents (brochures, floor plans, approvals, FAQs).", ToolAuthorityTier.TIER_1_READ_ONLY, ProjectDocsInput, _get_project_docs),
    ("free_visit_slots", "Upcoming free site-visit slots for a project.", ToolAuthorityTier.TIER_1_READ_ONLY, FreeSlotsInput, _free_visit_slots),
    ("update_lead_profile", "Save what the customer told you: name, phone, budget (BDT), areas, bedrooms, timeline, purpose.", ToolAuthorityTier.TIER_2_MUTATING_SAFE, UpdateLeadInput, _update_lead_profile),
    ("book_site_visit", "Book a site visit into a free slot from free_visit_slots.", ToolAuthorityTier.TIER_2_MUTATING_SAFE, BookVisitInput, _book_site_visit),
    ("reschedule_or_cancel_visit", "Move or cancel this customer's own visit.", ToolAuthorityTier.TIER_2_MUTATING_SAFE, ChangeVisitInput, _reschedule_or_cancel_visit),
    ("handoff_to_agent", "Pass the chat to a human sales agent. Use for negotiation, legal questions, complaints, or anything you can't answer from tools.", ToolAuthorityTier.TIER_2_MUTATING_SAFE, HandoffInput, _handoff_to_agent),
    ("request_unit_hold", "Ask a manager to hold an available unit for this customer. Does not hold it.", ToolAuthorityTier.TIER_2_MUTATING_SAFE, UnitHoldInput, _request_unit_hold),
    ("request_price_exception", "Pass a discount or custom payment request to a manager. Never promise it.", ToolAuthorityTier.TIER_2_MUTATING_SAFE, PriceExceptionInput, _request_price_exception),
]

for _name, _desc, _tier, _schema, _handler in TOOL_SPECS:
    sales_tools.register(GovernedTool(name=_name, description=_desc, tier=_tier, input_schema=_schema, handler=_handler))


def openai_tool_definitions(only: Optional[set[str]] = None) -> list[dict]:
    """Tool schemas in the OpenAI function-calling format (optionally a subset)."""
    defs = []
    for name, desc, _tier, schema, _handler in TOOL_SPECS:
        if only is not None and name not in only:
            continue
        params = schema.model_json_schema()
        params.pop("title", None)
        defs.append({"type": "function", "function": {"name": name, "description": desc, "parameters": params}})
    return defs
