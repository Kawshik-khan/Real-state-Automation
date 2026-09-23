"""Tests for Template 1 Mobile Micro-Card Formatting and Interactive CTA Hook.

Verifies:
1. Markdown tables (|---|) are prohibited and converted to emoji micro-cards.
2. Meta-tags like '(Banglish)' or '[Banglish]' are completely eliminated.
3. Placeholder phone numbers (+880 2 xxxx-xxxx) are replaced with verified corporate contacts.
4. Interactive 2-step qualification hook is always appended to project overviews.
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


def test_meta_tag_and_placeholder_sanitization():
    raw_response = (
        "GLG Assets er running project gulo holo (Banglish):\n\n"
        "🏢 1. GLG Gulshan Heights\n"
        "📍 Location: Gulshan 2\n"
        "💰 Price: ৳৯৫ লক্ষ\n\n"
        "Hotline: +880 2 xxxx-xxxx ba WhatsApp: 017xxxxxxxx"
    )
    cleaned = _sanitize_and_format_reply(
        text=raw_response,
        is_english=False,
        is_banglish=True,
        has_multi=True,
    )
    assert "(Banglish)" not in cleaned
    assert "xxxx-xxxx" not in cleaned
    assert "017xxxxxxxx" not in cleaned
    assert "+880-9612-888-999" in cleaned
    assert "+880-1700-777-666" in cleaned
    # Ensure 2-step CTA hook appended
    assert "1️⃣" in cleaned
    assert "2️⃣" in cleaned
    assert "Gulshan, Banani, naki Baridhara" in cleaned


def test_interactive_cta_hook_languages():
    # Banglish hook
    banglish_cta = _ensure_interactive_cta("Short text", is_english=False, is_banglish=True)
    assert "1️⃣ Apnar pochonder location konti?" in banglish_cta
    assert "2️⃣ Apnar koto bedroom er flat proyojon?" in banglish_cta

    # Bengali script hook
    bn_cta = _ensure_interactive_cta("Short text", is_english=False, is_banglish=False)
    assert "১️⃣ আপনার পছন্দের লোকেশন কোনটি?" in bn_cta
    assert "২️⃣ আপনার কত বেডরুমের ফ্ল্যাট প্রয়োজন?" in bn_cta

    # English hook
    en_cta = _ensure_interactive_cta("Short text", is_english=True, is_banglish=False)
    assert "1️⃣ Which location do you prefer?" in en_cta
    assert "2️⃣ What bedroom configuration do you need?" in en_cta


@pytest.mark.asyncio
async def test_property_agent_banglish_running_projects():
    """Verify that asking for running projects in Banglish formats Template 1 without tables."""
    reply = await property_agent.handle("Kon project gula running ace")
    assert "|---|" not in reply
    assert "(Banglish)" not in reply
    assert "xxxx-xxxx" not in reply
    assert "🏢" in reply
    assert "+880" in reply
    assert ("1️⃣" in reply or "১️⃣" in reply)
