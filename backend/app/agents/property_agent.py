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

        # Check for out-of-catalog location inquiry (e.g. Mirpur, Chittagong, Sylhet)
        searched_loc = location or search_res.get("filters", {}).get("location") or ""
        is_unsupported_location = bool(
            searched_loc and not projects and not property_repository.is_supported_location(searched_loc)
        )

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

        context_prefix = ""
        if is_unsupported_location:
            context_prefix = (
                f"--- NOTICE: CUSTOMER INQUIRY LOCATION OUT OF PORTFOLIO ---\n"
                f"The customer is inquiring about: '{searched_loc}'.\n"
                f"GLG Assets Limited DOES NOT currently have any ongoing or completed projects in '{searched_loc}'.\n"
                f"You MUST explicitly and politely inform the customer that GLG Assets has no ongoing projects in {searched_loc}.\n"
                f"You may mention our active luxury portfolio in Gulshan, Banani, Baridhara, and Uttara if helpful.\n"
                f"NEVER claim or imply that any project listed below is located in {searched_loc}.\n\n"
            )

        context_builder = (
            context_prefix
            + "--- VERIFIED CANONICAL PROPERTY RECORDS (AUTHORITATIVE) ---\n"
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
            if is_unsupported_location:
                if is_english:
                    raw_reply = (
                        f"Thank you for contacting GLG Assets. Currently, we do not have any ongoing projects in {searched_loc.title()}. "
                        f"Our primary luxury developments are located in Gulshan, Banani, Baridhara, and Uttara. "
                        f"Please contact our sales advisory desk if you would like details on our available developments."
                    )
                else:
                    raw_reply = (
                        f"GLG Assets-এ যোগাযোগ করার জন্য ধন্যবাদ। বর্তমানে {searched_loc}-এ আমাদের কোনো চলমান প্রকল্প নেই। "
                        f"আমাদের সক্রিয় প্রিমিয়াম প্রকল্পগুলো মূলত গুলশান, বনানী, বারিধারা ও উত্তরায় অবস্থিত। "
                        f"আমাদের বিদ্যমান প্রজেক্টসমূহ সম্পর্কে জানতে আমাদের সেলস টিমের সাথে যোগাযোগ করার অনুরোধ করছি।"
                    )
            elif any(retail_kw in message.lower() for retail_kw in ["jacket", "shirt", "pant", "chocolate", "kitkat", "candy", "phone", "food", "shoe"]):
                if is_english:
                    raw_reply = (
                        "Thank you for contacting GLG Assets Limited. We are a luxury real-estate developer in Bangladesh. "
                        "We do not sell retail consumer goods. If you are interested in luxury apartments or commercial spaces in Dhaka, we will gladly assist you."
                    )
                else:
                    raw_reply = (
                        "GLG Assets Limited-এ যোগাযোগ করার জন্য ধন্যবাদ। আমরা একটি লাক্সারি রিয়েল-এস্টেট ডেভেলপার প্রতিষ্ঠান। "
                        "আমরা শুধুমাত্র ফ্ল্যাট, অ্যাপার্টমেন্ট ও আবাসন প্রকল্প সম্পর্কিত সেবা দিয়ে থাকি। "
                        "আবাসন সম্পর্কিত যেকোনো তথ্যের জন্য আমাদের জানাতে পারেন।"
                    )
            elif projects and search_res.get("projects"):
                top_p = projects[0]
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
            else:
                if is_english:
                    raw_reply = (
                        "We apologize, but we are currently experiencing a brief delay retrieving property specifications. "
                        "Please connect directly with our sales advisory team for immediate assistance."
                    )
                else:
                    raw_reply = (
                        "আমি আন্তরিকভাবে দুঃখিত, এই মুহূর্তে প্রপার্টি সংক্রান্ত তথ্য পেতে সাময়িক বিলম্ব হচ্ছে। "
                        "অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন অথবা সরাসরি আমাদের সেলস টিমের সাথে যোগাযোগ করুন।"
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
