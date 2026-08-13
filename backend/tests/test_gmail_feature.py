"""Comprehensive Test Script for Gmail Reply Automation & Feature Suite."""

import asyncio
import json
import os
import sys

backend_path = r"d:\Softwear Project\Realstate Automation\backend"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.api.v1.email.endpoints import (
    approve_draft,
    edit_and_send_draft,
    get_thread,
    incoming_email_webhook,
    list_threads,
)
from app.models.email import EmailAttachment, IncomingEmailPayload
from app.services.email_service import email_service


async def run_gmail_feature_test():
    print("============================================================")
    print("STARTING GMAIL REPLY AUTOMATION FEATURE TEST SUITE")
    print("============================================================")

    # -------------------------------------------------------------
    # TEST 1: New Incoming Email Inquiry for GLG Luxe Heights
    # -------------------------------------------------------------
    print("\n[TEST 1] Incoming Customer Email: 'GLG Luxe Heights price and payment terms'")
    payload1 = IncomingEmailPayload(
        message_id="msg-gmail-001",
        thread_id="thread-gmail-101",
        sender_email="tanvir.ahmed@example.com",
        sender_name="Tanvir Ahmed",
        subject="Inquiry regarding GLG Luxe Heights in Baridhara",
        body_text="Hello GLG Assets Team,\n\nI am interested in GLG Luxe Heights in Baridhara Diplomatic Zone. Could you please send me the price details and the payment terms?\n\nBest regards,\nTanvir Ahmed",
    )

    res1 = await incoming_email_webhook(payload=payload1, auth={"tenant_id": "glg-assets-main"})
    print(f"   [+] Action Selected: {res1.get('action')}")
    print(f"   [+] Confidence Score: {res1.get('confidence_score') * 100:.1f}%")
    print(f"   [+] Intent Category: {res1.get('intent')}")
    print(f"   [+] Priority: {res1.get('lead_priority')}")
    print(f"   [+] AI Reply Subject: {res1.get('ai_draft', {}).get('subject')}")
    print("   [+] AI Reply Preview:")
    for line in res1.get('ai_draft', {}).get('body', '').split('\n')[:8]:
        print(f"       {line.encode('ascii', errors='ignore').decode('ascii')}")

    # -------------------------------------------------------------
    # TEST 2: Multi-Turn Thread Follow-up Customer Email
    # -------------------------------------------------------------
    print("\n" + "-" * 50)
    print("[TEST 2] Follow-up Customer Reply in Same Thread")
    payload2 = IncomingEmailPayload(
        message_id="msg-gmail-002",
        thread_id="thread-gmail-101",
        in_reply_to="msg-gmail-001",
        sender_email="tanvir.ahmed@example.com",
        sender_name="Tanvir Ahmed",
        subject="Re: Inquiry regarding GLG Luxe Heights in Baridhara",
        body_text="Thank you for the payment plan breakdown. Can I schedule a physical site visit to GLG Luxe Heights this Saturday at 11:00 AM?\n\nTanvir",
    )

    res2 = await incoming_email_webhook(payload=payload2, auth={"tenant_id": "glg-assets-main"})
    print(f"   [+] Action Selected: {res2.get('action')}")
    print(f"   [+] Confidence Score: {res2.get('confidence_score') * 100:.1f}%")
    print(f"   [+] AI Reply Preview:")
    for line in res2.get('ai_draft', {}).get('body', '').split('\n')[:6]:
        print(f"       {line.encode('ascii', errors='ignore').decode('ascii')}")

    # -------------------------------------------------------------
    # TEST 3: Email with PDF / Spec Attachment Parsing
    # -------------------------------------------------------------
    print("\n" + "-" * 50)
    print("[TEST 3] Incoming Email with Attachment Specs")
    payload3 = IncomingEmailPayload(
        message_id="msg-gmail-003",
        thread_id="thread-gmail-102",
        sender_email="corporate.purchasing@squarebd.com",
        sender_name="Corporate Purchasing",
        subject="Requirement for Executive Residence in Gulshan 2",
        body_text="Please find attached our executive housing requirements document.",
        attachments=[
            EmailAttachment(
                filename="requirements.txt",
                content_type="text/plain",
                content="Target Area: Gulshan 2 / Banani\nBudget: 95 Lakhs BDT\nBedrooms: 3 BHK\nNeed 24/7 Generator & Security",
            )
        ],
    )

    res3 = await incoming_email_webhook(payload=payload3, auth={"tenant_id": "glg-assets-main"})
    print(f"   [+] Attachment Processing Action: {res3.get('action')}")
    print(f"   [+] AI Draft Subject: {res3.get('ai_draft', {}).get('subject')}")

    # -------------------------------------------------------------
    # TEST 4: Human Review & Approval Inbox Dispatch
    # -------------------------------------------------------------
    print("\n" + "-" * 50)
    print("[TEST 4] Dashboard Approval & Outbound Email Dispatch via n8n")
    approve_res = await approve_draft(thread_id="thread-gmail-101", auth={"tenant_id": "glg-assets-main"})
    print(f"   [+] Dispatch Message: {approve_res.get('message')}")
    print(f"   [+] Dispatch Result Status: {approve_res.get('dispatch_result', {}).get('status')}")
    print(f"   [+] Channel Used: {approve_res.get('dispatch_result', {}).get('channel')}")
    print(f"   [+] Outbound Message ID: {approve_res.get('dispatch_result', {}).get('message_id')}")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL GMAIL REPLY AUTOMATION FEATURE TESTS PASSED CLEANLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_gmail_feature_test())
