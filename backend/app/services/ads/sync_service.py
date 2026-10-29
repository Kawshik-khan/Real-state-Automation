"""Pull ad metrics from each configured platform and upsert them.

Writes are idempotent (upserts keyed on platform IDs + date), so re-pulling a
window simply overwrites the rows with the platform's latest numbers. Platforms
restate recent days for up to ~28 days, which is why the nightly run re-pulls
that window.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.config import settings
from app.services.ads.factory import ConnectorSpec
from app.services.ads.types import Campaign, ConnectorAuthError, ConnectorError

logger = logging.getLogger(__name__)

HOURLY_LOOKBACK_DAYS = 3
NIGHTLY_LOOKBACK_DAYS = 28
BACKFILL_DAYS = 90
MAX_LOOKBACK_DAYS = 90
# A 'running' row older than this is treated as a crashed run, not a lock.
RUN_LOCK_MINUTES = 45

_process_lock = asyncio.Lock()


def reporting_today(now: Optional[datetime] = None) -> date:
    now = now or datetime.now(timezone.utc)
    try:
        return now.astimezone(ZoneInfo(settings.reporting_timezone)).date()
    except Exception:
        return now.date()


def _parse_dt(raw: Any) -> Optional[datetime]:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_locked(runs: list[dict[str, Any]], ad_account_id: str, now: datetime) -> bool:
    for run in runs:
        if run.get("ad_account_id") != ad_account_id or run.get("status") != "running":
            continue
        started = _parse_dt(run.get("started_at"))
        if started and now - started < timedelta(minutes=RUN_LOCK_MINUTES):
            return True
    return False


def plan_trigger(runs: list[dict[str, Any]], ad_account_id: str, now: datetime) -> Optional[tuple[str, int]]:
    """Decide what the background worker should run for one account, if anything.

    runs: recent ad_sync_runs rows, newest first (shared across instances via the DB).
    Returns (trigger, lookback_days) or None.
    """
    mine = [r for r in runs if r.get("ad_account_id") == ad_account_id and r.get("status") != "skipped"]
    if is_locked(runs, ad_account_id, now):
        return None
    if not any(r.get("status") in ("success", "partial") for r in mine):
        # Never synced successfully: backfill, but don't hammer a failing account.
        last = _parse_dt(mine[0].get("started_at")) if mine else None
        if last and now - last < timedelta(minutes=settings.ads_sync_interval_minutes):
            return None
        return "backfill", BACKFILL_DAYS

    today_utc = now.date()
    if now.hour >= settings.ads_sync_nightly_hour_utc:
        nightly_today = any(
            r.get("trigger") == "nightly" and (_parse_dt(r.get("started_at")) or now).date() == today_utc
            for r in mine
        )
        if not nightly_today:
            return "nightly", NIGHTLY_LOOKBACK_DAYS

    last_attempt = _parse_dt(mine[0].get("started_at")) if mine else None
    if not last_attempt or now - last_attempt >= timedelta(minutes=settings.ads_sync_interval_minutes):
        return "schedule", HOURLY_LOOKBACK_DAYS
    return None


def _merge_campaigns(payload_campaigns: list[Campaign], metrics: list, platform: str, account_id: str,
                     currency: Optional[str]) -> list[Campaign]:
    """Campaign list plus any campaign that only appears in insights (e.g. archived)."""
    known = {c.external_id for c in payload_campaigns}
    merged = list(payload_campaigns)
    for m in metrics:
        if m.external_campaign_id not in known:
            known.add(m.external_campaign_id)
            merged.append(Campaign(
                platform=platform, external_id=m.external_campaign_id, ad_account_id=account_id,
                name=m.campaign_name or m.external_campaign_id, status="UNKNOWN", currency=currency,
            ))
    return merged


async def sync_account(repo, spec: ConnectorSpec, since: date, until: date, trigger: str,
                       runs: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    runs = runs if runs is not None else await repo.recent_runs()
    run = {
        "id": str(uuid4()),
        "platform": spec.platform,
        "ad_account_id": spec.ad_account_id,
        "trigger": trigger,
        "since_date": since,
        "until_date": until,
        "started_at": now,
    }
    if is_locked(runs, spec.ad_account_id, now):
        await repo.start_run({**run, "status": "skipped", "finished_at": now,
                              "error": "Another sync for this account is still running."})
        return {**run, "status": "skipped"}

    await repo.start_run({**run, "status": "running"})
    try:
        payload = await spec.connector.fetch(since, until, include_posts=spec.include_posts)
        synced_at = datetime.now(timezone.utc)
        await repo.upsert_account(payload.account, synced_at)
        campaigns = _merge_campaigns(payload.campaigns, payload.daily_metrics, spec.platform,
                                     payload.account.id, payload.account.currency)
        n_campaigns = await repo.upsert_campaigns(campaigns, synced_at)
        n_metrics = await repo.upsert_daily_metrics(payload.daily_metrics, synced_at)
        await repo.upsert_period_reach(payload.period_reach, synced_at)
        n_posts = await repo.upsert_posts(payload.posts, synced_at) if payload.posts else 0
        try:
            await repo.auto_link_projects()
        except Exception as link_err:  # linking is a convenience; never fail the sync for it
            payload.warnings.append(f"Project auto-link skipped: {link_err}")
        result = {
            "status": "partial" if payload.warnings else "success",
            "finished_at": datetime.now(timezone.utc),
            "campaigns_upserted": n_campaigns,
            "metric_rows_upserted": n_metrics,
            "posts_upserted": n_posts,
            "error": "; ".join(payload.warnings)[:2000] or None,
        }
    except ConnectorAuthError as err:
        logger.warning("[ads] %s credentials rejected: %s", spec.ad_account_id, err.message)
        result = {"status": "failed", "finished_at": datetime.now(timezone.utc),
                  "error": f"Credentials rejected by {spec.platform}: {err.message}"[:2000]}
    except ConnectorError as err:
        logger.warning("[ads] %s sync failed: %s", spec.ad_account_id, err.message)
        result = {"status": "failed", "finished_at": datetime.now(timezone.utc), "error": err.message[:2000]}
    except Exception as err:
        logger.exception("[ads] %s sync crashed", spec.ad_account_id)
        result = {"status": "failed", "finished_at": datetime.now(timezone.utc),
                  "error": f"{type(err).__name__}: {err}"[:2000]}

    await repo.finish_run(run["id"], result)
    return {**run, **result}


async def sync_all(repo, specs: list[ConnectorSpec], trigger: str, lookback_days: int,
                   today: Optional[date] = None) -> list[dict[str, Any]]:
    """Manual / explicit sync of every given account over the same window."""
    lookback_days = max(1, min(int(lookback_days), MAX_LOOKBACK_DAYS))
    until = today or reporting_today()
    since = until - timedelta(days=lookback_days - 1)
    async with _process_lock:
        runs = await repo.recent_runs()
        return [await sync_account(repo, spec, since, until, trigger, runs) for spec in specs]


async def run_due_syncs(repo, specs: list[ConnectorSpec], now: Optional[datetime] = None) -> list[dict[str, Any]]:
    """One scheduler tick: run whatever each account is due for."""
    now = now or datetime.now(timezone.utc)
    if _process_lock.locked():
        return []
    async with _process_lock:
        runs = await repo.recent_runs()
        results = []
        until = reporting_today(now)
        for spec in specs:
            plan = plan_trigger(runs, spec.ad_account_id, now)
            if not plan:
                continue
            trigger, days = plan
            since = until - timedelta(days=days - 1)
            results.append(await sync_account(repo, spec, since, until, trigger, runs))
        return results


_WORKER_RUNNING = False


async def ads_sync_worker(check_interval_seconds: int = 60) -> None:
    """Background loop: every tick, sync each configured ad account that is due."""
    global _WORKER_RUNNING
    from app.repositories.ads_repository import get_ads_repository
    from app.services.ads.factory import build_connectors

    _WORKER_RUNNING = True
    logger.info("[ads] Sync worker started (tick every %ss, interval %s min).",
                check_interval_seconds, settings.ads_sync_interval_minutes)
    while _WORKER_RUNNING:
        try:
            repo = get_ads_repository()
            specs = await build_connectors() if (repo and settings.ads_sync_enabled) else []
            if specs:
                for result in await run_due_syncs(repo, specs):
                    logger.info("[ads] %s %s sync %s (%s → %s): %s campaigns, %s metric rows, %s posts%s",
                                result["ad_account_id"], result["trigger"], result["status"],
                                result["since_date"], result["until_date"],
                                result.get("campaigns_upserted", 0), result.get("metric_rows_upserted", 0),
                                result.get("posts_upserted", 0),
                                f" — {result['error']}" if result.get("error") else "")
        except asyncio.CancelledError:
            break
        except Exception as err:
            logger.warning("[ads] Sync worker tick failed: %s", err)
        await asyncio.sleep(check_interval_seconds)
    logger.info("[ads] Sync worker stopped.")


def stop_ads_sync_worker() -> None:
    global _WORKER_RUNNING
    _WORKER_RUNNING = False
