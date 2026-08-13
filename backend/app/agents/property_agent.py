"""Property Agent — handles property search and inquiries using PropertySearchTool."""

from app.services.llm import llm_service
from app.prompts.base import PROPERTY_AGENT_PROMPT
from app.tools.property_tool import property_search_tool, PROJECTS_DATABASE


class PropertyAgent:
    """Handles property search and inquiry conversations."""

    async def handle(self, message: str, entities: dict | None = None, extra_context: str = "") -> str:
        """Process a property query using SQL property search + RAG context."""
        entities = entities or {}
        location = entities.get("location")
        budget = entities.get("budget")

        # Run SQL Property Search Tool
        search_res = await property_search_tool.search(
            query=message,
            location=location,
        )

        projects = search_res.get("projects", [])
        if projects:
            from app.utils.language import is_english_query
            is_english = is_english_query(message)
            msg_lower = message.lower()

            # Aspect detection
            wants_payment = any(kw in msg_lower for kw in ["payment", "installment", "kisti", "down payment", "pament", "taka koto", "booking amount"])
            wants_price = any(kw in msg_lower for kw in ["price", "dam koto", "cost", "rate", "taka"]) and not wants_payment
            wants_location = any(kw in msg_lower for kw in ["location", "address", "kothay", "where"])
            wants_amenities = any(kw in msg_lower for kw in ["amenities", "facility", "facilities", "features", "ki ki ache"])

            formatted = []
            for p in projects:
                # 1. Targeted Payment Response
                if wants_payment:
                    if is_english:
                        formatted.append(
                            f"💳 *{p['name']} — Payment Terms & Plan*:\n"
                            f"• 10% Booking Amount upon reservation\n"
                            f"• 30% Milestone Construction Payments (spread over 36 months)\n"
                            f"• 60% Final Payment upon handover/possession\n"
                            f"• Pre-approved home loan financing available through partner banks."
                        )
                    else:
                        formatted.append(
                            f"💳 *{p['name']} — পেমেন্ট টার্মস ও কিস্তি সুবিধা*:\n"
                            f"• ১০% বুকিং মানি রেজারভেশনের সময়\n"
                            f"• ৩০% কনস্ট্রাকশন ভিত্তিক কিস্তি (৩৬ মাস মেয়াদী)\n"
                            f"• ৬০% হ্যান্ডওভার / পজেশনের সময়\n"
                            f"• পার্টনার ব্যাংকসমূহের মাধ্যমে সহজ হোম লোন সুবিধা রয়েছে।"
                        )
                # 2. Targeted Price Response
                elif wants_price:
                    if is_english:
                        formatted.append(f"💰 *{p['name']} — Pricing*: {p['price']} ({p['bedrooms']} BHK Luxury Suite).")
                    else:
                        formatted.append(f"💰 *{p['name']} — প্রাইজ লিস্ট*: {p['price']} ({p['bedrooms']} BHK লক্সারি অ্যাপার্টমেন্ট)।")
                # 3. Targeted Location Response
                elif wants_location:
                    if is_english:
                        formatted.append(f"📍 *{p['name']} — Location*: {p['location']}.")
                    else:
                        formatted.append(f"📍 *{p['name']} — লোকেশন*: {p['location']}।")
                # 4. Targeted Amenities Response
                elif wants_amenities:
                    if is_english:
                        formatted.append(f"✨ *{p['name']} — Key Amenities*: {', '.join(p['amenities'])}.")
                    else:
                        formatted.append(f"✨ *{p['name']} — সুবিধাসমূহ*: {', '.join(p['amenities'])}।")
                # 5. Full Overview Response (default)
                else:
                    if is_english:
                        formatted.append(
                            f"🏢 *{p['name']}*\n"
                            f"📍 Location: {p['location']}\n"
                            f"💰 Price: {p['price']} ({p['bedrooms']} BHK)\n"
                            f"📝 Overview: {p['description']}\n"
                            f"✨ Amenities: {', '.join(p['amenities'])}"
                        )
                    else:
                        formatted.append(
                            f"🏢 *{p['name']}*\n"
                            f"📍 লোকেশন: {p['location']}\n"
                            f"💰 দাম: {p['price']} ({p['bedrooms']} BHK)\n"
                            f"📝 বিস্তারিত: {p['description']}\n"
                            f"✨ সুবিধাসমূহ: {', '.join(p['amenities'])}"
                        )

            return "\n\n---\n\n".join(formatted)

        # Fallback to LLM with full context
        system_content = PROPERTY_AGENT_PROMPT + f"\n\nAvailable projects catalog: {PROJECTS_DATABASE}"
        if extra_context:
            system_content += f"\n\nAdditional RAG context:\n{extra_context}"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message}
        ]
        return await llm_service.chat(messages, temperature=0.3)

    async def get_projects(self) -> list[dict]:
        """Return all available projects."""
        return PROJECTS_DATABASE


property_agent = PropertyAgent()
