#!/usr/bin/env python3
"""Create httpHeaderAuth credential in local n8n and wire it to all HTTP nodes."""
import json, requests, sys, re

BASE = "http://localhost:5678"
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

def login():
    r = session.post(f"{BASE}/rest/login", json={
        "emailOrLdapLoginId": "admin@glgassets.local",
        "password": "Admin123!"
    })
    if r.status_code != 200:
        print(f"LOGIN FAILED: {r.status_code}")
        return False
    print(f"✅ Logged in as {r.json()['data']['email']}")
    return True

def find_or_create_credential():
    """Find existing httpHeaderAuth credential or create one."""
    r = session.get(f"{BASE}/rest/credentials")
    if r.status_code == 200:
        for cred in r.json().get("data", []):
            if cred.get("type") == "httpHeaderAuth" and "Backend Automation" in cred.get("name", ""):
                print(f"✅ Found existing credential: {cred['id']} ({cred['name']})")
                return cred["id"]

    # Create new credential
    payload = {
        "name": "Backend Automation Secret",
        "type": "httpHeaderAuth",
        "data": {
            "name": "X-Automation-Secret",
            "value": "3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8"
        }
    }
    r = session.post(f"{BASE}/rest/credentials", json=payload)
    if r.status_code in (200, 201):
        cid = r.json()["data"]["id"]
        print(f"✅ Created credential: {cid}")
        return cid
    print(f"❌ Failed to create credential: {r.status_code} {r.text[:200]}")
    return None

def wire_credentials(cred_id):
    """Update all HTTP Request nodes across all 22 workflows to use the credential."""
    r = session.get(f"{BASE}/rest/workflows?limit=50")
    if r.status_code != 200:
        print(f"❌ Failed to fetch workflows: {r.status_code}")
        return
    
    workflows = r.json().get("data", [])
    print(f"📋 Found {len(workflows)} workflows")
    
    updated = 0
    for wf in workflows:
        wf_id = wf["id"]
        name = wf["name"]
        
        # Get full workflow data (including nodes)
        detail = session.get(f"{BASE}/rest/workflows/{wf_id}")
        if detail.status_code != 200:
            continue
        
        full = detail.json().get("data", {})
        nodes = full.get("nodes", [])
        
        # Find HTTP nodes missing credentials
        changed = False
        for node in nodes:
            if node.get("type") != "n8n-nodes-base.httpRequest":
                continue
            creds = node.get("credentials", {})
            if "httpHeaderAuth" not in creds:
                node["credentials"] = {
                    "httpHeaderAuth": {
                        "id": cred_id,
                        "name": "Backend Automation Secret"
                    }
                }
                changed = True
        
        if not changed:
            continue
        
        # Update the workflow with new node credentials
        # n8n update API expects the full workflow object with nodes
        # Try PATCH /rest/workflows/{id}
        patch_payload = {"nodes": nodes}
        upd = session.patch(f"{BASE}/rest/workflows/{wf_id}", json=patch_payload)
        
        if upd.status_code in (200, 201):
            # Count how many nodes we updated
            http_count = sum(1 for n in nodes if n.get("type") == "n8n-nodes-base.httpRequest")
            print(f"  🔌 {name} — wired {http_count} HTTP nodes")
            updated += 1
        else:
            print(f"  ❌ {name}: {upd.status_code}")
    
    print(f"\n=== Updated {updated} workflows ===")

if __name__ == "__main__":
    if not login():
        sys.exit(1)
    cred_id = find_or_create_credential()
    if not cred_id:
        sys.exit(1)
    wire_credentials(cred_id)
