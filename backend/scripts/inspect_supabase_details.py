import os
import requests
import json
from dotenv import load_dotenv

load_dotenv("backend/.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}"
}

print("=" * 65)
print(" 🔍 SUPABASE FULL DEEP INSPECTION")
print("=" * 65)
print(f"URL: {url}\n")

# 1. Inspect OpenAPI spec from PostgREST root
r = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
if r.status_code == 200:
    spec = r.json()
    paths = list(spec.get("paths", {}).keys())
    definitions = list(spec.get("definitions", {}).keys())
    
    print(f"PostgREST Endpoints ({len(paths)}):")
    for p in paths:
        print(f"  - {p}")
        
    print(f"\nExposed Tables/Views ({len(definitions)}):")
    for d in definitions:
        print(f"  - {d}")
else:
    print(f"PostgREST root returned status {r.status_code}")

# 2. Check RPC functions
print("\n" + "-" * 65)
print("  RPC FUNCTIONS CHECK")
print("-" * 65)
rpc_tests = ["match_chunks", "match_documents", "exec_sql"]
for rpc in rpc_tests:
    r_rpc = requests.post(f"{url}/rest/v1/rpc/{rpc}", headers=headers, json={}, timeout=5)
    print(f"  RPC '{rpc}': HTTP {r_rpc.status_code} -> {r_rpc.text[:100]}")

# 3. Check Storage Buckets and Content
print("\n" + "-" * 65)
print("  STORAGE BUCKETS & OBJECT COUNTS")
print("-" * 65)
r_b = requests.get(f"{url}/storage/v1/bucket", headers=headers, timeout=5)
if r_b.status_code == 200:
    buckets = r_b.json()
    for b in buckets:
        b_name = b.get("name") or b.get("id")
        r_files = requests.post(
            f"{url}/storage/v1/object/list/{b_name}",
            headers=headers,
            json={"prefix": "", "limit": 100, "offset": 0, "sortBy": {"column": "name", "order": "asc"}},
            timeout=5
        )
        if r_files.status_code == 200:
            files = r_files.json()
            print(f"  Bucket '{b_name}': {len(files)} objects")
            for obj in files[:5]:
                print(f"    • {obj.get('name')} ({obj.get('metadata', {}).get('size', 0)} bytes)")
        else:
            print(f"  Bucket '{b_name}': status {r_files.status_code} -> {r_files.text[:100]}")

# 4. Check knowledge_chunks details
print("\n" + "-" * 65)
print("  KNOWLEDGE_CHUNKS SUMMARY")
print("-" * 65)
r_chunks = requests.get(f"{url}/rest/v1/knowledge_chunks?select=project,document_type,filename&limit=1000", headers=headers, timeout=10)
if r_chunks.status_code in (200, 206):
    chunks = r_chunks.json()
    print(f"  Sample chunks fetched: {len(chunks)}")
    projects = set(c.get("project") for c in chunks if c.get("project"))
    print(f"  Referenced projects in chunks ({len(projects)}):")
    for p in sorted(projects):
        print(f"    • {p}")
    doc_types = set(c.get("document_type") for c in chunks if c.get("document_type"))
    print(f"  Document types ({len(doc_types)}): {doc_types}")
else:
    print(f"  Failed: {r_chunks.status_code} -> {r_chunks.text}")
