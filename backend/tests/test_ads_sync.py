"""Sync service: idempotent upserts, run bookkeeping, locking and scheduling decisions."""

from datetime import date, datetime, timedelta, timezone

from ads_fakes import FakeAdsRepository, FakeConnector

from app.services.ads import sync_service
from app.services.ads.factory import ConnectorSpec
from app.services.ads.sync_service import plan_trigger, sync_all
from app.services.ads.types import (
    AdAccount,
    Campaign,
    ConnectorAuthError,
    DailyMetric,
    PeriodReach,
    SocialPost,
    SyncPayload,
)

TODAY = date(2026, 9, 27)


def _payload() -> SyncPayload:
    account = AdAccount("meta", "111", "GLG", "BDT")
    return SyncPayload(
        account=account,
        campaigns=[Campaign("meta", "c1", account.id, "GLG Sky Tower — Leads", "ACTIVE", "OUTCOME_LEADS", "lead_generation", "BDT")],
        daily_metrics=[
            DailyMetric("meta", "c1", date(2026, 9, 26), "facebook", account.id, "BDT", "GLG Sky Tower — Leads",
                        impressions=1000, clicks=50, spend=500.0, leads=4),
            DailyMetric("meta", "c1", date(2026, 9, 26), "instagram", account.id, "BDT", "GLG Sky Tower — Leads",
                        impressions=800, clicks=20, spend=300.0, leads=1),
            # Campaign missing from the campaign list (archived) must still get a campaign row.
            DailyMetric("meta", "c9", date(2026, 9, 25), "facebook", account.id, "BDT", "Old archived campaign",
                        impressions=10, spend=5.0),
        ],
        period_reach=[PeriodReach("meta", "c1", 7, date(2026, 9, 21), TODAY, 1500)],
        posts=[SocialPost("facebook", "p1", datetime(2026, 9, 20, tzinfo=timezone.utc), "Pool tour", likes=10)],
    )


def _spec(connector) -> ConnectorSpec:
    return ConnectorSpec("meta", "111", connector, include_posts=True)


async def test_sync_is_idempotent_and_records_run():
    repo = FakeAdsRepository()
    repo.projects = [{"project_id": "proj_103", "name": "GLG Sky Tower"}]
    connector = FakeConnector(_payload())

    first = await sync_all(repo, [_spec(connector)], trigger="manual", lookback_days=7, today=TODAY)
    snapshot = (len(repo.campaigns), len(repo.metrics), len(repo.reach), len(repo.posts))
    second = await sync_all(repo, [_spec(connector)], trigger="manual", lookback_days=7, today=TODAY)

    assert snapshot == (2, 3, 1, 1)
    assert (len(repo.campaigns), len(repo.metrics), len(repo.reach), len(repo.posts)) == snapshot
    assert first[0]["status"] == second[0]["status"] == "success"
    assert first[0]["metric_rows_upserted"] == 3
    assert connector.calls[0] == (date(2026, 9, 21), TODAY, True)
    assert repo.campaigns[("meta", "c9")]["campaign_name"] == "Old archived campaign"
    assert repo.campaigns[("meta", "c1")]["project_id"] == "proj_103"  # auto-linked by name
    assert [r["status"] for r in repo.runs] == ["success", "success"]
    assert repo.accounts["meta:111"]["last_synced_at"]


async def test_sync_records_auth_failure_without_raising():
    repo = FakeAdsRepository()
    connector = FakeConnector(_payload(), error=ConnectorAuthError("meta", "Error validating access token"))
    [result] = await sync_all(repo, [_spec(connector)], trigger="manual", lookback_days=3, today=TODAY)
    assert result["status"] == "failed"
    assert "Credentials rejected" in result["error"]
    assert repo.metrics == {}
    assert repo.runs[0]["status"] == "failed"


async def test_running_sync_blocks_a_second_one():
    repo = FakeAdsRepository()
    repo.runs = [{"id": "r0", "ad_account_id": "meta:111", "status": "running",
                  "started_at": datetime.now(timezone.utc).isoformat()}]
    connector = FakeConnector(_payload())
    [result] = await sync_all(repo, [_spec(connector)], trigger="manual", lookback_days=3, today=TODAY)
    assert result["status"] == "skipped"
    assert connector.calls == []


async def test_lookback_is_clamped_to_90_days():
    connector = FakeConnector(_payload())
    await sync_all(FakeAdsRepository(), [_spec(connector)], trigger="manual", lookback_days=400, today=TODAY)
    assert connector.calls[0][0] == TODAY - timedelta(days=89)


def _run(status, trigger, minutes_ago, now):
    return {"ad_account_id": "meta:111", "status": status, "trigger": trigger,
            "started_at": (now - timedelta(minutes=minutes_ago)).isoformat()}


def test_plan_trigger_decisions(monkeypatch):
    monkeypatch.setattr(sync_service.settings, "ads_sync_interval_minutes", 60)
    monkeypatch.setattr(sync_service.settings, "ads_sync_nightly_hour_utc", 20)
    morning = datetime(2026, 9, 27, 9, 0, tzinfo=timezone.utc)
    night = datetime(2026, 9, 27, 21, 0, tzinfo=timezone.utc)

    assert plan_trigger([], "meta:111", morning) == ("backfill", 90)
    # Failed first attempt: wait an interval before retrying the backfill.
    assert plan_trigger([_run("failed", "backfill", 10, morning)], "meta:111", morning) is None
    assert plan_trigger([_run("failed", "backfill", 70, morning)], "meta:111", morning) == ("backfill", 90)

    ok_recent = [_run("success", "schedule", 20, morning)]
    ok_old = [_run("success", "schedule", 61, morning)]
    assert plan_trigger(ok_recent, "meta:111", morning) is None
    assert plan_trigger(ok_old, "meta:111", morning) == ("schedule", 3)

    assert plan_trigger([_run("success", "schedule", 5, night)], "meta:111", night) == ("nightly", 28)
    assert plan_trigger([_run("success", "nightly", 30, night)], "meta:111", night) is None
    assert plan_trigger([_run("running", "schedule", 5, morning)], "meta:111", morning) is None
    # A crashed 'running' row older than the lock window does not block.
    assert plan_trigger([_run("running", "schedule", 120, morning), _run("success", "schedule", 130, morning)],
                        "meta:111", morning) == ("schedule", 3)
