"""Connector normalization tests with recorded-shape API responses (httpx.MockTransport)."""

import json
from datetime import date
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.services.ads.google_ads import GoogleAdsConnector
from app.services.ads.meta_ads import MetaAdsConnector, parse_leads
from app.services.ads.tiktok_ads import TikTokAdsConnector
from app.services.ads.types import ACCOUNT_REACH_KEY, ConnectorAuthError, ConnectorError


def _qs(request: httpx.Request) -> dict:
    return {k: v[0] for k, v in parse_qs(urlparse(str(request.url)).query).items()}


# ── Meta ────────────────────────────────────────────────────────────────

def test_meta_leads_prefers_aggregate_lead_action():
    both = [{"action_type": "lead", "value": "12"}, {"action_type": "onsite_conversion.lead_grouped", "value": "12"}]
    components = [{"action_type": "onsite_conversion.lead_grouped", "value": "7"},
                  {"action_type": "offsite_conversion.fb_pixel_lead", "value": "2"}]
    assert parse_leads(both) == 12  # never double counted
    assert parse_leads(components) == 9
    assert parse_leads(None) == 0


def _meta_handler(requests_seen: list):
    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        path = urlparse(str(request.url)).path
        q = _qs(request)
        assert q["access_token"] == "tok"
        assert "appsecret_proof" in q
        if path.endswith("/act_111") and "insights" not in path:
            return httpx.Response(200, json={"name": "GLG Main", "currency": "BDT", "timezone_name": "Asia/Dhaka", "account_status": 1})
        if path.endswith("/act_111/campaigns"):
            if q.get("after") == "page2":
                return httpx.Response(200, json={"data": [{"id": "c2", "name": "GLG Sky Tower Awareness", "effective_status": "PAUSED", "objective": "OUTCOME_AWARENESS", "lifetime_budget": "5000000"}]})
            return httpx.Response(200, json={
                "data": [{"id": "c1", "name": "GLG Sky Tower Leads", "effective_status": "ACTIVE", "objective": "OUTCOME_LEADS", "daily_budget": "250000"}],
                "paging": {"next": "https://graph.facebook.com/v25.0/act_111/campaigns?access_token=tok&appsecret_proof=x&after=page2"},
            })
        if path.endswith("/act_111/insights"):
            if q.get("time_increment") == "1":
                assert q["breakdowns"] == "publisher_platform"
                return httpx.Response(200, json={"data": [
                    {"campaign_id": "c1", "campaign_name": "GLG Sky Tower Leads", "date_start": "2026-09-01",
                     "publisher_platform": "facebook", "spend": "1500.50", "impressions": "20000", "reach": "15000",
                     "clicks": "400", "inline_link_clicks": "300", "inline_post_engagement": "900",
                     "actions": [{"action_type": "lead", "value": "5"},
                                 {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "3"}],
                     "video_play_actions": [{"action_type": "video_view", "value": "1200"}],
                     "video_p100_watched_actions": [{"action_type": "video_view", "value": "80"}]},
                    {"campaign_id": "c3", "campaign_name": "Archived Campaign", "date_start": "2026-09-01",
                     "publisher_platform": "instagram", "spend": "10", "impressions": "100"},
                ]})
            if q.get("level") == "account":
                return httpx.Response(200, json={"data": [{"reach": "50000"}]})
            return httpx.Response(200, json={"data": [{"campaign_id": "c1", "reach": "30000"}]})
        return httpx.Response(404, json={"error": {"message": f"unexpected {path}", "code": 100}})
    return handler


async def test_meta_fetch_normalizes_payload():
    seen: list = []
    client = httpx.AsyncClient(transport=httpx.MockTransport(_meta_handler(seen)))
    connector = MetaAdsConnector("tok", "act_111", app_secret="secret", client=client)
    payload = await connector.fetch(date(2026, 9, 1), date(2026, 9, 1), reach_windows=(7,), include_posts=False)

    assert payload.account.id == "meta:111"
    assert payload.account.currency == "BDT"
    assert [c.external_id for c in payload.campaigns] == ["c1", "c2"]  # paging followed
    c1, c2 = payload.campaigns
    assert c1.campaign_type == "lead_generation" and c1.budget_amount == 2500.0 and c1.budget_type == "daily"
    assert c2.status == "PAUSED" and c2.campaign_type == "brand_awareness" and c2.budget_type == "lifetime"

    m = payload.daily_metrics[0]
    assert (m.channel, m.spend, m.impressions, m.reach, m.clicks, m.link_clicks) == ("facebook", 1500.5, 20000, 15000, 400, 300)
    assert (m.leads, m.messaging_conversations, m.engagements, m.video_views, m.video_completions) == (5, 3, 900, 1200, 80)
    assert payload.daily_metrics[1].channel == "instagram" and payload.daily_metrics[1].leads == 0

    reach = {(r.external_campaign_id, r.window_days): r.reach for r in payload.period_reach}
    assert reach == {("c1", 7): 30000, (ACCOUNT_REACH_KEY, 7): 50000}
    await client.aclose()


