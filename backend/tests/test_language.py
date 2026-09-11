"""Language detection and localized response tests for GLG Assets."""

import asyncio
import pytest
from app.utils.language import is_english_query, detect_language
from app.agents.graph import greeting_handler_node, booking_handler_node, AIState


def test_is_english_query_detection():
    # Bangla script
    assert is_english_query("আপনার প্রজেক্টগুলোর দাম কত?") is False
    assert is_english_query("হ্যালো, কেমন আছেন?") is False

    # Banglish
    assert is_english_query("apnader project kothay?") is False
    assert is_english_query("flat er dam koto?") is False
    assert is_english_query("bhai kemon achen?") is False
    assert is_english_query("Gulshan 2 e luxury flat dekhbo") is False
    assert is_english_query("ami ekta 3BHK flat nite chai") is False

    # Default short greetings
    assert is_english_query("hi") is False
    assert is_english_query("hello") is False

    # English queries (strictly Dhaka/Bangladesh context, no foreign locations)
    assert is_english_query("What luxury residential properties do you have in Gulshan?") is True
    assert is_english_query("Can I schedule a site visit for tomorrow at Banani Crest?") is True
    assert is_english_query("Tell me about the payment terms and documentation required.") is True


def test_detect_language_multi_signal():
    # Bengali script
    res_bn = detect_language("গুলশান ২ এ ফ্ল্যাটের দাম কত?")
    assert res_bn["language"] == "bn"
    assert res_bn["confidence"] >= 0.70

    # Complex Banglish without single-word collision
    res_banglish = detect_language("Gulshan 2 e luxury flat dekhbo")
    assert res_banglish["language"] == "banglish"
    assert res_banglish["confidence"] >= 0.60

    # Mixed Banglish with English loan words
    res_mixed = detect_language("3BHK luxury apartment er brochure pabo?")
    assert res_mixed["language"] == "banglish"

    # English
    res_en = detect_language("Could you provide the official price for GLG Gulshan Heights?")
    assert res_en["language"] == "en"
    assert res_en["confidence"] >= 0.70


def test_greeting_handler_language_response():
    state_bangla = AIState(conversation_id="test-1", message="apnader project gulo dekhaw", channel="website")
    res_bangla = asyncio.run(greeting_handler_node(state_bangla))
    assert "স্বাগতম" in res_bangla["agent_reply"]

    state_english = AIState(conversation_id="test-2", message="Can you list your properties in Gulshan and Banani?", channel="website")
    res_english = asyncio.run(greeting_handler_node(state_english))
    assert "Welcome to *GLG Assets*" in res_english["agent_reply"]


def test_booking_handler_language_response():
    state_bangla = AIState(conversation_id="test-3", message="ami ekta flat book korte chai", channel="website")
    res_bangla = asyncio.run(booking_handler_node(state_bangla))
    assert "ধন্যবাদ" in res_bangla["agent_reply"]
    assert "+91" not in res_bangla["agent_reply"]
    assert "+880" in res_bangla["agent_reply"]

    state_english = AIState(conversation_id="test-4", message="I would like to book a site visit next Monday", channel="website")
    res_english = asyncio.run(booking_handler_node(state_english))
    assert "Thank you for your interest!" in res_english["agent_reply"]
    assert "+91" not in res_english["agent_reply"]
    assert "+880" in res_english["agent_reply"]
