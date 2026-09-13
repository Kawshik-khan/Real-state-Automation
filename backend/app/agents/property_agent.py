"""Property Agent — Handles property inquiries using canonical PropertyRepository + RAG context.

Audit Reference: prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md
Removes static template bypass, synthesizes SQL + RAG data, enforces PROPERTY_AGENT_PROMPT,
and validates response with GroundingValidator.
"""

import json
import logging

from app.prompts.property import PROPERTY_AGENT_PROMPT
from app.prompts.registry import log_prompt_telemetry
from app.repositories.policy_repository import policy_repository
from app.repositories.property_repository import property_repository
from app.services.grounding_validator import grounding_validator
from app.services.llm import llm_service
from app.tools.property_tool import property_search_tool
from app.utils.language import detect_language

logger = logging.getLogger(__name__)


class PropertyAgent:
    """Handles property search and inquiry conversations with strict factual grounding."""

    async def handle(self, message: str, entities: dict | None = None, extra_context: str = "") -> str:
        """Process a property query by synthesizing canonical repository records with RAG context."""
        entities = entities or {}
        location = entities.get("location")

        # 1. Detect customer language
        lang_info = detect_language(message)
        is_english = lang_info["language"] == "en"

        # 2. Query Canonical Property Database via Tool
        search_res = await property_search_tool.search(
            query=message,
            location=location,
        )
        projects = search_res.get("projects", [])

        # If no projects matched specific query, fetch relevant canonical records for context
        if not projects:
            projects = property_repository.to_legacy_dict_format()

        # 3. Construct Structured Verified Evidence Context (5-tier hierarchy)
        catalog_summary = []
        for p in projects:
            catalog_summary.append({
                "project_id": p.get("id"),
                "name": p.get("name"),
                "location": p.get("location"),
                "price": p.get("price"),
                "price_bn": p.get("price_bn"),
                "bedrooms": p.get("bedrooms"),
                "bathrooms": p.get("bathrooms"),
                "handover": p.get("handover_date"),
                "amenities": p.get("amenities"),
                "description": p.get("description"),
            })

        payment_policy = policy_repository.get_policy("standard_payment_plan")
        payment_info = payment_policy["answer_en"] if is_english else payment_policy["answer_bn"]

        context_builder = (
            "--- VERIFIED CANONICAL PROPERTY RECORDS (AUTHORITATIVE) ---\n"
            + json.dumps(catalog_summary, ensure_ascii=False, indent=2)
            + f"\n\n--- APPROVED PAYMENT POLICY ---\n{payment_info}\n"
        )

        if extra_context:
            context_builder += f"\n--- RETRIEVED RAG KNOWLEDGE BASE CONTEXT ---\n{extra_context}\n"

        # 4. Assemble Messages preserving system policy and role separation
        messages = [
            {"role": "system", "content": PROPERTY_AGENT_PROMPT},
            {"role": "system", "content": f"CURRENT VERIFIED BUSINESS EVIDENCE:\n{context_builder}"},
            {"role": "user", "content": message},
        ]

        # 5. Call LLM with conservative temperature
        raw_reply = ""
        try:
            raw_reply = await llm_service.chat(messages, temperature=0.2)
        except Exception as e:
            logger.error(f"LLM call failed in PropertyAgent: {e}")
            # Fallback to direct factual synthesis from canonical records
            top_p = projects[0] if projects else property_repository.to_legacy_dict_format()[0]
            if is_english:
                raw_reply = (
                    f"🏢 *{top_p['name']}*\n"
                    f"📍 Location: {top_p['location']}\n"
                    f"💰 Price: {top_p['price']} ({top_p['bedrooms']} BHK)\n"
                    f"✨ Verified Amenities: {', '.join(top_p['amenities'])}\n\n"
                    "For verified floor plans and private site visits, our advisory team is at your service."
                )
            else:
                raw_reply = (
                    f"🏢 *{top_p['name']}*\n"
                    f"📍 লোকেশন: {top_p['location']}\n"
                    f"💰 দাম: {top_p.get('price_bn', top_p['price'])} ({top_p['bedrooms']} BHK)\n"
                    f"✨ ভেরিফায়েড সুবিধাসমূহ: {', '.join(top_p['amenities'])}\n\n"
                    "বিস্তারিত ফ্লোর প্ল্যান ও সাইট পরিদর্শনের জন্য আমাদের সেলস টিমের সাথে যোগাযোগ করার অনুরোধ করছি।"
                )

        # 6. Pre-Send Grounding Validation
        validation = grounding_validator.validate(
            reply_text=raw_reply,
            is_english=is_english,
        )

        final_reply = raw_reply
        if not validation.is_grounded:
            logger.warning(f"PropertyAgent grounding violation detected: {validation.violations}")
            if validation.sanitized_reply:
                final_reply = validation.sanitized_reply

        # 7. Telemetry Logging
        log_prompt_telemetry(
            agent_name="property_agent",
            model_name="gemini-flash",
            temperature=0.2,
            language=lang_info["language"],
            grounding_status=validation.is_grounded,
        )

        return final_reply

    async def get_projects(self) -> list[dict]:
        """Return all available canonical projects."""
        return property_repository.to_legacy_dict_format()


property_agent = PropertyAgent()
