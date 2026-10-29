"""Dashboard aggregation math: periods, deltas, filters, reach, FX, SLA and manager view."""

from datetime import date

import pytest

from app.services.ads.analytics import (
    Filters,
    ai_sla,
    build_manager_overview,
    build_social_kpis,
    demo_metric_rows,
    fx_table,
    resolve_period,
)
from app.services.ads.types import ACCOUNT_REACH_KEY

TODAY = date(2026, 9, 27)
PERIOD = resolve_period("7d", TODAY)  # 21 Sep – 27 Sep, previous 14 – 20 Sep

CAMPAIGNS = [
    {"platform": "meta", "external_id": "c1", "campaign_name": "Sky Tower Leads", "status": "active",
     "campaign_type": "lead_generation", "project_id": "proj_103", "currency": "BDT"},
    {"platform": "google_ads", "external_id": "g1", "campaign_name": "Search Gulshan", "status": "active",
     "campaign_type": "traffic", "project_id": None, "currency": "USD"},
    {"platform": "meta", "external_id": "c2", "campaign_name": "Idle lead campaign", "status": "active",
     "campaign_type": "lead_generation", "project_id": None, "currency": "BDT"},
]


def row(platform, cid, day, channel, currency="BDT", **metrics):
    base = {"platform": platform, "external_campaign_id": cid, "metric_date": day, "channel": channel,
            "currency": currency, "impressions": 0, "clicks": 0, "link_clicks": 0, "engagements": 0, "spend": 0,
            "leads": 0, "messaging_conversations": 0, "conversions": 0, "video_views": 0, "video_completions": 0}
    base.update(metrics)
    return base


CURRENT = [
    row("meta", "c1", "2026-09-26", "facebook", impressions=10000, clicks=200, spend=3000, leads=10, messaging_conversations=5, reach=7000),
    row("meta", "c1", "2026-09-26", "instagram", impressions=5000, clicks=50, spend=1000, leads=2),
    row("google_ads", "g1", "2026-09-25", "google_search", currency="USD", impressions=2000, clicks=100, spend=10, leads=3),
    row("meta", "c2", "2026-09-24", "facebook", impressions=500, clicks=5, spend=800),
]
PREVIOUS = [
    row("meta", "c1", "2026-09-18", "facebook", impressions=8000, clicks=100, spend=2000, leads=5),
]
REACH = [
    {"platform": "meta", "external_campaign_id": ACCOUNT_REACH_KEY, "window_days": 7, "until_date": "2026-09-27", "reach": 12000},
    {"platform": "google_ads", "external_campaign_id": ACCOUNT_REACH_KEY, "window_days": 7, "until_date": "2026-09-27", "reach": 1000},
    {"platform": "meta", "external_campaign_id": "c1", "window_days": 7, "until_date": "2026-09-27", "reach": 11000},
    {"platform": "meta", "external_campaign_id": "c1", "window_days": 30, "until_date": "2026-09-27", "reach": 40000},
]
FX = fx_table([{"currency": "USD", "rate_to_bdt": 120}])


def build(filters=Filters(), fx=FX, current=CURRENT, previous=PREVIOUS, reach=REACH, **kw):
    return build_social_kpis(period=kw.get("period", PERIOD), filters=filters, campaigns=CAMPAIGNS, current_rows=current,
                             previous_rows=previous, reach_rows=reach, posts=kw.get("posts", []), projects=[
                                 {"project_id": "proj_103", "name": "GLG Sky Tower"}], fx=fx, sla=None)


def test_period_resolution():
    assert (PERIOD.since, PERIOD.until) == (date(2026, 9, 21), TODAY)
    assert (PERIOD.previous.since, PERIOD.previous.until) == (date(2026, 9, 14), date(2026, 9, 20))
    assert resolve_period("today", TODAY).days == 1
    assert resolve_period("bogus", TODAY).key == "30d"


def test_totals_fx_and_derived_ratios():
    out = build()
    k = out["kpis"]
    assert k["impressions"] == 17500
    assert k["clicks"] == 355
    assert k["leads"] == 15
    assert k["spend_bdt"] == pytest.approx(3000 + 1000 + 10 * 120 + 800)  # USD converted
    assert k["ctr_pct"] == pytest.approx(round(355 / 17500 * 100, 2))
    assert k["cpl_bdt"] == pytest.approx(round(6000 / 15, 2))
    assert k["cost_per_message_bdt"] == pytest.approx(1200.0)
    assert out["deltas"]["leads"] == pytest.approx(200.0)  # 15 vs 5
    assert out["deltas"]["spend_bdt"] == pytest.approx(200.0)  # 6000 vs 2000
    assert out["warnings"] == []


def test_missing_fx_excludes_spend_and_warns():
    out = build(fx=fx_table([]))
    assert out["kpis"]["spend_bdt"] == pytest.approx(4800.0)
    assert out["missing_fx"] == ["USD"]
    assert "USD" in out["warnings"][0]


def test_env_fx_fallback_is_used_when_db_has_no_rate():
    assert fx_table([], "USD=121.5, EUR=bad")["USD"] == 121.5
    assert fx_table([{"currency": "USD", "rate_to_bdt": 119}], "USD=121.5")["USD"] == 119


