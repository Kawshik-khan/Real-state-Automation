"""Google Ads API connector (REST googleAds:searchStream, read-only).

Needs a developer token (Basic access or higher), an OAuth client and a refresh
token for a user with access to the customer. Search campaigns expose no reach,
so reach is left NULL rather than reported as zero.
"""

from __future__ import annotations

import time
from datetime import date
from typing import Any, Optional

import httpx

from app.services.ads.http import DEFAULT_TIMEOUT, request_json
from app.services.ads.types import (
    PLATFORM_GOOGLE,
    AdAccount,
    Campaign,
    ConnectorAuthError,
    DailyMetric,
    SyncPayload,
    to_float,
    to_int,
)

TOKEN_URL = "https://oauth2.googleapis.com/token"

CHANNEL_TYPE_TO_CHANNEL = {
    "SEARCH": "google_search",
    "DISPLAY": "google_display",
    "VIDEO": "youtube",
    "PERFORMANCE_MAX": "google_pmax",
    "DEMAND_GEN": "google_demand_gen",
    "SHOPPING": "google_shopping",
}
CHANNEL_TYPE_TO_CAMPAIGN_TYPE = {
    "SEARCH": "traffic",
    "DISPLAY": "brand_awareness",
    "VIDEO": "video_views",
    "DEMAND_GEN": "engagement",
    "SHOPPING": "sales",
}
STATUS_MAP = {"ENABLED": "ACTIVE", "PAUSED": "PAUSED", "REMOVED": "DELETED"}


def _classify(status: int, body: Any) -> Optional[str]:
    # searchStream returns a JSON array on success and an object on error.
    if isinstance(body, list):
        return "ok" if status < 400 else "fail"
    err = body.get("error") if isinstance(body, dict) else None
    if not err:
        return None
    grpc_status = (err.get("status") or "").upper()
    if grpc_status in ("UNAUTHENTICATED", "PERMISSION_DENIED") or status in (401, 403):
        return "auth"
    if grpc_status in ("RESOURCE_EXHAUSTED", "UNAVAILABLE", "INTERNAL", "DEADLINE_EXCEEDED"):
        return "retry"
    return "fail"


