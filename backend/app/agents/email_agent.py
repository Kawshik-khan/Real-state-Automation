"""Email Agent — Specialized AI Agent for Email Ingestion & Auto-Reply Generation.

Audit Reference: prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md
Eliminates hardcoded $250k / 3.5 Cr price block, sources canonical properties and policies,
preserves role-separated message structure, and runs pre-send GroundingValidator.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.prompts.email import EMAIL_AGENT_SYSTEM_PROMPT
from app.prompts.registry import log_prompt_telemetry
from app.repositories.contact_repository import contact_repository
from app.repositories.policy_repository import policy_repository
from app.repositories.property_repository import property_repository
from app.services.grounding_validator import grounding_validator
from app.services.llm import llm_service

logger = logging.getLogger(__name__)


class EmailAgent:
    """Specialized AI Agent for Email Automation grounded in canonical data."""

    async def process_email(
        self,
        subject: str,
        body_text: str,
        sender_name: Optional[str] = None,
        sender_email: str = "",
        thread_history: Optional[List[Dict[str, str]]] = None,
        attachment_texts: Optional[List[str]] = None,
        rag_context: str = "",
    ) -> Dict[str, Any]:
        """Processes an incoming email within its thread context and generates an AI draft response."""

        # 1. Fetch Verified Canonical Context
        canonical_projects = property_repository.to_legacy_dict_format()
        projects_summary = []
        for p in canonical_projects:
            projects_summary.append({
                "name": p["name"],
                "location": p["location"],
                "price": p["price"],
                "bedrooms": p["bedrooms"],
                "amenities": p["amenities"],
                "handover": p.get("handover", "On Schedule"),
            })

        payment_policy = policy_repository.get_policy("standard_payment_plan")

        verified_evidence = (
            "--- VERIFIED GLG ASSETS PROPERTY INVENTORY ---\n"
            + json.dumps(projects_summary, indent=2)
            + f"\n\n--- APPROVED PAYMENT TERMS ---\n{payment_policy['answer_en']}\n"
            f"\n--- OFFICIAL CONTACT CONFIG ---\n{contact_repository.format_contact_card(is_english=True)}\n"
        )
        if rag_context:
            verified_evidence += f"\n--- RETRIEVED PROJECT RAG CONTEXT ---\n{rag_context}\n"
        if attachment_texts:
            verified_evidence += "\n--- EXTRACTED ATTACHMENT TEXT ---\n" + "\n".join(attachment_texts) + "\n"

        # 2. Build Structured Role-Separated Messages
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": EMAIL_AGENT_SYSTEM_PROMPT},
            {"role": "system", "content": f"AUTHORITATIVE BUSINESS EVIDENCE:\n{verified_evidence}"},
        ]

        # Append structured thread history without string flattening
        if thread_history:
            for turn in thread_history[-5:]:
                role_type = turn.get("sender_type", turn.get("role", "customer")).lower()
                role = "assistant" if role_type in ("assistant", "agent", "glg", "executive") else "user"
                content = turn.get("body_text", turn.get("text", turn.get("content", "")))
                if content.strip():
                    messages.append({"role": role, "content": content})

        # Append current incoming email turn
        current_email_payload = f"From: {sender_name or sender_email} <{sender_email}>\nSubject: {subject}\n\n{body_text}"
        messages.append({"role": "user", "content": current_email_payload})

        # 3. LLM Generation
        raw_reply = ""
        try:
            raw_reply = await llm_service.chat(messages, temperature=0.2)
        except Exception as e:
            logger.error(f"LLM call failed in EmailAgent: {e}")
            raw_reply = (
                f"Dear {sender_name or 'Valued Client'},\n\n"
                f"Thank you for contacting GLG Assets regarding '{subject}'. "
                "Our client advisory team has received your inquiry and will provide verified property details shortly.\n\n"
                + contact_repository.format_contact_card(is_english=True)
            )

        # 4. Grounding Validation
        validation = grounding_validator.validate(reply_text=raw_reply, is_english=True)
        final_body = raw_reply
        if not validation.is_grounded:
            logger.warning(f"EmailAgent grounding violation detected: {validation.violations}")
            if validation.sanitized_reply:
                final_body = validation.sanitized_reply

        # 5. Telemetry
        log_prompt_telemetry(
            agent_name="email_agent",
            model_name="gemini-flash",
            temperature=0.2,
            language="en",
            grounding_status=validation.is_grounded,
        )

        # 6. Intent Classification & Confidence Evaluation
        intent, priority, confidence = self._evaluate_intent_and_confidence(body_text, subject)
        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

        # 7. Policy decision
        auto_send_eligible = (
            confidence >= 0.80
            and intent not in ["complaint", "price_negotiation"]
            and validation.is_grounded
        )
        action = "AUTO_SEND" if auto_send_eligible else "REQUIRES_APPROVAL"

        return {
            "reply_subject": reply_subject,
            "reply_body": final_body,
            "intent": intent,
            "priority": priority,
            "confidence_score": confidence,
            "action": action,
            "auto_send_eligible": auto_send_eligible,
            "grounding_passed": validation.is_grounded,
        }

    def _evaluate_intent_and_confidence(
        self, body_text: str, subject: str
    ) -> tuple[str, str, float]:
        """Heuristic intent & confidence scorer."""
        combined = f"{subject} {body_text}".lower()

        if any(w in combined for w in ["cancel", "complaint", "legal", "scam", "refund", "issue"]):
            return "complaint", "high", 0.60
        elif any(w in combined for w in ["discount", "negotiate", "lowest price", "best offer", "deal"]):
            return "price_negotiation", "high", 0.70
        elif any(w in combined for w in ["tour", "visit", "schedule", "appointment", "see property"]):
            return "tour_request", "high", 0.90
        elif any(w in combined for w in ["price", "cost", "brochure", "floor plan", "details", "available"]):
            return "property_inquiry", "normal", 0.88
        else:
            return "general_inquiry", "normal", 0.85


email_agent = EmailAgent()
