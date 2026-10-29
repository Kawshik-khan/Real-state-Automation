"""Async Supabase (PostgREST) data access for ad metrics, posts, leads and dashboard inputs.

This is the single data path for the ads pipeline: the sync worker writes through
it and the /social-kpis and /manager-overview endpoints read through it. It talks
HTTPS to Supabase (the path that works in the Render deployment) and requires the
service_role key, because migration 0008 removes public access to these tables.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from typing import Any, Iterable, Optional

import httpx

from app.config import settings
from app.services.ads.types import AdAccount, Campaign, DailyMetric, PeriodReach, SocialPost

logger = logging.getLogger(__name__)

PENDING_POST_STATUSES = ("pending", "draft", "pending_approval")


class RepositoryError(Exception):
    pass


def _iso(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _in_list(values: Iterable[str]) -> str:
    quoted = ",".join('"' + str(v).replace('"', '') + '"' for v in values)
    return f"in.({quoted})"


class SupabaseRestClient:
    """Minimal async PostgREST client (select with paging, count, upsert, patch)."""

    def __init__(self, url: str, key: str, client: Optional[httpx.AsyncClient] = None, timeout: float = 20.0):
        self.base = url.rstrip("/") + "/rest/v1"
        self.key = key
        self._client = client
        self._timeout = timeout

    def _headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if extra:
            headers.update(extra)
        return headers

    async def _send(self, method: str, table: str, *, params: Any = None, json: Any = None,
                    headers: Optional[dict[str, str]] = None) -> httpx.Response:
        url = f"{self.base}/{table}"
        if self._client is not None:
            resp = await self._client.request(method, url, params=params, json=json, headers=self._headers(headers))
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(method, url, params=params, json=json, headers=self._headers(headers))
        if resp.status_code >= 400:
            raise RepositoryError(f"{method} {table} failed: HTTP {resp.status_code} {resp.text[:300]}")
        return resp

    async def select(self, table: str, params: Optional[dict[str, Any]] = None, page_size: int = 1000,
                     max_rows: int = 100_000) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        while offset < max_rows:
            query = {**(params or {}), "limit": page_size, "offset": offset}
            resp = await self._send("GET", table, params=query)
            batch = resp.json() if resp.content else []
            rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        return rows

    async def count(self, table: str, params: Optional[dict[str, Any]] = None) -> int:
        resp = await self._send("GET", table, params={**(params or {}), "select": "*", "limit": 1},
                                headers={"Prefer": "count=exact"})
        content_range = resp.headers.get("content-range", "")
        total = content_range.rsplit("/", 1)[-1] if "/" in content_range else ""
        return int(total) if total.isdigit() else len(resp.json() or [])

    async def upsert(self, table: str, rows: list[dict[str, Any]], on_conflict: str, chunk_size: int = 500) -> int:
        if not rows:
            return 0
        for i in range(0, len(rows), chunk_size):
            await self._send("POST", table, params={"on_conflict": on_conflict}, json=rows[i:i + chunk_size],
                             headers={"Prefer": "resolution=merge-duplicates,return=minimal"})
        return len(rows)

    async def insert(self, table: str, row: dict[str, Any]) -> None:
        await self._send("POST", table, json=row, headers={"Prefer": "return=minimal"})

    async def patch(self, table: str, filters: dict[str, str], values: dict[str, Any]) -> None:
        await self._send("PATCH", table, params=filters, json=values, headers={"Prefer": "return=minimal"})


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def match_project(campaign_name: str, projects: list[dict[str, Any]]) -> Optional[str]:
    """Longest project name contained in the campaign name wins (e.g. 'GLG Sky Tower')."""
    name = f" {_norm(campaign_name)} "
    best: tuple[int, Optional[str]] = (0, None)
    for p in projects:
        pname = _norm(p.get("name") or "")
        if len(pname) >= 4 and f" {pname} " in name and len(pname) > best[0]:
            best = (len(pname), p.get("project_id"))
    return best[1]


class AdsRepository:
    def __init__(self, rest: SupabaseRestClient):
        self.rest = rest

    # ── sync writes ─────────────────────────────────────────────────────
    async def upsert_account(self, account: AdAccount, synced_at: datetime) -> None:
        await self.rest.upsert("ad_accounts", [{
            "id": account.id,
            "platform": account.platform,
            "external_account_id": account.external_account_id,
            "name": account.name,
            "currency": account.currency,
            "timezone": account.timezone,
            "status": account.status,
            "last_synced_at": synced_at.isoformat(),
            "updated_at": synced_at.isoformat(),
        }], on_conflict="id")

    async def upsert_campaigns(self, campaigns: list[Campaign], synced_at: datetime) -> int:
        rows = [{
            "platform": c.platform,
            "external_id": c.external_id,
            "ad_account_id": c.ad_account_id,
            "campaign_name": c.name[:256],
            "status": (c.status or "unknown").lower(),
            "objective": c.objective,
            "campaign_type": c.campaign_type,
            "currency": c.currency,
            "budget_amount": c.budget_amount,
            "budget_type": c.budget_type,
            "source": c.platform,
            "is_demo": False,
            "last_synced_at": synced_at.isoformat(),
            "updated_at": synced_at.isoformat(),
        } for c in campaigns]
        return await self.rest.upsert("ad_campaigns", rows, on_conflict="platform,external_id")

    async def upsert_daily_metrics(self, metrics: list[DailyMetric], synced_at: datetime) -> int:
        rows = [{
            "platform": m.platform,
            "external_campaign_id": m.external_campaign_id,
            "metric_date": m.metric_date.isoformat(),
            "channel": m.channel,
            "ad_account_id": m.ad_account_id,
            "currency": m.currency,
            "impressions": m.impressions,
            "reach": m.reach,
            "clicks": m.clicks,
            "link_clicks": m.link_clicks,
            "engagements": m.engagements,
            "spend": round(m.spend, 2),
            "leads": m.leads,
            "messaging_conversations": m.messaging_conversations,
            "conversions": round(m.conversions, 2),
            "video_views": m.video_views,
            "video_completions": m.video_completions,
            "raw": m.raw,
            "synced_at": synced_at.isoformat(),
        } for m in metrics]
        return await self.rest.upsert("ad_campaign_daily_metrics", rows,
                                      on_conflict="platform,external_campaign_id,metric_date,channel")

    async def upsert_period_reach(self, reach: list[PeriodReach], synced_at: datetime) -> int:
        rows = [{
            "platform": r.platform,
            "external_campaign_id": r.external_campaign_id,
            "window_days": r.window_days,
            "since_date": r.since_date.isoformat(),
            "until_date": r.until_date.isoformat(),
            "reach": r.reach,
            "synced_at": synced_at.isoformat(),
        } for r in reach]
        return await self.rest.upsert("ad_campaign_period_reach", rows,
                                      on_conflict="platform,external_campaign_id,window_days")

    async def upsert_posts(self, posts: list[SocialPost], synced_at: datetime) -> int:
        rows = []
        for p in posts:
            first_line = (p.message or "").strip().splitlines()[0] if (p.message or "").strip() else ""
            topic = first_line[:120] or f"{p.platform.title()} post {p.published_at.date().isoformat() if p.published_at else ''}".strip()
            rows.append({
                "platform": p.platform,
                "external_post_id": p.external_post_id,
                "topic": topic,
                "post_content": p.message or "",
                "permalink": p.permalink,
                "media_url": p.media_url,
                "media_type": p.media_type,
                "status": "published",
                "published_at": _iso(p.published_at),
                "likes_count": p.likes,
                "comments_count": p.comments,
                "shares_count": p.shares,
                "views": p.views,
                "reach": p.reach,
                "saves": p.saves,
                "metrics_synced_at": synced_at.isoformat(),
                "source": "platform_sync",
                "created_by": "platform_sync",
                "is_demo": False,
                "updated_at": synced_at.isoformat(),
            })
        return await self.rest.upsert("social_posts", rows, on_conflict="platform,external_post_id")

    async def start_run(self, row: dict[str, Any]) -> None:
        await self.rest.insert("ad_sync_runs", {k: _iso(v) for k, v in row.items()})

    async def finish_run(self, run_id: str, values: dict[str, Any]) -> None:
        await self.rest.patch("ad_sync_runs", {"id": f"eq.{run_id}"}, {k: _iso(v) for k, v in values.items()})

    async def recent_runs(self, limit: int = 200) -> list[dict[str, Any]]:
        return await self.rest.select("ad_sync_runs", {"select": "*", "order": "started_at.desc"},
                                      page_size=limit, max_rows=limit)

    async def auto_link_projects(self) -> int:
        """Attach synced campaigns to a project when the campaign name contains its name."""
        unlinked = await self.rest.select("ad_campaigns", {
            "select": "platform,external_id,campaign_name",
            "project_id": "is.null", "is_demo": "eq.false", "external_id": "not.is.null",
        })
        if not unlinked:
            return 0
        projects = await self.list_projects()
        linked = 0
        for c in unlinked:
            project_id = match_project(c.get("campaign_name") or "", projects)
            if project_id:
                await self.set_campaign_project(c["platform"], c["external_id"], project_id)
                linked += 1
        return linked

    async def set_campaign_project(self, platform: str, external_id: str, project_id: Optional[str]) -> None:
        await self.rest.patch("ad_campaigns", {"platform": f"eq.{platform}", "external_id": f"eq.{external_id}"},
                              {"project_id": project_id})

    async def upsert_fx_rate(self, currency: str, rate_to_bdt: float, source: str = "manual") -> None:
        await self.rest.upsert("fx_rates", [{
            "currency": currency.upper(), "rate_to_bdt": rate_to_bdt, "source": source,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }], on_conflict="currency")

    async def upsert_lead(self, row: dict[str, Any]) -> None:
        await self.rest.upsert("leads", [{k: _iso(v) for k, v in row.items()}], on_conflict="lead_id")

    # ── dashboard reads ─────────────────────────────────────────────────
    async def list_projects(self) -> list[dict[str, Any]]:
        return await self.rest.select("projects", {"select": "project_id,name", "order": "name.asc"})

    async def list_campaigns(self, demo: bool = False) -> list[dict[str, Any]]:
        params = {"select": "*", "order": "campaign_name.asc", "is_demo": f"eq.{str(demo).lower()}"}
        if not demo:
            params["external_id"] = "not.is.null"
        return await self.rest.select("ad_campaigns", params)

    async def list_daily_metrics(self, since: date, until: date) -> list[dict[str, Any]]:
        return await self.rest.select("ad_campaign_daily_metrics", {
            "select": "platform,external_campaign_id,metric_date,channel,currency,impressions,reach,clicks,"
                      "link_clicks,engagements,spend,leads,messaging_conversations,conversions,video_views,video_completions",
            "and": f"(metric_date.gte.{since.isoformat()},metric_date.lte.{until.isoformat()})",
            "order": "metric_date.asc,platform.asc,external_campaign_id.asc,channel.asc",
        })

    async def list_period_reach(self) -> list[dict[str, Any]]:
        return await self.rest.select("ad_campaign_period_reach", {"select": "*"})

    async def list_accounts(self) -> list[dict[str, Any]]:
        return await self.rest.select("ad_accounts", {"select": "*", "order": "platform.asc"})

    async def list_posts(self, demo: bool = False, limit: int = 200) -> list[dict[str, Any]]:
        params = {"select": "*", "order": "published_at.desc.nullslast", "is_demo": f"eq.{str(demo).lower()}"}
        if not demo:
            params["external_post_id"] = "not.is.null"
        return await self.rest.select("social_posts", params, page_size=limit, max_rows=limit)

    async def count_pending_posts(self) -> int:
        return await self.rest.count("social_posts", {"status": _in_list(PENDING_POST_STATUSES), "is_demo": "eq.false"})

    async def list_fx_rates(self) -> list[dict[str, Any]]:
        return await self.rest.select("fx_rates", {"select": "*"})

    async def list_conversations_since(self, since: datetime) -> list[dict[str, Any]]:
        return await self.rest.select("conversations", {
            "select": "conversation_id,channel,status,created_at",
            "created_at": f"gte.{since.isoformat()}", "order": "created_at.asc",
        })

    async def list_messages_for(self, conversation_ids: list[str]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for i in range(0, len(conversation_ids), 100):
            rows.extend(await self.rest.select("messages", {
                "select": "conversation_id,sender,created_at",
                "conversation_id": _in_list(conversation_ids[i:i + 100]),
                "order": "created_at.asc",
            }))
        return rows

    async def list_bookings(self, since: date, until: date) -> list[dict[str, Any]]:
        return await self.rest.select("bookings", {
            "select": "id,status,tour_date,project_id",
            "and": f"(tour_date.gte.{since.isoformat()},tour_date.lte.{until.isoformat()})",
        })

    async def list_tour_milestones(self, since: date, until: date) -> list[dict[str, Any]]:
        return await self.rest.select("calendar_milestones", {
            "select": "id,status,milestone_date,project_id",
            "milestone_type": "eq.tour",
            "and": f"(milestone_date.gte.{since.isoformat()},milestone_date.lte.{until.isoformat()})",
        })

    async def list_leads_since(self, since: datetime) -> list[dict[str, Any]]:
        return await self.rest.select("leads", {
            "select": "lead_id,source,platform,external_campaign_id,created_at",
            "created_at": f"gte.{since.isoformat()}",
        })


def get_ads_repository() -> Optional[AdsRepository]:
    """Repository when Supabase is configured, else None (dashboards report 'unconfigured')."""
    url = settings.supabase_url
    key = settings.supabase_service_role_key or settings.supabase_anon_key
    if not url or not key:
        return None
    if not settings.supabase_service_role_key:
        logger.warning("[ads] SUPABASE_SERVICE_ROLE_KEY is not set; reads/writes will fail once RLS lockdown (0008) is applied.")
    return AdsRepository(SupabaseRestClient(url, key))
