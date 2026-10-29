"""TikTok Business API (Marketing API v1.3) connector, read-only.

Needs a long-term access token obtained from the advertiser's authorization of
the TikTok for Business developer app. TikTok returns every metric as a string.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any, Optional

import httpx

from app.services.ads.http import DEFAULT_TIMEOUT, request_json
from app.services.ads.types import (
    ACCOUNT_REACH_KEY,
    PLATFORM_TIKTOK,
    AdAccount,
    Campaign,
    ConnectorError,
    DailyMetric,
    PeriodReach,
    SyncPayload,
    to_float,
    to_int,
    to_opt_int,
)

BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"
REPORT_METRICS = [
    "campaign_name",
    "spend",
    "impressions",
    "reach",
    "clicks",
    "conversion",
    "likes",
    "comments",
    "shares",
    "video_play_actions",
    "video_views_p100",
]
OBJECTIVE_TO_TYPE = {
    "LEAD_GENERATION": "lead_generation",
    "REACH": "brand_awareness",
    "TRAFFIC": "traffic",
    "VIDEO_VIEWS": "video_views",
    "ENGAGEMENT": "engagement",
    "COMMUNITY_INTERACTION": "engagement",
    "CONVERSIONS": "sales",
    "WEB_CONVERSIONS": "sales",
    "PRODUCT_SALES": "sales",
}
# Day-level reports accept at most 30 days per request.
REPORT_CHUNK_DAYS = 30
RATE_LIMIT_CODES = {40100, 40133}
AUTH_CODES = {40001, 40104, 40105, 40106}


def _classify(status: int, body: Any) -> Optional[str]:
    if not isinstance(body, dict) or "code" not in body:
        return None
    code = body.get("code")
    if code == 0:
        return "ok"
    if code in RATE_LIMIT_CODES or 50000 <= int(code or 0) < 60000:
        return "retry"
    if code in AUTH_CODES:
        return "auth"
    return "fail"


def parse_report_row(row: dict[str, Any], account: AdAccount, objective_by_campaign: dict[str, str]) -> DailyMetric:
    dims = row.get("dimensions") or {}
    m = row.get("metrics") or {}
    campaign_id = str(dims.get("campaign_id"))
    conversions = to_float(m.get("conversion"))
    is_lead_gen = objective_by_campaign.get(campaign_id) == "LEAD_GENERATION"
    return DailyMetric(
        platform=PLATFORM_TIKTOK,
        external_campaign_id=campaign_id,
        metric_date=datetime.strptime(str(dims["stat_time_day"])[:10], "%Y-%m-%d").date(),
        channel="tiktok",
        ad_account_id=account.id,
        currency=account.currency,
        campaign_name=m.get("campaign_name"),
        impressions=to_int(m.get("impressions")),
        reach=to_opt_int(m.get("reach")),
        clicks=to_int(m.get("clicks")),
        link_clicks=to_int(m.get("clicks")),
        engagements=to_int(m.get("likes")) + to_int(m.get("comments")) + to_int(m.get("shares")),
        spend=to_float(m.get("spend")),
        # 'conversion' counts the optimization event; it is a lead only for
        # lead-generation campaigns.
        leads=int(round(conversions)) if is_lead_gen else 0,
        conversions=conversions,
        video_views=to_int(m.get("video_play_actions")),
        video_completions=to_int(m.get("video_views_p100")),
    )


class TikTokAdsConnector:
    platform = PLATFORM_TIKTOK

    def __init__(self, access_token: str, advertiser_id: str, client: Optional[httpx.AsyncClient] = None):
        self.access_token = access_token
        self.advertiser_id = str(advertiser_id).strip()
        self._client = client

    def _client_ctx(self) -> httpx.AsyncClient:
        return self._client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)

    async def _get(self, client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict[str, Any]:
        body = await request_json(client, self.platform, "GET", f"{BASE_URL}/{path.strip('/')}/", params=params,
                                  headers={"Access-Token": self.access_token}, classify=_classify)
        return body.get("data") or {}

    async def _get_pages(self, client: httpx.AsyncClient, path: str, params: dict[str, Any], max_pages: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            data = await self._get(client, path, {**params, "page": page, "page_size": 1000})
            rows.extend(data.get("list") or [])
            total_pages = to_int((data.get("page_info") or {}).get("total_page")) or 1
            if page >= total_pages:
                break
            page += 1
        return rows

    async def fetch_account(self, client: Optional[httpx.AsyncClient] = None) -> AdAccount:
        own = client is None
        client = client or self._client_ctx()
        try:
            data = await self._get(client, "advertiser/info", {
                "advertiser_ids": json.dumps([self.advertiser_id]),
                "fields": json.dumps(["name", "currency", "timezone", "status"]),
            })
        finally:
            if own and self._client is None:
                await client.aclose()
        info = (data.get("list") or [{}])[0]
        if not info:
            raise ConnectorError(self.platform, f"advertiser {self.advertiser_id} not visible to this token")
        return AdAccount(
            platform=self.platform,
            external_account_id=self.advertiser_id,
            name=info.get("name"),
            currency=info.get("currency"),
            timezone=info.get("timezone"),
            status="active" if str(info.get("status", "")).endswith("ENABLE") else "inactive",
        )

    async def fetch(self, since: date, until: date, reach_windows: tuple[int, ...] = (7, 30, 90),
                    include_posts: bool = False) -> SyncPayload:
        client = self._client_ctx()
        try:
            account = await self.fetch_account(client)
            payload = SyncPayload(account=account)

            objective_by_campaign: dict[str, str] = {}
            for r in await self._get_pages(client, "campaign/get", {"advertiser_id": self.advertiser_id}):
                cid = str(r.get("campaign_id"))
                objective = (r.get("objective_type") or "").upper()
                objective_by_campaign[cid] = objective
                budget_mode = r.get("budget_mode") or ""
                payload.campaigns.append(Campaign(
                    platform=self.platform,
                    external_id=cid,
                    ad_account_id=account.id,
                    name=r.get("campaign_name") or cid,
                    status="ACTIVE" if r.get("operation_status") == "ENABLE" else "PAUSED",
                    objective=objective or None,
                    campaign_type=OBJECTIVE_TO_TYPE.get(objective, "other"),
                    currency=account.currency,
                    budget_amount=to_float(r.get("budget")) if budget_mode != "BUDGET_MODE_INFINITE" else None,
                    budget_type="daily" if budget_mode == "BUDGET_MODE_DAY" else ("lifetime" if budget_mode == "BUDGET_MODE_TOTAL" else None),
                ))

            start = since
            while start <= until:
                end = min(start + timedelta(days=REPORT_CHUNK_DAYS - 1), until)
                rows = await self._get_pages(client, "report/integrated/get", {
                    "advertiser_id": self.advertiser_id,
                    "report_type": "BASIC",
                    "data_level": "AUCTION_CAMPAIGN",
                    "dimensions": json.dumps(["campaign_id", "stat_time_day"]),
                    "metrics": json.dumps(REPORT_METRICS),
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                })
                payload.daily_metrics.extend(
                    parse_report_row(r, account, objective_by_campaign)
                    for r in rows if (r.get("dimensions") or {}).get("stat_time_day")
                )
                start = end + timedelta(days=1)

            for days in reach_windows:
                w_since = until - timedelta(days=days - 1)
                common = {"advertiser_id": self.advertiser_id, "report_type": "BASIC",
                          "metrics": json.dumps(["reach"]), "start_date": w_since.isoformat(), "end_date": until.isoformat()}
                for r in await self._get_pages(client, "report/integrated/get", {
                        **common, "data_level": "AUCTION_CAMPAIGN", "dimensions": json.dumps(["campaign_id"])}):
                    payload.period_reach.append(PeriodReach(
                        self.platform, str((r.get("dimensions") or {}).get("campaign_id")), days, w_since, until,
                        to_opt_int((r.get("metrics") or {}).get("reach"))))
                acct_rows = await self._get_pages(client, "report/integrated/get", {
                    **common, "data_level": "AUCTION_ADVERTISER", "dimensions": json.dumps(["advertiser_id"])})
                if acct_rows:
                    payload.period_reach.append(PeriodReach(
                        self.platform, ACCOUNT_REACH_KEY, days, w_since, until,
                        to_opt_int((acct_rows[0].get("metrics") or {}).get("reach"))))
            return payload
        finally:
            if self._client is None:
                await client.aclose()
