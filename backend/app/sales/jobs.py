"""Durable jobs on Postgres (Procrastinate). Replaces the n8n schedules and webhooks for the sales flow.

Run the worker with ``python -m app.worker``. Jobs survive restarts, are retried on failure, and a conversation
never has two agent turns running at once (``lock``) or more than one waiting (``queueing_lock``).
"""

import logging
import re
from datetime import datetime
from typing import Any, Optional

import procrastinate
from procrastinate import RetryStrategy, exceptions

from app.config import settings

logger = logging.getLogger(__name__)


def psycopg_dsn(url: Optional[str] = None) -> str:
    """SQLAlchemy URL → plain libpq DSN for psycopg (drops the +asyncpg driver suffix)."""
    url = (url or settings.database_url or "").strip()
    url = re.sub(r"^postgres(ql)?\+\w+://", "postgresql://", url)
    return re.sub(r"^postgres://", "postgresql://", url)


def _connector():
    return procrastinate.PsycopgConnector(conninfo=psycopg_dsn(), kwargs={"prepare_threshold": None})


queue = procrastinate.App(connector=_connector(), import_paths=["app.sales.jobs"])

_RETRY = RetryStrategy(max_attempts=3, wait=30, exponential_wait=2)


# ── Tasks ─────────────────────────────────────────────────────────────

@queue.task(name="sales.run_agent_turn", queue="agent", retry=RetryStrategy(max_attempts=2, wait=5))
async def run_agent_turn(conversation_id: str) -> dict:
    from app.sales.agent import run_turn

    result = await run_turn(conversation_id)
    return {"status": result.status, "reason": result.reason, "message_status": result.message_status}


@queue.task(name="sales.visit_reminder", queue="sales", retry=_RETRY)
async def visit_reminder(visit_id: str, kind: str) -> dict:
    from app.sales import workflows

    return await workflows.send_visit_reminder(visit_id, kind)


@queue.task(name="sales.visit_outcome_check", queue="sales", retry=_RETRY)
async def visit_outcome_check(visit_id: str) -> dict:
    from app.sales import workflows

    return await workflows.check_visit_outcome(visit_id)


@queue.task(name="sales.followup_step", queue="sales", retry=_RETRY)
async def followup_step(enrollment_id: str) -> dict:
    from app.sales import workflows

    return await workflows.run_followup_step(enrollment_id)


@queue.task(name="sales.unit_match_alert", queue="sales", retry=_RETRY)
async def unit_match_alert(tenant_id: str, unit_id: str) -> dict:
    from app.sales import workflows

    return await workflows.send_unit_match_alerts(tenant_id, unit_id)


# 02:00 UTC = 08:00 Asia/Dhaka
@queue.periodic(cron="0 2 * * *", periodic_id="daily-digest")
@queue.task(name="sales.daily_digest", queue="sales", queueing_lock="sales.daily_digest")
async def daily_digest(timestamp: int) -> dict:
    from app.sales import workflows

    return await workflows.send_daily_digests()


@queue.periodic(cron="17 * * * *", periodic_id="stale-lead-sweep")
@queue.task(name="sales.stale_lead_sweep", queue="sales", queueing_lock="sales.stale_lead_sweep")
async def stale_lead_sweep(timestamp: int) -> dict:
    from app.sales import workflows

    return await workflows.sweep_stale_leads()


@queue.periodic(cron="*/15 * * * *", periodic_id="release-holds")
@queue.task(name="sales.release_holds", queue="sales", queueing_lock="sales.release_holds")
async def release_holds(timestamp: int) -> dict:
    from app.sales import workflows

    return await workflows.release_expired_holds()


# 04:00 UTC Sunday = 10:00 Asia/Dhaka
@queue.periodic(cron="0 4 * * 0", periodic_id="weekly-content-drafts")
@queue.task(name="sales.content_drafts", queue="sales", queueing_lock="sales.content_drafts")
async def content_drafts(timestamp: int) -> dict:
    from app.sales.content import draft_weekly_posts

    return await draft_weekly_posts(settings.default_tenant_id)


# ── Deferring ─────────────────────────────────────────────────────────

async def defer(task, *, schedule_at: Optional[datetime] = None, schedule_in: Optional[dict] = None,
                lock: Optional[str] = None, queueing_lock: Optional[str] = None, **kwargs: Any) -> Optional[int]:
    """Queue a job. Returns the job id, or None when an identical job is already waiting or the queue is down.

    Callers record what happened; nothing assumes a job exists when this returns None.
    """
    options: dict = {}
    if schedule_at is not None:
        options["schedule_at"] = schedule_at
    if schedule_in is not None:
        options["schedule_in"] = schedule_in
    if lock:
        options["lock"] = lock
    if queueing_lock:
        options["queueing_lock"] = queueing_lock
    try:
        return await task.configure(**options).defer_async(**kwargs)
    except exceptions.AlreadyEnqueued:
        return None
    except Exception as exc:  # queue not reachable: logged loudly, the caller decides what to tell people
        logger.error("[sales.jobs] could not queue %s: %s", task.name, exc)
        return None


async def defer_agent_turn(conversation_id: str) -> Optional[int]:
    # Wait 2 s so a burst of customer messages is answered in one turn.
    return await defer(
        run_agent_turn, conversation_id=conversation_id, schedule_in={"seconds": 2},
        lock=f"conv:{conversation_id}", queueing_lock=f"turn:{conversation_id}",
    )