async def test_meta_daily_insights_are_chunked_to_30_days():
    seen: list = []
    client = httpx.AsyncClient(transport=httpx.MockTransport(_meta_handler(seen)))
    connector = MetaAdsConnector("tok", "111", app_secret="secret", client=client)
    await connector.fetch(date(2026, 6, 1), date(2026, 8, 29), reach_windows=(), include_posts=False)
    ranges = [json.loads(_qs(r)["time_range"]) for r in seen if _qs(r).get("time_increment") == "1"]
    assert ranges == [
        {"since": "2026-06-01", "until": "2026-06-30"},
        {"since": "2026-07-01", "until": "2026-07-30"},
        {"since": "2026-07-31", "until": "2026-08-29"},
    ]
    await client.aclose()


async def test_meta_invalid_token_raises_auth_error():
    def handler(request):
        return httpx.Response(400, json={"error": {"message": "Error validating access token", "code": 190}})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ConnectorAuthError):
        await MetaAdsConnector("tok", "111", client=client).fetch_account(client)
    await client.aclose()


async def test_meta_rate_limit_is_retried(monkeypatch):
    import app.services.ads.http as http_mod

    async def no_sleep(*args, **kwargs):
        return None
    monkeypatch.setattr(http_mod, "_backoff", no_sleep)
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(400, json={"error": {"message": "User request limit reached", "code": 17}})
        return httpx.Response(200, json={"name": "A", "currency": "USD", "account_status": 1})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    account = await MetaAdsConnector("tok", "111", client=client).fetch_account(client)
    assert account.currency == "USD" and calls["n"] == 3
    await client.aclose()


async def test_meta_posts_tolerate_missing_insights():
    def handler(request):
        path = urlparse(str(request.url)).path
        if path.endswith("/act_1"):
            return httpx.Response(200, json={"name": "A", "currency": "BDT", "account_status": 1})
        if path.endswith("/campaigns") or path.endswith("/act_1/insights"):
            return httpx.Response(200, json={"data": []})
        if path.endswith("/page1/published_posts"):
            return httpx.Response(200, json={"data": [{
                "id": "page1_99", "message": "Rooftop pool tour\nBook now", "created_time": "2026-09-20T10:00:00+0000",
                "permalink_url": "https://fb.com/p/99", "shares": {"count": 4},
                "reactions": {"summary": {"total_count": 120}}, "comments": {"summary": {"total_count": 9}},
            }]})
        if path.endswith("/insights"):
            return httpx.Response(400, json={"error": {"message": "metric deprecated", "code": 100}})
        return httpx.Response(404, json={})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    payload = await MetaAdsConnector("tok", "1", page_id="page1", client=client).fetch(
        date(2026, 9, 20), date(2026, 9, 27), reach_windows=(), include_posts=True)
    post = payload.posts[0]
    assert (post.likes, post.comments, post.shares, post.views) == (120, 9, 4, None)
    assert post.published_at.isoformat() == "2026-09-20T10:00:00+00:00"
    await client.aclose()


# ── Google Ads ──────────────────────────────────────────────────────────

async def test_google_ads_normalizes_search_stream():
    queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith("https://oauth2.googleapis.com/token"):
            assert b"grant_type=refresh_token" in request.content
            return httpx.Response(200, json={"access_token": "ya29", "expires_in": 3599})
        assert request.headers["developer-token"] == "dev"
        assert request.headers["login-customer-id"] == "9998887777"
        assert url.endswith("/v25/customers/1234567890/googleAds:searchStream")
        query = json.loads(request.content)["query"]
        queries.append(query)
        if "FROM customer" in query:
            return httpx.Response(200, json=[{"results": [{"customer": {"id": "1234567890", "descriptiveName": "GLG", "currencyCode": "BDT", "timeZone": "Asia/Dhaka"}}]}])
        if "segments.date" in query:
            return httpx.Response(200, json=[{"results": [{
                "campaign": {"id": "55", "name": "Search - Gulshan", "advertisingChannelType": "SEARCH"},
                "segments": {"date": "2026-09-02"},
                "metrics": {"impressions": "1000", "clicks": "80", "costMicros": "2500000000", "conversions": 4.0},
            }]}])
        return httpx.Response(200, json=[{"results": [{
            "campaign": {"id": "55", "name": "Search - Gulshan", "status": "ENABLED", "advertisingChannelType": "SEARCH"},
            "campaignBudget": {"amountMicros": "1000000000"},
        }]}])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    connector = GoogleAdsConnector("dev", "cid", "secret", "refresh", "123-456-7890",
                                   login_customer_id="999-888-7777", client=client)
    payload = await connector.fetch(date(2026, 9, 1), date(2026, 9, 7))
    assert payload.account.id == "google_ads:1234567890"
    camp = payload.campaigns[0]
    assert (camp.status, camp.campaign_type, camp.budget_amount) == ("ACTIVE", "traffic", 1000.0)
    m = payload.daily_metrics[0]
    assert (m.channel, m.spend, m.clicks, m.leads, m.reach) == ("google_search", 2500.0, 80, 4, None)
    assert "BETWEEN '2026-09-01' AND '2026-09-07'" in queries[-1]
    await client.aclose()


