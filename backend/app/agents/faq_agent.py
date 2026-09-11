"""FAQ Agent — Handles general company, documentation, policy and contact questions.

Audit Reference: prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md
Replaces static Indian FAQ dictionaries with approved PolicyRepository and ContactRepository data.
"""

from typing import Optional
import logging

from app.services.llm import llm_service
from app.prompts.faq import FAQ_AGENT_PROMPT
from app.prompts.registry import log_prompt_telemetry
from app.repositories.policy_repository import policy_repository
from app.repositories.contact_repository import contact_repository
from app.services.grounding_validator import grounding_validator
from app.utils.language import detect_language

logger = logging.getLogger(__name__)


class FAQAgent:
    """Handles general knowledge and FAQ conversations using verified policies and contacts."""

    async def handle(self, message: str, extra_context: str = "") -> str:
        """Process an FAQ inquiry using approved policies and contact repositories."""
        lang_info = detect_language(message)
        is_english = lang_info["language"] == "en"
        query_lower = message.lower()

        # 1. Check for Contact Info Request
        if any(kw in query_lower for kw in ["contact", "phone", "number", "email", "address", "office", "helpline", "jogajog", "thikana", "kothay"]):
            if any(c_kw in query_lower for c_kw in ["office", "thikana", "address", "phone", "number", "jogajog", "contact", "helpline"]):
                contact_card = contact_repository.format_contact_card(is_english=is_english)
                title = "Contact Information" if is_english else "যোগাযোগের বিবরণ"
                return f"📋 *{title}*\n\n{contact_card}"

        # 2. Check Approved Policy Repository Match
        matched_policy = policy_repository.match_policy(message)
        if matched_policy:
            title = matched_policy["title_en"] if is_english else matched_policy["title_bn"]
            body = matched_policy["answer_en"] if is_english else matched_policy["answer_bn"]
            return f"📋 *{title}*\n\n{body}"

        # 3. Assemble Structured Evidence Context for LLM
        contact_info = contact_repository.get_contact_info()
        doc_purchase = policy_repository.get_policy("required_documents_purchase")
        doc_rental = policy_repository.get_policy("required_documents_rental")
        payment_policy = policy_repository.get_policy("standard_payment_plan")

        approved_context = (
            f"--- OFFICIAL COMPANY CONTACT ---\n{contact_repository.format_contact_card(is_english=is_english)}\n\n"
            f"--- PURCHASE DOCUMENTS POLICY ---\n{doc_purchase['answer_en'] if is_english else doc_purchase['answer_bn']}\n\n"
            f"--- RENTAL DOCUMENTS POLICY ---\n{doc_rental['answer_en'] if is_english else doc_rental['answer_bn']}\n\n"
            f"--- PAYMENT PLAN POLICY ---\n{payment_policy['answer_en'] if is_english else payment_policy['answer_bn']}\n"
        )
        if extra_context:
            approved_context += f"\n--- RETRIEVED KNOWLEDGE CONTEXT ---\n{extra_context}\n"

        messages = [
            {"role": "system", "content": FAQ_AGENT_PROMPT},
            {"role": "system", "content": f"APPROVED BUSINESS KNOWLEDGE:\n{approved_context}"},
            {"role": "user", "content": message}
        ]

        try:
            raw_reply = await llm_service.chat(messages, temperature=0.2)
        except Exception as e:
            logger.error(f"LLM call failed in FAQAgent: {e}")
            raw_reply = (
                "For detailed company information, purchase procedures, and documentation guidelines in Dhaka, "
                "please contact our client advisory team:\n\n" + contact_repository.format_contact_card(is_english=is_english)
            )

        # 4. Grounding Validation
        validation = grounding_validator.validate(reply_text=raw_reply, is_english=is_english)
        final_reply = validation.sanitized_reply if not validation.is_grounded and validation.sanitized_reply else raw_reply

        # 5. Telemetry
        log_prompt_telemetry(
            agent_name="faq_agent",
            model_name="gemini-flash",
            temperature=0.2,
            language=lang_info["language"],
            grounding_status=validation.is_grounded,
        )

        return final_reply


faq_agent = FAQAgent()
