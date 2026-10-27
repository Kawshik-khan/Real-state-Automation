"""Unit inventory: search, live lookups, manager edits, holds and payment-plan maths."""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProjectRecord
from app.sales.db import as_utc, now_utc
from app.sales.errors import Conflict, NotFound, SalesError
from app.sales.models import UNIT_STATUSES, PaymentPlan, PropertyUnit

STALE_UNIT_DAYS = 14


def unit_to_dict(unit: PropertyUnit, project: Optional[ProjectRecord] = None) -> dict:
    updated = as_utc(unit.updated_at)
    return {
        "unit_id": unit.unit_id,
        "unit_code": unit.unit_code,
        "project_id": unit.project_id,
        "project_name": project.name if project else None,
        "location": project.location if project else None,
        "floor": unit.floor,
        "bedrooms": unit.bedrooms,
        "bathrooms": unit.bathrooms,
        "size_sqft": unit.size_sqft,
        "facing": unit.facing,
        "list_price_bdt": unit.list_price_bdt,
        "status": unit.status,
        "held_until": as_utc(unit.held_until).isoformat() if unit.held_until else None,
        "held_for_lead_id": unit.held_for_lead_id,
        "notes": unit.notes,
        "version": unit.version,
        "updated_at": updated.isoformat() if updated else None,
        # Staff haven't touched this unit for two weeks: the assistant must say availability needs confirming.
        "needs_confirmation": bool(updated and now_utc() - updated > timedelta(days=STALE_UNIT_DAYS)),
    }


async def list_projects(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(select(ProjectRecord).order_by(ProjectRecord.name))).scalars().all()
    return [
        {"project_id": p.project_id, "name": p.name, "location": p.location, "description": p.description}
        for p in rows
    ]


async def get_project(session: AsyncSession, project_id: str) -> ProjectRecord:
    project = await session.get(ProjectRecord, project_id)
    if not project:
        raise NotFound("PROJECT_NOT_FOUND", f"Project '{project_id}' does not exist")
    return project


async def search_units(
    session: AsyncSession,
    tenant_id: str,
    *,
    area: Optional[str] = None,
    project_id: Optional[str] = None,
    bedrooms: Optional[int] = None,
    budget_min_bdt: Optional[int] = None,
    budget_max_bdt: Optional[int] = None,
    min_size_sqft: Optional[int] = None,
    limit: int = 5,
) -> list[dict]:
    """Available units only, cheapest first."""
    stmt = (
        select(PropertyUnit, ProjectRecord)
        .join(ProjectRecord, ProjectRecord.project_id == PropertyUnit.project_id)
        .where(PropertyUnit.tenant_id == tenant_id, PropertyUnit.status == "AVAILABLE")
    )
    if project_id:
        stmt = stmt.where(PropertyUnit.project_id == project_id)
    if area:
        like = f"%{area.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(ProjectRecord.location).like(like), func.lower(ProjectRecord.name).like(like)))
    if bedrooms:
        stmt = stmt.where(PropertyUnit.bedrooms == bedrooms)
    if budget_max_bdt:
        stmt = stmt.where(PropertyUnit.list_price_bdt <= budget_max_bdt)
    if budget_min_bdt:
        stmt = stmt.where(PropertyUnit.list_price_bdt >= budget_min_bdt)
    if min_size_sqft:
        stmt = stmt.where(PropertyUnit.size_sqft >= min_size_sqft)
    stmt = stmt.order_by(PropertyUnit.list_price_bdt).limit(max(1, min(limit, 10)))
    rows = (await session.execute(stmt)).all()
    return [unit_to_dict(u, p) for u, p in rows]


async def get_unit_row(session: AsyncSession, tenant_id: str, unit_id: str) -> PropertyUnit:
    unit = await session.get(PropertyUnit, unit_id)
    if not unit or unit.tenant_id != tenant_id:
        raise NotFound("UNIT_NOT_FOUND", f"Unit '{unit_id}' does not exist")
    return unit


