"""Comprehensive verification script to test all environment keys configured in backend/.env:
1. Supabase REST & Storage API
2. PostgreSQL Database Connection
3. LLM API (Groq / OpenAI)
4. Pinecone Vector Database
5. Telegram Bot API
6. Gmail OAuth / App Password Credentials
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Set stdout encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)

from app.config import settings

def test_supabase_rest_and_storage():
    print("\n" + "=" * 65)
    print(" 1. SUPABASE REST API & STORAGE BUCKETS")
    print("=" * 65)
    url = getattr(settings, "supabase_url", None) or os.getenv("SUPABASE_URL")
    anon_key = getattr(settings, "supabase_anon_key", None) or os.getenv("SUPABASE_ANON_KEY")
    service_key = getattr(settings, "supabase_service_role_key", None) or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url:
        print("[-] SUPABASE_URL: Not configured")
        return

    print(f"[*] Supabase URL: {url}")
    key_to_use = service_key or anon_key
    if not key_to_use:
        print("[-] Supabase API Keys: Missing")
        return

    headers = {
        "apikey": key_to_use,
        "Authorization": f"Bearer {key_to_use}"
    }

    # REST API Check
    try:
        r = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
        if r.status_code == 200:
            print("[+] Supabase REST API: CONNECTED (HTTP 200 OK)")
        else:
            print(f"[!] Supabase REST API returned HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"[!] Supabase REST API Connection Error: {e}")

    # Storage Buckets Check
    try:
        r = requests.get(f"{url}/storage/v1/bucket", headers=headers, timeout=10)
        if r.status_code == 200:
            buckets = r.json()
            bucket_names = [b.get("name") or b.get("id") for b in buckets] if isinstance(buckets, list) else []
            print(f"[+] Supabase Storage: CONNECTED ({len(bucket_names)} buckets found: {bucket_names})")
        else:
            print(f"[!] Supabase Storage returned HTTP {r.status_code}")
    except Exception as e:
        print(f"[!] Supabase Storage Error: {e}")


async def test_database():
    print("\n" + "=" * 65)
    print(" 2. DATABASE CONNECTION & POSTGRES")
    print("=" * 65)
    db_url = getattr(settings, "database_url", None) or os.getenv("DATABASE_URL")
    print(f"[*] Configured DATABASE_URL: {db_url}")

    if not db_url:
        print("[-] DATABASE_URL is not set")
        return

    async_url = db_url
    if not async_url.startswith("postgresql+asyncpg://"):
        if async_url.startswith("postgresql://"):
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    try:
        engine = create_async_engine(async_url, connect_args={"timeout": 5})
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT version();"))
            row = res.fetchone()
            print(f"[+] PostgreSQL Database: CONNECTED")
            print(f"    Version: {row[0] if row else 'Unknown'}")
        await engine.dispose()
    except Exception as e:
        print(f"[!] PostgreSQL Connection Failed: {e}")
        if "localhost" in db_url:
            print("    (Note: Local PostgreSQL is not running on localhost:5432. For production, set Supabase Cloud connection string.)")


def test_llm_groq_openai():
    print("\n" + "=" * 65)
    print(" 3. LLM ENGINE (GROQ / OPENAI)")
    print("=" * 65)
    api_key = getattr(settings, "openai_api_key", None) or os.getenv("OPENAI_API_KEY")
    base_url = getattr(settings, "openai_base_url", None) or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = getattr(settings, "openai_model", None) or os.getenv("OPENAI_MODEL") or "llama-3.3-70b-versatile"

    if not api_key:
        print("[-] OPENAI_API_KEY: Not set")
        return

    masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"[*] Endpoint: {base_url}")
    print(f"[*] Model:    {model}")
    print(f"[*] API Key:  {masked_key}")

    endpoint = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a test assistant. Answer in 5 words."},
            {"role": "user", "content": "Respond: 'GLG Social AI OS online'"}
        ],
        "max_tokens": 20
    }

    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=12)
        if r.status_code == 200:
            data = r.json()
            reply = data["choices"][0]["message"]["content"].strip()
            print(f"[+] LLM Generation: CONNECTED & FUNCTIONAL")
            print(f"    Model Response: \"{reply}\"")
        else:
            print(f"[!] LLM API returned HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"[!] LLM API Error: {e}")


def test_pinecone():
    print("\n" + "=" * 65)
    print(" 4. PINECONE VECTOR STORE")
    print("=" * 65)
    api_key = getattr(settings, "pinecone_api_key", None) or os.getenv("PINECONE_API_KEY")
    host = getattr(settings, "pinecone_host", None) or os.getenv("PINECONE_HOST")
    index_name = getattr(settings, "pinecone_index_name", None) or os.getenv("PINECONE_INDEX_NAME")

    if not api_key:
        print("[-] PINECONE_API_KEY: Not set")
        return

    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"[*] Index:    {index_name}")
    print(f"[*] Host:     {host}")
    print(f"[*] API Key:  {masked_key}")

    if host:
        stats_url = host.rstrip("/") + "/describe_index_stats"
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        try:
            r = requests.post(stats_url, headers=headers, json={}, timeout=10)
            if r.status_code == 200:
                stats = r.json()
                total_vector_count = stats.get("totalVectorCount", 0)
                dim = stats.get("dimension", 0)
                print(f"[+] Pinecone Vector Index: CONNECTED (Vector Count: {total_vector_count}, Dimension: {dim})")
            else:
                print(f"[!] Pinecone Host returned HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"[!] Pinecone Connection Error: {e}")
    else:
        # Fallback to control plane check
        try:
            r = requests.get("https://api.pinecone.io/indexes", headers={"Api-Key": api_key}, timeout=10)
            if r.status_code == 200:
                print(f"[+] Pinecone Control Plane: CONNECTED")
            else:
                print(f"[!] Pinecone returned HTTP {r.status_code}")
        except Exception as e:
            print(f"[!] Pinecone Error: {e}")


def test_telegram_bot():
    print("\n" + "=" * 65)
    print(" 5. TELEGRAM BOT API")
    print("=" * 65)
    token = getattr(settings, "telegram_bot_token", None) or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = getattr(settings, "default_telegram_chat_id", None) or os.getenv("DEFAULT_TELEGRAM_CHAT_ID")

    if not token:
        print("[-] TELEGRAM_BOT_TOKEN: Not set")
        return

    masked_token = token[:10] + "..." + token[-4:] if len(token) > 14 else "***"
    print(f"[*] Token:   {masked_token}")
    print(f"[*] Chat ID: {chat_id}")

    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"[+] Telegram Bot: CONNECTED & VALID")
                print(f"    Bot Name:     @{bot_info.get('username')} ({bot_info.get('first_name')})")
                print(f"    Can Join Groups: {bot_info.get('can_join_groups')}")
            else:
                print(f"[!] Telegram getMe failed: {data}")
        else:
            print(f"[!] Telegram returned HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"[!] Telegram API Error: {e}")


def test_gmail():
    print("\n" + "=" * 65)
    print(" 6. GMAIL APP PASSWORD & OAUTH CREDENTIALS")
    print("=" * 65)
    user_email = os.getenv("GMAIL_USER_EMAIL")
    app_pwd = os.getenv("GMAIL_APP_PASSWORD")
    client_id = os.getenv("GMAIL_CLIENT_ID")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

    print(f"[*] Gmail Account: {user_email}")
    print(f"[*] App Password Configured: {'YES' if app_pwd else 'NO'}")
    print(f"[*] OAuth Refresh Token:     {'YES' if refresh_token else 'NO'}")

    # Test IMAP SSL login if app password is provided
    if user_email and app_pwd:
        import imaplib
        try:
            clean_pwd = app_pwd.replace(" ", "")
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(user_email, clean_pwd)
            mail.select("INBOX")
            status, data = mail.search(None, "ALL")
            msg_count = len(data[0].split()) if data and data[0] else 0
            mail.logout()
            print(f"[+] Gmail IMAP SSL: CONNECTED & AUTHENTICATED ({msg_count} messages in INBOX)")
        except Exception as e:
            print(f"[!] Gmail IMAP Auth Error: {e}")


async def main():
    print("\n" + "#" * 65)
    print("  GLG ASSETS — PRODUCTION ENVIRONMENT KEYS TEST RUNNER")
    print("#" * 65)
    test_supabase_rest_and_storage()
    await test_database()
    test_llm_groq_openai()
    test_pinecone()
    test_telegram_bot()
    test_gmail()
    print("\n" + "#" * 65)
    print("  TEST RUN COMPLETE")
    print("#" * 65 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
