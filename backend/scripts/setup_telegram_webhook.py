"""Register or remove the public webhook URL for Telegram Bot API."""
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    print("TELEGRAM_BOT_TOKEN is missing!")
    sys.exit(1)

base_url = f"https://api.telegram.org/bot{token}"

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Set Webhook:   python setup_telegram_webhook.py set <PUBLIC_HTTPS_BASE_URL>")
        print("                 e.g. python setup_telegram_webhook.py set https://glg-realestate-backend.onrender.com")
        print("  Delete Webhook: python setup_telegram_webhook.py delete")
        print("  Check Status:   python setup_telegram_webhook.py status")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    with httpx.Client(timeout=15.0) as client:
        if cmd == "set":
            if len(sys.argv) < 3:
                print("Error: Missing URL argument. Example: https://glg-realestate-backend.onrender.com")
                sys.exit(1)
            raw_url = sys.argv[2].rstrip("/")
            webhook_url = f"{raw_url}/api/v1/social/telegram"
            print(f"Setting Telegram Webhook to: {webhook_url} ...")
            r = client.post(f"{base_url}/setWebhook", json={"url": webhook_url})
            print(f"Response: {r.json()}")

        elif cmd == "delete":
            print("Deleting Telegram Webhook (enabling long-polling)...")
            r = client.post(f"{base_url}/deleteWebhook")
            print(f"Response: {r.json()}")

        elif cmd == "status":
            r = client.get(f"{base_url}/getWebhookInfo")
            print(f"Webhook Info: {r.json()}")

if __name__ == "__main__":
    main()
