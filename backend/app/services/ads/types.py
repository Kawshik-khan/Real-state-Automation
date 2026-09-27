"""Platform-neutral records produced by the ad connectors.

Every connector (Meta, Google Ads, TikTok) normalizes its API responses into these
dataclasses so the sync service and analytics never see platform-specific shapes.
Money is always in the ad account's own currency; conversion to BDT happens at
read time from fx_rates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Optional

PLATFORM_META = "meta"
PLATFORM_GOOGLE = "google_ads"
PLATFORM_TIKTOK = "tiktok"
ALL_PLATFORMS = (PLATFORM_META, PLATFORM_GOOGLE, PLATFORM_TIKTOK)

ACCOUNT_REACH_KEY = "__account__"

# Normalized campaign types used by the dashboard filter.
CAMPAIGN_TYPES = (
    "lead_generation",
    "messages",
    "traffic",
    "engagement",
    "brand_awareness",
    "video_views",
    "sales",
    "other",
)


class ConnectorError(Exception):
    """A platform API call failed after retries."""

    def __init__(self, platform: str, message: str, status_code: Optional[int] = None):
        super().__init__(f"[{platform}] {message}")
        self.platform = platform
        self.message = message
        self.status_code = status_code


class ConnectorAuthError(ConnectorError):
    """Credentials were rejected (expired, revoked, or missing permission)."""


@dataclass
class AdAccount:
    platform: str
    external_account_id: str
    name: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    status: str = "active"

    @property
    def id(self) -> str:
        return f"{self.platform}:{self.external_account_id}"


@dataclass
class Campaign:
    platform: str
    external_id: str
    ad_account_id: str
    name: str
    status: str  # ACTIVE | PAUSED | ARCHIVED | DELETED | UNKNOWN
    objective: Optional[str] = None
    campaign_type: str = "other"
    currency: Optional[str] = None
    budget_amount: Optional[float] = None
    budget_type: Optional[str] = None  # daily | lifetime


@dataclass
class DailyMetric:
    platform: str
    external_campaign_id: str
    metric_date: date
    channel: str = "all"
    ad_account_id: Optional[str] = None
    currency: Optional[str] = None
    campaign_name: Optional[str] = None
    impressions: int = 0
    reach: Optional[int] = None
    clicks: int = 0
    link_clicks: int = 0
    engagements: int = 0
    spend: float = 0.0
    leads: int = 0
    messaging_conversations: int = 0
    conversions: float = 0.0
    video_views: int = 0
    video_completions: int = 0
    raw: Optional[dict[str, Any]] = None


@dataclass
class PeriodReach:
    platform: str
    external_campaign_id: str  # ACCOUNT_REACH_KEY for account-level reach
    window_days: int
    since_date: date
    until_date: date
    reach: Optional[int]


@dataclass
class SocialPost:
    platform: str  # facebook | instagram
    external_post_id: str
    published_at: Optional[datetime]
    message: str = ""
    permalink: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    views: Optional[int] = None
    reach: Optional[int] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: Optional[int] = None


@dataclass
class SyncPayload:
    """Everything one connector pulled for one account in one run."""

    account: AdAccount
    campaigns: list[Campaign] = field(default_factory=list)
    daily_metrics: list[DailyMetric] = field(default_factory=list)
    period_reach: list[PeriodReach] = field(default_factory=list)
    posts: list[SocialPost] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def to_int(value: Any) -> int:
    """Parse platform numbers (Meta/TikTok send strings, Google sends int64 strings)."""
    if value is None or value == "" or value == "-":
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def to_opt_int(value: Any) -> Optional[int]:
    if value is None or value == "" or value == "-":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> float:
    if value is None or value == "" or value == "-":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def record_dict(obj: Any) -> dict[str, Any]:
    return asdict(obj)
