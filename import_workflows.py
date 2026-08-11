"""Import all 22 modular workflows from cloud export data into local n8n."""
import json, requests, time, uuid, sys

BASE = "http://localhost:5678"
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

def login():
    resp = session.post(f"{BASE}/rest/login", json={
        "emailOrLdapLoginId": "admin@glgassets.local",
        "password": "Admin123!"
    })
    if resp.status_code != 200:
        print(f"Login FAILED: {resp.status_code} {resp.text}")
        return False
    print(f"Login OK — user: {resp.json()['data']['email']}")
    return True

def get_existing():
    """Get existing workflow names so we can skip duplicates."""
    resp = session.get(f"{BASE}/rest/workflows")
    existing = {}
    if resp.status_code == 200:
        for wf in resp.json().get("data", []):
            existing[wf["name"]] = wf["id"]
            print(f"  Existing: {wf['name']}")
    return existing

def strip_cloud_meta(workflow):
    """Remove cloud-specific fields so n8n regenerates them locally."""
    import copy
    wf = copy.deepcopy(workflow)
    
    # Strip workflow-level metadata
    for field in ["id", "versionId", "activeVersionId", "createdAt", "updatedAt", 
                  "scopes", "canExecute", "activeVersion", "active", "isArchived",
                  "triggerCount", "parentFolderId", "meta"]:
        wf.pop(field, None)
    
    # Strip node-level IDs and webhookIds (n8n will regenerate)
    for node in wf.get("nodes", []):
        node.pop("id", None)
        node.pop("webhookId", None)
        
        # Clear credential IDs but keep names/types so they can be re-matched
        if "credentials" in node and node["credentials"]:
            for cred_key, cred_val in node["credentials"].items():
                if isinstance(cred_val, dict):
                    cred_val.pop("id", None)
    
    # Handle __rl references in parameter values (resource locator refs)
    # These reference workflows by ID which won't match locally, so strip cached names
    # but keep the value so it can be resolved by name
    def clean_params(obj):
        if isinstance(obj, dict):
            if "__rl" in obj:
                # Resource locator pattern: keep mode and value, drop cachedResultName
                obj.pop("cachedResultName", None)
            for key, val in obj.items():
                obj[key] = clean_params(val)
        elif isinstance(obj, list):
            obj = [clean_params(item) for item in obj]
        return obj
    
    wf["nodes"] = clean_params(wf["nodes"])
    wf.get("connections", {})
    
    return wf

def import_workflow(wf_data):
    """POST a single workflow to the local n8n instance."""
    url = f"{BASE}/rest/workflows"
    payload = {
        "name": wf_data["name"],
        "nodes": wf_data["nodes"],
        "connections": wf_data["connections"],
        "settings": wf_data.get("settings", {}),
        "tags": wf_data.get("tags", []),
        "pinData": wf_data.get("pinData", None),
    }
    if "description" in wf_data:
        payload["description"] = wf_data["description"]
    
    resp = session.post(url, json=payload)
    return resp

# The 22 cloud workflow exports (data from MCP calls)
CLOUD_DATA = {%s}
