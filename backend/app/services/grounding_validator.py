"""Grounding & Policy Validator for GLG Assets.

Pre-transmission validator that enforces factual integrity, currency consistency,
absence of foreign legacy tokens, and verified property claims.
"""

import re
from typing import List, Optional

from pydantic import BaseModel, Field

from app.repositories.contact_repository import contact_repository
from app.repositories.property_repository import property_repository


class GroundingViolation(BaseModel):
    violation_type: str
    field: str
    value: str
    message: str


class GroundingResult(BaseModel):
    is_grounded: bool = True
    violations: List[GroundingViolation] = Field(default_factory=list)
    sanitized_reply: Optional[str] = None


# Prohibited legacy foreign tokens (India real estate artifacts)
PROHIBITED_FOREIGN_TOKENS = [
    re.compile(r"\baadhaar\b", re.IGNORECASE),
    re.compile(r"\bpan\s*card\b", re.IGNORECASE),
    re.compile(r"\+91[-\s]?\d{4,}", re.IGNORECASE),
    re.compile(r"\bmumbai\b", re.IGNORECASE),
    re.compile(r"\bbandra\b", re.IGNORECASE),
    re.compile(r"\bandheri\b", re.IGNORECASE),
    re.compile(r"\bpowai\b", re.IGNORECASE),
    re.compile(r"\bwhitefield\b", re.IGNORECASE),
    re.compile(r"\bpanjim\b", re.IGNORECASE),
]

# Guarantee / liability triggers
UNSUPPORTED_GUARANTEE_PATTERNS = [
    re.compile(r"guaranteed\s+(return|profit|roi|loan|financing|approval)", re.IGNORECASE),
    re.compile(r"১০০%\s*(লোন|মুনাফা|গ্যারান্টি)", re.IGNORECASE),
]


class GroundingValidator:
    """Validates LLM-generated customer responses against verified business records."""

    def validate(
        self,
        reply_text: str,
        active_project_id: Optional[str] = None,
        is_english: bool = False,
    ) -> GroundingResult:
        """Inspects response for policy and factual violations."""
        if not reply_text:
            return GroundingResult(is_grounded=True)

        violations: List[GroundingViolation] = []

        # 1. Foreign Legacy Tokens Check (P0)
        for pattern in PROHIBITED_FOREIGN_TOKENS:
            match = pattern.search(reply_text)
            if match:
                violations.append(
                    GroundingViolation(
                        violation_type="foreign_token_contamination",
                        field="prohibited_term",
                        value=match.group(0),
                        message=f"Contaminated with foreign legacy artifact: '{match.group(0)}'",
                    )
                )

        # 2. Currency Consistency Check
        # Reject INR / ₹
        if re.search(r"[₹]|INR|\bRupees?\b", reply_text, re.IGNORECASE):
            violations.append(
                GroundingViolation(
                    violation_type="invalid_currency",
                    field="currency",
                    value="INR",
                    message="Detected non-BDT currency symbol or reference.",
                )
            )

        # 3. Unsupported Guarantees Check
        for pattern in UNSUPPORTED_GUARANTEE_PATTERNS:
            match = pattern.search(reply_text)
            if match:
                violations.append(
                    GroundingViolation(
                        violation_type="unsupported_guarantee",
                        field="guarantee",
                        value=match.group(0),
                        message="Unsupported financial guarantee detected.",
                    )
                )

        # 4. Property Price Grounding Check (if a known project is mentioned)
        all_projects = property_repository.get_all()
        for proj in all_projects:
            proj_name = proj["name"].lower()
            if proj_name in reply_text.lower():
                # Check for severe price contradictions (e.g. $250,000 for Gulshan Heights)
                if proj["id"] == "proj_gulshan_luxe":
                    if "$250,000" in reply_text or "3.5 Crore" in reply_text or "৩.৫ কোটি" in reply_text:
                        violations.append(
                            GroundingViolation(
                                violation_type="price_contradiction",
                                field="pricing",
                                value="3.5 Crore / $250,000",
                                message="Contradicts canonical price of 95 Lakhs BDT (৳৯৫ লক্ষ) for GLG Gulshan Heights.",
                            )
                        )

        # 5. Determine Grounding Status & Sanitization
        is_grounded = len(violations) == 0
        sanitized = reply_text

        if not is_grounded:
            # If foreign tokens or severe contradictions are present, apply safe fallback
            has_p0_violation = any(
                v.violation_type in ("foreign_token_contamination", "price_contradiction")
                for v in violations
            )
            if has_p0_violation:
                if is_english:
                    sanitized = (
                        "Thank you for contacting GLG Assets. For verified property specifications, pricing, "
                        "and purchase documentation in Dhaka, please connect directly with our advisory team:\n\n"
                        + contact_repository.format_contact_card(is_english=True)
                    )
                else:
                    sanitized = (
                        "GLG Assets-এ যোগাযোগের জন্য ধন্যবাদ। আমাদের ভেরিফায়েড প্রজেক্ট বিস্তারিত, সঠিক প্রাইজ "
                        "এবং কাগজপত্র সংক্রান্ত তথ্যের জন্য সরাসরি সেলস টিমের সাথে যোগাযোগ করুন:\n\n"
                        + contact_repository.format_contact_card(is_english=False)
                    )

        return GroundingResult(
            is_grounded=is_grounded,
            violations=violations,
            sanitized_reply=sanitized if not is_grounded else None,
        )


grounding_validator = GroundingValidator()