async def test_google_ads_revoked_refresh_token_is_auth_error():
    def handler(request):
        return httpx.Response(400, json={"error": "invalid_grant", "error_description": "Token has been expired or revoked."})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ConnectorAuthError):
        await GoogleAdsConnector("dev", "cid", "secret", "refresh", "1", client=client).fetch_account(client)
    await client.aclose()


# ── TikTok ──────────────────────────────────────────────────────────────

def _tiktok_handler(seen: list):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.headers["Access-Token"] == "tt"
        path = urlparse(str(request.url)).path
        q = _qs(request)
        if path.endswith("/advertiser/info/"):
            return httpx.Response(200, json={"code": 0, "data": {"list": [{"name": "GLG TikTok", "currency": "USD", "timezone": "Asia/Dhaka", "status": "STATUS_ENABLE"}]}})
        if path.endswith("/campaign/get/"):
            return httpx.Response(200, json={"code": 0, "data": {"list": [
                {"campaign_id": "t1", "campaign_name": "Lead Form", "objective_type": "LEAD_GENERATION", "operation_status": "ENABLE", "budget": 50, "budget_mode": "BUDGET_MODE_DAY"},
                {"campaign_id": "t2", "campaign_name": "Views", "objective_type": "VIDEO_VIEWS", "operation_status": "DISABLE", "budget_mode": "BUDGET_MODE_INFINITE"},
            ], "page_info": {"total_page": 1}}})
        if path.endswith("/report/integrated/get/"):
            dims = json.loads(q["dimensions"])
            if "stat_time_day" in dims:
                return httpx.Response(200, json={"code": 0, "data": {"list": [
                    {"dimensions": {"campaign_id": "t1", "stat_time_day": "2026-09-03 00:00:00"},
                     "metrics": {"campaign_name": "Lead Form", "spend": "12.40", "impressions": "3000", "reach": "2500", "clicks": "60",
                                 "conversion": "6", "likes": "10", "comments": "2", "shares": "1", "video_play_actions": "900", "video_views_p100": "90"}},
                    {"dimensions": {"campaign_id": "t2", "stat_time_day": "2026-09-03 00:00:00"},
                     "metrics": {"spend": "3", "impressions": "900", "conversion": "40"}},
                ], "page_info": {"total_page": 1}}})
            if dims == ["advertiser_id"]:
                return httpx.Response(200, json={"code": 0, "data": {"list": [{"metrics": {"reach": "7000"}}], "page_info": {"total_page": 1}}})
            return httpx.Response(200, json={"code": 0, "data": {"list": [{"dimensions": {"campaign_id": "t1"}, "metrics": {"reach": "5000"}}], "page_info": {"total_page": 1}}})
        return httpx.Response(404)
    return handler


async def test_tiktok_normalizes_report_and_only_counts_leads_for_lead_gen():
    seen: list = []
    client = httpx.AsyncClient(transport=httpx.MockTransport(_tiktok_handler(seen)))
    payload = await TikTokAdsConnector("tt", "adv1", client=client).fetch(date(2026, 9, 1), date(2026, 9, 7), reach_windows=(7,))
    assert payload.account.currency == "USD"
    by_id = {m.external_campaign_id: m for m in payload.daily_metrics}
    t1, t2 = by_id["t1"], by_id["t2"]
    assert (t1.spend, t1.leads, t1.conversions, t1.engagements, t1.video_completions, t1.channel) == (12.4, 6, 6.0, 13, 90, "tiktok")
    assert (t2.leads, t2.conversions) == (0, 40.0)  # video-views conversions are not leads
    assert {(r.external_campaign_id, r.reach) for r in payload.period_reach} == {("t1", 5000), (ACCOUNT_REACH_KEY, 7000)}
    assert payload.campaigns[1].budget_amount is None
    await client.aclose()


async def test_tiktok_error_code_raises():
    def handler(request):
        return httpx.Response(200, json={"code": 40105, "message": "Access token expired"})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ConnectorAuthError):
        await TikTokAdsConnector("tt", "adv1", client=client).fetch_account(client)
    await client.aclose()

    def handler2(request):
        return httpx.Response(200, json={"code": 40002, "message": "Invalid metric"})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler2))
    with pytest.raises(ConnectorError):
        await TikTokAdsConnector("tt", "adv1", client=client).fetch_account(client)
    await client.aclose()
