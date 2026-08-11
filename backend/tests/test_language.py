import asyncio
import pytest
from app.utils.language import is_english_query
from app.agents.graph import greeting_handler_node, booking_handler_node, AIState


def test_is_english_query_detection():
    # Bangla script
    assert is_english_query("আপনার প্রজেক্টগুলোর দাম কত?") is False
    assert is_english_query("হ্যালো, কেমন আছেন?") is False

    # Banglish
    assert is_english_query("apnader project kothay?") is False
    assert is_english_query("flat er dam koto?") is False
    assert is_english_query("bhai kemon achen?") is False

    # Default short greetings
    assert is_english_query("hi") is False
    assert is_english_query("hello") is False

    # English queries
    assert is_english_query("What properties do you have in Mumbai?") is True
    assert is_english_query("Can I schedule a site visit for tomorrow?") is True
    assert is_english_query("Tell me about the payment terms and documentation required.") is True


def test_greeting_handler_language_response():
    state_bangla = AIState(conversation_id="test-1", message="apnader project gulo dekhaw", channel="website")
    res_bangla = asyncio.run(greeting_handler_node(state_bangla))
    assert "স্বাগতম" in res_bangla["agent_reply"]

    state_english = AIState(conversation_id="test-2", message="Can you list your properties in Mumbai?", channel="website")
    res_english = asyncio.run(greeting_handler_node(state_english))
    assert "Welcome to *GLG Assets*" in res_english["agent_reply"]


def test_booking_handler_language_response():
    state_bangla = AIState(conversation_id="test-3", message="ami ekta flat book korte chai", channel="website")
    res_bangla = asyncio.run(booking_handler_node(state_bangla))
    assert "ধন্যবাদ" in res_bangla["agent_reply"]

    state_english = AIState(conversation_id="test-4", message="I would like to book a site visit next Monday", channel="website")
    res_english = asyncio.run(booking_handler_node(state_english))
    assert "Thank you for your interest!" in res_english["agent_reply"]


