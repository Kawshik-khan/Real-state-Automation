#!/usr/bin/env python3
"""Wire the httpHeaderAuth credential to all HTTP nodes in all workflows."""
import json, requests, sys

BASE = "http://localhost:5678"
AUTH_TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
CRED_ID = sys.argv[2] if len(sys.argv) > 2 else ""

HEADERS = {"Content-Type": "application/json", "Cookie": f"n8n-auth={AUTH_TOKEN}"}

# Get all workflows
r = requests.get(f"{BASE}/rest/workflows?limit=50", headers=HEADERS)
if r.status_code != 200:
    print(f"❌ Failed to get workflows: {r.status_code}")
    sys.exit(1)

workflows = r.json().get("data", [])
print(f"📋 Found {len(workflows)} workflows")

updated = 0
for wf in workflows:
    wf_id = wf["id"]
    name = wf["name"]
    
    r2 = requests.get(f"{BASE}/rest/workflows/{wf_id}", headers=HEADERS)
    if r2.status_code != 200:
        print(f"  ⚠  {name}: GET failed {r2.status_code}")
        continue
    
    full = r2.json().get("data", {})
    nodes = full.get("nodes", [])
    
    changed = False
    for node in nodes:
        if node.get("type") != "n8n-nodes-base.httpRequest":
            continue
        creds = node.get("credentials", {})
        if "httpHeaderAuth" not in creds:
            node["credentials"] = {
                "httpHeaderAuth": {
                    "id": CRED_ID,
                    "name": "Backend Automation Secret"
                }
            }
            changed = True
    
    if not changed:
        continue
    
    r3 = requests.patch(f"{BASE}/rest/workflows/{wf_id}", headers=HEADERS, json={"nodes": nodes})
    if r3.status_code in (200, 201):
        http_count = sum(1 for n in nodes if n.get("type") == "n8n-nodes-base.httpRequest")
        print(f"  🔌 {name} — {http_count} HTTP nodes")
        updated += 1
    else:
        print(f"  ❌ {name}: {r3.status_code} {r3.text[:150]}")

print(f"\n=== Wired {updated} workflows ===")
