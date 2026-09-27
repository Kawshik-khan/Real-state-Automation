"""In-memory stand-ins for AdsRepository and ad connectors used by the ads tests.

FakeAdsRepository mirrors AdsRepository's upsert keys and read filters closely
enough to run sync → storage → dashboard end to end without Supabase.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from app.repositories.ads_repository import match_project
from app.services.ads.types import AdAccount, Campaign, DailyMetric, PeriodReach, SocialPost, SyncPayload


def _d(value: Any) -> str:
    return value.isoformat() if isinstance(value, (date, datetime)) else str(value)


class FakeAdsRepository:
    def __init__(self) -> None:
        self.accounts: dict[str, dict] = {}
        self.campaigns: dict[tuple, dict] = {}
        self.metrics: dict[tuple, dict] = {}
        self.reach: dict[tuple, dict] = {}
        self.posts: dict[tuple, dict] = {}
        self.runs: list[dict] = []
        self.leads: dict[str, dict] = {}
        self.projects: list[dict] = []
        self.fx_rates: list[dict] = []
        self.conversations: list[dict] = []
        self.messages: list[dict] = []
        self.bookings: list[dict] = []
        self.milestones: list[dict] = []
        self.pending_posts = 0
        self.demo_campaigns: list[dict] = []
        self.demo_posts: list[dict] = []

    # ── writes ──────────────────────────────────────────────────────────
    async def upsert_account(self, account: AdAccount, synced_at: datetime) -> None:
        self.accounts[account.id] = {"id": account.id, "platform": account.platform, "name": account.name,
                                     "currency": account.currency, "last_synced_at": synced_at.isoformat()}

    async def upsert_campaigns(self, campaigns: list[Campaign], synced_at: datetime) -> int:
        for c in campaigns:
            key = (c.platform, c.external_id)
            existing = self.campaigns.get(key, {})
            self.campaigns[key] = {
                **existing,
                "platform": c.platform, "external_id": c.external_id, "ad_account_id": c.ad_account_id,
                "campaign_name": c.name, "status": c.status.lower(), "objective": c.objective,
                "campaign_type": c.campaign_type, "currency": c.currency, "budget_amount": c.budget_amount,
                "budget_type": c.budget_type, "is_demo": False, "project_id": existing.get("project_id"),
            }
        return len(campaigns)

    async def upsert_daily_metrics(self, metrics: list[DailyMetric], synced_at: datetime) -> int:
        for m in metrics:
            self.metrics[(m.platform, m.external_campaign_id, m.metric_date.isoformat(), m.channel)] = {
                "platform": m.platform, "external_campaign_id": m.external_campaign_id,
                "metric_date": m.metric_date.isoformat(), "channel": m.channel, "currency": m.currency,
                "impressions": m.impressions, "reach": m.reach, "clicks": m.clicks, "link_clicks": m.link_clicks,
                "engagements": m.engagements, "spend": m.spend, "leads": m.leads,
                "messaging_conversations": m.messaging_conversations, "conversions": m.conversions,
                "video_views": m.video_views, "video_completions": m.video_completions,
            }
        return len(metrics)

    async def upsert_period_reach(self, reach: list[PeriodReach], synced_at: datetime) -> int:
        for r in reach:
            self.reach[(r.platform, r.external_campaign_id, r.window_days)] = {
                "platform": r.platform, "external_campaign_id": r.external_campaign_id,
                "window_days": r.window_days, "since_date": r.since_date.isoformat(),
                "until_date": r.until_date.isoformat(), "reach": r.reach,
            }
        return len(reach)

    async def upsert_posts(self, posts: list[SocialPost], synced_at: datetime) -> int:
        for p in posts:
            self.posts[(p.platform, p.external_post_id)] = {
                "id": f"{p.platform}-{p.external_post_id}", "platform": p.platform, "external_post_id": p.external_post_id,
                "topic": (p.message or "").splitlines()[0][:120] if p.message else f"{p.platform} post",
                "post_content": p.message, "published_at": _d(p.published_at) if p.published_at else None,
                "likes_count": p.likes, "comments_count": p.comments, "shares_count": p.shares,
                "views": p.views, "reach": p.reach, "saves": p.saves, "is_demo": False,
            }
        return len(posts)

    async def start_run(self, row: dict) -> None:
        self.runs.insert(0, {k: _d(v) if isinstance(v, (date, datetime)) else v for k, v in row.items()})

    async def finish_run(self, run_id: str, values: dict) -> None:
        for run in self.runs:
            if run["id"] == run_id:
                run.update({k: _d(v) if isinstance(v, (date, datetime)) else v for k, v in values.items()})

    async def recent_runs(self, limit: int = 200) -> list[dict]:
        return self.runs[:limit]

    async def auto_link_projects(self) -> int:
        linked = 0
        for c in self.campaigns.values():
            if not c.get("project_id"):
                pid = match_project(c["campaign_name"], self.projects)
                if pid:
                    c["project_id"] = pid
                    linked += 1
        return linked

    async def set_campaign_project(self, platform: str, external_id: str, project_id: Optional[str]) -> None:
        self.campaigns[(platform, external_id)]["project_id"] = project_id

    async def upsert_fx_rate(self, currency: str, rate_to_bdt: float, source: str = "manual") -> None:
        self.fx_rates = [r for r in self.fx_rates if r["currency"] != currency.upper()]
        self.fx_rates.append({"currency": currency.upper(), "rate_to_bdt": rate_to_bdt, "source": source})

    async def upsert_lead(self, row: dict) -> None:
        self.leads[row["lead_id"]] = row

    # ── reads ───────────────────────────────────────────────────────────
    async def list_projects(self) -> list[dict]:
        return list(self.projects)

    async def list_campaigns(self, demo: bool = False) -> list[dict]:
        return list(self.demo_campaigns) if demo else list(self.campaigns.values())

    async def list_daily_metrics(self, since: date, until: date) -> list[dict]:
        return [m for m in self.metrics.values() if since.isoformat() <= m["metric_date"] <= until.isoformat()]

    async def list_period_reach(self) -> list[dict]:
        return list(self.reach.values())

    async def list_accounts(self) -> list[dict]:
        return list(self.accounts.values())

    async def list_posts(self, demo: bool = False, limit: int = 200) -> list[dict]:
        return list(self.demo_posts) if demo else list(self.posts.values())[:limit]

    async def count_pending_posts(self) -> int:
        return self.pending_posts

    async def list_fx_rates(self) -> list[dict]:
        return list(self.fx_rates)

    async def list_conversations_since(self, since: datetime) -> list[dict]:
        return [c for c in self.conversations if c["created_at"] >= since.isoformat()]

    async def list_messages_for(self, conversation_ids: list[str]) -> list[dict]:
        return [m for m in self.messages if m["conversation_id"] in conversation_ids]

    async def list_bookings(self, since: date, until: date) -> list[dict]:
        return [b for b in self.bookings if since.isoformat() <= b["tour_date"] <= until.isoformat()]

    async def list_tour_milestones(self, since: date, until: date) -> list[dict]:
        return [m for m in self.milestones if since.isoformat() <= m["milestone_date"] <= until.isoformat()]


class FakeConnector:
    """Returns a fixed payload; can be told to raise instead."""

    def __init__(self, payload: SyncPayload, error: Optional[Exception] = None):
        self.payload = payload
        self.error = error
        self.calls: list[tuple] = []

    async def fetch(self, since: date, until: date, reach_windows=(7, 30, 90), include_posts: bool = True) -> SyncPayload:
        self.calls.append((since, until, include_posts))
        if self.error:
            raise self.error
        return self.payload
