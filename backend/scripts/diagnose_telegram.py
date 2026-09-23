"""Diagnose Telegram Bot API, Webhook configuration, and pending updates."""
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")

token = os.getenv("TELEGRAM_BOT_TOKEN")
default_chat_id = os.getenv("DEFAULT_TELEGRAM_CHAT_ID")

print("=" * 60)
print("  GLG Assets — Telegram Bot Diagnostic Suite")
print("=" * 60)
if not token:
    print("[-] TELEGRAM_BOT_TOKEN is missing or empty in .env!")
    sys.exit(1)

masked_token = token[:8] + "..." + token[-4:]
print(f"Token: {masked_token}")
print(f"Default Chat ID: {default_chat_id}")

base_url = f"https://api.telegram.org/bot{token}"

with httpx.Client(timeout=15.0) as client:
    # 1. getMe
    print("\n[1] Checking Bot Identity (getMe)...")
    try:
        r = client.get(f"{base_url}/getMe")
        me_data = r.json()
        if me_data.get("ok"):
            bot = me_data["result"]
            print(f" -> Bot ID: {bot.get('id')}")
            print(f" -> Bot Name: {bot.get('first_name')}")
            print(f" -> Bot Username: @{bot.get('username')}")
            print(f" -> Can Join Groups: {bot.get('can_join_groups')}")
            print(f" -> Can Read All Group Messages: {bot.get('can_read_all_group_messages')}")
            print(f" -> Supports Inline Queries: {bot.get('supports_inline_queries')}")
        else:
            print(f"[-] getMe failed: {me_data}")
    except Exception as e:
        print(f"[-] Error calling getMe: {e}")

    # 2. getWebhookInfo
    print("\n[2] Checking Webhook Status (getWebhookInfo)...")
    try:
        r = client.get(f"{base_url}/getWebhookInfo")
        wh_data = r.json()
        if wh_data.get("ok"):
            res = wh_data["result"]
            print(f" -> Registered Webhook URL: '{res.get('url')}'")
            print(f" -> Has Custom Certificate: {res.get('has_custom_certificate')}")
            print(f" -> Pending Update Count: {res.get('pending_update_count')}")
            print(f" -> Last Error Date: {res.get('last_error_date')}")
            print(f" -> Last Error Message: {res.get('last_error_message')}")
            print(f" -> Max Connections: {res.get('max_connections')}")
            print(f" -> IP Address: {res.get('ip_address')}")
        else:
            print(f"[-] getWebhookInfo failed: {wh_data}")
    except Exception as e:
        print(f"[-] Error calling getWebhookInfo: {e}")

    # 3. If no webhook or pending updates, inspect getUpdates
    wh_url = wh_data.get("result", {}).get("url") if "wh_data" in locals() and wh_data.get("ok") else ""
    if not wh_url:
        print("\n[3] No Webhook Registered! Checking pending updates via getUpdates...")
        try:
            r = client.get(f"{base_url}/getUpdates?limit=5")
            updates = r.json()
            if updates.get("ok"):
                res = updates.get("result", [])
                print(f" -> Found {len(res)} pending updates:")
                for u in res:
                    msg = u.get("message") or u.get("edited_message") or {}
                    sender = msg.get("from", {})
                    chat = msg.get("chat", {})
                    print(f"    - Update ID {u.get('update_id')}: from {sender.get('first_name')} (@{sender.get('username')}) in chat {chat.get('id')}: '{msg.get('text')}'")
            else:
                print(f"[-] getUpdates failed: {updates}")
        except Exception as e:
            print(f"[-] Error calling getUpdates: {e}")
    else:
        print(f"\n[3] Webhook is active pointing to: {wh_url}")
        print("Note: When a webhook is active, Telegram forwards all updates directly to that URL and disables getUpdates.")

    # 4. Check if backend can send a test ping to default_chat_id
    if default_chat_id:
        print(f"\n[4] Testing Send Message to DEFAULT_TELEGRAM_CHAT_ID ({default_chat_id})...")
        try:
            test_msg = "🤖 [GLG Assets System Diagnosis]: Telegram Bot connectivity verified successfully."
            r = client.post(f"{base_url}/sendMessage", json={"chat_id": default_chat_id, "text": test_msg})
            send_res = r.json()
            if send_res.get("ok"):
                print(f" -> Successfully sent test message to chat_id {default_chat_id}!")
            else:
                print(f"[-] Send message failed: {send_res}")
        except Exception as e:
            print(f"[-] Error sending message: {e}")

print("=" * 60)
