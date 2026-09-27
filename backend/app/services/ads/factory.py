"""Build ad connectors from stored credentials (system_integrations) or environment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.config import settings
from app.services.ads.google_ads import GoogleAdsConnector
from app.services.ads.meta_ads import MetaAdsConnector
from app.services.ads.tiktok_ads import TikTokAdsConnector
from app.services.ads.types import PLATFORM_GOOGLE, PLATFORM_META, PLATFORM_TIKTOK

# Integration catalog keys (see integration_service.INTEGRATION_CATALOG)
SERVICE_KEYS = {PLATFORM_META: "meta_ads", PLATFORM_GOOGLE: "google_ads", PLATFORM_TIKTOK: "tiktok_ads"}

REQUIRED_FIELDS = {
    PLATFORM_META: ("access_token", "ad_account_ids"),
    PLATFORM_GOOGLE: ("developer_token", "client_id", "client_secret", "refresh_token", "customer_ids"),
    PLATFORM_TIKTOK: ("access_token", "advertiser_ids"),
}


@dataclass
class ConnectorSpec:
    platform: str
    account_ref: str  # normalized external account ID (no act_ prefix, digits only for Google)
    connector: Any
    include_posts: bool = False

    @property
    def ad_account_id(self) -> str:
        return f"{self.platform}:{self.account_ref}"


def split_ids(raw: Optional[str]) -> list[str]:
    return [part.strip() for part in str(raw or "").replace(";", ",").split(",") if part.strip()]


def env_credentials(platform: str) -> dict[str, Any]:
    """Credentials from settings/.env; empty dict when the required ones are missing."""
    if platform == PLATFORM_META:
        creds = {
            "access_token": settings.meta_ads_access_token,
            "ad_account_ids": settings.meta_ad_account_ids,
            "app_secret": settings.facebook_app_secret,
            "page_id": settings.facebook_page_id,
            "page_access_token": settings.facebook_page_access_token,
            "instagram_account_id": settings.instagram_account_id,
        }
    elif platform == PLATFORM_GOOGLE:
        creds = {
            "developer_token": settings.google_ads_developer_token,
            "client_id": settings.google_ads_client_id,
            "client_secret": settings.google_ads_client_secret,
            "refresh_token": settings.google_ads_refresh_token,
            "login_customer_id": settings.google_ads_login_customer_id,
            "customer_ids": settings.google_ads_customer_ids,
        }
    elif platform == PLATFORM_TIKTOK:
        creds = {"access_token": settings.tiktok_ads_access_token, "advertiser_ids": settings.tiktok_advertiser_ids}
    else:
        return {}
    creds = {k: v for k, v in creds.items() if v}
    return creds if has_required(platform, creds) else {}


def has_required(platform: str, creds: Optional[dict[str, Any]]) -> bool:
    return bool(creds) and all(creds.get(f) for f in REQUIRED_FIELDS.get(platform, ()))


def connectors_for(platform: str, creds: dict[str, Any]) -> list[ConnectorSpec]:
    """One connector per configured account ID."""
    if not has_required(platform, creds):
        return []
    specs: list[ConnectorSpec] = []
    if platform == PLATFORM_META:
        for i, account_id in enumerate(split_ids(creds["ad_account_ids"])):
            connector = MetaAdsConnector(
                access_token=creds["access_token"],
                ad_account_id=account_id,
                api_version=settings.meta_graph_api_version,
                app_secret=creds.get("app_secret") or settings.facebook_app_secret,
                page_id=creds.get("page_id") or settings.facebook_page_id,
                page_access_token=creds.get("page_access_token") or settings.facebook_page_access_token,
                instagram_account_id=creds.get("instagram_account_id") or settings.instagram_account_id,
            )
            # Organic posts belong to the page, not the ad account: fetch them once.
            specs.append(ConnectorSpec(platform, connector.account_id, connector, include_posts=(i == 0)))
    elif platform == PLATFORM_GOOGLE:
        for customer_id in split_ids(creds["customer_ids"]):
            connector = GoogleAdsConnector(
                developer_token=creds["developer_token"],
                client_id=creds["client_id"],
                client_secret=creds["client_secret"],
                refresh_token=creds["refresh_token"],
                customer_id=customer_id,
                login_customer_id=creds.get("login_customer_id"),
                api_version=settings.google_ads_api_version,
            )
            specs.append(ConnectorSpec(platform, connector.customer_id, connector))
    elif platform == PLATFORM_TIKTOK:
        for advertiser_id in split_ids(creds["advertiser_ids"]):
            connector = TikTokAdsConnector(access_token=creds["access_token"], advertiser_id=advertiser_id)
            specs.append(ConnectorSpec(platform, connector.advertiser_id, connector))
    return specs


async def load_credentials(platform: str) -> dict[str, Any]:
    """Encrypted DB credentials first (saved from the Developer Console), then env."""
    from app.database import is_db_reachable
    from app.services.integration_service import integration_service

    # The vault lives behind the SQLAlchemy connection; when that database is not
    # reachable (e.g. Render talking to Supabase over HTTPS only) skip straight to
    # env instead of waiting on a connect timeout every call.
    creds = integration_service.get_cached_credentials(SERVICE_KEYS[platform])
    if not has_required(platform, creds) and is_db_reachable():
        creds = await integration_service.get_active_credentials(SERVICE_KEYS[platform])
    return creds if has_required(platform, creds) else env_credentials(platform)


async def build_connectors(platforms: Optional[list[str]] = None) -> list[ConnectorSpec]:
    specs: list[ConnectorSpec] = []
    for platform in platforms or list(SERVICE_KEYS):
        if platform not in SERVICE_KEYS:
            continue
        specs.extend(connectors_for(platform, await load_credentials(platform)))
    return specs
