"""Weekly marketing-post drafts from new inventory. Nothing is published without a manager's approval.

The old content agent answered customers inside the chat pipeline. Here it never talks to customers: once a week it
drafts one post per project that got new available units, built from inventory facts. An optional AI rewrite is kept
only if the grounding gate finds no price, unit code or date that isn't in those facts. Each draft becomes a
``CONTENT_POST`` approval.
"""

import logging
from datetime import timedelta

from sqlalchemy import select

from app.models.models import ProjectRecord
from app.sales.db import now_utc, session_scope
from app.sales.grounding import check_reply
from app.sales.models import PropertyUnit, SalesApproval

logger = logging.getLogger(__name__)

REWRITE_PROMPT = (
    "Rewrite this real-estate social media post for GLG Assets in a warm, professional tone, English then Bangla. "
    "Use ONLY the facts given; do not add prices, dates, amenities, discounts or claims that aren't in them. "
    "At most 80 words. Return only the post text."
)


def _bedrooms(values: list) -> str:
    beds = sorted({b for b in values if b})
    if not beds:
        return ""
    return f"{beds[0]}" if len(beds) == 1 else f"{beds[0]}–{beds[-1]}"


def template_post(facts: dict) -> str:
    beds = f" ({facts['bedrooms']} bed)" if facts.get("bedrooms") else ""
    return (
        f"New at {facts['project_name']}, {facts['location']}: {facts['available_units']} flat"
        f"{'s' if facts['available_units'] != 1 else ''} available now{beds}, from ৳{facts['price_from_bdt']:,}. "
        "Message us to book a site visit."
    )


async def _rewrite(text: str, facts: dict) -> str:
    """Optional AI polish; the template stands whenever the provider is missing or the rewrite adds a fact."""
    from app.services.llm import llm_service

    if llm_service.get_client() is None:
        return text
    try:
        polished = (await llm_service.chat(
            [{"role": "system", "content": REWRITE_PROMPT}, {"role": "user", "content": f"Facts: {facts}\nPost: {text}"}],
            temperature=0.4, max_tokens=300,
        )).strip()
    except Exception as exc:
        logger.info("[sales.content] rewrite unavailable: %s", exc)
        return text
    report = check_reply(polished, tool_results=[facts], tools_used=["search_units"])
    if not polished or not report.ok:
        logger.info("[sales.content] rewrite dropped: %s", report.violations)
        return text
    return polished


async def draft_weekly_posts(tenant_id: str, days: int = 7) -> dict:
    """One CONTENT_POST approval per project with units added in the last ``days`` days (skipping projects that
    already have a pending post)."""
    since = now_utc() - timedelta(days=days)
    async with session_scope() as session:
        rows = (await session.execute(
            select(PropertyUnit, ProjectRecord)
            .join(ProjectRecord, ProjectRecord.project_id == PropertyUnit.project_id)
            .where(PropertyUnit.tenant_id == tenant_id, PropertyUnit.status == "AVAILABLE", PropertyUnit.created_at >= since)
        )).all()
        pending_payloads = (await session.execute(
            select(SalesApproval.payload).where(
                SalesApproval.tenant_id == tenant_id, SalesApproval.kind == "CONTENT_POST", SalesApproval.status == "PENDING"
            )
        )).scalars().all()
        pending = {(p or {}).get("project_id") for p in pending_payloads}
        by_project: dict[str, dict] = {}
        for unit, project in rows:
            entry = by_project.setdefault(project.project_id, {
                "project_id": project.project_id, "project_name": project.name, "location": project.location,
                "beds": [], "prices": [], "codes": [],
            })
            entry["beds"].append(unit.bedrooms)
            entry["prices"].append(unit.list_price_bdt)
            entry["codes"].append(unit.unit_code)

    created, skipped = [], []
    for project_id, entry in by_project.items():
        if project_id in pending:
            skipped.append(project_id)
            continue
        facts = {
            "project_id": project_id, "project_name": entry["project_name"], "location": entry["location"],
            "available_units": len(entry["codes"]), "bedrooms": _bedrooms(entry["beds"]),
            "price_from_bdt": min(entry["prices"]), "unit_codes": sorted(entry["codes"]),
        }
        text = await _rewrite(template_post(facts), facts)
        async with session_scope() as session:
            approval = SalesApproval(
                tenant_id=tenant_id, kind="CONTENT_POST", lead_id=None, requested_by="ai",
                payload={"project_id": project_id, "project_name": entry["project_name"], "text": text, "facts": facts},
            )
            session.add(approval)
            await session.flush()
            created.append(approval.approval_id)
    return {"created": created, "skipped_pending": skipped}