def test_reach_uses_account_dedup_then_campaign_windows():
    assert (build()["kpis"]["reach"], build()["reach_method"]) == (13000, "account_dedup")
    by_project = build(filters=Filters(project_id="proj_103"))
    assert (by_project["kpis"]["reach"], by_project["reach_method"]) == (11000, "campaign_sum")
    by_channel = build(filters=Filters(channel="instagram"))
    assert (by_channel["kpis"]["reach"], by_channel["reach_method"]) == (None, "unavailable")
    meta_only = build(filters=Filters(channel="meta"))
    assert meta_only["kpis"]["reach"] == 12000
    today = build(period=resolve_period("today", date(2026, 9, 26)))
    assert today["reach_method"] == "campaign_sum"


def test_filters_channel_platform_type_project():
    assert build(filters=Filters(channel="instagram"))["kpis"]["leads"] == 2
    assert build(filters=Filters(channel="meta"))["kpis"]["leads"] == 12
    assert build(filters=Filters(campaign_type="traffic"))["kpis"]["leads"] == 3
    out = build(filters=Filters(project_id="proj_103"))
    assert out["kpis"]["leads"] == 12
    assert [c["name"] for c in out["campaigns"]] == ["Sky Tower Leads"]
    assert out["campaigns"][0]["project"] == "GLG Sky Tower"


def test_channels_campaigns_series_and_insights():
    out = build()
    assert [c["id"] for c in out["platforms"]] == ["facebook", "google_search", "instagram"]  # by spend
    fb = out["platforms"][0]
    assert fb["leads"] == 10 and fb["leads_delta_pct"] == pytest.approx(100.0)
    assert fb["cpl_bdt"] == pytest.approx(380.0)  # (3000 + 800) / 10
    assert len(out["time_series"]) == 7
    assert out["time_series"][0]["date"] == "2026-09-21" and out["time_series"][0]["leads"] == 0
    assert out["time_series"][5]["leads"] == 12
    idle = next(c for c in out["campaigns"] if c["external_id"] == "c2")
    assert idle["leads"] == 0 and idle["cpl_bdt"] is None
    assert any("Idle lead campaign" in i["title"] for i in out["insights"])


def test_no_rows_means_no_fake_values():
    out = build(current=[], previous=[], reach=[])
    k = out["kpis"]
    assert k["leads"] == 0 and k["spend_bdt"] == 0
    assert k["cpl_bdt"] is None and k["ctr_pct"] is None and k["reach"] is None
    assert all(v is None for v in out["deltas"].values())


def test_demo_rows_are_single_period_totals():
    demo = [{"id": "uuid-1", "external_id": None, "platform": "facebook", "campaign_name": "Seed", "ad_spend_bdt": 425000,
             "impressions": 540000, "reach": 420000, "engagements": 32400, "leads_generated": 268, "campaign_type": "lead_generation"}]
    out = build_social_kpis(period=resolve_period("30d", TODAY), filters=Filters(), campaigns=demo,
                            current_rows=demo_metric_rows(demo, TODAY), previous_rows=[], reach_rows=[], posts=[],
                            projects=[], fx=fx_table([]), sla=None, demo=True)
    assert out["kpis"]["leads"] == 268 and out["kpis"]["spend_bdt"] == 425000
    assert out["reach_method"] == "demo" and out["kpis"]["reach"] == 420000


def test_ai_sla_from_conversations():
    convs = [{"conversation_id": "a", "channel": "whatsapp"}, {"conversation_id": "b", "channel": "whatsapp"},
             {"conversation_id": "c", "channel": "facebook"}, {"conversation_id": "d", "channel": "facebook"}]
    msgs = [
        {"conversation_id": "a", "sender": "user", "created_at": "2026-09-26T10:00:00+00:00"},
        {"conversation_id": "a", "sender": "ai", "created_at": "2026-09-26T10:00:04+00:00"},
        {"conversation_id": "b", "sender": "user", "created_at": "2026-09-26T11:00:00+00:00"},
        {"conversation_id": "c", "sender": "user", "created_at": "2026-09-26T12:00:00+00:00"},
        {"conversation_id": "c", "sender": "human_agent", "created_at": "2026-09-26T12:10:00+00:00"},
        {"conversation_id": "d", "sender": "ai", "created_at": "2026-09-26T12:00:00+00:00"},  # outbound only
    ]
    sla = ai_sla(convs, msgs)
    assert sla["inbound_conversations"] == 3
    assert sla["answered_conversations"] == 2
    assert sla["response_rate_pct"] == pytest.approx(66.7)
    assert sla["median_first_reply_seconds"] == pytest.approx(302.0)
    assert {c["channel"]: c["answered"] for c in sla["channels"]} == {"whatsapp": 1, "facebook": 1}
    assert ai_sla([], [])["response_rate_pct"] is None


def test_manager_overview_weeks_and_tours():
    social = build(period=resolve_period("30d", TODAY))
    tours = [{"date": "2026-09-26"}, {"date": "2026-09-10"}, {"date": "2026-07-01"}]
    rows_4w = CURRENT + [row("meta", "c1", "2026-09-05", "facebook", leads=7)]
    out = build_manager_overview(social=social, tours=tours, pending_posts=2, until=TODAY, daily_rows_4w=rows_4w)
    k = out["kpis"]
    assert k["confirmed_tours"] == 2  # July tour is outside the 30-day window
    assert k["pending_social_posts"] == 2
    assert k["leads"] == 15
    assert k["tour_conversion_pct"] == pytest.approx(13.3)
    weeks = k["leads_vs_tours"]
    assert len(weeks) == 4
    assert sum(w["leads"] for w in weeks) == 22 and sum(w["tours"] for w in weeks) == 2
    assert weeks[-1]["leads"] == 15 and weeks[-1]["tours"] == 1
    assert {c["name"] for c in out["campaigns"]} == {"Sky Tower Leads", "Search Gulshan", "Idle lead campaign"}
