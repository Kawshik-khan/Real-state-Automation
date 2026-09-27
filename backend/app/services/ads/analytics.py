"""Dashboard aggregations over synced ad metrics (pure functions, no I/O).

Everything here is computed from database rows: no multipliers, no fallback
numbers. A metric that cannot be computed from the data is returned as None and
the UI shows it as unavailable.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from app.services.ads.types import ACCOUNT_REACH_KEY, to_float, to_int

REPORTING_CURRENCY = "BDT"

PERIODS = {"24h": 1, "today": 1, "7d": 7, "30d": 30, "90d": 90, "quarterly": 90}

CHANNELS: dict[str, dict[str, str]] = {
    "facebook": {"name": "Facebook", "color": "#1877F2", "icon": "facebook"},
    "instagram": {"name": "Instagram", "color": "#E1306C", "icon": "instagram"},
    "messenger": {"name": "Messenger", "color": "#0084FF", "icon": "messenger"},
    "audience_network": {"name": "Meta Audience Network", "color": "#4267B2", "icon": "facebook"},
    "threads": {"name": "Threads", "color": "#6B7280", "icon": "threads"},
    "google_search": {"name": "Google Search", "color": "#4285F4", "icon": "google"},
    "google_display": {"name": "Google Display", "color": "#34A853", "icon": "google"},
    "google_pmax": {"name": "Google Performance Max", "color": "#FBBC05", "icon": "google"},
    "google_demand_gen": {"name": "Google Demand Gen", "color": "#EA4335", "icon": "google"},
    "google_shopping": {"name": "Google Shopping", "color": "#34A853", "icon": "google"},
    "google_other": {"name": "Google Ads (other)", "color": "#4285F4", "icon": "google"},
    "youtube": {"name": "YouTube", "color": "#FF0000", "icon": "youtube"},
    "tiktok": {"name": "TikTok", "color": "#00F2FE", "icon": "tiktok"},
    "linkedin": {"name": "LinkedIn", "color": "#0A66C2", "icon": "linkedin"},
}
PLATFORM_NAMES = {"meta": "Meta Ads", "google_ads": "Google Ads", "tiktok": "TikTok Ads"}
LEAD_CAMPAIGN_TYPES = {"lead_generation", "messages"}

SUM_FIELDS = ("impressions", "clicks", "link_clicks", "engagements", "leads", "messaging_conversations",
              "video_views", "video_completions")


def channel_meta(channel: str) -> dict[str, str]:
    meta = CHANNELS.get(channel)
    if meta:
        return {"id": channel, **meta}
    return {"id": channel, "name": channel.replace("_", " ").title(), "color": "#8B5CF6", "icon": "default"}


@dataclass(frozen=True)
class Period:
    key: str
    days: int
    since: date
    until: date

    @property
    def previous(self) -> "Period":
        return Period(self.key, self.days, self.since - timedelta(days=self.days), self.since - timedelta(days=1))

    def as_dict(self) -> dict[str, Any]:
        prev = self.previous
        return {"key": self.key, "days": self.days, "since": self.since.isoformat(), "until": self.until.isoformat(),
                "previous_since": prev.since.isoformat(), "previous_until": prev.until.isoformat()}


def resolve_period(key: str, today: date) -> Period:
    key = (key or "30d").lower()
    days = PERIODS.get(key, 30)
    if key not in PERIODS:
        key = "30d"
    return Period(key, days, today - timedelta(days=days - 1), today)


# ── helpers ─────────────────────────────────────────────────────────────
def fx_table(rows: Iterable[dict[str, Any]], env_fallback: Optional[str] = None) -> dict[str, float]:
    """Currency → BDT rate. DB rows win over the env fallback ("USD=122.5,EUR=133")."""
    rates: dict[str, float] = {REPORTING_CURRENCY: 1.0}
    for part in (env_fallback or "").split(","):
        if "=" in part:
            cur, _, val = part.partition("=")
            if to_float(val) > 0:
                rates[cur.strip().upper()] = to_float(val)
    for r in rows:
        if r.get("currency") and to_float(r.get("rate_to_bdt")) > 0:
            rates[str(r["currency"]).upper()] = to_float(r["rate_to_bdt"])
    return rates


def pct_change(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def ratio(num: float, den: float, scale: float = 1.0, digits: int = 2) -> Optional[float]:
    if not den:
        return None
    return round(num / den * scale, digits)


def _date(value: Any) -> Optional[date]:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class Totals:
    """Accumulator for additive metrics with FX conversion of spend."""

    def __init__(self) -> None:
        self.values = {f: 0 for f in SUM_FIELDS}
        self.spend_bdt = 0.0
        self.conversions = 0.0
        self.rows = 0

    def add(self, row: dict[str, Any], fx: dict[str, float], missing_fx: set[str]) -> None:
        self.rows += 1
        for f in SUM_FIELDS:
            self.values[f] += to_int(row.get(f))
        self.conversions += to_float(row.get("conversions"))
        currency = (row.get("currency") or "").upper()
        rate = fx.get(currency)
        spend = to_float(row.get("spend"))
        if rate is None:
            if spend:
                missing_fx.add(currency or "UNKNOWN")
        else:
            self.spend_bdt += spend * rate

    def summary(self) -> dict[str, Any]:
        v = self.values
        spend = round(self.spend_bdt, 2)
        return {
            **v,
            "spend_bdt": spend,
            "conversions": round(self.conversions, 2),
            "ctr_pct": ratio(v["clicks"], v["impressions"], 100),
            "engagement_rate_pct": ratio(v["engagements"], v["impressions"], 100),
            "cpl_bdt": ratio(spend, v["leads"]),
            "cost_per_message_bdt": ratio(spend, v["messaging_conversations"]),
            "cpc_bdt": ratio(spend, v["clicks"]),
            "cpm_bdt": ratio(spend, v["impressions"], 1000),
            "video_completion_pct": ratio(v["video_completions"], v["video_views"], 100),
        }


DELTA_KEYS = ("impressions", "clicks", "engagements", "leads", "messaging_conversations", "video_views",
              "spend_bdt", "ctr_pct", "cpl_bdt", "cost_per_message_bdt")


def deltas(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Optional[float]]:
    return {k: pct_change(current.get(k), previous.get(k)) for k in DELTA_KEYS}


# ── filters ─────────────────────────────────────────────────────────────
@dataclass
class Filters:
    channel: str = "all"         # channel id (facebook, youtube, …) or platform id (meta, google_ads, tiktok)
    campaign_type: str = "all"
    project_id: str = "all"

    @property
    def is_default(self) -> bool:
        return self.channel == "all" and self.campaign_type == "all" and self.project_id == "all"


def campaign_key(platform: Any, external_id: Any) -> str:
    return f"{platform}:{external_id}"


def campaign_allowed(camp: Optional[dict[str, Any]], f: Filters) -> bool:
    if f.campaign_type != "all":
        if not camp or (camp.get("campaign_type") or "other") != f.campaign_type:
            return False
    if f.project_id != "all":
        if not camp or (camp.get("project_id") or "") != f.project_id:
            return False
    return True


def row_allowed(row: dict[str, Any], camp: Optional[dict[str, Any]], f: Filters) -> bool:
    if f.channel != "all" and row.get("channel") != f.channel and row.get("platform") != f.channel:
        return False
    return campaign_allowed(camp, f)


# ── reach ───────────────────────────────────────────────────────────────
def compute_reach(period: Period, f: Filters, reach_rows: list[dict[str, Any]], current_rows: list[dict[str, Any]],
                  allowed_campaigns: set[str]) -> tuple[Optional[int], str]:
    """Reach is not additive across days, so it comes from platform-deduplicated windows.

    Returns (reach, method): 'account_dedup' (per platform, summed across platforms),
    'campaign_sum' (sum of campaign-level windows or single-day rows; people reached
    by two campaigns count twice) or 'unavailable'.
    """
    if period.days == 1:
        vals = [to_int(r.get("reach")) for r in current_rows if r.get("reach") is not None]
        return (sum(vals), "campaign_sum") if vals else (None, "unavailable")

    matching = [r for r in reach_rows
                if to_int(r.get("window_days")) == period.days
                and abs(((_date(r.get("until_date")) or period.until) - period.until).days) <= 1]
    if not matching:
        return None, "unavailable"
    if f.channel != "all" and f.channel not in ("meta", "google_ads", "tiktok"):
        return None, "unavailable"  # windows are stored per campaign, not per delivery channel

    platform_filter = f.channel if f.channel in ("meta", "google_ads", "tiktok") else None
    if f.campaign_type == "all" and f.project_id == "all":
        account_rows = [r for r in matching if r.get("external_campaign_id") == ACCOUNT_REACH_KEY
                        and (platform_filter is None or r.get("platform") == platform_filter)]
        if account_rows:
            return sum(to_int(r.get("reach")) for r in account_rows), "account_dedup"
    camp_rows = [r for r in matching if r.get("external_campaign_id") != ACCOUNT_REACH_KEY
                 and campaign_key(r.get("platform"), r.get("external_campaign_id")) in allowed_campaigns]
    if not camp_rows:
        return None, "unavailable"
    return sum(to_int(r.get("reach")) for r in camp_rows), "campaign_sum"


# ── AI reply SLA from conversations ─────────────────────────────────────
def ai_sla(conversations: list[dict[str, Any]], messages: list[dict[str, Any]]) -> dict[str, Any]:
    by_conv: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in messages:
        by_conv[m.get("conversation_id")].append(m)
    inbound = answered = 0
    latencies: list[float] = []
    per_channel: dict[str, dict[str, Any]] = defaultdict(lambda: {"inbound": 0, "answered": 0, "latencies": []})
    for conv in conversations:
        msgs = sorted(by_conv.get(conv.get("conversation_id"), []), key=lambda m: str(m.get("created_at")))
        first_user = next((m for m in msgs if m.get("sender") == "user"), None)
        if not first_user:
            continue
        inbound += 1
        ch = per_channel[conv.get("channel") or "unknown"]
        ch["inbound"] += 1
        t_user = _dt(first_user.get("created_at"))
        reply = next((m for m in msgs if m.get("sender") in ("ai", "human_agent")
                      and (_dt(m.get("created_at")) or t_user) >= t_user), None) if t_user else None
        if reply:
            answered += 1
            ch["answered"] += 1
            latency = ((_dt(reply.get("created_at")) or t_user) - t_user).total_seconds()
            latencies.append(latency)
            ch["latencies"].append(latency)
    return {
        "inbound_conversations": inbound,
        "answered_conversations": answered,
        "unanswered_conversations": inbound - answered,
        "response_rate_pct": ratio(answered, inbound, 100, 1),
        "median_first_reply_seconds": round(statistics.median(latencies), 1) if latencies else None,
        "channels": [
            {"channel": k, **channel_meta(k), "inbound": v["inbound"], "answered": v["answered"],
             "response_rate_pct": ratio(v["answered"], v["inbound"], 100, 1),
             "median_first_reply_seconds": round(statistics.median(v["latencies"]), 1) if v["latencies"] else None}
            for k, v in sorted(per_channel.items(), key=lambda kv: -kv[1]["inbound"])
        ],
    }


# ── posts ───────────────────────────────────────────────────────────────
def format_post(p: dict[str, Any], projects: dict[str, str]) -> dict[str, Any]:
    likes, comments, shares = to_int(p.get("likes_count")), to_int(p.get("comments_count")), to_int(p.get("shares_count"))
    saves = p.get("saves")
    interactions = likes + comments + shares + to_int(saves)
    reach = p.get("reach")
    views = p.get("views")
    base = to_int(reach) or to_int(views)
    return {
        "id": p.get("id"),
        "external_post_id": p.get("external_post_id"),
        "title": p.get("topic"),
        "caption": p.get("post_content") or "",
        "platform": p.get("platform"),
        "format": (p.get("media_type") or "post").replace("_", " ").title(),
        "project": projects.get(p.get("project_id") or "", None),
        "published_at": p.get("published_at"),
        "permalink": p.get("permalink"),
        "media_url": p.get("media_url"),
        "views": to_int(views) if views is not None else None,
        "reach": to_int(reach) if reach is not None else None,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "saves": to_int(saves) if saves is not None else None,
        "engagement_rate_pct": ratio(interactions, base, 100, 1) if base else None,
        "engagement_rate_basis": "reach" if to_int(reach) else ("views" if to_int(views) else None),
        "metrics_synced_at": p.get("metrics_synced_at"),
        "is_demo": bool(p.get("is_demo")),
    }


# ── demo rows → pseudo metric rows ──────────────────────────────────────
def demo_metric_rows(campaigns: list[dict[str, Any]], on: date) -> list[dict[str, Any]]:
    """Seed campaigns only carry lifetime totals; expose them as one BDT row each."""
    rows = []
    for c in campaigns:
        platform = (c.get("platform") or "other").lower()
        rows.append({
            "platform": platform,
            "external_campaign_id": c.get("external_id") or str(c.get("id")),
            "metric_date": on.isoformat(),
            "channel": platform if platform in CHANNELS else "other",
            "currency": REPORTING_CURRENCY,
            "impressions": to_int(c.get("impressions")),
            "reach": to_int(c.get("reach")),
            "clicks": 0,
            "link_clicks": 0,
            "engagements": to_int(c.get("engagements")),
            "spend": to_float(c.get("ad_spend_bdt")),
            "leads": to_int(c.get("leads_generated")),
            "messaging_conversations": 0,
            "conversions": to_int(c.get("leads_generated")),
            "video_views": 0,
            "video_completions": 0,
        })
    return rows


def demo_campaign_index(campaigns: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {campaign_key((c.get("platform") or "other").lower(), c.get("external_id") or str(c.get("id"))): c
            for c in campaigns}


# ── main builders ───────────────────────────────────────────────────────
def build_social_kpis(
    *,
    period: Period,
    filters: Filters,
    campaigns: list[dict[str, Any]],
    current_rows: list[dict[str, Any]],
    previous_rows: list[dict[str, Any]],
    reach_rows: list[dict[str, Any]],
    posts: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    fx: dict[str, float],
    sla: Optional[dict[str, Any]],
    demo: bool = False,
) -> dict[str, Any]:
    project_names = {p.get("project_id"): p.get("name") for p in projects}
    camp_index = demo_campaign_index(campaigns) if demo else {
        campaign_key(c.get("platform"), c.get("external_id")): c for c in campaigns}
    missing_fx: set[str] = set()

    cur_rows = [r for r in current_rows if row_allowed(r, camp_index.get(campaign_key(r.get("platform"), r.get("external_campaign_id"))), filters)]
    prev_rows = [r for r in previous_rows if row_allowed(r, camp_index.get(campaign_key(r.get("platform"), r.get("external_campaign_id"))), filters)]

    total, prev_total = Totals(), Totals()
    by_channel: dict[str, Totals] = defaultdict(Totals)
    prev_by_channel: dict[str, Totals] = defaultdict(Totals)
    by_campaign: dict[str, Totals] = defaultdict(Totals)
    campaign_channels: dict[str, set[str]] = defaultdict(set)
    by_day: dict[str, Totals] = defaultdict(Totals)
    for r in cur_rows:
        key = campaign_key(r.get("platform"), r.get("external_campaign_id"))
        total.add(r, fx, missing_fx)
        by_channel[r.get("channel") or "all"].add(r, fx, missing_fx)
        by_campaign[key].add(r, fx, missing_fx)
        campaign_channels[key].add(r.get("channel") or "all")
        by_day[str(r.get("metric_date"))[:10]].add(r, fx, missing_fx)
    for r in prev_rows:
        prev_total.add(r, fx, missing_fx)
        prev_by_channel[r.get("channel") or "all"].add(r, fx, missing_fx)

    kpis = total.summary()
    prev_kpis = prev_total.summary()
    allowed_campaigns = {k for k, c in camp_index.items() if campaign_allowed(c, filters)}
    if demo:
        reach_value = sum(to_int(r.get("reach")) for r in cur_rows) if cur_rows else None
        reach_method = "demo"
    else:
        reach_value, reach_method = compute_reach(period, filters, reach_rows, cur_rows, allowed_campaigns)
    kpis["reach"] = reach_value

    channels = []
    for ch, t in sorted(by_channel.items(), key=lambda kv: -kv[1].spend_bdt):
        s = t.summary()
        p = prev_by_channel[ch].summary() if ch in prev_by_channel else None
        channels.append({**channel_meta(ch), **s,
                         "leads_delta_pct": pct_change(s["leads"], p["leads"]) if p else None,
                         "spend_delta_pct": pct_change(s["spend_bdt"], p["spend_bdt"]) if p else None,
                         "lead_share_pct": ratio(s["leads"], kpis["leads"], 100, 1)})

    campaign_list = []
    keys = set(by_campaign)
    if not demo:
        keys |= {k for k in allowed_campaigns if (camp_index[k].get("status") or "").lower() == "active"
                 and (filters.channel == "all" or filters.channel == camp_index[k].get("platform"))}
    for key in keys:
        c = camp_index.get(key) or {}
        s = (by_campaign.get(key) or Totals()).summary()
        campaign_list.append({
            "key": key,
            "platform": c.get("platform") or key.split(":", 1)[0],
            "platform_name": PLATFORM_NAMES.get(c.get("platform") or "", (c.get("platform") or "").title()),
            "external_id": c.get("external_id"),
            "name": c.get("campaign_name") or key.split(":", 1)[-1],
            "status": (c.get("status") or "unknown").upper(),
            "campaign_type": c.get("campaign_type") or "other",
            "objective": c.get("objective"),
            "project_id": c.get("project_id"),
            "project": project_names.get(c.get("project_id")),
            "currency": c.get("currency"),
            "budget_amount": to_float(c.get("budget_amount")) if c.get("budget_amount") is not None else None,
            "budget_type": c.get("budget_type"),
            "channels": sorted(campaign_channels.get(key, set())),
            **s,
        })
    campaign_list.sort(key=lambda x: (-x["spend_bdt"], x["name"]))

    series = []
    for i in range(period.days):
        d = (period.since + timedelta(days=i)).isoformat()
        s = (by_day.get(d) or Totals()).summary()
        series.append({"date": d, "impressions": s["impressions"], "clicks": s["clicks"], "leads": s["leads"],
                       "spend_bdt": s["spend_bdt"], "messaging_conversations": s["messaging_conversations"]})

    post_list = [format_post(p, project_names) for p in posts
                 if filters.channel in ("all", "meta") or p.get("platform") == filters.channel]

    warnings = []
    if missing_fx:
        warnings.append(f"No BDT conversion rate for {', '.join(sorted(missing_fx))}; that spend is excluded "
                        f"from money totals. Set it via PUT /api/v1/ads/fx-rates.")

    return {
        "currency": REPORTING_CURRENCY,
        "period": period.as_dict(),
        "kpis": kpis,
        "previous_kpis": prev_kpis,
        "deltas": deltas(kpis, prev_kpis),
        "reach_method": reach_method,
        "platforms": channels,
        "campaigns": campaign_list,
        "time_series": series,
        "posts": post_list,
        "ai_sla": sla,
        "insights": build_insights(channels, campaign_list, kpis, prev_kpis),
        "warnings": warnings,
        "missing_fx": sorted(missing_fx),
        "available": {
            "channels": [channel_meta(ch) for ch in sorted({r.get("channel") for r in current_rows + previous_rows if r.get("channel")})],
            "campaign_types": sorted({(c.get("campaign_type") or "other") for c in camp_index.values()}),
            "projects": [{"project_id": p.get("project_id"), "name": p.get("name")} for p in projects],
        },
    }


def build_insights(channels: list[dict[str, Any]], campaigns: list[dict[str, Any]], kpis: dict[str, Any],
                   prev: dict[str, Any]) -> list[dict[str, Any]]:
    """Rule-based observations computed only from the numbers above."""
    out: list[dict[str, Any]] = []
    with_leads = [c for c in channels if c["leads"] >= 5 and c["cpl_bdt"] is not None]
    if len(with_leads) >= 2:
        best = min(with_leads, key=lambda c: c["cpl_bdt"])
        worst = max(with_leads, key=lambda c: c["cpl_bdt"])
        if worst["cpl_bdt"] > best["cpl_bdt"] * 1.2:
            out.append({
                "priority": "HIGH",
                "title": f"{best['name']} has the lowest cost per lead",
                "detail": f"৳{best['cpl_bdt']:,.0f} per lead over {best['leads']} leads, vs ৳{worst['cpl_bdt']:,.0f} on {worst['name']}.",
                "metric": "cpl_bdt",
            })
    for c in campaigns:
        if c["campaign_type"] in LEAD_CAMPAIGN_TYPES and c["spend_bdt"] > 0 and c["leads"] == 0 and c["messaging_conversations"] == 0:
            out.append({
                "priority": "HIGH",
                "title": f"'{c['name']}' spent with no leads",
                "detail": f"৳{c['spend_bdt']:,.0f} spent in this period without a lead or conversation.",
                "metric": "leads",
            })
            if len(out) >= 4:
                break
    change = pct_change(kpis.get("cpl_bdt"), prev.get("cpl_bdt"))
    if change is not None and abs(change) >= 20:
        out.append({
            "priority": "MEDIUM",
            "title": f"Cost per lead {'rose' if change > 0 else 'fell'} {abs(change):.0f}%",
            "detail": f"৳{kpis['cpl_bdt']:,.0f} now vs ৳{prev['cpl_bdt']:,.0f} in the previous period.",
            "metric": "cpl_bdt",
        })
    return out[:5]


def weekly_buckets(period_until: date, weeks: int = 4) -> list[tuple[str, date, date]]:
    buckets = []
    for i in range(weeks, 0, -1):
        end = period_until - timedelta(days=7 * (i - 1))
        start = end - timedelta(days=6)
        buckets.append((f"{start.strftime('%d %b')}–{end.strftime('%d %b')}", start, end))
    return buckets


def build_manager_overview(
    *,
    social: dict[str, Any],
    tours: list[dict[str, Any]],
    pending_posts: int,
    until: date,
    daily_rows_4w: list[dict[str, Any]],
) -> dict[str, Any]:
    """Manager dashboard view on top of build_social_kpis output (same filters, same numbers)."""
    k = social["kpis"]
    buckets = weekly_buckets(until)
    leads_by_day: dict[date, int] = defaultdict(int)
    for r in daily_rows_4w:
        d = _date(r.get("metric_date"))
        if d:
            leads_by_day[d] += to_int(r.get("leads"))
    tour_dates = [_date(t.get("date")) for t in tours]
    leads_vs_tours = []
    for label, start, end in buckets:
        leads_vs_tours.append({
            "period": label,
            "leads": sum(v for d, v in leads_by_day.items() if start <= d <= end),
            "tours": sum(1 for d in tour_dates if d and start <= d <= end),
        })
    period = social["period"]
    since, p_until = date.fromisoformat(period["since"]), date.fromisoformat(period["until"])
    tours_in_period = sum(1 for d in tour_dates if d and since <= d <= p_until)
    sla = social.get("ai_sla") or {}
    return {
        "currency": REPORTING_CURRENCY,
        "period": period,
        "kpis": {
            "total_ad_spend_bdt": k["spend_bdt"],
            "ad_spend_delta_pct": social["deltas"].get("spend_bdt"),
            "spend_trend": [{"date": p["date"], "spend_bdt": p["spend_bdt"]} for p in social["time_series"]],
            "reach": k.get("reach"),
            "reach_method": social.get("reach_method"),
            "impressions": k["impressions"],
            "messages_received": k["messaging_conversations"],
            "cost_per_message_bdt": k["cost_per_message_bdt"],
            "ai_response_rate_pct": sla.get("response_rate_pct"),
            "ai_median_first_reply_seconds": sla.get("median_first_reply_seconds"),
            "ai_inbound_conversations": sla.get("inbound_conversations"),
            "leads": k["leads"],
            "leads_delta_pct": social["deltas"].get("leads"),
            "confirmed_tours": tours_in_period,
            "tour_conversion_pct": ratio(tours_in_period, k["leads"], 100, 1),
            "leads_vs_tours": leads_vs_tours,
            "pending_social_posts": pending_posts,
        },
        "campaigns": [
            {
                "key": c["key"], "platform": c["platform"], "platform_name": c["platform_name"],
                "name": c["name"], "status": c["status"], "channels": c["channels"],
                "spend_bdt": c["spend_bdt"], "impressions": c["impressions"],
                "messages": c["messaging_conversations"], "leads": c["leads"], "cpl_bdt": c["cpl_bdt"],
                "project": c["project"],
            }
            for c in social["campaigns"]
        ],
        "warnings": social.get("warnings", []),
    }
