"""Meta Lead Ads ingestion: leadgen webhook → Graph API lead → public.leads.

The webhook only carries IDs; the lead's answers are fetched with a page token
that has `leads_retrieval`. Leads keep their campaign/ad IDs for attribution.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Optional

import httpx

from app.config import settings
from app.services.ads.factory import load_credentials
from app.services.ads.http import DEFAULT_TIMEOUT, request_json
from app.services.ads.types import PLATFORM_META, ConnectorError

logger = logging.getLogger(__name__)

LEAD_FIELDS = "id,created_time,field_data,ad_id,adset_id,campaign_id,form_id,platform"


def verify_signature(raw_body: bytes, signature_header: Optional[str], app_secret: Optional[str]) -> bool:
    """Validate Meta's X-Hub-Signature-256 header (sha256 HMAC of the raw body)."""
    if not app_secret:
        return True  # verification not configured
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header[len("sha256="):], expected)


def parse_lead(body: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    answers = {f.get("name"): (f.get("values") or [None])[0] for f in body.get("field_data") or []}
    name = answers.get("full_name") or " ".join(
        part for part in (answers.get("first_name"), answers.get("last_name")) if part
    ) or None
    return {
        "lead_id": f"meta:{body['id']}",
        "tenant_id": tenant_id,
        "name": name,
        "contact": answers.get("phone_number") or answers.get("email"),
        "source": "meta_lead_ad",
        "status": "new",
        "version": 1,
        "created_at": body.get("created_time"),
        "platform": PLATFORM_META,
        "external_lead_id": str(body["id"]),
        "external_campaign_id": body.get("campaign_id"),
        "external_ad_id": body.get("ad_id"),
        "form_id": body.get("form_id"),
        "raw": {"field_data": body.get("field_data"), "platform": body.get("platform")},
    }


async def ingest_leadgen(leadgen_id: str, client: Optional[httpx.AsyncClient] = None) -> Optional[dict[str, Any]]:
    from app.repositories.ads_repository import get_ads_repository

    repo = get_ads_repository()
    creds = await load_credentials(PLATFORM_META)
    token = creds.get("page_access_token") or settings.facebook_page_access_token or creds.get("access_token")
    if not repo or not token:
        logger.warning("[meta-leads] leadgen %s received but Supabase or a Meta page token is not configured", leadgen_id)
        return None

    params = {"fields": LEAD_FIELDS, "access_token": token}
    app_secret = creds.get("app_secret") or settings.facebook_app_secret
    if app_secret:
        params["appsecret_proof"] = hmac.new(app_secret.encode(), token.encode(), hashlib.sha256).hexdigest()

    own = client is None
    client = client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
    try:
        body = await request_json(client, PLATFORM_META, "GET",
                                  f"https://graph.facebook.com/{settings.meta_graph_api_version}/{leadgen_id}",
                                  params=params)
    except ConnectorError as err:
        logger.warning("[meta-leads] could not fetch lead %s: %s", leadgen_id, err.message)
        return None
    finally:
        if own:
            await client.aclose()

    row = parse_lead(body, settings.default_tenant_id)
    await repo.upsert_lead(row)
    logger.info("[meta-leads] stored lead %s (campaign %s)", row["lead_id"], row["external_campaign_id"])
    return row
