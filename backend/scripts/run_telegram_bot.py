"""GLG Assets — Telegram Real-Time AI Bot Polling Service.

Continuously listens for incoming Telegram updates via long polling,
processes inquiries through the LangGraph AI multi-agent orchestration,
and delivers instant real estate recommendations.
"""
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
load_dotenv(backend_dir / ".env")

from app.agents.graph import ai_graph  # noqa: E402
from app.agents.state import AIState  # noqa: E402
from app.services.multimodal import multimodal_service  # noqa: E402
from app.services.telegram import telegram_service  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [TelegramBot] %(message)s",
)
logger = logging.getLogger("telegram_bot")

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("TELEGRAM_BOT_TOKEN is not set in .env! Exiting.")
    sys.exit(1)

base_url = f"https://api.telegram.org/bot{token}"
running = True


def handle_shutdown(signum, frame):
    global running
    logger.info("Shutdown signal received. Stopping Telegram polling loop...")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


async def process_update(client: httpx.AsyncClient, update: dict) -> int:
    update_id = update["update_id"]
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    sender = msg.get("from", {})
    username = sender.get("username", sender.get("first_name", "Unknown"))

    if not chat_id:
        return update_id + 1

    text = ""

    # 1. Voice Note / Audio Message
    if "voice" in msg or "audio" in msg:
        audio_info = msg.get("voice") or msg.get("audio") or {}
        file_id = audio_info.get("file_id")
        logger.info(f"Received voice note from @{username} (chat_id: {chat_id}). Downloading and transcribing...")
        await telegram_service.send_chat_action(chat_id, "record_voice")

        if file_id:
            audio_bytes, path = await telegram_service.download_file_bytes(file_id)
            if audio_bytes:
                text = await multimodal_service.transcribe_audio(audio_bytes, filename=path or "voice.ogg")
                if text:
                    logger.info(f"Transcribed voice from @{username}: '{text}'")
                else:
                    await telegram_service.send_message(
                        chat_id=chat_id,
                        text="I received your voice note, but couldn't transcribe it clearly. Could you please send it again or type your message?",
                    )
                    return update_id + 1

    # 2. Photo / Floor Plan Image
    elif "photo" in msg or (msg.get("document", {}).get("mime_type", "").startswith("image/")):
        photos = msg.get("photo") or []
        file_id = photos[-1].get("file_id") if photos else msg.get("document", {}).get("file_id")
        caption = msg.get("caption", "").strip()
        logger.info(f"Received photo/floor plan from @{username} (chat_id: {chat_id}). Analyzing via Vision AI...")
        await telegram_service.send_chat_action(chat_id, "upload_photo")

        if file_id:
            img_bytes, path = await telegram_service.download_file_bytes(file_id)
            if img_bytes:
                ext = path.split(".")[-1].lower() if "." in path else "jpeg"
                mime = f"image/{ext}" if ext in ["jpeg", "jpg", "png", "webp"] else "image/jpeg"
                analysis = await multimodal_service.analyze_image(img_bytes, caption=caption, mime_type=mime)
                if analysis:
                    logger.info(f"Visual analysis complete for @{username}: '{analysis[:80]}...'")
                    text = (
                        f"[Customer uploaded property photo / floor plan. Visual Analysis: {analysis}]\n"
                        f"Customer inquiry: {caption or 'Please provide details, pricing, and availability for this unit.'}"
                    )
                elif caption:
                    text = caption

    # 3. Standard Text
    if not text:
        text = msg.get("text", "").strip()

    if not text:
        return update_id + 1

    logger.info(f"Processing inquiry from @{username} (chat_id: {chat_id}): '{text[:80]}...'")
    await telegram_service.send_chat_action(chat_id, "typing")

    # Process through LangGraph
    state = AIState(
        message=text,
        conversation_id=f"tg_{chat_id}",
        channel="telegram",
        user_id=str(chat_id),
    )

    try:
        result = await ai_graph.ainvoke(state)
        reply = (
            result.get("final_response")
            or result.get("reply")
            or result.get("agent_reply")
            or result.get("message")
            or "Thank you for contacting GLG Assets! Our luxury property consultant will reach out shortly."
        )
    except Exception as e:
        logger.error(f"Error in LangGraph execution: {e}")
        reply = "Thank you for reaching out to GLG Assets! A property consultant will get back to you shortly."

    # Deliver response
    send_res = await telegram_service.send_message(chat_id=chat_id, text=reply)
    if send_res.get("success"):
        logger.info(f"Delivered AI reply to {chat_id} (length: {len(reply)} chars)")
    else:
        logger.error(f"Failed to deliver message to {chat_id}: {send_res}")

    return update_id + 1


async def run_poller():
    global running
    logger.info("=" * 60)
    logger.info("  GLG Assets — Telegram Real-Time AI Poller Active")
    logger.info("  Bot: @GLG_Asset_LTD_bot")
    logger.info("  Listening for customer messages (Ctrl+C to stop)...")
    logger.info("=" * 60)

    # 1. Clear any stale webhook before starting long polling
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            wh_info = await client.get(f"{base_url}/getWebhookInfo")
            if wh_info.json().get("result", {}).get("url"):
                logger.info("Deleting existing webhook to enable long polling...")
                await client.post(f"{base_url}/deleteWebhook")
        except Exception as e:
            logger.warning(f"Could not check/clear webhook: {e}")

        offset = None

        while running:
            try:
                params = {"timeout": 20, "limit": 10}
                if offset is not None:
                    params["offset"] = offset

                r = await client.get(f"{base_url}/getUpdates", params=params, timeout=30.0)
                data = r.json()

                if not data.get("ok"):
                    logger.warning(f"getUpdates error: {data}")
                    await asyncio.sleep(2)
                    continue

                updates = data.get("result", [])
                for update in updates:
                    offset = await process_update(client, update)

            except httpx.TimeoutException:
                # Normal long polling timeout, just loop again
                continue
            except httpx.RequestError as e:
                logger.warning(f"Network error during polling: {e}, retrying in 3s...")
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(2)

    logger.info("Telegram Poller stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(run_poller())