async def find_unit(
    session: AsyncSession, tenant_id: str, *, unit_id: Optional[str] = None, project_id: Optional[str] = None,
    unit_code: Optional[str] = None,
) -> dict:
    if unit_id:
        unit = await get_unit_row(session, tenant_id, unit_id)
    elif project_id and unit_code:
        unit = (
            await session.execute(
                select(PropertyUnit).where(
                    PropertyUnit.tenant_id == tenant_id,
                    PropertyUnit.project_id == project_id,
                    func.lower(PropertyUnit.unit_code) == unit_code.strip().lower(),
                )
            )
        ).scalar_one_or_none()
        if not unit:
            raise NotFound("UNIT_NOT_FOUND", f"No unit '{unit_code}' in project '{project_id}'")
    else:
        raise SalesError("INVALID_ARGS", "Give a unit_id, or a project_id with a unit_code")
    project = await session.get(ProjectRecord, unit.project_id)
    return unit_to_dict(unit, project)


async def list_units(
    session: AsyncSession, tenant_id: str, *, project_id: Optional[str] = None, status: Optional[str] = None
) -> list[dict]:
    stmt = (
        select(PropertyUnit, ProjectRecord)
        .join(ProjectRecord, ProjectRecord.project_id == PropertyUnit.project_id)
        .where(PropertyUnit.tenant_id == tenant_id)
    )
    if project_id:
        stmt = stmt.where(PropertyUnit.project_id == project_id)
    if status:
        stmt = stmt.where(PropertyUnit.status == status)
    stmt = stmt.order_by(ProjectRecord.name, PropertyUnit.unit_code)
    return [unit_to_dict(u, p) for u, p in (await session.execute(stmt)).all()]


_EDITABLE = {"unit_code", "floor", "bedrooms", "bathrooms", "size_sqft", "facing", "list_price_bdt", "status", "notes"}


def _validate_unit_fields(fields: dict) -> None:
    status = fields.get("status")
    if status is not None and status not in UNIT_STATUSES:
        raise SalesError("INVALID_STATUS", f"Status must be one of {', '.join(UNIT_STATUSES)}")
    price = fields.get("list_price_bdt")
    if price is not None and int(price) <= 0:
        raise SalesError("INVALID_PRICE", "List price must be a positive amount in BDT")


async def create_unit(session: AsyncSession, tenant_id: str, fields: dict, actor: str) -> dict:
    await get_project(session, fields["project_id"])
    _validate_unit_fields(fields)
    unit = PropertyUnit(
        tenant_id=tenant_id,
        project_id=fields["project_id"],
        updated_by=actor,
        **{k: v for k, v in fields.items() if k in _EDITABLE},
    )
    session.add(unit)
    await session.flush()
    return unit_to_dict(unit, await session.get(ProjectRecord, unit.project_id))


@dataclass
class UnitChange:
    unit: dict
    became_available: bool = False
    price_dropped: bool = False
    changed: list = field(default_factory=list)


async def update_unit(
    session: AsyncSession, tenant_id: str, unit_id: str, fields: dict, actor: str,
    expected_version: Optional[int] = None,
) -> UnitChange:
    """Manager edit. Takes effect for the assistant's very next lookup."""
    unit = await get_unit_row(session, tenant_id, unit_id)
    if expected_version is not None and unit.version != expected_version:
        raise Conflict("STALE_VERSION", "Someone changed this unit since you loaded it; reload and try again")
    _validate_unit_fields(fields)
    old_status, old_price = unit.status, unit.list_price_bdt
    changed = []
    for key, value in fields.items():
        if key in _EDITABLE and getattr(unit, key) != value:
            setattr(unit, key, value)
            changed.append(key)
    if "status" in changed and unit.status != "HELD":
        unit.held_until = None
        unit.held_for_lead_id = None
    unit.updated_by = actor
    unit.updated_at = now_utc()  # a review with no field change still counts as "checked today"
    await session.flush()
    return UnitChange(
        unit=unit_to_dict(unit, await session.get(ProjectRecord, unit.project_id)),
        became_available=old_status != "AVAILABLE" and unit.status == "AVAILABLE",
        price_dropped=unit.status == "AVAILABLE" and unit.list_price_bdt < old_price,
        changed=changed,
    )


