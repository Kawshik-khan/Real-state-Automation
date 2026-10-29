"""Meta Marketing API connector (Facebook & Instagram ads, plus organic posts).

Read-only. Needs a system-user access token with `ads_read`; organic post metrics
additionally need `pages_read_engagement`, `read_insights`, `instagram_basic` and
`instagram_manage_insights` on the page token.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from app.services.ads.http import DEFAULT_TIMEOUT, request_json
from app.services.ads.types import (
    ACCOUNT_REACH_KEY,
    PLATFORM_META,
    AdAccount,
    Campaign,
    ConnectorError,
    DailyMetric,
    PeriodReach,
    SocialPost,
    SyncPayload,
    to_float,
    to_int,
    to_opt_int,
)

logger = logging.getLogger(__name__)

INSIGHT_FIELDS = ",".join([
    "campaign_id",
    "campaign_name",
    "date_start",
    "spend",
    "impressions",
    "reach",
    "clicks",
    "inline_link_clicks",
    "inline_post_engagement",
    "actions",
    "video_play_actions",
    "video_p100_watched_actions",
])

# 'lead' is Meta's de-duplicated total of all lead actions; the other two are
# its components, used only when 'lead' is absent (never summed with it).
LEAD_ACTION = "lead"
LEAD_COMPONENT_ACTIONS = ("onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead")
MESSAGING_ACTION = "onsite_conversion.messaging_conversation_started_7d"

OBJECTIVE_TO_TYPE = {
    "OUTCOME_LEADS": "lead_generation",
    "LEAD_GENERATION": "lead_generation",
    "MESSAGES": "messages",
    "OUTCOME_TRAFFIC": "traffic",
    "LINK_CLICKS": "traffic",
    "OUTCOME_ENGAGEMENT": "engagement",
    "POST_ENGAGEMENT": "engagement",
    "PAGE_LIKES": "engagement",
    "OUTCOME_AWARENESS": "brand_awareness",
    "BRAND_AWARENESS": "brand_awareness",
    "REACH": "brand_awareness",
    "VIDEO_VIEWS": "video_views",
    "OUTCOME_SALES": "sales",
    "CONVERSIONS": "sales",
    "PRODUCT_CATALOG_SALES": "sales",
}

# Budgets are returned in the currency's minor unit; these currencies have none.
ZERO_DECIMAL_CURRENCIES = {"JPY", "KRW", "VND", "CLP", "PYG", "ISK", "UGX"}

# Meta error codes: 190 = invalid/expired token, 10/200-299 = missing permission,
# 4/17/32/613/80000-80014 = rate limiting.
AUTH_ERROR_CODES = {190, 102, 10} | set(range(200, 300))
RATE_LIMIT_CODES = {4, 17, 32, 613} | set(range(80000, 80015))

INSIGHT_CHUNK_DAYS = 30
POST_LOOKBACK_DAYS = 90
MAX_POSTS = 50


def _classify(status: int, body: Any) -> Optional[str]:
    err = body.get("error") if isinstance(body, dict) else None
    if not err:
        return None
    code = err.get("code")
    if code in RATE_LIMIT_CODES or err.get("is_transient"):
        return "retry"
    if code in AUTH_ERROR_CODES:
        return "auth"
    return "fail"


def _normalize_account_id(raw: str) -> str:
    raw = (raw or "").strip()
    return raw[4:] if raw.startswith("act_") else raw


def _action_sum(actions: Optional[list[dict[str, Any]]], types: tuple[str, ...]) -> float:
    total = 0.0
    for a in actions or []:
        if a.get("action_type") in types:
            total += to_float(a.get("value"))
    return total


def parse_leads(actions: Optional[list[dict[str, Any]]]) -> int:
    if any(a.get("action_type") == LEAD_ACTION for a in actions or []):
        return int(_action_sum(actions, (LEAD_ACTION,)))
    return int(_action_sum(actions, LEAD_COMPONENT_ACTIONS))


def parse_insight_row(row: dict[str, Any], account: AdAccount) -> DailyMetric:
    actions = row.get("actions")
    engagements = row.get("inline_post_engagement")
    if engagements is None:
        engagements = _action_sum(actions, ("post_engagement",))
    leads = parse_leads(actions)
    return DailyMetric(
        platform=PLATFORM_META,
        external_campaign_id=str(row.get("campaign_id")),
        metric_date=date.fromisoformat(row["date_start"]),
        channel=(row.get("publisher_platform") or "all").lower(),
        ad_account_id=account.id,
        currency=account.currency,
        campaign_name=row.get("campaign_name"),
        impressions=to_int(row.get("impressions")),
        reach=to_opt_int(row.get("reach")),
        clicks=to_int(row.get("clicks")),
        link_clicks=to_int(row.get("inline_link_clicks")),
        engagements=to_int(engagements),
        spend=to_float(row.get("spend")),
        leads=leads,
        messaging_conversations=int(_action_sum(actions, (MESSAGING_ACTION,))),
        conversions=float(leads),
        video_views=int(_action_sum(row.get("video_play_actions"), ("video_view",))),
        video_completions=int(_action_sum(row.get("video_p100_watched_actions"), ("video_view",))),
        raw={"actions": actions} if actions else None,
    )


def _date_chunks(since: date, until: date, days: int) -> list[tuple[date, date]]:
    chunks = []
    start = since
    while start <= until:
        end = min(start + timedelta(days=days - 1), until)
        chunks.append((start, end))
        start = end + timedelta(days=1)
    return chunks


class MetaAdsConnector:
    platform = PLATFORM_META

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        api_version: str = "v25.0",
        app_secret: Optional[str] = None,
        page_id: Optional[str] = None,
        page_access_token: Optional[str] = None,
        instagram_account_id: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.access_token = access_token
        self.account_id = _normalize_account_id(ad_account_id)
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.app_secret = app_secret
        self.page_id = page_id
        self.page_access_token = page_access_token or access_token
        self.instagram_account_id = instagram_account_id
        self._client = client

    # ── plumbing ────────────────────────────────────────────────────────
    def _auth_params(self, token: Optional[str] = None) -> dict[str, str]:
        token = token or self.access_token
        params = {"access_token": token}
        if self.app_secret:
            params["appsecret_proof"] = hmac.new(
                self.app_secret.encode(), token.encode(), hashlib.sha256
            ).hexdigest()
        return params

    async def _get(self, client: httpx.AsyncClient, path_or_url: str, params: Optional[dict[str, Any]] = None,
                   token: Optional[str] = None) -> Any:
        if path_or_url.startswith("http"):
            # Paging URLs from Meta already carry every query parameter.
            return await request_json(client, self.platform, "GET", path_or_url, classify=_classify)
        merged = {**(params or {}), **self._auth_params(token)}
        return await request_json(client, self.platform, "GET", f"{self.base_url}/{path_or_url.lstrip('/')}",
                                  params=merged, classify=_classify)

    async def _get_all(self, client: httpx.AsyncClient, path: str, params: dict[str, Any],
                       token: Optional[str] = None, max_pages: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        body = await self._get(client, path, params, token)
        for _ in range(max_pages):
            rows.extend(body.get("data", []) if isinstance(body, dict) else [])
            next_url = (body.get("paging") or {}).get("next") if isinstance(body, dict) else None
            if not next_url:
                break
            body = await self._get(client, next_url)
        return rows

    def _client_ctx(self) -> httpx.AsyncClient:
        return self._client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)

    # ── public API ──────────────────────────────────────────────────────
    async def fetch_account(self, client: Optional[httpx.AsyncClient] = None) -> AdAccount:
        own = client is None
        client = client or self._client_ctx()
        try:
            body = await self._get(client, f"act_{self.account_id}", {"fields": "name,currency,timezone_name,account_status"})
        finally:
            if own and self._client is None:
                await client.aclose()
        return AdAccount(
            platform=self.platform,
            external_account_id=self.account_id,
            name=body.get("name"),
            currency=body.get("currency"),
            timezone=body.get("timezone_name"),
            status="active" if body.get("account_status") == 1 else "inactive",
        )

    async def fetch(self, since: date, until: date, reach_windows: tuple[int, ...] = (7, 30, 90),
                    include_posts: bool = True) -> SyncPayload:
        client = self._client_ctx()
        try:
            account = await self.fetch_account(client)
            payload = SyncPayload(account=account)
            payload.campaigns = await self._fetch_campaigns(client, account)
            payload.daily_metrics = await self._fetch_daily(client, account, since, until)
            payload.period_reach = await self._fetch_period_reach(client, until, reach_windows)
            if include_posts and self.page_id:
                payload.posts, post_warnings = await self._fetch_posts(client, until)
                payload.warnings.extend(post_warnings)
            return payload
        finally:
            if self._client is None:
                await client.aclose()

    async def _fetch_campaigns(self, client: httpx.AsyncClient, account: AdAccount) -> list[Campaign]:
        rows = await self._get_all(client, f"act_{self.account_id}/campaigns", {
            "fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget",
            "limit": 200,
        })
        divisor = 1 if (account.currency or "").upper() in ZERO_DECIMAL_CURRENCIES else 100
        campaigns = []
        for r in rows:
            budget, budget_type = None, None
            if r.get("daily_budget"):
                budget, budget_type = to_float(r["daily_budget"]) / divisor, "daily"
            elif r.get("lifetime_budget"):
                budget, budget_type = to_float(r["lifetime_budget"]) / divisor, "lifetime"
            objective = r.get("objective")
            campaigns.append(Campaign(
                platform=self.platform,
                external_id=str(r["id"]),
                ad_account_id=account.id,
                name=r.get("name") or str(r["id"]),
                status=(r.get("effective_status") or r.get("status") or "UNKNOWN").upper(),
                objective=objective,
                campaign_type=OBJECTIVE_TO_TYPE.get((objective or "").upper(), "other"),
                currency=account.currency,
                budget_amount=budget,
                budget_type=budget_type,
            ))
        return campaigns

    async def _fetch_daily(self, client: httpx.AsyncClient, account: AdAccount, since: date, until: date) -> list[DailyMetric]:
        metrics: list[DailyMetric] = []
        for start, end in _date_chunks(since, until, INSIGHT_CHUNK_DAYS):
            rows = await self._get_all(client, f"act_{self.account_id}/insights", {
                "level": "campaign",
                "time_increment": 1,
                "time_range": json.dumps({"since": start.isoformat(), "until": end.isoformat()}),
                "breakdowns": "publisher_platform",
                "fields": INSIGHT_FIELDS,
                "limit": 500,
            })
            metrics.extend(parse_insight_row(r, account) for r in rows if r.get("campaign_id") and r.get("date_start"))
        return metrics

    async def _fetch_period_reach(self, client: httpx.AsyncClient, until: date, windows: tuple[int, ...]) -> list[PeriodReach]:
        out: list[PeriodReach] = []
        for days in windows:
            since = until - timedelta(days=days - 1)
            time_range = json.dumps({"since": since.isoformat(), "until": until.isoformat()})
            campaign_rows = await self._get_all(client, f"act_{self.account_id}/insights", {
                "level": "campaign", "time_range": time_range, "fields": "campaign_id,reach", "limit": 500,
            })
            for r in campaign_rows:
                out.append(PeriodReach(self.platform, str(r.get("campaign_id")), days, since, until, to_opt_int(r.get("reach"))))
            account_rows = await self._get_all(client, f"act_{self.account_id}/insights", {
                "level": "account", "time_range": time_range, "fields": "reach",
            })
            if account_rows:
                out.append(PeriodReach(self.platform, ACCOUNT_REACH_KEY, days, since, until, to_opt_int(account_rows[0].get("reach"))))
        return out

    async def _fetch_posts(self, client: httpx.AsyncClient, until: date) -> tuple[list[SocialPost], list[str]]:
        warnings: list[str] = []
        posts: list[SocialPost] = []
        since_dt = datetime.combine(until - timedelta(days=POST_LOOKBACK_DAYS), datetime.min.time(), tzinfo=timezone.utc)
        token = self.page_access_token

        try:
            fb_rows = await self._get_all(client, f"{self.page_id}/published_posts", {
                "fields": "id,message,created_time,permalink_url,full_picture,status_type,shares,"
                          "reactions.summary(total_count).limit(0),comments.summary(total_count).limit(0)",
                "since": int(since_dt.timestamp()),
                "limit": MAX_POSTS,
            }, token=token, max_pages=1)
        except ConnectorError as err:
            warnings.append(f"Facebook page posts unavailable: {err.message}")
            fb_rows = []

        insight_failures = 0
        for r in fb_rows[:MAX_POSTS]:
            post = SocialPost(
                platform="facebook",
                external_post_id=str(r["id"]),
                published_at=_parse_ts(r.get("created_time")),
                message=r.get("message") or "",
                permalink=r.get("permalink_url"),
                media_url=r.get("full_picture"),
                media_type=r.get("status_type"),
                likes=to_int(((r.get("reactions") or {}).get("summary") or {}).get("total_count")),
                comments=to_int(((r.get("comments") or {}).get("summary") or {}).get("total_count")),
                shares=to_int((r.get("shares") or {}).get("count")),
            )
            if insight_failures < 3:
                try:
                    ins = await self._get(client, f"{post.external_post_id}/insights",
                                          {"metric": "post_media_view,post_total_media_view_unique"}, token)
                    values = _insight_values(ins)
                    post.views = values.get("post_media_view")
                    post.reach = values.get("post_total_media_view_unique")
                except ConnectorError as err:
                    insight_failures += 1
                    if insight_failures == 3:
                        warnings.append(f"Facebook post insights unavailable: {err.message}")
            posts.append(post)

        if self.instagram_account_id:
            try:
                ig_rows = await self._get_all(client, f"{self.instagram_account_id}/media", {
                    "fields": "id,caption,media_type,media_product_type,timestamp,permalink,media_url,"
                              "thumbnail_url,like_count,comments_count",
                    "limit": MAX_POSTS,
                }, token=token, max_pages=1)
            except ConnectorError as err:
                warnings.append(f"Instagram media unavailable: {err.message}")
                ig_rows = []
            insight_failures = 0
            for r in ig_rows[:MAX_POSTS]:
                published = _parse_ts(r.get("timestamp"))
                if published and published < since_dt:
                    continue
                post = SocialPost(
                    platform="instagram",
                    external_post_id=str(r["id"]),
                    published_at=published,
                    message=r.get("caption") or "",
                    permalink=r.get("permalink"),
                    media_url=r.get("thumbnail_url") or r.get("media_url"),
                    media_type=r.get("media_product_type") or r.get("media_type"),
                    likes=to_int(r.get("like_count")),
                    comments=to_int(r.get("comments_count")),
                )
                if insight_failures < 3:
                    try:
                        ins = await self._get(client, f"{post.external_post_id}/insights",
                                              {"metric": "views,reach,saved,shares"}, token)
                        values = _insight_values(ins)
                        post.views = values.get("views")
                        post.reach = values.get("reach")
                        post.saves = values.get("saved")
                        post.shares = values.get("shares") or 0
                    except ConnectorError as err:
                        insight_failures += 1
                        if insight_failures == 3:
                            warnings.append(f"Instagram media insights unavailable: {err.message}")
                posts.append(post)
        return posts, warnings


def _insight_values(body: Any) -> dict[str, Optional[int]]:
    values: dict[str, Optional[int]] = {}
    for item in (body or {}).get("data", []):
        name = item.get("name")
        series = item.get("values") or []
        if name and series:
            values[name] = to_opt_int(series[-1].get("value"))
        elif name and "total_value" in item:
            values[name] = to_opt_int((item.get("total_value") or {}).get("value"))
    return values


def _parse_ts(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        # Meta uses '+0000' offsets, which fromisoformat accepts from Python 3.11.
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
