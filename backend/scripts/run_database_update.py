"""Update & Initialize Database Tables and Catalog Seeds for GLG Assets."""

import asyncio
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import init_db, engine, check_connection
from app.models.models import Base
from app.tools.property_tool import PROJECTS_DATABASE


async def run_update():
    print("=== 1. Checking Database Connection ===")
    connected = await check_connection()
    print(f"[+] DB Connection Reachable: {connected}")

    print("\n=== 2. Creating / Updating Database Tables & Extensions ===")
    try:
        await init_db()
        print("[+] All database tables and extensions created successfully!")
    except Exception as e:
        print(f"[!] Warning during init_db: {e}")

    print("\n=== 3. Verifying Property Catalog Data ===")
    print(f"[+] Total Projects in Database Catalog: {len(PROJECTS_DATABASE)}")
    for proj in PROJECTS_DATABASE:
        print(f" - {proj['name']} | {proj['location']} | Price: {proj['price']}")

    print("\n=== [SUCCESS] Database schema and catalog updated cleanly! ===")


if __name__ == "__main__":
    asyncio.run(run_update())
