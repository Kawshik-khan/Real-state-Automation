"""Social Bridge Agent — Coordinated Public Comment Reply + Private DM Lead Hook.

Specialized agent for Facebook Page posts and Instagram Business media.
Generates:
1. Public Comment Reply: Social-proof booster acknowledging the comment.
2. Private DM Payload: Rich conversational lead capture hook with property details & action buttons.
"""

from typing import Optional, Any
from app.utils.language import is_english_query
from app.tools.property_tool import property_search_tool, PROJECTS_DATABASE
from app.services.llm import llm_service


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
        is_en = is_english_query(comment_text)
        text_lower = comment_text.lower()

        # 1. Entity & Location Extraction
        location = ""
        for known_loc in ["banani", "gulshan", "uttara", "dhanmondi", "mumbai", "bandra"]:
            if known_loc in text_lower:
                location = known_loc.capitalize()
                break

        # 2. Query Property Database
        search_res = await property_search_tool.search(query=comment_text, location=location)
        projects = search_res.get("projects", [])
        top_project = projects[0] if projects else PROJECTS_DATABASE[0]

        # 3. Intent & Aspect Detection
        wants_price = any(kw in text_lower for kw in ["price", "dam", "cost", "taka", "koto", "budget"])
        wants_location = any(kw in text_lower for kw in ["location", "address", "kothay", "where"])
        has_phone = any(char.isdigit() for char in comment_text) and len([c for c in comment_text if c.isdigit()]) >= 8

        # 4. Generate Public Comment Reply
        clean_author = author_name.strip() or ("Buyer" if is_en else "সম্মানিত গ্রাহক")
        if is_en:
            if wants_price:
                public_reply = f"Thank you @{clean_author}! We've sent the complete pricing details and floor plans directly to your inbox. Please check your messages! 📩✨"
            else:
                public_reply = f"Thank you for your interest, @{clean_author}! We've sent the project overview and brochure directly to your inbox. Please check your messages! 😊"
        else:
            if wants_price:
                public_reply = f"ধন্যবাদ @{clean_author}! প্রজেক্টের বিস্তারিত প্রাইজ ও কিস্তি সুবিধা আপনার ইনবক্সে পাঠানো হয়েছে। অনুগ্রহ করে মেসেজ চেক করুন! 📩✨"
            else:
                public_reply = f"ধন্যবাদ @{clean_author}! আমাদের প্রজেক্টের বিস্তারিত তথ্য ও ব্রোশিউর আপনার ইনবক্সে পাঠিয়ে দিয়েছি। অনুগ্রহ করে ইনবক্স চেক করুন! 😊"

        # 5. Generate Private DM Message
        if is_en:
            dm_text = (
                f"👋 Hello {clean_author}! Thank you for reaching out on our {platform.capitalize()} post.\n\n"
                f"🏢 *{top_project['name']}*\n"
                f"📍 *Location*: {top_project['location']}\n"
                f"💰 *Price*: {top_project['price']} ({top_project.get('bedrooms', 3)} BHK Luxury Suite)\n"
                f"📝 *Overview*: {top_project.get('description', 'Prime residential development')}\n"
                f"✨ *Key Amenities*: {', '.join(top_project.get('amenities', []))}\n\n"
                f"💳 *Flexible Payment*: 10% Booking, 30% Construction Milestones, 60% upon Handover. Home loan assistance available.\n\n"
                f"Would you like to schedule a private site visit this week or receive the detailed PDF brochure?"
            )
        else:
            dm_text = (
                f"👋 আসসালামু আলাইকুম {clean_author}! আমাদের {platform.capitalize()} পোস্টে আগ্রহ প্রকাশের জন্য ধন্যবাদ।\n\n"
                f"🏢 *{top_project['name']}*\n"
                f"📍 *লোকেশন*: {top_project['location']}\n"
                f"💰 *দাম*: {top_project['price']} ({top_project.get('bedrooms', 3)} BHK লক্সারি অ্যাপার্টমেন্ট)\n"
                f"📝 *বিস্তারিত*: {top_project.get('description', 'অভিজাত এলাকায় প্রিমিয়াম রেসিডেন্সিয়াল প্রজেক্ট')}\n"
                f"✨ *সুবিধাসমূহ*: {', '.join(top_project.get('amenities', []))}\n\n"
                f"💳 *পেমেন্ট সুবিধা*: ১০% বুকিং মানি, ৩০% সহজ কিস্তি (৩৬ মাস মেয়াদী), ৬০% হ্যান্ডওভারের সময়।\n\n"
                f"আপনি কি এই সপ্তাহে প্রজেক্টটি সরাসরি ভিজিট করতে চান অথবা বিস্তারিত পিডিএফ ব্রোশিউর দেখতে চান?"
            )

        # 6. Calculate Lead Intent Score (0-100)
        score = 65  # Base score for commenting on an ad/post
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
