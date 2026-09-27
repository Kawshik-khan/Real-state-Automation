"""Resilient Persistence Store for Report Schedules and Delivery Audit Logs.

Supports dual-persistence: writes to Supabase / PostgreSQL tables via SQLAlchemy
async sessions when available, with automatic local JSON fallback for resilient continuity.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, update

from app.database import async_session_factory, is_db_reachable
from app.models.models import GeneratedReportRecord, ReportScheduleRecord

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FALLBACK_STORE_FILE = DATA_DIR / "report_store.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Canonical Seed Schedules (Manager & Admin Recipients) ──

DEFAULT_SCHEDULES = [
    {
        "id": "sched-daily-pulse",
        "name": "Daily Executive Operational Pulse",
        "report_type": "daily_digest",
        "frequency": "daily",
        "execution_hour_utc": 8,  # 08:00 UTC / 14:00 BST
        "execution_day_of_week": 0,
        "is_active": True,
        "recipients": [
            {
                "id": "recip-admin",
                "role": "admin",
                "name": "Alex Mercer (Admin)",
                "email": "admin@glgassets.com",
                "telegram_chat_id": "glg_admin_alerts",
                "whatsapp_phone": "+8801700000001",
                "channels": ["email", "telegram", "whatsapp"],
                "is_active": True,
            },
            {
                "id": "recip-manager",
                "role": "manager",
                "name": "Sarah Connor (Operations Manager)",
                "email": "manager@glgassets.com",
                "telegram_chat_id": "glg_manager_ops",
                "whatsapp_phone": "+8801700000002",
                "channels": ["email", "telegram", "whatsapp"],
                "is_active": True,
            },
        ],
        "channels": ["email", "telegram", "whatsapp", "in_app"],
        "tenant_id": "glg-assets",
        "created_at": utc_iso(),
        "updated_at": utc_iso(),
    },
    {
        "id": "sched-weekly-digest",
        "name": "Weekly Cross-Role Executive Briefing",
        "report_type": "weekly_cross_role",
        "frequency": "weekly",
        "execution_hour_utc": 8,  # 08:00 UTC
        "execution_day_of_week": 0,  # Monday
        "is_active": True,
        "recipients": [
            {
                "id": "recip-admin",
                "role": "admin",
                "name": "Alex Mercer (Admin)",
                "email": "admin@glgassets.com",
                "telegram_chat_id": "glg_admin_alerts",
                "whatsapp_phone": "+8801700000001",
                "channels": ["email", "telegram", "whatsapp"],
                "is_active": True,
            },
            {
                "id": "recip-manager",
                "role": "manager",
                "name": "Sarah Connor (Operations Manager)",
                "email": "manager@glgassets.com",
                "telegram_chat_id": "glg_manager_ops",
                "whatsapp_phone": "+8801700000002",
                "channels": ["email", "telegram", "whatsapp"],
                "is_active": True,
            },
        ],
        "channels": ["email", "telegram", "whatsapp", "in_app"],
        "tenant_id": "glg-assets",
        "created_at": utc_iso(),
        "updated_at": utc_iso(),
    },
]


class ReportStore:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._memory_schedules: Dict[str, Dict[str, Any]] = {s["id"]: dict(s) for s in DEFAULT_SCHEDULES}
        self._memory_reports: List[Dict[str, Any]] = []
        self._load_fallback_from_disk()

    def _load_fallback_from_disk(self):
        if FALLBACK_STORE_FILE.exists():
            try:
                with open(FALLBACK_STORE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "schedules" in data and isinstance(data["schedules"], dict):
                        self._memory_schedules.update(data["schedules"])
                    if "reports" in data and isinstance(data["reports"], list):
                        self._memory_reports = data["reports"]
            except Exception as e:
                logger.warning(f"[ReportStore] Warning loading fallback store: {e}")

    def _save_fallback_to_disk(self):
        try:
            with open(FALLBACK_STORE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schedules": self._memory_schedules,
                        "reports": self._memory_reports[-50:],  # retain latest 50
                    },
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            logger.warning(f"[ReportStore] Warning saving fallback store: {e}")

    async def get_all_schedules(self, tenant_id: str = "glg-assets") -> List[Dict[str, Any]]:
        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    res = await session.execute(
                        select(ReportScheduleRecord).order_by(ReportScheduleRecord.created_at.asc())
                    )
                    rows = res.scalars().all()
                    if rows:
                        return [
                            {
                                "id": r.id,
                                "name": r.name,
                                "report_type": r.report_type,
                                "frequency": r.frequency,
                                "execution_hour_utc": r.execution_hour_utc,
                                "execution_day_of_week": r.execution_day_of_week,
                                "is_active": r.is_active,
                                "recipients": r.recipients or [],
                                "channels": r.channels or [],
                                "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
                                "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
                                "tenant_id": r.tenant_id,
                                "created_at": r.created_at.isoformat() if r.created_at else None,
                                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                            }
                            for r in rows
                        ]
            except Exception as e:
                logger.warning(f"[ReportStore] Error querying DB schedules, using fallback: {e}")

        return list(self._memory_schedules.values())

    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        schedules = await self.get_all_schedules()
        for s in schedules:
            if s["id"] == schedule_id:
                return s
        return self._memory_schedules.get(schedule_id)

    async def save_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        s_id = schedule_data.get("id") or f"sched-{uuid4().hex[:8]}"
        schedule_data["id"] = s_id
        schedule_data["updated_at"] = utc_iso()
        if "created_at" not in schedule_data:
            schedule_data["created_at"] = utc_iso()

        self._memory_schedules[s_id] = schedule_data
        self._save_fallback_to_disk()

        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    existing = await session.get(ReportScheduleRecord, s_id)
                    if existing:
                        for k, v in schedule_data.items():
                            if hasattr(existing, k) and k not in ("created_at", "last_run_at", "next_run_at"):
                                setattr(existing, k, v)
                    else:
                        rec = ReportScheduleRecord(
                            id=s_id,
                            name=schedule_data.get("name", "Untitled Schedule"),
                            report_type=schedule_data.get("report_type", "daily_digest"),
                            frequency=schedule_data.get("frequency", "daily"),
                            execution_hour_utc=schedule_data.get("execution_hour_utc", 8),
                            execution_day_of_week=schedule_data.get("execution_day_of_week", 0),
                            is_active=schedule_data.get("is_active", True),
                            recipients=schedule_data.get("recipients", []),
                            channels=schedule_data.get("channels", ["email", "telegram", "whatsapp"]),
                            tenant_id=schedule_data.get("tenant_id", "glg-assets"),
                        )
                        session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"[ReportStore] Error persisting schedule to DB: {e}")

        return schedule_data

    async def toggle_schedule(self, schedule_id: str, is_active: bool) -> Optional[Dict[str, Any]]:
        sched = await self.get_schedule(schedule_id)
        if not sched:
            return None

        sched["is_active"] = is_active
        sched["updated_at"] = utc_iso()
        self._memory_schedules[schedule_id] = sched
        self._save_fallback_to_disk()

        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    rec = await session.get(ReportScheduleRecord, schedule_id)
                    if rec:
                        rec.is_active = is_active
                        await session.commit()
            except Exception as e:
                logger.warning(f"[ReportStore] Error toggling DB schedule: {e}")

        return sched

    async def update_last_run(self, schedule_id: str, last_run: datetime, next_run: Optional[datetime] = None):
        sched = self._memory_schedules.get(schedule_id)
        if sched:
            sched["last_run_at"] = last_run.isoformat()
            if next_run:
                sched["next_run_at"] = next_run.isoformat()
            self._save_fallback_to_disk()

        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    rec = await session.get(ReportScheduleRecord, schedule_id)
                    if rec:
                        rec.last_run_at = last_run
                        if next_run:
                            rec.next_run_at = next_run
                        await session.commit()
            except Exception as e:
                logger.warning(f"[ReportStore] Error updating last_run in DB: {e}")

    async def record_generated_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        rep_id = report_data.get("id") or f"rep-{utc_now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        report_data["id"] = rep_id
        if "created_at" not in report_data:
            report_data["created_at"] = utc_iso()

        self._memory_reports.insert(0, report_data)
        self._save_fallback_to_disk()

        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    rec = GeneratedReportRecord(
                        id=rep_id,
                        schedule_id=report_data.get("schedule_id"),
                        title=report_data.get("title", "Generated Intelligence Report"),
                        report_type=report_data.get("report_type", "daily_digest"),
                        period_start=utc_now(),
                        period_end=utc_now(),
                        metrics_data=report_data.get("metrics_data", {}),
                        executive_summary=report_data.get("executive_summary", ""),
                        html_content=report_data.get("html_content"),
                        whatsapp_content=report_data.get("whatsapp_content"),
                        telegram_content=report_data.get("telegram_content"),
                        delivery_status=report_data.get("delivery_status", "delivered"),
                        delivery_details=report_data.get("delivery_details", []),
                        triggered_by=report_data.get("triggered_by", "scheduled_worker"),
                        tenant_id=report_data.get("tenant_id", "glg-assets"),
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"[ReportStore] Error recording generated report in DB: {e}")

        return report_data

    async def get_report_history(self, limit: int = 20, tenant_id: str = "glg-assets") -> List[Dict[str, Any]]:
        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    res = await session.execute(
                        select(GeneratedReportRecord)
                        .order_by(GeneratedReportRecord.created_at.desc())
                        .limit(limit)
                    )
                    rows = res.scalars().all()
                    if rows:
                        return [
                            {
                                "id": r.id,
                                "schedule_id": r.schedule_id,
                                "title": r.title,
                                "report_type": r.report_type,
                                "period_start": r.period_start.isoformat() if r.period_start else None,
                                "period_end": r.period_end.isoformat() if r.period_end else None,
                                "metrics_data": r.metrics_data or {},
                                "executive_summary": r.executive_summary,
                                "html_content": r.html_content,
                                "whatsapp_content": r.whatsapp_content,
                                "telegram_content": r.telegram_content,
                                "delivery_status": r.delivery_status,
                                "delivery_details": r.delivery_details or [],
                                "triggered_by": r.triggered_by,
                                "created_at": r.created_at.isoformat() if r.created_at else None,
                            }
                            for r in rows
                        ]
            except Exception as e:
                logger.warning(f"[ReportStore] Error querying DB reports, using fallback: {e}")

        return self._memory_reports[:limit]

    async def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        history = await self.get_report_history(limit=50)
        for r in history:
            if r["id"] == report_id:
                return r
        for r in self._memory_reports:
            if r["id"] == report_id:
                return r
        return None


report_store = ReportStore()
