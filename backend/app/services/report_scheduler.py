"""Report Scheduler Engine & Multi-Channel Dispatch Worker for GLG Assets.

Manages automated scheduling, live telemetry aggregation, executive AI synthesis,
and multi-channel delivery to Managers and Admins across Email, Telegram, WhatsApp,
and the In-App Hub.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.persistence.report_store import report_store
from app.services.email_service import email_service
from app.services.report_builder import report_builder
from app.services.telegram import telegram_service
from app.services.whatsapp_dispatcher import whatsapp_dispatcher

logger = logging.getLogger(__name__)

_SCHEDULER_RUNNING = False
_SCHEDULER_TASK: Optional[asyncio.Task] = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReportSchedulerService:
    def __init__(self):
        self._is_running = False

    async def generate_and_deliver(
        self,
        schedule_id: Optional[str] = None,
        schedule_data: Optional[Dict[str, Any]] = None,
        triggered_by: str = "scheduled_worker",
        recipients_override: Optional[List[Dict[str, Any]]] = None,
        channels_override: Optional[List[str]] = None,
        period_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Core execution pipeline: gathers telemetry, synthesizes AI insights, and dispatches to recipients."""
        # 1. Resolve schedule
        sched = schedule_data
        if not sched and schedule_id:
            sched = await report_store.get_schedule(schedule_id)

        if not sched:
            sched = {
                "id": "sched-adhoc-trigger",
                "name": "Executive Intelligence On-Demand Report",
                "report_type": "daily_digest",
                "frequency": "daily",
                "channels": ["email", "telegram", "whatsapp"],
                "recipients": [
                    {
                        "role": "admin",
                        "name": "Alex Mercer (Admin)",
                        "email": "admin@glgassets.com",
                        "telegram_chat_id": "glg_admin_alerts",
                        "whatsapp_phone": "+8801700000001",
                        "channels": ["email", "telegram", "whatsapp"],
                    },
                    {
                        "role": "manager",
                        "name": "Sarah Connor (Operations Manager)",
                        "email": "manager@glgassets.com",
                        "telegram_chat_id": "glg_manager_ops",
                        "whatsapp_phone": "+8801700000002",
                        "channels": ["email", "telegram", "whatsapp"],
                    },
                ],
            }

        report_type = sched.get("report_type", "daily_digest")
        days = period_days or (7 if report_type == "weekly_cross_role" else 1)
        title = sched.get("name", "Executive Intelligence Digest")

        # 2. Gather live telemetry & synthesize AI takeaways
        metrics = await report_builder.gather_live_metrics(period_days=days)
        insights = report_builder.synthesize_insights(metrics, report_type=report_type)

        recipients = recipients_override or sched.get("recipients", [])
        active_channels = channels_override or sched.get("channels", ["email", "telegram", "whatsapp"])

        delivery_details = []
        delivered_any = False
        failed_any = False

        # Render canonical templates
        html_template = report_builder.render_html_report(metrics, insights, title, "Executive")
        tg_template = report_builder.render_telegram_report(metrics, insights, title, "Executive")
        wa_template = report_builder.render_whatsapp_report(metrics, insights, title, "Executive")

        # 3. Iterate through active recipients and dispatch across enabled channels
        for recip in recipients:
            r_name = recip.get("name", "Executive Stakeholder")
            r_role = recip.get("role", "admin")
            r_channels = recip.get("channels", active_channels)
            is_active = recip.get("is_active", True)
            if not is_active:
                continue

            # (A) Email Channel
            if "email" in r_channels and recip.get("email"):
                r_email = recip["email"]
                try:
                    personalized_html = report_builder.render_html_report(metrics, insights, title, r_name)
                    email_res = await email_service.send_direct_email(
                        to_email=r_email,
                        subject=f"📊 {title} — {date.today().isoformat()}",
                        html_body=personalized_html,
                        text_body=insights["summary"],
                    )
                    delivery_details.append({
                        "recipient_name": r_name,
                        "recipient_role": r_role,
                        "channel": "email",
                        "target": r_email,
                        "status": email_res.get("status", "sent"),
                        "details": email_res.get("details", "Email dispatched"),
                        "delivered_at": utc_now().isoformat(),
                    })
                    delivered_any = True
                except Exception as err:
                    logger.error(f"[ReportScheduler] Email dispatch failed for {r_email}: {err}")
                    delivery_details.append({
                        "recipient_name": r_name,
                        "recipient_role": r_role,
                        "channel": "email",
                        "target": r_email,
                        "status": "failed",
                        "details": str(err),
                        "delivered_at": utc_now().isoformat(),
                    })
                    failed_any = True

            # (B) Telegram Channel
            if "telegram" in r_channels and recip.get("telegram_chat_id"):
                r_tg = recip["telegram_chat_id"]
                try:
                    personalized_tg = report_builder.render_telegram_report(metrics, insights, title, r_name)
                    tg_res = await telegram_service.send_message(
                        chat_id=r_tg,
                        text=personalized_tg,
                        parse_mode="Markdown",
                    )
                    status_str = "sent" if tg_res.get("success") else "simulated"
                    delivery_details.append({
                        "recipient_name": r_name,
                        "recipient_role": r_role,
                        "channel": "telegram",
                        "target": str(r_tg),
                        "status": status_str,
                        "details": "Sent via Telegram Bot API" if tg_res.get("success") else tg_res.get("error", "Simulated alert"),
                        "delivered_at": utc_now().isoformat(),
                    })
                    delivered_any = True
                except Exception as err:
                    logger.error(f"[ReportScheduler] Telegram dispatch failed for {r_tg}: {err}")
                    delivery_details.append({
                        "recipient_name": r_name,
                        "recipient_role": r_role,
                        "channel": "telegram",
                        "target": str(r_tg),
                        "status": "failed",
                        "details": str(err),
                        "delivered_at": utc_now().isoformat(),
                    })
                    failed_any = True

            # (C) WhatsApp Channel
            if "whatsapp" in r_channels and recip.get("whatsapp_phone"):
                r_wa = recip["whatsapp_phone"]
                try:
                    personalized_wa = report_builder.render_whatsapp_report(metrics, insights, title, r_name)
                    wa_res = await whatsapp_dispatcher.send_executive_brief(
                        phone_number=r_wa,
                        message_text=personalized_wa,
                    )
                    delivery_details.append({
                        "recipient_name": r_name,
                        "recipient_role": r_role,
                        "channel": "whatsapp",
                        "target": r_wa,
                        "status": wa_res.get("status", "sent"),
                        "details": wa_res.get("details", "Dispatched to WhatsApp"),
                        "delivered_at": utc_now().isoformat(),
                    })
                    delivered_any = True
                except Exception as err:
                    logger.error(f"[ReportScheduler] WhatsApp dispatch failed for {r_wa}: {err}")
                    delivery_details.append({
                        "recipient_name": r_name,
                        "recipient_role": r_role,
                        "channel": "whatsapp",
                        "target": r_wa,
                        "status": "failed",
                        "details": str(err),
                        "delivered_at": utc_now().isoformat(),
                    })
                    failed_any = True

        overall_status = "delivered"
        if failed_any and delivered_any:
            overall_status = "partially_delivered"
        elif failed_any and not delivered_any:
            overall_status = "failed"

        # 4. Save generated report to persistent history
        report_record = {
            "schedule_id": sched.get("id"),
            "title": title,
            "report_type": report_type,
            "period_start": (utc_now() - timedelta(days=days)).isoformat(),
            "period_end": utc_now().isoformat(),
            "metrics_data": metrics,
            "executive_summary": insights["summary"],
            "html_content": html_template,
            "whatsapp_content": wa_template,
            "telegram_content": tg_template,
            "delivery_status": overall_status,
            "delivery_details": delivery_details,
            "triggered_by": triggered_by,
            "created_at": utc_now().isoformat(),
        }

        saved_report = await report_store.record_generated_report(report_record)

        # 5. Update schedule last_run_at and next_run_at
        if sched.get("id"):
            next_run = utc_now() + timedelta(days=7 if report_type == "weekly_cross_role" else 1)
            await report_store.update_last_run(sched["id"], last_run=utc_now(), next_run=next_run)

        logger.info(
            f"[ReportScheduler] Report '{title}' completed with status '{overall_status}'. "
            f"Delivered {len(delivery_details)} channel notifications."
        )
        return saved_report

    async def check_schedules_tick(self):
        """Evaluates active schedules against current UTC time."""
        now = utc_now()
        current_hour = now.hour
        current_minute = now.minute
        current_weekday = now.weekday()  # 0 = Monday

        # We evaluate on the top of the scheduled hour (minute < 3 to tolerate async tick jitter)
        if current_minute > 2:
            return

        schedules = await report_store.get_all_schedules()
        for sched in schedules:
            if not sched.get("is_active", True):
                continue

            target_hour = sched.get("execution_hour_utc", 8)
            freq = sched.get("frequency", "daily")

            # Check hour match
            if current_hour != target_hour:
                continue

            # Check weekly match
            if freq == "weekly":
                target_day = sched.get("execution_day_of_week", 0)
                if current_weekday != target_day:
                    continue

            # Check if already executed in the last 6 hours to avoid duplicate triggers
            last_run = sched.get("last_run_at")
            if last_run:
                try:
                    if isinstance(last_run, str):
                        last_dt = datetime.fromisoformat(last_run)
                    else:
                        last_dt = last_run
                    if (now - last_dt).total_seconds() < 21600:  # 6 hours
                        continue
                except Exception:
                    pass

            logger.info(f"[ReportScheduler] Triggering scheduled report: {sched.get('name')}")
            try:
                await self.generate_and_deliver(
                    schedule_id=sched["id"],
                    schedule_data=sched,
                    triggered_by="scheduled_worker",
                )
            except Exception as e:
                logger.error(f"[ReportScheduler] Execution error on {sched.get('id')}: {e}")


report_scheduler = ReportSchedulerService()


async def report_scheduler_worker(check_interval_seconds: int = 60):
    """Background loop that periodically ticks the report scheduler."""
    global _SCHEDULER_RUNNING
    _SCHEDULER_RUNNING = True
    logger.info("[ReportScheduler] Background worker started (evaluating every 60s).")

    while _SCHEDULER_RUNNING:
        try:
            await report_scheduler.check_schedules_tick()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"[ReportScheduler] Error in scheduler loop: {e}")
        await asyncio.sleep(check_interval_seconds)

    logger.info("[ReportScheduler] Background worker terminated.")


def stop_report_scheduler():
    global _SCHEDULER_RUNNING, _SCHEDULER_TASK
    _SCHEDULER_RUNNING = False
    if _SCHEDULER_TASK and not _SCHEDULER_TASK.done():
        _SCHEDULER_TASK.cancel()
