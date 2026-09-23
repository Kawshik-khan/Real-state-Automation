"""Scheduled Reporting & Delivery Endpoints — Admin & Manager Command Hub.

Exposes REST APIs for managing schedules, triggering ad-hoc report generation,
dispatching test alerts across Email, Telegram, and WhatsApp, and reviewing delivery logs.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import (
    get_current_user,
    require_automation_secret,
    require_roles,
)
from app.models.report import (
    DeliveryChannel,
    GeneratedReportResponse,
    ReportScheduleCreate,
    ReportScheduleResponse,
    ReportScheduleUpdate,
    ReportTriggerRequest,
    TestDispatchRequest,
)
from app.models.user import UserRole
from app.persistence.report_store import report_store
from app.services.report_scheduler import report_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Scheduled Reports & Executive Delivery"])

_admin_or_manager = require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.DEVELOPER])
_admin_only = require_roles([UserRole.ADMIN, UserRole.DEVELOPER])


@router.get("/schedules", response_model=List[Dict[str, Any]], summary="List all report schedules")
async def list_schedules(current_user: dict = Depends(_admin_or_manager)):
    """Lists all automated report schedules and configured multi-channel recipients."""
    schedules = await report_store.get_all_schedules(tenant_id=current_user.get("tenant_id", "glg-assets"))
    return schedules


@router.post("/schedules", summary="Create or configure a report schedule")
async def create_schedule(
    req: ReportScheduleCreate,
    current_user: dict = Depends(_admin_only),
):
    """Creates a new automated report schedule (Admin only)."""
    schedule_dict = req.model_dump()
    schedule_dict["tenant_id"] = current_user.get("tenant_id", "glg-assets")
    saved = await report_store.save_schedule(schedule_dict)
    return {"success": True, "schedule": saved}


@router.patch("/schedules/{schedule_id}/toggle", summary="Enable or disable a schedule")
async def toggle_schedule(
    schedule_id: str,
    body: Dict[str, bool],
    current_user: dict = Depends(_admin_or_manager),
):
    """Toggles active state of a schedule on or off."""
    is_active = body.get("is_active", True)
    updated = await report_store.toggle_schedule(schedule_id, is_active=is_active)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Schedule '{schedule_id}' not found")
    return {"success": True, "schedule": updated}


@router.post("/schedules/{schedule_id}/trigger", summary="Trigger immediate report generation & delivery")
async def trigger_schedule_now(
    schedule_id: str,
    req: Optional[ReportTriggerRequest] = None,
    current_user: dict = Depends(_admin_or_manager),
):
    """Manually triggers immediate report generation and multi-channel delivery to recipients."""
    sched = await report_store.get_schedule(schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail=f"Schedule '{schedule_id}' not found")

    recipients_override = None
    if req and req.target_recipients:
        recipients_override = [r.model_dump() for r in req.target_recipients]

    channels_override = None
    if req and req.channels_override:
        channels_override = [c.value for c in req.channels_override]

    period_days = req.period_days if req else None

    result = await report_scheduler.generate_and_deliver(
        schedule_id=schedule_id,
        schedule_data=sched,
        triggered_by=f"manual_{current_user.get('email', 'admin')}",
        recipients_override=recipients_override,
        channels_override=channels_override,
        period_days=period_days,
    )

    return {
        "success": True,
        "message": f"Report '{sched.get('name')}' generated and dispatched.",
        "report": result,
    }


@router.post("/cron-trigger", summary="External n8n / cron trigger endpoint")
async def cron_trigger(
    body: Optional[Dict[str, Any]] = None,
    auth: dict = Depends(require_automation_secret),
):
    """Webhook endpoint for external schedulers (e.g. n8n WF5 Daily Digest) to trigger scheduled reports."""
    schedule_id = (body or {}).get("schedule_id", "sched-daily-pulse")
    sched = await report_store.get_schedule(schedule_id)
    if not sched:
        # Fall back to daily schedule
        schedules = await report_store.get_all_schedules()
        sched = schedules[0] if schedules else None

    result = await report_scheduler.generate_and_deliver(
        schedule_id=schedule_id,
        schedule_data=sched,
        triggered_by="n8n_cron_webhook",
    )
    return {"success": True, "dispatched": True, "report_id": result.get("id")}


@router.get("/history", summary="List historical generated reports & audit logs")
async def get_report_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(_admin_or_manager),
):
    """Returns chronologically sorted list of generated intelligence reports with channel delivery statuses."""
    reports = await report_store.get_report_history(
        limit=limit, tenant_id=current_user.get("tenant_id", "glg-assets")
    )
    return {
        "success": True,
        "total": len(reports),
        "reports": reports,
    }


@router.get("/history/{report_id}", summary="Get detailed report content & HTML preview")
async def get_report_detail(
    report_id: str,
    current_user: dict = Depends(_admin_or_manager),
):
    """Returns single report payload including metrics data, HTML preview, and delivery logs."""
    report = await report_store.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return {"success": True, "report": report}


@router.post("/test-dispatch", summary="Dispatch a test report across Email / Telegram / WhatsApp")
async def test_dispatch(
    req: TestDispatchRequest,
    current_user: dict = Depends(_admin_or_manager),
):
    """Sends an immediate test briefing to specified email, Telegram, or WhatsApp targets to verify channel health."""
    recip = {
        "role": current_user.get("role", "admin"),
        "name": req.recipient_name or current_user.get("full_name", "Test User"),
        "email": req.email or current_user.get("email"),
        "telegram_chat_id": req.telegram_chat_id,
        "whatsapp_phone": req.whatsapp_phone,
        "channels": [],
    }

    if recip["email"]:
        recip["channels"].append("email")
    if recip["telegram_chat_id"]:
        recip["channels"].append("telegram")
    if recip["whatsapp_phone"]:
        recip["channels"].append("whatsapp")

    if not recip["channels"]:
        raise HTTPException(
            status_code=400,
            detail="At least one target destination (email, telegram_chat_id, or whatsapp_phone) must be provided.",
        )

    test_sched = {
        "id": "sched-test-dispatch",
        "name": f"Test Intelligence Brief ({req.report_type.value})",
        "report_type": req.report_type.value,
        "frequency": "daily",
        "recipients": [recip],
        "channels": recip["channels"],
    }

    result = await report_scheduler.generate_and_deliver(
        schedule_data=test_sched,
        triggered_by=f"test_dispatch_by_{current_user.get('email', 'admin')}",
    )

    return {
        "success": True,
        "message": f"Test report dispatched across {recip['channels']}.",
        "delivery_details": result.get("delivery_details", []),
        "report_id": result.get("id"),
    }
