"""Requests only a person may grant. Approval is checked again against the unit as it stands at decision time."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales.db import now_utc
from app.sales.errors import Conflict, NotFound, SalesError
from app.sales.leads import add_event, iso
from app.sales.models import PropertyUnit, SalesApproval, SalesLead
from app.sales.units import get_unit_row, hold_unit


def approval_to_dict(a: SalesApproval, lead: Optional[SalesLead] = None, unit: Optional[PropertyUnit] = None) -> dict:
    return {
        "approval_id": a.approval_id,
        "kind": a.kind,
        "lead_id": a.lead_id,
        "lead_name": lead.name if lead else None,
        "unit_id": a.unit_id,
        "unit_code": unit.unit_code if unit else (a.payload or {}).get("unit_code"),
        "unit_status_now": unit.status if unit else None,
        "unit_version": a.unit_version,
        "payload": a.payload or {},
        "status": a.status,
        "requested_by": a.requested_by,
        "decided_by": a.decided_by,
        "decided_at": iso(a.decided_at),
        "decision_reason": a.decision_reason,
        "created_at": iso(a.created_at),
    }


async def _pending_for(session: AsyncSession, lead_id: str, kind: str, unit_id: Optional[str]) -> Optional[SalesApproval]:
    stmt = select(SalesApproval).where(
        SalesApproval.lead_id == lead_id, SalesApproval.kind == kind, SalesApproval.status == "PENDING"
    )
    if unit_id:
        stmt = stmt.where(SalesApproval.unit_id == unit_id)
    return (await session.execute(stmt)).scalars().first()


async def request_unit_hold(session: AsyncSession, lead: SalesLead, unit_id: str, note: str, requested_by: str) -> dict:
    unit = await get_unit_row(session, lead.tenant_id, unit_id)
    if unit.status != "AVAILABLE":
        raise Conflict("UNIT_NOT_AVAILABLE", f"Unit {unit.unit_code} is {unit.status}; it can't be held")
    existing = await _pending_for(session, lead.lead_id, "UNIT_HOLD", unit_id)
    if existing:
        return approval_to_dict(existing, lead, unit)
    approval = SalesApproval(
        tenant_id=lead.tenant_id, kind="UNIT_HOLD", lead_id=lead.lead_id, unit_id=unit.unit_id,
        unit_version=unit.version, requested_by=requested_by,
        payload={"unit_code": unit.unit_code, "list_price_bdt": unit.list_price_bdt, "note": note.strip()},
    )
    session.add(approval)
    await session.flush()
    await add_event(session, lead, "approval_requested", requested_by, {"approval_id": approval.approval_id, "kind": "UNIT_HOLD", "unit_code": unit.unit_code})
    return approval_to_dict(approval, lead, unit)


async def request_price_exception(
    session: AsyncSession, lead: SalesLead, *, unit_id: Optional[str], requested_price_bdt: Optional[int],
    request: str, requested_by: str,
) -> dict:
    if not request.strip():
        raise SalesError("EMPTY_REQUEST", "Describe what the customer is asking for")
    unit = await get_unit_row(session, lead.tenant_id, unit_id) if unit_id else None
    existing = await _pending_for(session, lead.lead_id, "PRICE_EXCEPTION", unit_id)
    if existing:
        return approval_to_dict(existing, lead, unit)
    approval = SalesApproval(
        tenant_id=lead.tenant_id, kind="PRICE_EXCEPTION", lead_id=lead.lead_id,
        unit_id=unit.unit_id if unit else None, unit_version=unit.version if unit else None,
        requested_by=requested_by,
        payload={
            "unit_code": unit.unit_code if unit else None,
            "list_price_bdt": unit.list_price_bdt if unit else None,
            "requested_price_bdt": requested_price_bdt,
            "request": request.strip(),
        },
    )
    session.add(approval)
    await session.flush()
    await add_event(session, lead, "approval_requested", requested_by, {"approval_id": approval.approval_id, "kind": "PRICE_EXCEPTION"})
    return approval_to_dict(approval, lead, unit)


async def decide(
    session: AsyncSession, tenant_id: str, approval_id: str, decision: str, actor: str, reason: Optional[str],
    hold_hours: int,
) -> dict:
    approval = await session.get(SalesApproval, approval_id)
    if not approval or approval.tenant_id != tenant_id:
        raise NotFound("APPROVAL_NOT_FOUND", "Approval does not exist")
    if approval.status != "PENDING":
        raise Conflict("ALREADY_DECIDED", f"This request is already {approval.status}")
    if decision not in ("APPROVED", "REJECTED"):
        raise SalesError("INVALID_DECISION", "Decision must be APPROVED or REJECTED")
    if approval.requested_by == actor:
        raise SalesError("SELF_APPROVAL", "You can't decide a request you raised yourself", 403)
    lead = await session.get(SalesLead, approval.lead_id) if approval.lead_id else None
    unit = await session.get(PropertyUnit, approval.unit_id) if approval.unit_id else None
    if decision == "APPROVED" and approval.kind == "UNIT_HOLD":
        # The unit must still be exactly as it was when the request was raised.
        if unit is None or unit.status != "AVAILABLE" or unit.version != approval.unit_version:
            approval.status, approval.decided_by, approval.decided_at = "STALE", actor, now_utc()
            approval.decision_reason = "Unit changed since the request (sold, held or edited)"
            await add_event(session, lead, "approval_stale", actor, {"approval_id": approval.approval_id})
            await session.flush()
            raise Conflict("APPROVAL_STALE", "The unit changed since this request was raised; it was not held")
        await hold_unit(session, unit, lead.lead_id, hold_hours, actor)
    approval.status, approval.decided_by, approval.decided_at = decision, actor, now_utc()
    approval.decision_reason = (reason or "").strip() or None
    if lead is not None:
        await add_event(session, lead, "approval_decided", actor, {
            "approval_id": approval.approval_id, "kind": approval.kind, "decision": decision, "reason": approval.decision_reason,
        })
    await session.flush()
    return approval_to_dict(approval, lead, unit)


async def list_approvals(session: AsyncSession, tenant_id: str, status: Optional[str] = "PENDING") -> list[dict]:
    stmt = (
        select(SalesApproval, SalesLead)
        .outerjoin(SalesLead, SalesLead.lead_id == SalesApproval.lead_id)
        .where(SalesApproval.tenant_id == tenant_id)
    )
    if status:
        stmt = stmt.where(SalesApproval.status == status)
    rows = (await session.execute(stmt.order_by(SalesApproval.created_at.desc()).limit(200))).all()
    result = []
    for approval, lead in rows:
        unit = await session.get(PropertyUnit, approval.unit_id) if approval.unit_id else None
        result.append(approval_to_dict(approval, lead, unit))
    return result
