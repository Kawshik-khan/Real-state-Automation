"""Process pending Telegram updates and send AI replies."""
import asyncio
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
load_dotenv(backend_dir / ".env")

from app.agents.graph import ai_graph  # noqa: E402
from app.agents.state import AIState  # noqa: E402
from app.services.telegram import telegram_service  # noqa: E402

token = os.getenv("TELEGRAM_BOT_TOKEN")
base_url = f"https://api.telegram.org/bot{token}"

async def main():
    print("=" * 60)
    print("  Processing Pending Telegram Updates")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Fetch updates
        r = await client.get(f"{base_url}/getUpdates?limit=10")
        data = r.json()
        if not data.get("ok"):
            print(f"Error fetching updates: {data}")
            return
        
        updates = data.get("result", [])
        print(f"Found {len(updates)} pending updates in Telegram queue.")
        
        for u in updates:
            update_id = u["update_id"]
            msg = u.get("message") or u.get("edited_message") or {}
            chat = msg.get("chat", {})
            chat_id = chat.get("id")
            text = msg.get("text", "").strip()
            sender = msg.get("from", {})
            sender_name = sender.get("first_name", "User")
            
            print(f"\nProcessing Update #{update_id}:")
            print(f" -> From: {sender_name} (chat_id: {chat_id})")
            print(f" -> Message: '{text}'")
            
            if not chat_id or not text:
                print(" -> Skipped (no text or chat_id)")
                # Acknowledge update
                await client.get(f"{base_url}/getUpdates?offset={update_id + 1}")
                continue
            
            # Send 'typing' chat action
            try:
                await client.post(f"{base_url}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})
            except Exception:
                pass
            
            # Execute through LangGraph AI pipeline
            print(" -> Running through LangGraph AI pipeline...")
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
                    or "Thank you for contacting GLG Assets! Our luxury property consultant will reach out to you shortly."
                )
            except Exception as e:
                print(f" -> AI error: {e}")
                reply = "Thank you for reaching out to GLG Assets! A property consultant will get back to you shortly."
            
            print(f" -> AI Reply: '{reply[:120]}...'")
            
            # Send message to Telegram user
            send_res = await telegram_service.send_message(chat_id=chat_id, text=reply)
            if send_res.get("success"):
                print(f" -> Successfully delivered reply to Telegram user {chat_id}!")
            else:
                print(f" -> Error sending reply: {send_res}")
            
            # Acknowledge update so Telegram clears it
            await client.get(f"{base_url}/getUpdates?offset={update_id + 1}")
            print(f" -> Update #{update_id} acknowledged and cleared.")

    print("\n" + "=" * 60)
    print("All pending Telegram messages have been processed and replied to!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
