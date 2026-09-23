"""Tests for Template 1 Mobile Micro-Card Formatting and Intent-Driven Contact Sharing.

Verifies:
1. Markdown tables (|---|) are prohibited and converted to emoji micro-cards.
2. Meta-tags like '(Banglish)' or '[Banglish]' are completely eliminated.
3. Placeholder phone numbers (+880 2 xxxx-xxxx) are replaced with verified corporate contacts.
4. Interactive 2-step qualification hook is appended to project overviews WITHOUT premature hotlines.
5. Hotlines are only provided when:
   (a) Customer explicitly requests contact / sales info.
   (b) AI cannot solve the query (unsolvable / missing info / out-of-catalog escalation).
"""

import pytest

from app.agents.property_agent import (
    _convert_markdown_table_to_cards,
    _ensure_interactive_cta,
    _sanitize_and_format_reply,
    property_agent,
)


def test_markdown_table_conversion():
    table_text = (
        "Here are our active projects:\n\n"
        "| Project Name | Location | Price | Bedrooms | Handover | Amenities |\n"
        "|---|---|---|---|---|---|\n"
        "| GLG Gulshan Heights | Gulshan 2 | ৳৯৫ লক্ষ | 3 BHK | Dec 2026 | Pool, Gym |\n"
        "| GLG Banani Crest | Banani | ৳১.২ কোটি | 3 BHK | Dec 2026 | Pool, Concierge |\n\n"
        "Contact sales for more details."
    )
    converted = _convert_markdown_table_to_cards(table_text, is_english=False, is_banglish=True)
    assert "|---|" not in converted
    assert "🏢 *1. GLG Gulshan Heights*" in converted
    assert "📍 Location: Gulshan 2" in converted
    assert "💰 Price: ৳৯৫ লক্ষ" in converted
    assert "🛏️ Size: 3 BHK" in converted
    assert "🏢 *2. GLG Banani Crest*" in converted
    assert "📍 Location: Banani" in converted


def test_meta_tag_and_routine_hotline_filtering():
    raw_response = (
        "GLG Assets er running project gulo holo (Banglish):\n\n"
        "🏢 1. GLG Gulshan Heights\n"
        "📍 Location: Gulshan 2\n"
        "💰 Price: ৳৯৫ লক্ষ\n\n"
        "📞 Hotline: +880 2 xxxx-xxxx ba WhatsApp: 017xxxxxxxx"
    )
    # Routine discovery: customer did NOT ask for contact info -> hotline stripped from routine reply
    cleaned = _sanitize_and_format_reply(
        text=raw_response,
        is_english=False,
        is_banglish=True,
        has_multi=True,
        wants_contact=False,
        is_unsolvable=False,
    )
    assert "(Banglish)" not in cleaned
    assert "xxxx-xxxx" not in cleaned
    assert "017xxxxxxxx" not in cleaned
    assert "Hotline" not in cleaned
    # Ensure 2-step CTA hook appended without hotline
    assert "1️⃣" in cleaned
    assert "2️⃣" in cleaned
    assert "Gulshan, Banani, naki Baridhara" in cleaned


def test_intent_driven_and_unsolvable_contact_preservation():
    raw_response = (
        "GLG Assets contact info:\n\n"
        "📞 Hotline: +880 2 xxxx-xxxx ba WhatsApp: 017xxxxxxxx"
    )
    # 1. When customer explicitly asked for contact details
    cleaned_intent = _sanitize_and_format_reply(
        text=raw_response,
        is_english=False,
        is_banglish=True,
        has_multi=False,
        wants_contact=True,
        is_unsolvable=False,
    )
    assert "+880-13178610" in cleaned_intent
    assert "013178610" in cleaned_intent

    # 2. When query cannot be solved by AI (escalation)
    cleaned_unsolvable = _sanitize_and_format_reply(
        text=raw_response,
        is_english=False,
        is_banglish=True,
        has_multi=False,
        wants_contact=False,
        is_unsolvable=True,
    )
    assert "+880-13178610" in cleaned_unsolvable


def test_interactive_cta_hook_languages_clean():
    # Banglish hook has NO premature hotline
    banglish_cta = _ensure_interactive_cta("Short text", is_english=False, is_banglish=True)
    assert "1️⃣ Apnar pochonder location konti?" in banglish_cta
    assert "2️⃣ Apnar koto bedroom er flat proyojon?" in banglish_cta
    assert "+880" not in banglish_cta

    # Bengali script hook has NO premature hotline
    bn_cta = _ensure_interactive_cta("Short text", is_english=False, is_banglish=False)
    assert "১️⃣ আপনার পছন্দের লোকেশন কোনটি?" in bn_cta
    assert "২️⃣ আপনার কত বেডরুমের ফ্ল্যাট প্রয়োজন?" in bn_cta
    assert "+880" not in bn_cta

    # English hook has NO premature hotline
    en_cta = _ensure_interactive_cta("Short text", is_english=True, is_banglish=False)
    assert "1️⃣ Which location do you prefer?" in en_cta
    assert "2️⃣ What bedroom configuration do you need?" in en_cta
    assert "+880" not in en_cta


@pytest.mark.asyncio
async def test_property_agent_banglish_running_projects_routine():
    """Verify routine running projects query: micro-cards + 2-step hook, NO premature hotline."""
    reply = await property_agent.handle("Kon project gula running ace")
    assert "|---|" not in reply
    assert "(Banglish)" not in reply
    assert "xxxx-xxxx" not in reply
    assert "🏢" in reply
    assert ("1️⃣" in reply or "১️⃣" in reply)
    # The AI solved the query, so routine hotline should not be forced on the user
    assert "Sorasori kotha bolte hotline" not in reply


@pytest.mark.asyncio
async def test_property_agent_unsupported_location_gives_hotline():
    """Verify that when AI cannot solve (unsupported location Mirpur), it provides the hotline."""
    reply = await property_agent.handle("Mirpur e kono 3BHK flat ache?")
    assert "Mirpur" in reply or "মিরপুর" in reply
    # Because Mirpur is not in catalog (AI cannot solve/provide unit), it escalates with the hotline
    assert "+880" in reply