def _digits(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return "".join(ch for ch in str(raw) if ch.isdigit()) or None


def parse_daily_row(row: dict[str, Any], account: AdAccount) -> DailyMetric:
    campaign = row.get("campaign") or {}
    metrics = row.get("metrics") or {}
    segments = row.get("segments") or {}
    channel_type = (campaign.get("advertisingChannelType") or "").upper()
    conversions = to_float(metrics.get("conversions"))
    return DailyMetric(
        platform=PLATFORM_GOOGLE,
        external_campaign_id=str(campaign.get("id")),
        metric_date=date.fromisoformat(segments["date"]),
        channel=CHANNEL_TYPE_TO_CHANNEL.get(channel_type, "google_other"),
        ad_account_id=account.id,
        currency=account.currency,
        campaign_name=campaign.get("name"),
        impressions=to_int(metrics.get("impressions")),
        reach=None,
        clicks=to_int(metrics.get("clicks")),
        link_clicks=to_int(metrics.get("clicks")),
        engagements=to_int(metrics.get("engagements")),
        spend=round(to_int(metrics.get("costMicros")) / 1_000_000, 2),
        # Google has no 'lead' action; conversions are the lead signal when the
        # account's conversion actions are lead forms / calls (the usual setup).
        leads=int(round(conversions)),
        conversions=conversions,
    )


class GoogleAdsConnector:
    platform = PLATFORM_GOOGLE

    def __init__(
        self,
        developer_token: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        customer_id: str,
        login_customer_id: Optional[str] = None,
        api_version: str = "v25",
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.developer_token = developer_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.customer_id = _digits(customer_id) or ""
        self.login_customer_id = _digits(login_customer_id)
        self.base_url = f"https://googleads.googleapis.com/{api_version}"
        self._client = client
        self._token: Optional[str] = None
        self._token_expiry = 0.0

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        def classify(status: int, body: Any) -> Optional[str]:
            if isinstance(body, dict) and body.get("error") in ("invalid_grant", "invalid_client", "unauthorized_client"):
                return "auth"
            return None

        body = await request_json(client, self.platform, "POST", TOKEN_URL, data={
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }, classify=classify)
        token = body.get("access_token") if isinstance(body, dict) else None
        if not token:
            raise ConnectorAuthError(self.platform, "OAuth token response had no access_token")
        self._token = token
        self._token_expiry = time.time() + float(body.get("expires_in") or 3000)
        return token

    async def search(self, client: httpx.AsyncClient, query: str) -> list[dict[str, Any]]:
        token = await self._access_token(client)
        headers = {
            "Authorization": f"Bearer {token}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json",
        }
        if self.login_customer_id:
            headers["login-customer-id"] = self.login_customer_id
        batches = await request_json(
            client, self.platform, "POST",
            f"{self.base_url}/customers/{self.customer_id}/googleAds:searchStream",
            json={"query": query}, headers=headers, classify=_classify,
        )
        results: list[dict[str, Any]] = []
        for batch in batches if isinstance(batches, list) else []:
            results.extend(batch.get("results", []))
        return results

    def _client_ctx(self) -> httpx.AsyncClient:
        return self._client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)

    async def fetch_account(self, client: Optional[httpx.AsyncClient] = None) -> AdAccount:
        own = client is None
        client = client or self._client_ctx()
        try:
            rows = await self.search(client, "SELECT customer.id, customer.descriptive_name, customer.currency_code, "
                                             "customer.time_zone, customer.status FROM customer LIMIT 1")
        finally:
            if own and self._client is None:
                await client.aclose()
        customer = (rows[0] if rows else {}).get("customer") or {}
        return AdAccount(
            platform=self.platform,
            external_account_id=self.customer_id,
            name=customer.get("descriptiveName"),
            currency=customer.get("currencyCode"),
            timezone=customer.get("timeZone"),
            status="active" if customer.get("status") in (None, "ENABLED") else "inactive",
        )

    async def fetch(self, since: date, until: date, reach_windows: tuple[int, ...] = (7, 30, 90),
                    include_posts: bool = False) -> SyncPayload:
        client = self._client_ctx()
        try:
            account = await self.fetch_account(client)
            payload = SyncPayload(account=account)

            campaign_rows = await self.search(client, (
                "SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, "
                "campaign_budget.amount_micros FROM campaign WHERE campaign.status != 'REMOVED'"
            ))
            for row in campaign_rows:
                c = row.get("campaign") or {}
                channel_type = (c.get("advertisingChannelType") or "").upper()
                budget_micros = (row.get("campaignBudget") or {}).get("amountMicros")
                payload.campaigns.append(Campaign(
                    platform=self.platform,
                    external_id=str(c.get("id")),
                    ad_account_id=account.id,
                    name=c.get("name") or str(c.get("id")),
                    status=STATUS_MAP.get((c.get("status") or "").upper(), "UNKNOWN"),
                    objective=channel_type or None,
                    campaign_type=CHANNEL_TYPE_TO_CAMPAIGN_TYPE.get(channel_type, "other"),
                    currency=account.currency,
                    budget_amount=round(to_int(budget_micros) / 1_000_000, 2) if budget_micros else None,
                    budget_type="daily" if budget_micros else None,
                ))

            daily_rows = await self.search(client, (
                "SELECT campaign.id, campaign.name, campaign.advertising_channel_type, segments.date, "
                "metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.engagements "
                f"FROM campaign WHERE segments.date BETWEEN '{since.isoformat()}' AND '{until.isoformat()}'"
            ))
            payload.daily_metrics = [parse_daily_row(r, account) for r in daily_rows if (r.get("segments") or {}).get("date")]
            # Reach is not available for Search/PMax reporting; nothing to store.
            return payload
        finally:
            if self._client is None:
                await client.aclose()
