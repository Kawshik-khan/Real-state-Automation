"""Deterministic lead scoring and qualification, computed in code so the model can't inflate it."""

from typing import Optional

QUALIFIED_THRESHOLD = 45


def timeline_points(timeline: Optional[str]) -> int:
    if not timeline:
        return 0
    t = timeline.lower()
    if any(k in t for k in ("now", "immediate", "this month", "1 month", "within 3", "3 month", "এখনই")):
        return 25
    if any(k in t for k in ("6 month", "six month", "this year", "within 6")):
        return 15
    return 5


def compute_score(
    *,
    budget_max_bdt: Optional[int],
    preferred_areas: Optional[list],
    bedrooms: Optional[int],
    timeline: Optional[str],
    phone: Optional[str],
    has_active_visit: bool = False,
) -> int:
    score = 0
    if budget_max_bdt:
        score += 25
    if preferred_areas:
        score += 15
    if bedrooms:
        score += 10
    score += timeline_points(timeline)
    if phone:
        score += 10
    if has_active_visit:
        score += 15
    return min(score, 100)


def is_qualified(*, budget_max_bdt: Optional[int], preferred_areas: Optional[list], bedrooms: Optional[int]) -> bool:
    """A lead is qualified once we know what they can spend and at least where or what they want."""
    return bool(budget_max_bdt) and bool(preferred_areas or bedrooms)
