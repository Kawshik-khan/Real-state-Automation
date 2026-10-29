"""Deterministic grounding gate for assistant replies.

A reply may only state facts that appeared in this turn's tool results (or that the customer said themselves):
- any BDT amount (৳, Tk, BDT, taka, lakh, crore, লক্ষ, কোটি …),
- any unit code the tenant has,
- any year (handover, approval) and any clock time (visit slots).
It may never promise a discount. Unit availability may only be claimed after a unit lookup in the same turn.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Iterable

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

_MULTIPLIERS = {
    "lakh": 100_000, "lac": 100_000, "lakhs": 100_000, "lacs": 100_000, "লক্ষ": 100_000, "লাখ": 100_000,
    "crore": 10_000_000, "crores": 10_000_000, "cr": 10_000_000, "কোটি": 10_000_000,
}
_NUM = r"\d[\d,]*(?:\.\d+)?"
_UNIT_WORD = r"(lakhs?|lacs?|crores?|cr|লক্ষ|লাখ|কোটি)"
_CURRENCY = r"(?:৳|tk\.?|bdt|taka|টাকা)"

_AMOUNT_PATTERNS = [
    re.compile(rf"{_CURRENCY}\s*({_NUM})\s*{_UNIT_WORD}?", re.IGNORECASE),
    re.compile(rf"({_NUM})\s*{_UNIT_WORD}", re.IGNORECASE),
    re.compile(rf"({_NUM})\s*{_CURRENCY}", re.IGNORECASE),
]
_YEAR = re.compile(r"\b(20[2-4]\d)\b")
_TIME = re.compile(r"\b(\d{1,2}):(\d{2})\s*([ap]\.?m\.?)?", re.IGNORECASE)
_DISCOUNT = re.compile(
    r"(\d+\s*%\s*(off|discount|ছাড়))|(discount\s+(of|is|has been|approved))|(ছাড়\s*(দেওয়া|দিচ্ছি|দিতে পারি))",
    re.IGNORECASE,
)
_AVAILABILITY = re.compile(
    r"(flat|unit|apartment|ফ্ল্যাট|ইউনিট)\W+(?:\w+\W+){0,5}?(available|still free|khali|ache|আছে|খালি)|"
    r"(available|khali|খালি)\W+(?:\w+\W+){0,3}?(flat|unit|apartment|ফ্ল্যাট|ইউনিট)",
    re.IGNORECASE,
)
MIN_AMOUNT_BDT = 10_000
UNIT_LOOKUP_TOOLS = {"search_units", "get_unit", "calc_payment_plan"}


@dataclass
class GroundingReport:
    ok: bool
    violations: list = field(default_factory=list)


def _to_number(raw: str) -> float:
    return float(raw.replace(",", ""))


def extract_amounts(text: str) -> set[int]:
    text = text.translate(_BN_DIGITS)
    found: set[int] = set()
    for pattern in _AMOUNT_PATTERNS:
        for match in pattern.finditer(text):
            groups = [g for g in match.groups() if g]
            if not groups:
                continue
            value = _to_number(groups[0])
            unit = groups[1].lower() if len(groups) > 1 else None
            if unit:
                value *= _MULTIPLIERS.get(unit, 1)
            if value >= MIN_AMOUNT_BDT:
                found.add(int(round(value)))
    return found


def _numbers_in(value) -> set[int]:
    """Every integer-valued number anywhere in a tool result."""
    found: set[int] = set()
    if isinstance(value, bool):
        return found
    if isinstance(value, (int, float)):
        found.add(int(round(value)))
    elif isinstance(value, dict):
        for v in value.values():
            found |= _numbers_in(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            found |= _numbers_in(v)
    elif isinstance(value, str):
        found |= extract_amounts(value)
    return found


def _matches(amount: int, allowed: Iterable[int]) -> bool:
    # 1% tolerance covers "95 lakh" for 9,512,000 style rounding and "3.17 lakh" for 316,667.
    return any(a > 0 and abs(amount - a) <= max(1, a * 0.01) for a in allowed)


def _times_in(text: str) -> set[tuple[int, int]]:
    result = set()
    for h, m, ampm in _TIME.findall(text.translate(_BN_DIGITS)):
        hour = int(h)
        if ampm and ampm.lower().startswith("p") and hour < 12:
            hour += 12
        if ampm and ampm.lower().startswith("a") and hour == 12:
            hour = 0
        result.add((hour % 24, int(m)))
        result.add((int(h), int(m)))  # also the literal reading, for 24-hour labels
    return result


def check_reply(
    reply: str,
    *,
    tool_results: list[dict],
    tools_used: Iterable[str],
    customer_text: str = "",
    known_unit_codes: Iterable[str] = (),
) -> GroundingReport:
    violations = []
    evidence_text = json.dumps(tool_results, ensure_ascii=False, default=str)
    allowed_amounts = _numbers_in(tool_results) | extract_amounts(customer_text) | {
        int(n) for n in re.findall(r"\d+", customer_text.translate(_BN_DIGITS)) if int(n) >= MIN_AMOUNT_BDT
    }

    for amount in sorted(extract_amounts(reply)):
        if not _matches(amount, allowed_amounts):
            violations.append({"type": "amount", "value": amount})

    reply_lower = reply.lower()
    evidence_lower = evidence_text.lower()
    for code in known_unit_codes:
        if not code or len(code) < 2:
            continue
        if re.search(rf"(?<![\w-]){re.escape(code.lower())}(?![\w-])", reply_lower) and code.lower() not in evidence_lower:
            violations.append({"type": "unit_code", "value": code})

    allowed_years = set(_YEAR.findall(evidence_text)) | set(_YEAR.findall(customer_text.translate(_BN_DIGITS)))
    for year in set(_YEAR.findall(reply.translate(_BN_DIGITS))):
        if year not in allowed_years:
            violations.append({"type": "year", "value": year})

    # Every clock time in the reply must match a time in a tool result (slot labels are local time) or the
    # customer's own message.
    # ISO timestamps in tool results are UTC; only the human labels count as local times.
    evidence_without_iso = re.sub(r"\d{4}-\d{2}-\d{2}[T ][\d:.]+(?:[+-]\d{2}:\d{2}|Z)?", "", evidence_text)
    allowed_times = _times_in(evidence_without_iso) | _times_in(customer_text)
    for match in _TIME.finditer(reply.translate(_BN_DIGITS)):
        if not _times_in(match.group(0)) & allowed_times:
            violations.append({"type": "time", "value": match.group(0).strip()})

    if _DISCOUNT.search(reply):
        violations.append({"type": "discount_promise"})

    used = set(tools_used)
    if _AVAILABILITY.search(reply) and not used & UNIT_LOOKUP_TOOLS:
        violations.append({"type": "availability_without_lookup"})

    return GroundingReport(ok=not violations, violations=violations)
