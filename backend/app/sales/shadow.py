"""Shadow comparison and AI quality numbers: the evidence for retiring the old pipeline.

Staff rate each stored pair (old reply vs sales draft) better / same / worse. ``quality_report`` combines those
ratings with the sales assistant's own turn records (model calls, latency, grounding blocks, handoffs) and checks
them against the retirement gates in the AI workflow fix plan.
"""

from datetime import timedelta
from statistics import median
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sales.db import now_utc
from app.sales.errors import NotFound, SalesError
from app.sales.leads import iso
from app.sales.models import SHADOW_RATINGS, AIShadowPair, SalesAgentTurn

# Retirement gates (plan, Phases D and E)
GATES = {
    "min_rated_pairs": 50,
    # Performance numbers only count once there is enough traffic behind them
    "min_turns": 1000,
    "max_worse_pct": 10.0,
    "min_better_or_same_pct": 85.0,
    "max_median_model_calls": 2,
    "max_p95_model_calls": 3,
    "max_p95_latency_ms": 8000,
    "max_grounding_blocks_per_100": 10.0,
}


def pair_to_dict(p: AIShadowPair) -> dict:
    return {
        "pair_id": p.pair_id,
        "conversation_id": p.conversation_id,
        "legacy_conversation_id": p.legacy_conversation_id,
        "channel": p.channel,
        "customer_text": p.customer_text,
        "legacy_reply": p.legacy_reply,
        "legacy_agent": p.legacy_agent,
        "legacy_escalated": p.legacy_escalated,
        "sales_reply": p.sales_reply,
        "sales_outcome": p.sales_outcome,
        "sales_reason": p.sales_reason,
        "rating": p.rating,
        "rating_note": p.rating_note,
        "rated_by": p.rated_by,
        "rated_at": iso(p.rated_at),
        "created_at": iso(p.created_at),
    }


async def list_pairs(
    session: AsyncSession, tenant_id: str, *, rated: Optional[bool] = None, limit: int = 50
) -> list[dict]:
    stmt = select(AIShadowPair).where(AIShadowPair.tenant_id == tenant_id)
    if rated is True:
        stmt = stmt.where(AIShadowPair.rating.is_not(None))
    elif rated is False:
        stmt = stmt.where(AIShadowPair.rating.is_(None))
    rows = (await session.execute(stmt.order_by(AIShadowPair.created_at.desc()).limit(max(1, min(limit, 200))))).scalars().all()
    return [pair_to_dict(p) for p in rows]


async def rate_pair(
    session: AsyncSession, tenant_id: str, pair_id: str, rating: str, actor: str, note: Optional[str] = None
) -> dict:
    if rating not in SHADOW_RATINGS:
        raise SalesError("INVALID_RATING", f"Rating must be one of {', '.join(SHADOW_RATINGS)}")
    pair = await session.get(AIShadowPair, pair_id)
    if not pair or pair.tenant_id != tenant_id:
        raise NotFound("PAIR_NOT_FOUND", "Comparison does not exist")
    if not pair.sales_reply:
        raise SalesError("NOTHING_TO_COMPARE", "The sales assistant made no draft for this message")
    pair.rating, pair.rating_note, pair.rated_by, pair.rated_at = rating, (note or "").strip() or None, actor, now_utc()
    await session.flush()
    return pair_to_dict(pair)


def _p95(values: list[int]) -> Optional[int]:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]


def _pct(part: int, whole: int) -> Optional[float]:
    return round(100 * part / whole, 1) if whole else None


async def quality_report(session: AsyncSession, tenant_id: str, days: int = 14) -> dict:
    since = now_utc() - timedelta(days=days)
    ratings = dict((await session.execute(
        select(AIShadowPair.rating, func.count())
        .where(AIShadowPair.tenant_id == tenant_id, AIShadowPair.created_at >= since)
        .group_by(AIShadowPair.rating)
    )).all())
    rated = sum(ratings.get(r, 0) for r in SHADOW_RATINGS)
    better, same, worse = (ratings.get(r, 0) for r in SHADOW_RATINGS)
    comparison = {
        "pairs": sum(ratings.values()), "rated": rated, "better": better, "same": same, "worse": worse,
        "worse_pct": _pct(worse, rated), "better_or_same_pct": _pct(better + same, rated),
    }

    turns = (await session.execute(
        select(SalesAgentTurn.model_calls, SalesAgentTurn.duration_ms, SalesAgentTurn.tokens, SalesAgentTurn.outcome,
               SalesAgentTurn.conversation_id)
        .where(SalesAgentTurn.tenant_id == tenant_id, SalesAgentTurn.created_at >= since, SalesAgentTurn.model_calls > 0)
    )).all()
    calls = [t.model_calls for t in turns]
    latency = [t.duration_ms for t in turns]
    outcomes: dict[str, int] = {}
    for t in turns:
        key = t.outcome.split(":", 1)[-1]
        outcomes[key] = outcomes.get(key, 0) + 1
    conversations = {t.conversation_id for t in turns}
    performance = {
        "turns": len(turns),
        "median_model_calls": median(calls) if calls else None,
        "p95_model_calls": _p95(calls),
        "p50_latency_ms": int(median(latency)) if latency else None,
        "p95_latency_ms": _p95(latency),
        "tokens_per_conversation": round(sum(t.tokens for t in turns) / len(conversations)) if conversations else None,
        "outcomes": outcomes,
        "handoff_pct": _pct(outcomes.get("handoff", 0) + outcomes.get("grounding_failed", 0) + outcomes.get("error", 0), len(turns)),
        "grounding_blocks_per_100": round(100 * outcomes.get("grounding_failed", 0) / len(turns), 1) if turns else None,
    }

    def check(value, limit, higher_is_better=False):
        if value is None:
            return None
        return value >= limit if higher_is_better else value <= limit

    enough_turns = len(turns) >= GATES["min_turns"]

    def measured(value, limit):
        return check(value, limit) if enough_turns else None

    gates = {
        "enough_ratings": rated >= GATES["min_rated_pairs"],
        "enough_turns": enough_turns,
        "worse_under_limit": check(comparison["worse_pct"], GATES["max_worse_pct"]),
        "better_or_same": check(comparison["better_or_same_pct"], GATES["min_better_or_same_pct"], higher_is_better=True),
        "median_model_calls": measured(performance["median_model_calls"], GATES["max_median_model_calls"]),
        "p95_model_calls": measured(performance["p95_model_calls"], GATES["max_p95_model_calls"]),
        "p95_latency": measured(performance["p95_latency_ms"], GATES["max_p95_latency_ms"]),
        "grounding_blocks": measured(performance["grounding_blocks_per_100"], GATES["max_grounding_blocks_per_100"]),
    }
    return {
        "days": days,
        "comparison": comparison,
        "performance": performance,
        "gates": gates,
        "thresholds": GATES,
        "ready_to_retire_legacy": all(v is True for v in gates.values()),
    }
