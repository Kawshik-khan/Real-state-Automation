"""Ad platform sync control: status, manual sync, campaign → project links, FX rates."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import require_roles
from app.models.user import UserRole
from app.repositories.ads_repository import RepositoryError, get_ads_repository
from app.services.ads.factory import SERVICE_KEYS, build_connectors, load_credentials, split_ids
from app.services.ads.sync_service import HOURLY_LOOKBACK_DAYS, MAX_LOOKBACK_DAYS, reporting_today, sync_all
from app.services.ads.types import ALL_PLATFORMS

logger = logging.getLogger(__name__)
router = APIRouter()

PLATFORM_LABELS = {"meta": "Meta Ads (Facebook & Instagram)", "google_ads": "Google Ads", "tiktok": "TikTok Ads"}
_VIEW_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT, UserRole.DEVELOPER, UserRole.SERVICE]
_OPERATE_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.SERVICE]
_ADMIN_ROLES = [UserRole.ADMIN, UserRole.SERVICE]

# Strong references so manual sync tasks are not garbage-collected mid-run.
_background_tasks: set[asyncio.Task] = set()


class SyncRequest(BaseModel):
    platforms: Optional[list[str]] = None
    lookback_days: int = Field(default=HOURLY_LOOKBACK_DAYS, ge=1, le=MAX_LOOKBACK_DAYS)


class CampaignProjectLink(BaseModel):
    project_id: Optional[str] = None


class FxRateIn(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    rate_to_bdt: float = Field(gt=0)


def _require_repo():
    repo = get_ads_repository()
    if repo is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY).")
    return repo


@router.get("/status", summary="Ad platform connections and last sync results")
async def ads_status(user: dict = Depends(require_roles(_VIEW_ROLES))) -> dict[str, Any]:
    repo = get_ads_repository()
    runs: list[dict[str, Any]] = []
    accounts: list[dict[str, Any]] = []
    error: Optional[str] = None
    if repo:
        try:
            runs = await repo.recent_runs(limit=100)
            accounts = await repo.list_accounts()
        except RepositoryError as err:
            error = str(err)

    platforms = []
    for platform in ALL_PLATFORMS:
        creds = await load_credentials(platform)
        ids_field = {"meta": "ad_account_ids", "google_ads": "customer_ids", "tiktok": "advertiser_ids"}[platform]
        platform_runs = [r for r in runs if r.get("platform") == platform]
        last_success = next((r for r in platform_runs if r.get("status") in ("success", "partial")), None)
        platforms.append({
            "platform": platform,
            "display_name": PLATFORM_LABELS[platform],
            "service_key": SERVICE_KEYS[platform],
            "configured": bool(creds),
            "account_count": len(split_ids(creds.get(ids_field))) if creds else 0,
            "accounts": [
                {"id": a["id"], "name": a.get("name"), "currency": a.get("currency"),
                 "last_synced_at": a.get("last_synced_at")}
                for a in accounts if a.get("platform") == platform
            ],
            "last_run": platform_runs[0] if platform_runs else None,
            "last_success_at": (last_success or {}).get("finished_at"),
        })
    return {
        "success": True,
        "repository_configured": repo is not None,
        "sync_enabled": settings.ads_sync_enabled,
        "sync_interval_minutes": settings.ads_sync_interval_minutes,
        "running": any(r.get("status") == "running" for r in runs[:20]),
        "platforms": platforms,
        "error": error,
    }


@router.post("/sync", status_code=202, summary="Start a manual ad metrics sync")
async def trigger_sync(body: SyncRequest, user: dict = Depends(require_roles(_OPERATE_ROLES))) -> dict[str, Any]:
    repo = _require_repo()
    platforms = [p for p in (body.platforms or list(ALL_PLATFORMS)) if p in ALL_PLATFORMS]
    specs = await build_connectors(platforms)
    if not specs:
        raise HTTPException(status_code=409, detail="No ad platform credentials are configured for the requested platforms.")

    async def _run():
        try:
            await sync_all(repo, specs, trigger="manual", lookback_days=body.lookback_days)
        except Exception:
            logger.exception("[ads] Manual sync failed")

    task = asyncio.create_task(_run())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    until = reporting_today()
    return {
        "success": True,
        "accepted": True,
        "accounts": [s.ad_account_id for s in specs],
        "lookback_days": body.lookback_days,
        "until": until.isoformat(),
        "message": "Sync started. Poll /api/v1/ads/status for the result.",
    }


@router.patch("/campaigns/{platform}/{external_id}/project", summary="Link a synced campaign to a project")
async def link_campaign_project(platform: str, external_id: str, body: CampaignProjectLink,
                                user: dict = Depends(require_roles(_OPERATE_ROLES))) -> dict[str, Any]:
    if platform not in ALL_PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")
    repo = _require_repo()
    await repo.set_campaign_project(platform, external_id, body.project_id)
    return {"success": True, "platform": platform, "external_id": external_id, "project_id": body.project_id}


@router.get("/fx-rates", summary="Currency conversion rates into BDT")
async def list_fx_rates(user: dict = Depends(require_roles(_VIEW_ROLES))) -> dict[str, Any]:
    repo = _require_repo()
    return {"success": True, "rates": await repo.list_fx_rates()}


@router.put("/fx-rates", summary="Set a currency's conversion rate into BDT")
async def set_fx_rate(body: FxRateIn, user: dict = Depends(require_roles(_ADMIN_ROLES))) -> dict[str, Any]:
    repo = _require_repo()
    await repo.upsert_fx_rate(body.currency, body.rate_to_bdt, source=f"manual:{user.get('email') or user.get('sub') or 'admin'}")
    return {"success": True, "currency": body.currency.upper(), "rate_to_bdt": body.rate_to_bdt}
