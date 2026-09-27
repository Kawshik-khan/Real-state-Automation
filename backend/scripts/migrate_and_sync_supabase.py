"""Supabase Live Data Sync & Migration Engine for GLG Assets.

Synchronizes canonical property projects, PDF brochures, vector knowledge embeddings,
and database tables directly to Supabase Cloud (fdjzbtkypedzlkwpzzzt).
"""

import asyncio
import os
import sys
import uuid
import requests
from pathlib import Path
from typing import Dict, Any, List

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

workspace_root = backend_dir.parent

from app.config import settings
from app.services.supabase_db import supabase_db
from app.repositories.property_repository import property_repository
from scripts.sync_databases import sync_pinecone_and_supabase


async def sync_canonical_projects_to_supabase() -> int:
    """Upsert canonical luxury real estate properties into Supabase Cloud projects table."""
    print("\n[Step 1/3] Syncing Canonical Properties to Supabase Cloud...")
    supabase_url = (settings.supabase_url or "").rstrip("/")
    supabase_key = settings.supabase_service_role_key or settings.supabase_anon_key

    if not supabase_url or not supabase_key:
        print("[!] Supabase URL or Key missing in configuration.")
        return 0

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    from app.repositories.property_repository import CANONICAL_PROPERTIES
    properties = CANONICAL_PROPERTIES
    upserted_count = 0

    for p in properties:
        payload = {
            "project_id": p["id"],
            "name": p["name"],
            "location": p["location"]["formatted"],
            "price": p["pricing"]["display_en"],
            "price_val": p["pricing"]["amount"],
            "bedrooms": p["facts"]["bedrooms"],
            "description": p["description"],
            "features": {
                "amenities": p["facts"]["amenities"],
                "handover": p["facts"]["handover_date"],
                "bathrooms": p["facts"]["bathrooms"],
                "size_sqft": p["facts"]["size_sqft"],
                "images": p.get("images", []),
                "brochure_url": p.get("brochure_url", ""),
                "status": p.get("status", "active"),
                "area": p["location"]["area"],
                "city": p["location"]["city"],
            }
        }

        try:
            resp = requests.post(
                f"{supabase_url}/rest/v1/projects",
                headers=headers,
                json=payload,
                timeout=10,
            )
            if resp.status_code in [200, 201]:
                print(f"  [+] Synced {p['id']} - {p['name']} [OK]")
                upserted_count += 1
            else:
                print(f"  [!] Note on {p['id']} (HTTP {resp.status_code}): {resp.text[:100]}")
        except Exception as e:
            print(f"  [!] Error syncing {p['id']}: {e}")

    return upserted_count


async def run_database_schema_initialization() -> Dict[str, Any]:
    """Execute SQLAlchemy Base.metadata.create_all if database connection is available."""
    print("\n[Step 2/3] Checking Database Engine & Table Schema...")
    from app.database import check_connection, init_db
    is_connected = await check_connection()
    if is_connected:
        try:
            await init_db()
            print("  [+] Database connection verified — schema initialized successfully.")
            return {"connected": True, "initialized": True}
        except Exception as e:
            print(f"  [!] Schema init note: {e}")
            return {"connected": True, "initialized": False, "error": str(e)}
    else:
        print("  [i] Direct PostgreSQL port unreachable from current runtime; REST client active.")
        return {"connected": False, "initialized": False}


async def main():
    print("=" * 70)
    print(" 🌟 GLG ASSETS — SUPABASE LIVE DATA UPDATE, SYNC & MIGRATION")
    print("=" * 70)
    print(f"Target Supabase Cloud: {settings.supabase_url}")

    # Health Pre-flight
    health = supabase_db.check_health()
    print(f"Supabase REST Status: {health.get('status')} (Reachable: {health.get('reachable')})")

    # Step 1: Sync Canonical Projects
    proj_synced = await sync_canonical_projects_to_supabase()

    # Step 2: Database Schema Init
    db_res = await run_database_schema_initialization()

    # Step 3: Run Full PDF Knowledge & Vector Sync
    print("\n[Step 3/3] Synchronizing Knowledge Documents & Vectors...")
    vector_stats = await sync_pinecone_and_supabase()

    print("\n" + "=" * 70)
    print(" ✨ SUPABASE SYNCHRONIZATION SUMMARY")
    print("=" * 70)
    print(f" - Canonical Properties Synced: {proj_synced}")
    print(f" - PDF Knowledge Documents Processed: {vector_stats.get('pdf_files_processed', 0)}")
    print(f" - Supabase Storage PDFs Uploaded: {vector_stats.get('supabase_storage_uploaded', 0)}")
    print(f" - Supabase Knowledge Chunks Synced: {vector_stats.get('supabase_chunks_synced', 0)}")
    print(f" - Pinecone Vectors Indexed: {vector_stats.get('pinecone_upserted', 0)}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
