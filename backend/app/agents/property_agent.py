"""Property Agent — Handles property inquiries using canonical PropertyRepository + RAG context.

Audit Reference: prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md
Removes static template bypass, synthesizes SQL + RAG data, enforces PROPERTY_AGENT_PROMPT,
and validates response with GroundingValidator.
"""

import json
import logging
import re

from app.prompts.property import PROPERTY_AGENT_PROMPT
from app.prompts.registry import log_prompt_telemetry
from app.repositories.contact_repository import contact_repository
from app.repositories.policy_repository import policy_repository
from app.repositories.property_repository import property_repository
from app.services.grounding_validator import grounding_validator
from app.services.llm import llm_service
from app.tools.property_tool import property_search_tool
from app.utils.language import detect_language

logger = logging.getLogger(__name__)


def _convert_markdown_table_to_cards(text: str, is_english: bool = False, is_banglish: bool = False) -> str:
    """Parses raw markdown table syntax (|---|) and converts into clean mobile micro-cards."""
    lines = text.split("\n")
    table_lines = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(table_lines) < 3:
        return text

    # Extract headers
    header_raw = [c.strip() for c in table_lines[0].split("|")[1:-1]]
    header_lower = [h.lower() for h in header_raw]

    # Find data rows
    data_rows = []
    for row_line in table_lines[1:]:
        if re.search(r"^\|(\s*:?-+:?\s*\|)+$", row_line):
            continue
        cols = [c.strip() for c in row_line.split("|")[1:-1]]
        if any(cols):
            data_rows.append(cols)

    if not data_rows:
        return text

    cards = []
    for idx, row in enumerate(data_rows, 1):
        row_dict = {}
        for h, val in zip(header_lower, row):
            row_dict[h] = val

        name = ""
        location = ""
        price = ""
        size = ""
        handover = ""
        amenities = ""

        for k, v in row_dict.items():
            if any(term in k for term in ["project", "name", "building", "প্রজেক্ট", "নাম"]):
                name = v
            elif any(term in k for term in ["location", "area", "লোকেশন", "ঠিকানা"]):
                location = v
            elif any(term in k for term in ["price", "cost", "dam", "দাম", "মূল্য"]):
                price = v
            elif any(term in k for term in ["size", "bedroom", "bhk", "সাইজ", "বেডরুম"]):
                size = v
            elif any(term in k for term in ["handover", "date", "timeline", "হ্যান্ডওভার"]):
                handover = v
            elif any(term in k for term in ["amenit", "highlight", "feature", "সুবিধা"]):
                amenities = v

        if not name and row:
            name = row[0]

        card_lines = [f"🏢 *{idx}. {name}*"]
        if location:
            loc_label = "Location" if (is_english or is_banglish) else "লোকেশন"
            card_lines.append(f"📍 {loc_label}: {location}")
        if price:
            price_label = "Price" if (is_english or is_banglish) else "মূল্য"
            card_lines.append(f"💰 {price_label}: {price}")
        if size:
            size_label = "Size" if (is_english or is_banglish) else "সাইজ"
            card_lines.append(f"🛏️ {size_label}: {size}")
        if handover:
            handover_label = "Handover" if (is_english or is_banglish) else "হ্যান্ডওভার"
            card_lines.append(f"📅 {handover_label}: {handover}")
        if amenities:
            amenity_label = "Highlights" if (is_english or is_banglish) else "প্রধান সুবিধা"
            card_lines.append(f"✨ {amenity_label}: {amenities}")

        cards.append("\n".join(card_lines))

    # Locate table segment in original text
    first_tbl_idx = -1
    last_tbl_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and line.strip().endswith("|"):
            if first_tbl_idx == -1:
                first_tbl_idx = i
            last_tbl_idx = i

    before = "\n".join(lines[:first_tbl_idx]).strip()
    after = "\n".join(lines[last_tbl_idx + 1:]).strip()

    cards_text = "\n\n".join(cards)
    parts = [p for p in [before, cards_text, after] if p]
    return "\n\n".join(parts)


