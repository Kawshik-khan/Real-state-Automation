import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import requests

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

load_dotenv(backend_dir / ".env")

url = os.getenv("SUPABASE_URL", "https://fdjzbtkypedzlkwpzzzt.supabase.co")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": service_key,
    "Authorization": f"Bearer {service_key}",
    "Content-Type": "application/json"
}

# Tables expected by Backend models:
EXPECTED_TABLES = [
    "projects",
    "conversations",
    "messages",
    "users",
    "leads",
    "knowledge_documents",
    "knowledge_chunks",
    "escalations",
    "social_posts",
    "social_engagements",
    "calendar_events",
    "audit_logs",
    "agent_configurations",
    "ai_policy_rules",
    "ai_models",
    "ai_prompt_versions",
    "ai_fine_tuning_jobs",
    "ai_datasets",
    "ai_ab_experiments",
    "ai_benchmarks",
    "ai_governance_logs"
]

print("=" * 65)
print("  GLG ASSETS — SUPABASE SYNC & GAP ANALYSIS")
print("=" * 65)
print(f"Endpoint: {url}\n")

existing_tables = {}
missing_tables = []
error_tables = []

for table in EXPECTED_TABLES:
    try:
        # Request table with limit 1 to verify existence and count
        r = requests.get(
            f"{url}/rest/v1/{table}?select=*&limit=1",
            headers={**headers, "Prefer": "count=exact"},
            timeout=5
        )
        if r.status_code in (200, 206):
            content_range = r.headers.get("content-range", "")
            count = content_range.split("/")[-1] if "/" in content_range else len(r.json())
            sample = r.json()
            cols = list(sample[0].keys()) if sample else []
            existing_tables[table] = {"count": count, "cols": cols}
            print(f" [✓] {table:<24} EXISTS  (Rows: {count:>3})")
        elif r.status_code == 404:
            missing_tables.append(table)
            print(f" [✗] {table:<24} MISSING (404 Not Found)")
        else:
            error_tables.append((table, r.status_code, r.text[:80]))
            print(f" [!] {table:<24} ERROR ({r.status_code}: {r.text[:60]})")
    except Exception as e:
        error_tables.append((table, "Timeout/Exception", str(e)))
        print(f" [!] {table:<24} EXCEPTION: {e}")

print("\n" + "-" * 65)
print("  STORAGE BUCKETS STATUS")
print("-" * 65)
expected_buckets = ["brochures", "floorplans", "ocr-documents"]
try:
    r = requests.get(f"{url}/storage/v1/bucket", headers=headers, timeout=5)
    if r.status_code == 200:
        buckets = [b.get("name") or b.get("id") for b in r.json()]
        for b in expected_buckets:
            if b in buckets:
                print(f" [✓] Bucket '{b}': EXISTS")
            else:
                print(f" [✗] Bucket '{b}': MISSING")
    else:
        print(f" [!] Storage API Error {r.status_code}: {r.text}")
except Exception as e:
    print(f" [!] Storage check failed: {e}")

print("\n" + "=" * 65)
print("  ANALYSIS SUMMARY")
print("=" * 65)
print(f"Total Model Tables Checked: {len(EXPECTED_TABLES)}")
print(f"Tables Present in Supabase: {len(existing_tables)}")
print(f"Tables Missing in Supabase: {len(missing_tables)}")
if missing_tables:
    print("\nMissing Tables to Create on Supabase:")
    for m in missing_tables:
        print(f" - {m}")

