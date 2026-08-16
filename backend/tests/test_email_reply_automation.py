"""Test suite for Email Reply Automation pipeline."""

import asyncio
import pytest
from app.models.email import IncomingEmailPayload, EmailAttachment, DraftApprovalRequest
from app.services.email_service import email_service
from app.services.attachment_parser import attachment_parser
from app.agents.email_agent import email_agent
from app.api.v1.email.endpoints import incoming_email_webhook, list_threads, approve_draft, get_thread


@pytest.mark.anyio
async def test_email_attachment_parser():
    """Verify text extraction from plain text / PDF simulation."""
    text_content = attachment_parser.extract_text_from_attachment(
        filename="specs.txt",
        content_type="text/plain",
        file_bytes=b"Looking for 4 BHK with 2 car parking spaces in Gulshan.",
    )
    assert "4 BHK" in text_content


@pytest.mark.anyio
async def test_incoming_email_ingestion_and_ai_draft():
    """Verify incoming email webhook ingests payload and triggers EmailAgent."""
    payload = IncomingEmailPayload(
        message_id="test-msg-001",
        thread_id="test-thread-001",
        sender_email="test.client@example.com",
        sender_name="Test Client",
        subject="Pricing Inquiry for GLG Gulshan Heights",
        body_text="Hello, please provide the price list and payment terms for GLG Gulshan Heights.",
        attachments=[
            EmailAttachment(
                filename="requirements.txt",
                content_type="text/plain",
                extracted_text="Budget is up to $300k. Interested in high floor units."
            )
        ]
    )

    auth = {"tenant_id": "glg-assets"}
    res = await incoming_email_webhook(payload, auth=auth)

    assert res["success"] is True
    assert res["thread_id"] == "test-thread-001"
    assert "ai_draft" in res
    assert "Re: Pricing Inquiry" in res["ai_draft"]["subject"]


@pytest.mark.anyio
async def test_customer_reply_to_existing_thread():
    """Verify customer reply links to previous thread and maintains conversation context."""
    # First turn
    payload_turn1 = IncomingEmailPayload(
        message_id="turn1-msg",
        thread_id="thread-multi-turn",
        sender_email="multi.turn@example.com",
        sender_name="Multi Turn Client",
        subject="Inquiry about Banani Project",
        body_text="What units are available in Banani Crest?"
    )
    auth = {"tenant_id": "glg-assets"}
    await incoming_email_webhook(payload_turn1, auth=auth)

    # Customer Reply (Turn 2) with In-Reply-To header set
    payload_turn2 = IncomingEmailPayload(
        message_id="turn2-msg",
        in_reply_to="turn1-msg",
        sender_email="multi.turn@example.com",
        sender_name="Multi Turn Client",
        subject="Re: Inquiry about Banani Project",
        body_text="Thanks! Can I schedule a tour tomorrow at 4 PM?"
    )

    res2 = await incoming_email_webhook(payload_turn2, auth=auth)
    assert res2["success"] is True

    # Check thread details
    thread_resp = await get_thread(res2["thread_id"], auth=auth)
    thread_data = thread_resp["thread"]

    assert len(thread_data["messages"]) >= 2
    assert thread_data["lead_priority"].lower() == "high"  # Escalated priority on tour request


if __name__ == "__main__":
    asyncio.run(test_email_attachment_parser())
    asyncio.run(test_incoming_email_ingestion_and_ai_draft())
    asyncio.run(test_customer_reply_to_existing_thread())
    print("[SUCCESS] All Email Reply Automation unit tests passed cleanly!")