def _ensure_interactive_cta(text: str, is_english: bool, is_banglish: bool) -> str:
    """Appends Template 1 2-step interactive lead qualification CTA hook if absent."""
    has_hook = any(marker in text for marker in ["1️⃣", "১️⃣", "poroborti podokkhep", "পরবর্তী পদক্ষেপ", "Next Step", "Next step"])
    if has_hook:
        return text

    if is_english:
        hook = (
            "\n\n---\n"
            "📌 *Next Steps for You*:\n"
            "1️⃣ Which location do you prefer? (Gulshan, Banani, or Baridhara?)\n"
            "2️⃣ What bedroom configuration do you need? (2 Bed, 3 Bed, or 4 Bed?)\n\n"
            "👉 *Simply reply with your preferred area or bedroom count, and I will share the detailed brochure and floor plans!*\n"
            "📞 Direct Hotline: +880-9612-888-999 | WhatsApp: +880-1700-777-666"
        )
    elif is_banglish:
        hook = (
            "\n\n---\n"
            "📌 *Apnar subidharte poroborti podokkhep*:\n"
            "1️⃣ Apnar pochonder location konti? (Gulshan, Banani, naki Baridhara?)\n"
            "2️⃣ Apnar koto bedroom er flat proyojon? (2 Bed, 3 Bed, naki 4 Bed?)\n\n"
            "👉 *Shudhu elaka ba bedroom likhe reply din, ami apnake bistatito brochure o floor plan pathacchi!*\n"
            "📞 Sorasori kotha bolte hotline: +880-9612-888-999 | WhatsApp: +880-1700-777-666"
        )
    else:
        hook = (
            "\n\n---\n"
            "📌 *আপনার সুবিধার্থে পরবর্তী পদক্ষেপ*:\n"
            "১️⃣ আপনার পছন্দের লোকেশন কোনটি? (Gulshan, Banani, নাকি Baridhara?)\n"
            "২️⃣ আপনার কত বেডরুমের ফ্ল্যাট প্রয়োজন? (2 Bed, 3 Bed, নাকি 4 Bed?)\n\n"
            "👉 *শুধু এলাকা বা বেডরুম লিখে রিপ্লাই দিন, আমি আপনাকে বিস্তারিত ব্রোশার ও ফ্লোর প্ল্যান পাঠাচ্ছি!*\n"
            "📞 সরাসরি কথা বলতে হটলাইন: +880-9612-888-999 | WhatsApp: +880-1700-777-666"
        )
    return text.strip() + hook


