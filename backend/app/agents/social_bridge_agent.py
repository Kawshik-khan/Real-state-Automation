"""Social Bridge Agent — Coordinated Public Comment Reply + Private DM Lead Hook.

Audit Reference: prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md
Purges Indian locations, grounds private DM payload in canonical PropertyRepository,
and applies multi-signal language detection.
"""

from typing import Any

from app.repositories.property_repository import property_repository
from app.services.grounding_validator import grounding_validator
from app.tools.property_tool import property_search_tool
from app.utils.language import detect_language


class SocialBridgeAgent:
    """Orchestrates public comment replies and private DM bridge generation."""

    async def process_comment(
        self,
        comment_text: str,
        author_name: str = "Friend",
        platform: str = "facebook",
        post_context: str = ""
    ) -> dict[str, Any]:
        """Processes a comment and returns public reply, private DM, lead score, and detected entities."""
        lang_info = detect_language(comment_text)
        is_en = lang_info["language"] == "en"
        text_lower = comment_text.lower()

        # 1. Entity & Location Extraction (Dynamic query from ProjectRecord with fallback)
        from app.services.location_service import location_service
        location = await location_service.resolve_location_from_text(comment_text)

        # 2. Query Property Database
        search_res = await property_search_tool.search(query=comment_text, location=location)
        projects = search_res.get("projects", [])
        all_canonical = property_repository.to_legacy_dict_format()
        top_project = projects[0] if projects else all_canonical[0]

        # 3. Intent & Aspect Detection
        wants_price = any(kw in text_lower for kw in ["price", "dam", "cost", "taka", "koto", "budget"])
        has_phone = any(char.isdigit() for char in comment_text) and len([c for c in comment_text if c.isdigit()]) >= 8

        # 4. Generate Public Comment Reply
        clean_author = author_name.strip() or ("Buyer" if is_en else "সম্মানিত গ্রাহক")
        if is_en:
            if wants_price:
                public_reply = f"Thank you @{clean_author}! We've sent the verified pricing details and floor plans directly to your inbox. Please check your messages! 📩✨"
            else:
                public_reply = f"Thank you for your interest, @{clean_author}! We've sent the project overview and brochure directly to your inbox. Please check your messages! 😊"
        else:
            if wants_price:
                public_reply = f"ধন্যবাদ @{clean_author}! প্রজেক্টের ভেরিফায়েড প্রাইজ ও কিস্তি সুবিধা আপনার ইনবক্সে পাঠানো হয়েছে। অনুগ্রহ করে মেসেজ চেক করুন! 📩✨"
            else:
                public_reply = f"ধন্যবাদ @{clean_author}! আমাদের প্রজেক্টের বিস্তারিত তথ্য ও ব্রোশিউর আপনার ইনবক্সে পাঠিয়ে দিয়েছি। অনুগ্রহ করে ইনবক্স চেক করুন! 😊"

        # 5. Generate Private DM Message
        price_display = top_project["price"] if is_en else top_project.get("price_bn", top_project["price"])
        if is_en:
            dm_text = (
                f"👋 Hello {clean_author}! Thank you for reaching out on our {platform.capitalize()} post.\n\n"
                f"🏢 *{top_project['name']}*\n"
                f"📍 *Location*: {top_project['location']}\n"
                f"💰 *Price*: {price_display} ({top_project.get('bedrooms', 3)} BHK Luxury Suite)\n"
                f"📝 *Overview*: {top_project.get('description', 'Prime residential development in Dhaka')}\n"
                f"✨ *Verified Amenities*: {', '.join(top_project.get('amenities', []))}\n\n"
                f"💳 *Flexible Payment*: 10% Booking, 30% Construction Milestones, 60% upon Handover. Home loan assistance available.\n\n"
                f"Would you like to schedule a private site visit this week or receive the detailed PDF brochure?"
            )
        else:
            dm_text = (
                f"👋 আসসালামু আলাইকুম {clean_author}! আমাদের {platform.capitalize()} পোস্টে আগ্রহ প্রকাশের জন্য ধন্যবাদ।\n\n"
                f"🏢 *{top_project['name']}*\n"
                f"📍 *লোকেশন*: {top_project['location']}\n"
                f"💰 *দাম*: {price_display} ({top_project.get('bedrooms', 3)} BHK লক্সারি অ্যাপার্টমেন্ট)\n"
                f"📝 *বিস্তারিত*: {top_project.get('description', 'অভিজাত ঢাকায় প্রিমিয়াম রেসিডেন্সিয়াল প্রজেক্ট')}\n"
                f"✨ *ভেরিফায়েড সুবিধাসমূহ*: {', '.join(top_project.get('amenities', []))}\n\n"
                f"💳 *পেমেন্ট সুবিধা*: ১০% বুকিং মানি, ৩০% সহজ মাইলস্টোন কিস্তি, ৬০% হ্যান্ডওভারের সময়।\n\n"
                f"আপনি কি এই সপ্তাহে প্রজেক্টটি সরাসরি ভিজিট করতে চান অথবা বিস্তারিত ব্রোশিউর দেখতে চান?"
            )

        # 6. Pre-send Grounding Validation
        validation = grounding_validator.validate(reply_text=dm_text, is_english=is_en)
        if not validation.is_grounded and validation.sanitized_reply:
            dm_text = validation.sanitized_reply

        # 7. Calculate Lead Intent Score (0-100)
        score = 65
        if wants_price:
            score += 15
        if location:
            score += 10
        if has_phone:
            score += 15
        lead_score = min(100, score)

        return {
            "public_reply": public_reply,
            "private_dm": dm_text,
            "project": top_project,
            "lead_score": lead_score,
            "is_hot_lead": lead_score >= 80,
            "language": "en" if is_en else "bn",
            "entities": {
                "location": location or top_project.get("location", ""),
                "project_name": top_project["name"],
                "has_phone": has_phone
            },
            "quick_replies": [
                {"title": "📅 Book Site Tour" if is_en else "📅 সাইট ভিজিট বুকিং", "payload": "BOOK_VISIT"},
                {"title": "📥 Download Brochure" if is_en else "📥 ব্রোশিউর ডাউনলোড", "payload": "BROCHURE"},
                {"title": "💬 Talk to Consultant" if is_en else "💬 প্রতিনিধির সাথে কথা বলুন", "payload": "TALK_SALES"}
            ]
        }


social_bridge_agent = SocialBridgeAgent()