async def hold_unit(session: AsyncSession, unit: PropertyUnit, lead_id: str, hours: int, actor: str) -> None:
    if unit.status != "AVAILABLE":
        raise Conflict("UNIT_NOT_AVAILABLE", f"Unit {unit.unit_code} is {unit.status}")
    unit.status = "HELD"
    unit.held_for_lead_id = lead_id
    unit.held_until = now_utc() + timedelta(hours=hours)
    unit.updated_by = actor
    await session.flush()


async def release_expired_holds(session: AsyncSession) -> list[str]:
    """Put units whose hold ran out back on sale. Returns the released unit ids."""
    now = now_utc()
    rows = (
        await session.execute(select(PropertyUnit).where(PropertyUnit.status == "HELD", PropertyUnit.held_until.is_not(None)))
    ).scalars().all()
    released = []
    for unit in rows:
        if as_utc(unit.held_until) <= now:
            unit.status = "AVAILABLE"
            unit.held_until = None
            unit.held_for_lead_id = None
            unit.updated_by = "system:hold-expiry"
            released.append(unit.unit_id)
    await session.flush()
    return released


# ── Payment plans ─────────────────────────────────────────────────────

def plan_to_dict(plan: PaymentPlan) -> dict:
    return {
        "plan_id": plan.plan_id,
        "project_id": plan.project_id,
        "name": plan.name,
        "booking_money_bdt": plan.booking_money_bdt,
        "down_payment_pct": plan.down_payment_pct,
        "installment_months": plan.installment_months,
        "active": plan.active,
    }


async def list_plans(session: AsyncSession, tenant_id: str, project_id: Optional[str] = None) -> list[dict]:
    stmt = select(PaymentPlan).where(PaymentPlan.tenant_id == tenant_id)
    if project_id:
        stmt = stmt.where(PaymentPlan.project_id == project_id)
    return [plan_to_dict(p) for p in (await session.execute(stmt.order_by(PaymentPlan.name))).scalars().all()]


async def create_plan(session: AsyncSession, tenant_id: str, fields: dict) -> dict:
    await get_project(session, fields["project_id"])
    pct = float(fields.get("down_payment_pct", 0))
    months = int(fields.get("installment_months", 0))
    if not 0 <= pct <= 100 or months < 0:
        raise SalesError("INVALID_PLAN", "Down payment must be 0–100% and installments 0 or more months")
    plan = PaymentPlan(
        tenant_id=tenant_id,
        project_id=fields["project_id"],
        name=fields["name"],
        booking_money_bdt=int(fields.get("booking_money_bdt", 0)),
        down_payment_pct=pct,
        installment_months=months,
        active=bool(fields.get("active", True)),
    )
    session.add(plan)
    await session.flush()
    return plan_to_dict(plan)


def calculate_plan(price_bdt: int, plan: PaymentPlan) -> dict:
    """Split a list price by a published plan. All amounts are whole taka; rounding goes to the last installment."""
    booking = min(plan.booking_money_bdt, price_bdt)
    down = round(price_bdt * plan.down_payment_pct / 100)
    down_after_booking = max(down - booking, 0)
    remaining = price_bdt - booking - down_after_booking
    months = plan.installment_months
    if months > 0:
        monthly = remaining // months
        last = remaining - monthly * (months - 1)
    else:
        monthly, last = 0, 0
    return {
        "plan_name": plan.name,
        "list_price_bdt": price_bdt,
        "booking_money_bdt": booking,
        "down_payment_bdt": down_after_booking + booking,
        "down_payment_due_after_booking_bdt": down_after_booking,
        "installment_months": months,
        "monthly_installment_bdt": monthly,
        "last_installment_bdt": last,
        "balance_on_handover_bdt": remaining if months == 0 else 0,
    }