def _sanitize_and_format_reply(text: str, is_english: bool, is_banglish: bool, has_multi: bool) -> str:
    """Cleans up raw LLM responses to conform strictly with Template 1 standards."""
    # 1. Strip meta tags like (Banglish), [Banglish], (Bangla), (English)
    cleaned = re.sub(r"\s*[\(\[]\s*Banglish\s*[\)\]]", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*[\(\[]\s*Bangla\s*[\)\]]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*[\(\[]\s*English\s*[\)\]]", "", cleaned, flags=re.IGNORECASE)

    # 2. Fix any placeholder telephone numbers
    cleaned = re.sub(r"\+880\s*2\s*x{3,}[-\s]*x{3,}", "+880-9612-888-999", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\+880\s*1\s*x{3,}[-\s]*x{3,}", "+880-1700-777-666", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"017xxxxxxxx", "+880-1700-777-666", cleaned, flags=re.IGNORECASE)

    # 3. Convert markdown tables to cards if any table slipped through
    if "|" in cleaned and "---" in cleaned:
        cleaned = _convert_markdown_table_to_cards(cleaned, is_english=is_english, is_banglish=is_banglish)

    # 4. Attach interactive CTA hook for multi-project/running project inquiries
    if has_multi:
        cleaned = _ensure_interactive_cta(cleaned, is_english=is_english, is_banglish=is_banglish)

    return cleaned


class PropertyAgent:
    """Handles property search and inquiry conversations with strict factual grounding."""

    async def handle(self, message: str, entities: dict | None = None, extra_context: str = "") -> str:
        """Process a property query by synthesizing canonical repository records with RAG context."""
        entities = entities or {}
        location = entities.get("location")

        # 1. Detect customer language
        lang_info = detect_language(message)
        lang = lang_info.get("language", "en")
        is_english = lang == "en"
        is_banglish = lang in ("banglish", "mixed")

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

        # Check if query requests multi-project list or overview
        is_multi_project_query = (
            not location
            or len(projects) > 1
            or any(kw in message.lower() for kw in [
                "running", "ongoing", "project gula", "project gulo", "ki ki project",
                "all project", "options", "available", "list", "প্রজেক্টগুলো", "চলমান"
            ])
        )

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
        contact_card = contact_repository.format_contact_card(is_english=is_english)

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
            + f"\n--- VERIFIED OFFICIAL CONTACT DETAILS ---\n{contact_card}\n"
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
            elif projects:
                # Format Template 1 Micro-Cards fallback
                cards = []
                for idx, p in enumerate(projects[:4], 1):
                    p_name = p.get("name", "GLG Project")
                    p_loc = p.get("location", "Dhaka")
                    p_price = p.get("price") if is_english else p.get("price_bn", p.get("price"))
                    p_beds = p.get("bedrooms", 3)
                    p_handover = p.get("handover_date", "December 2026")
                    p_amenities = ", ".join(p.get("amenities", [])[:3])
                    if is_english:
                        card = (
                            f"🏢 *{idx}. {p_name}*\n"
                            f"📍 Location: {p_loc}\n"
                            f"💰 Price: {p_price} ({p_beds} BHK)\n"
                            f"📅 Handover: {p_handover}\n"
                            f"✨ Highlights: {p_amenities}"
                        )
                    elif is_banglish:
                        card = (
                            f"🏢 *{idx}. {p_name}*\n"
                            f"📍 Location: {p_loc}\n"
                            f"💰 Price: {p_price} ({p_beds} BHK)\n"
                            f"📅 Handover: {p_handover}\n"
                            f"✨ Highlights: {p_amenities}"
                        )
                    else:
                        card = (
                            f"🏢 *{idx}. {p_name}*\n"
                            f"📍 লোকেশন: {p_loc}\n"
                            f"💰 মূল্য: {p_price} ({p_beds} BHK)\n"
                            f"📅 হ্যান্ডওভার: {p_handover}\n"
                            f"✨ প্রধান সুবিধা: {p_amenities}"
                        )
                    cards.append(card)

                if is_english:
                    intro = "Here are our premier active and upcoming luxury developments in Dhaka:\n\n"
                elif is_banglish:
                    intro = "GLG Assets er bortomane active ebong upcoming luxury project gulo holo:\n\n"
                else:
                    intro = "GLG Assets-এর বর্তমান চলমান ও আসন্ন লাক্সারি প্রজেক্টসমূহ:\n\n"

                raw_reply = intro + "\n\n".join(cards)
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

        # 6. Apply Template 1 Sanitization and Formatting (strips tables, tags, placeholder numbers)
        formatted_reply = _sanitize_and_format_reply(
            text=raw_reply,
            is_english=is_english,
            is_banglish=is_banglish,
            has_multi=is_multi_project_query,
        )

        # 7. Pre-Send Grounding Validation
        validation = grounding_validator.validate(
            reply_text=formatted_reply,
            is_english=is_english,
        )

        final_reply = formatted_reply
        if not validation.is_grounded:
            logger.warning(f"PropertyAgent grounding violation detected: {validation.violations}")
            if validation.sanitized_reply:
                final_reply = validation.sanitized_reply

        # 8. Telemetry Logging
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
