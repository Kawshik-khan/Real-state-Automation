"""Check Supabase REST API, PostgreSQL database, and pgvector extension status."""

import asyncio
import os
import sys
import requests
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Set stdout encoding for Windows compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Explicitly load backend/.env
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)

from app.config import settings

async def check_supabase_async():
    supabase_url = getattr(settings, "supabase_url", None) or os.getenv("SUPABASE_URL")
    supabase_service_key = getattr(settings, "supabase_service_role_key", None) or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    print("=" * 60)
    print("  SUPABASE & PGVECTOR CONNECTION CHECK")
    print("=" * 60)
    print(f"[*] Supabase Endpoint: {supabase_url}")

    # 1. Test Supabase REST API
    if supabase_url and supabase_service_key:
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}"
        }
        try:
            r = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
            if r.status_code == 200:
                print(f"[+] Supabase REST API HTTP Status: 200 OK [CONNECTED - OK]")
            else:
                print(f"[!] Supabase REST API status code: {r.status_code}")
        except Exception as e:
            print(f"[!] Supabase REST API Connection Error: {e}")
    else:
        print("[!] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing in .env")

    # 2. Check Database URL & pgvector
    db_url = getattr(settings, "database_url", None) or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    print(f"\n[*] Configured DATABASE_URL: {db_url}")

    if not db_url.startswith("postgresql+asyncpg://"):
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"[*] Testing PostgreSQL Connection via asyncpg to: {db_url} ...")
    try:
        engine = create_async_engine(db_url, connect_args={"timeout": 10})
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT version();"))
            row = res.fetchone()
            print(f"[+] Connected to PostgreSQL Database! [CONNECTED - OK]")
            print(f"   Version: {row[0] if row else 'Unknown'}")

            print("\n[*] Checking / Enabling 'vector' extension (pgvector)...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.commit()

            vec_res = await conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"))
            vec_row = vec_res.fetchone()
            if vec_row:
                print(f"[+] pgvector extension is ACTIVE! [OK] (Name: {vec_row[0]}, Version: {vec_row[1]})")
            else:
                print(f"[!] pgvector extension is not listed in pg_extension.")

        await engine.dispose()

    except Exception as err:
        print(f"[!] PostgreSQL Connection Error: {err}")
        print("\n[*] NOTE FOR SUPABASE CLOUD DATABASE CONNECTION:")
        print("   If connecting to Supabase Cloud PostgreSQL directly, update backend/.env:")
        print("   DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres")
        print("   or direct connection: postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[project-ref].supabase.co:5432/postgres")

def main():
    asyncio.run(check_supabase_async())

if __name__ == "__main__":
    main()
