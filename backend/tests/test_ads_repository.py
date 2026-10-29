"""AdsRepository → PostgREST request formation (upsert conflict keys, paging, counts)."""

import json
from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.repositories.ads_repository import AdsRepository, RepositoryError, SupabaseRestClient, match_project
from app.services.ads.types import DailyMetric


def _repo(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return AdsRepository(SupabaseRestClient("https://x.supabase.co", "service-key", client=client)), client


async def test_upsert_daily_metrics_uses_composite_conflict_key():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(201)
    repo, client = _repo(handler)
    metrics = [DailyMetric("meta", f"c{i}", date(2026, 9, 1), "facebook", spend=1.234) for i in range(3)]
    count = await repo.upsert_daily_metrics(metrics, datetime(2026, 9, 27, tzinfo=timezone.utc))
    req = seen[0]
    assert count == 3
    assert req.method == "POST" and urlparse(str(req.url)).path == "/rest/v1/ad_campaign_daily_metrics"
    assert parse_qs(urlparse(str(req.url)).query)["on_conflict"] == ["platform,external_campaign_id,metric_date,channel"]
    assert req.headers["Prefer"] == "resolution=merge-duplicates,return=minimal"
    assert req.headers["apikey"] == "service-key" and req.headers["Authorization"] == "Bearer service-key"
    body = json.loads(req.content)
    assert body[0]["spend"] == 1.23 and body[0]["metric_date"] == "2026-09-01"
    assert len({tuple(sorted(r)) for r in body}) == 1  # PostgREST bulk insert needs identical keys
    await client.aclose()


async def test_select_pages_until_short_page():
    offsets = []

    def handler(request):
        q = parse_qs(urlparse(str(request.url)).query)
        offset, limit = int(q["offset"][0]), int(q["limit"][0])
        offsets.append(offset)
        remaining = max(0, 2500 - offset)
        return httpx.Response(200, json=[{"n": offset + i} for i in range(min(limit, remaining))])
    repo, client = _repo(handler)
    rows = await repo.list_daily_metrics(date(2026, 9, 1), date(2026, 9, 30))
    assert len(rows) == 2500 and offsets == [0, 1000, 2000]
    await client.aclose()


async def test_date_range_filter_and_count_header():
    seen = []

    def handler(request):
        seen.append(request)
        if request.headers.get("Prefer") == "count=exact":
            return httpx.Response(200, json=[{}], headers={"content-range": "0-0/7"})
        return httpx.Response(200, json=[])
    repo, client = _repo(handler)
    await repo.list_daily_metrics(date(2026, 9, 1), date(2026, 9, 30))
    q = parse_qs(urlparse(str(seen[0].url)).query)
    assert q["and"] == ["(metric_date.gte.2026-09-01,metric_date.lte.2026-09-30)"]
    assert await repo.count_pending_posts() == 7
    q2 = parse_qs(urlparse(str(seen[1].url)).query)
    assert q2["status"] == ['in.("pending","draft","pending_approval")']
    await client.aclose()


async def test_http_errors_raise_repository_error():
    repo, client = _repo(lambda r: httpx.Response(401, json={"message": "permission denied for table ad_campaigns"}))
    with pytest.raises(RepositoryError):
        await repo.list_campaigns()
    await client.aclose()


def test_match_project_prefers_longest_name():
    projects = [{"project_id": "p1", "name": "GLG Sky"}, {"project_id": "p2", "name": "GLG Sky Tower"},
                {"project_id": "p3", "name": "Oasis"}]
    assert match_project("Leads | GLG Sky Tower — Gulshan 3BHK", projects) == "p2"
    assert match_project("Brand awareness Dhaka", projects) is None
    assert match_project("GLG Skyline launch", projects) is None  # whole words only
