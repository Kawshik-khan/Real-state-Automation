"""Enterprise Policy Engine for GLG Assets Autonomous AI System.

Pillar 1 of the Enterprise AI Governance Architecture:
- Evaluates inbound customer messages deterministically before LLM invocation (Pre-Guard).
- Enforces Bangladesh PII redaction (10/13/17-digit NID, bank accounts, cards).
- Inspects outbound agent completions before client transmission (Post-Guard).
- Intercepts foreign legacy token contamination, unverified pricing claims, and guarantee liabilities.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.llm_guardrails import llm_guardrails, GuardrailResult
from app.services.grounding_validator import grounding_validator, GroundingResult, GroundingViolation

logger = logging.getLogger(__name__)


class PolicyEvaluationResult(BaseModel):
    """Encapsulates the deterministic decision of the Policy Engine."""
    is_allowed: bool = True
    action: str = "allow"  # allow | sanitize | block | fallback
    sanitized_text: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    fallback_message_bn: Optional[str] = None
    fallback_message_en: Optional[str] = None


class PolicyEngine:
    """Deterministic, code-level policy enforcement layer (Pillar 1)."""

    def evaluate_inbound_message(self, message: str) -> PolicyEvaluationResult:
        """Evaluates customer input for prompt injection, jailbreaks, and PII.
        
        Runs prior to LLM or agent nodes in the orchestration graph.
        """
        if not message or not message.strip():
            return PolicyEvaluationResult(is_allowed=True, action="allow", sanitized_text=message)

        guard_res: GuardrailResult = llm_guardrails.pre_guard(message)

        if guard_res.action == "block":
            logger.warning(f"[PolicyEngine] Inbound message BLOCKED: {guard_res.reason}")
            return PolicyEvaluationResult(
                is_allowed=False,
                action="block",
                sanitized_text=guard_res.sanitized_text,
                reasons=[guard_res.reason or "Message blocked by deterministic security policy."],
                fallback_message_bn="দুঃখিত, আপনার বার্তাটি আমাদের নিরাপত্তা নীতিমালা অনুযায়ী প্রসেস করা সম্ভব হয়নি। দয়া করে মার্জিত ও প্রাসঙ্গিক বার্তা পাঠান।",
                fallback_message_en="We apologize, but your message cannot be processed under our security guidelines. Please keep our conversation polite and relevant.",
            )

        # Action is either allow or sanitize (e.g. PII redacted)
        return PolicyEvaluationResult(
            is_allowed=True,
            action=guard_res.action,
            sanitized_text=guard_res.sanitized_text or message,
            reasons=[guard_res.reason] if guard_res.reason else [],
        )

    def evaluate_outbound_response(
        self,
        reply_text: str,
        is_english: bool = False,
        active_project_id: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Evaluates generated LLM response before delivery to the customer.
        
        Verifies:
        1. Absence of foreign legacy tokens (Mumbai, Bandra, Aadhaar, PAN, +91).
        2. Pricing consistency with canonical repository records.
        3. Rejection of unsupported liability/financial guarantees (100% bank loan approval).
        4. Absence of leaked internal secrets (API keys, DB connection strings).
        """
        if not reply_text:
            return PolicyEvaluationResult(is_allowed=True, action="allow", sanitized_text="")

        # 1. Post-Guard for secret leaks (API keys, JWT, Postgres URLs)
        sanitized_reply, had_leak = llm_guardrails.post_guard(reply_text)
        if had_leak:
            logger.critical("[PolicyEngine] CRITICAL LEAK BLOCKED in outbound response")
            safe_fallback = (
                "Our client services team is at your service. Please contact our Banani head office for direct assistance."
                if is_english else
                "আমাদের ক্লায়েন্ট সার্ভিস টিম আপনার সেবায় নিয়োজিত। বিস্তারিত তথ্যের জন্য আমাদের বনানী প্রধান কার্যালয়ে যোগাযোগের অনুরোধ করছি।"
            )
            return PolicyEvaluationResult(
                is_allowed=False,
                action="block",
                sanitized_text=safe_fallback,
                reasons=["Secret leakage prevented by post-guard."],
            )

        # 2. Grounding and factual compliance validation
        grounding_res: GroundingResult = grounding_validator.validate(
            reply_text=reply_text,
            active_project_id=active_project_id,
            is_english=is_english,
        )

        if not grounding_res.is_grounded:
            violation_reasons = [v.message for v in grounding_res.violations]
            logger.warning(f"[PolicyEngine] Outbound grounding violations: {violation_reasons}")
            
            # Use sanitized reply if available, otherwise safe fallback
            sanitized = grounding_res.sanitized_reply
            if not sanitized:
                sanitized = (
                    "This information is currently being verified by our sales desk. Please contact our advisory team for accurate specifications."
                    if is_english else
                    "এই তথ্যটি বর্তমানে আমাদের সেলস টিম দ্বারা যাচাই করা হচ্ছে। সঠিক তথ্যের জন্য সরাসরি আমাদের অ্যাডভাইজরি টিমে যোগাযোগ করার অনুরোধ করছি।"
                )

            return PolicyEvaluationResult(
                is_allowed=True,  # Allowed after sanitization/fallback
                action="fallback",
                sanitized_text=sanitized,
                reasons=violation_reasons,
                violations=[v.model_dump() for v in grounding_res.violations],
            )

        return PolicyEvaluationResult(
            is_allowed=True,
            action="allow",
            sanitized_text=reply_text,
        )


# Global singleton policy engine instance
policy_engine = PolicyEngine()
