"""Comprehensive Database Update & Seeding Script for GLG Assets.

Populates:
1. Local SQLite Database (real_estate.db) — Tenants, Projects, Inventory Units, Leads, Bookings, Customers
2. AI Control Plane Store (backend/data/ai_control_plane_store.json) — Agents, Models, Providers, Prompts, Guardrails
3. Supabase Cloud Status & Sync verification
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")

backend_dir = Path(__file__).resolve().parent.parent
data_dir = backend_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)

now_iso = datetime.now(timezone.utc).isoformat()

# =====================================================================
# 1. SEED LOCAL SQLITE (real_estate.db)
# =====================================================================
def seed_sqlite():
    print("\n" + "=" * 65)
    print(" 🏢 1. SEEDING LOCAL SQLITE DATABASE (real_estate.db)")
    print("=" * 65)
    
    conn = sqlite3.connect("real_estate.db")
    cur = conn.cursor()
    
    # 1.1 Tenant
    cur.execute(
        "INSERT OR REPLACE INTO tenants (tenant_id, name, created_at) VALUES (?, ?, ?)",
        ("glg-assets-main", "GLG Assets Limited", now_iso)
    )
    print("  [✓] Seeded tenant: glg-assets-main")
    
    # 1.2 Canonical Projects
    projects = [
        ("proj_101", "glg-assets-main", "GLG Gulshan Heights", "Road 79, Gulshan-2, Dhaka", "Ultra-luxury residential landmark in the diplomatic zone with panoramic lake views, Italian marble, and automated climate control.", 1, now_iso),
        ("proj_102", "glg-assets-main", "Baridhara Luxury Suites", "Park Road, Baridhara Diplomatic Zone, Dhaka", "Exclusive boutique residences for HNIs and ambassadors featuring duplex suites, heated indoor pool, and private garden verandas.", 1, now_iso),
        ("proj_103", "glg-assets-main", "GLG Sky Tower", "Gulshan Avenue, Gulshan 1, Dhaka", "Modern architectural high-rise offering 20:80 flexible subvention payment plans, glass facades, and rooftop fitness club.", 1, now_iso),
        ("proj_104", "glg-assets-main", "Banani Crest Towers", "Road 11, Block C, Banani, Dhaka", "Contemporary urban living on Banani vibrant Road 11 corridor. Proximity to top international schools, fine dining, and Kemal Ataturk Avenue.", 1, now_iso),
        ("proj_105", "glg-assets-main", "Dhanmondi Lake Oasis", "Road 8/A, Dhanmondi, Dhaka", "Serene lake-facing residences in Dhanmondi cultural and educational heart, designed for multi-generational family comfort.", 1, now_iso),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO projects (project_id, tenant_id, name, location, description, version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        projects
    )
    print(f"  [✓] Seeded {len(projects)} luxury projects")
    
    # 1.3 Inventory Units
    units = [
        ("unit_101_3a", "glg-assets-main", "proj_101", 3, "BDT 4.80 Cr", "available", 1, now_iso),
        ("unit_101_4b", "glg-assets-main", "proj_101", 4, "BDT 6.20 Cr", "available", 1, now_iso),
        ("unit_101_ph", "glg-assets-main", "proj_101", 5, "BDT 8.50 Cr", "reserved", 1, now_iso),
        ("unit_102_dx", "glg-assets-main", "proj_102", 5, "BDT 9.80 Cr", "available", 1, now_iso),
        ("unit_102_4a", "glg-assets-main", "proj_102", 4, "BDT 7.50 Cr", "available", 1, now_iso),
        ("unit_103_3a", "glg-assets-main", "proj_103", 3, "BDT 3.50 Cr", "available", 1, now_iso),
        ("unit_103_4b", "glg-assets-main", "proj_103", 4, "BDT 5.20 Cr", "available", 1, now_iso),
        ("unit_104_3a", "glg-assets-main", "proj_104", 3, "BDT 3.20 Cr", "available", 1, now_iso),
        ("unit_104_3b", "glg-assets-main", "proj_104", 3, "BDT 3.60 Cr", "available", 1, now_iso),
        ("unit_105_3a", "glg-assets-main", "proj_105", 3, "BDT 2.80 Cr", "available", 1, now_iso),
        ("unit_105_4a", "glg-assets-main", "proj_105", 4, "BDT 4.10 Cr", "available", 1, now_iso),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO inventory_units (unit_id, tenant_id, project_id, bedrooms, price, status, version, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        units
    )
    print(f"  [✓] Seeded {len(units)} inventory units")
    
    # 1.4 Customers
    customers = [
        ("cust_001", "glg-assets-main", "ext_tanvir", json.dumps({"name": "Tanvir Ahmed", "email": "tanvir.ahmed@example.com", "phone": "+8801711000001", "intent": "High Intent HNI"}), now_iso),
        ("cust_002", "glg-assets-main", "ext_nusrat", json.dumps({"name": "Nusrat Jahan", "email": "nusrat.j@example.com", "phone": "+8801819000002", "intent": "Investor"}), now_iso),
        ("cust_003", "glg-assets-main", "ext_rahim", json.dumps({"name": "Rahim Chowdhury", "email": "r.chowdhury@example.com", "phone": "+8801914000003", "intent": "Penthouse Buyer"}), now_iso),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO customers (customer_id, tenant_id, external_ref, profile, created_at) VALUES (?, ?, ?, ?, ?)",
        customers
    )
    print(f"  [✓] Seeded {len(customers)} customers")
    
    # 1.5 Leads
    leads = [
        ("lead_001", "glg-assets-main", "cust_001", "Tanvir Ahmed", "+8801711000001", "website", "qualified", 1, now_iso),
        ("lead_002", "glg-assets-main", "cust_002", "Nusrat Jahan", "+8801819000002", "whatsapp", "in_progress", 1, now_iso),
        ("lead_003", "glg-assets-main", "cust_003", "Rahim Chowdhury", "+8801914000003", "telegram", "hot", 1, now_iso),
        ("lead_004", "glg-assets-main", None, "Farhana Karim", "+8801722000004", "instagram", "new", 1, now_iso),
        ("lead_005", "glg-assets-main", None, "Dr. Asif Mahmud", "+8801633000005", "facebook", "contacted", 1, now_iso),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO leads (lead_id, tenant_id, customer_id, name, contact, source, status, version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        leads
    )
    print(f"  [✓] Seeded {len(leads)} active sales leads")
    
    # 1.6 Bookings
    bookings = [
        ("book_001", "glg-assets-main", "cust_001", "proj_101", now_iso, "confirmed", now_iso),
        ("book_002", "glg-assets-main", "cust_002", "proj_102", now_iso, "scheduled", now_iso),
        ("book_003", "glg-assets-main", "cust_003", "proj_103", now_iso, "pending", now_iso),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO bookings (booking_id, tenant_id, customer_id, project_id, slot, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        bookings
    )
    print(f"  [✓] Seeded {len(bookings)} VIP tour bookings")
    
    conn.commit()
    conn.close()


# =====================================================================
# 2. SEED AI CONTROL PLANE STORE (backend/data/ai_control_plane_store.json)
# =====================================================================
def seed_ai_control_plane():
    print("\n" + "=" * 65)
    print(" 🧠 2. SEEDING AI CONTROL PLANE & STUDIO PERSISTENCE")
    print("=" * 65)
    
    store_file = data_dir / "ai_control_plane_store.json"
    
    # Import INITIAL_SEEDS from backend/app/persistence/ai_control_plane_store.py
    sys.path.insert(0, str(backend_dir))
    from app.persistence.ai_control_plane_store import INITIAL_SEEDS
    
    with open(store_file, "w", encoding="utf-8") as f:
        json.dump(INITIAL_SEEDS, f, indent=2, ensure_ascii=False)
        
    print(f"  [✓] Populated: {store_file.relative_to(backend_dir.parent)}")
    print(f"      • Autonomous Agents: {len(INITIAL_SEEDS.get('agents', []))}")
    print(f"      • AI Models:         {len(INITIAL_SEEDS.get('models', []))}")
    print(f"      • Inference Gateways:{len(INITIAL_SEEDS.get('providers', []))}")
    print(f"      • Tools Catalog:     {len(INITIAL_SEEDS.get('tools', []))}")
    print(f"      • Guardrail Policies:{len(INITIAL_SEEDS.get('guardrail_policies', []))}")
    print(f"      • Benchmark Suites:  {len(INITIAL_SEEDS.get('benchmarks', []))}")


# =====================================================================
# 3. VERIFY SUPABASE CLOUD STATUS & SEED KNOWLEDGE CHUNKS
# =====================================================================
def verify_supabase():
    print("\n" + "=" * 65)
    print(" ☁️  3. SUPABASE CLOUD LIVE VERIFICATION")
    print("=" * 65)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    
    # Check knowledge_chunks count
    r = requests.get(f"{url}/rest/v1/knowledge_chunks?select=id", headers={**headers, "Prefer": "count=exact"}, timeout=10)
    if r.status_code in (200, 206):
        cnt = r.headers.get("content-range", "").split("/")[-1]
        print(f"  [✓] knowledge_chunks: {cnt} chunks already indexed in pgvector!")
    else:
        print(f"  [!] knowledge_chunks status: {r.status_code}")
        
    # Check storage buckets
    r_b = requests.get(f"{url}/storage/v1/bucket", headers=headers, timeout=5)
    if r_b.status_code == 200:
        buckets = [b.get("name") for b in r_b.json()]
        print(f"  [✓] Storage buckets active: {', '.join(buckets)}")


if __name__ == "__main__":
    seed_sqlite()
    seed_ai_control_plane()
    verify_supabase()
    print("\n" + "=" * 65)
    print(" ✨ DATABASE UPDATE & SEED COMPLETED SUCCESSFULLY!")
    print("=" * 65)
