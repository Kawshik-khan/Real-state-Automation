"""Gmail IMAP Inbox Listener & Auto-Reply Poller.

Continuously polls imap.gmail.com for unread incoming emails from real customers,
triggers the AI Email Agent pipeline, dispatches replies via Gmail SMTP,
and marks processed emails as seen.
"""

import asyncio
import email
from email.header import decode_header
import imaplib
import logging
from typing import Optional

from app.config import settings
from app.models.email import IncomingEmailPayload
from app.api.v1.email.endpoints import incoming_email_webhook

logger = logging.getLogger(__name__)

# List of common no-reply / promotional domains to ignore
IGNORE_SENDER_PATTERNS = [
    "noreply", "no-reply", "notification", "digest", "info@",
    "foodpanda", "openai", "github", "google.com", "facebookmail",
    "linkedin", "twitter", "newsletter", "marketing"
]

_POLLER_RUNNING = False


def _decode_str(header_value: Optional[str]) -> str:
    if not header_value:
        return ""
    decoded_res = ""
    for part, encoding in decode_header(header_value):
        if isinstance(part, bytes):
            decoded_res += part.decode(encoding or "utf-8", errors="replace")
        else:
            decoded_res += str(part)
    return decoded_res


async def poll_gmail_inbox_once():
    """Polls Gmail IMAP once for unread emails and processes customer inquiries."""
    gmail_user = settings.gmail_user_email
    gmail_pass = settings.gmail_app_password

    if not gmail_user or not gmail_pass:
        return

    def sync_fetch_and_process():
        processed_count = 0
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(gmail_user, gmail_pass)
            mail.select("inbox")

            status, response = mail.search(None, "UNSEEN")
            if status != "OK" or not response[0]:
                mail.logout()
                return 0

            msg_ids = response[0].split()
            for msg_id in msg_ids:
                try:
                    res, data = mail.fetch(msg_id, "(RFC822)")
                    if res != "OK":
                        continue

                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    sender_header = _decode_str(msg.get("From"))
                    subject = _decode_str(msg.get("Subject", "Property Inquiry"))
                    message_id = msg.get("Message-ID", f"msg-imap-{msg_id.decode()}")
                    in_reply_to = msg.get("In-Reply-To")

                    # Skip promotional / bot senders
                    sender_lower = sender_header.lower()
                    if any(pat in sender_lower for pat in IGNORE_SENDER_PATTERNS):
                        # Mark as seen so we don't re-process spam
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                        continue

                    # Extract sender email address from "Name <email@domain.com>"
                    sender_email = sender_header
                    sender_name = "Valued Lead"
                    if "<" in sender_header and ">" in sender_header:
                        sender_name = sender_header.split("<")[0].strip('" ')
                        sender_email = sender_header.split("<")[1].split(">")[0].strip()

                    # Extract body text
                    body_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                payload_bytes = part.get_payload(decode=True)
                                if payload_bytes:
                                    body_text = payload_bytes.decode(errors="replace")
                                    break
                    else:
                        payload_bytes = msg.get_payload(decode=True)
                        if payload_bytes:
                            body_text = payload_bytes.decode(errors="replace")

                    if not body_text:
                        body_text = subject

                    payload = IncomingEmailPayload(
                        message_id=message_id,
                        thread_id=f"thread-{message_id.replace('<','').replace('>','').replace('@','-')[:30]}",
                        in_reply_to=in_reply_to,
                        sender_email=sender_email,
                        sender_name=sender_name,
                        subject=subject,
                        body_text=body_text,
                    )

                    # Trigger asyncio incoming email processing
                    loop = asyncio.get_event_loop()
                    future = asyncio.run_coroutine_threadsafe(
                        incoming_email_webhook(payload, auth={"tenant_id": settings.default_tenant_id}),
                        loop
                    )
                    res = future.result(timeout=20)
                    logger.info(f"[IMAP POLLER] Processed incoming email from {sender_email}: {res.get('action')}")

                    # Mark email as seen in Gmail inbox
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                    processed_count += 1
                except Exception as ex:
                    logger.error(f"[IMAP POLLER] Error processing message {msg_id}: {ex}")

            mail.logout()
        except Exception as e:
            logger.error(f"[IMAP POLLER] Connection error: {e}")

        return processed_count

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sync_fetch_and_process)


async def email_poller_worker(interval_seconds: int = 15):
    """Background async worker loop for polling Gmail inbox."""
    global _POLLER_RUNNING
    _POLLER_RUNNING = True
    logger.info(f"[IMAP POLLER WORKER] Started Gmail inbox poller (interval={interval_seconds}s)")

    while _POLLER_RUNNING:
        try:
            await poll_gmail_inbox_once()
        except Exception as e:
            logger.error(f"[IMAP POLLER WORKER] Loop iteration error: {e}")
        await asyncio.sleep(interval_seconds)


def stop_email_poller():
    global _POLLER_RUNNING
    _POLLER_RUNNING = False
    logger.info("[IMAP POLLER WORKER] Stopped Gmail inbox poller.")
