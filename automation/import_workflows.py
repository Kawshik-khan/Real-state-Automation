"""Import all 22 modular workflows into local n8n instance via REST API."""
import json, requests, time
from pathlib import Path

BASE = "http://localhost:5678"
SLEEP = 0.3  # delay between imports

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

def login():
    r = session.post(f"{BASE}/rest/login", json={
        "emailOrLdapLoginId": "admin@glgassets.local",
        "password": "Admin123!"
    })
    if r.status_code != 200:
        print(f"LOGIN FAILED: {r.status_code} {r.text[:200]}")
        return False
    print(f"Logged in as {r.json()['data']['email']}")
    return True

def get_existing():
    r = session.get(f"{BASE}/rest/workflows")
    existing = {}
    if r.status_code == 200:
        for wf in r.json().get("data", []):
            existing[wf["name"]] = wf["id"]
    return existing

def clean_workflow(wf):
    """Strip cloud metadata so n8n regenerates locally."""
    import copy
    w = copy.deepcopy(wf)
    for field in ["id","versionId","activeVersionId","activeVersion","createdAt",
                  "updatedAt","active","isArchived","triggerCount","parentFolderId",
                  "meta","scopes","canExecute","webhookId"]:
        w.pop(field, None)
    for node in w.get("nodes", []):
        node.pop("id", None)
        node.pop("webhookId", None)
        if "credentials" in node:
            for ck, cv in node["credentials"].items():
                if isinstance(cv, dict):
                    cv.pop("id", None)
    # Clean __rl resource locator refs
    def _clean(o):
        if isinstance(o, dict):
            o.pop("cachedResultName", None)
            for v in o.values():
                _clean(v)
        elif isinstance(o, list):
            for i in o:
                _clean(i)
    _clean(w)
    return w

def import_workflow(wf):
    cleaned = clean_workflow(wf)
    payload = {
        "name": cleaned["name"],
        "nodes": cleaned["nodes"],
        "connections": cleaned["connections"],
        "settings": cleaned.get("settings", {}),
        "tags": cleaned.get("tags", []),
        "pinData": cleaned.get("pinData"),
    }
    if cleaned.get("description"):
        payload["description"] = cleaned["description"]
    r = session.post(f"{BASE}/rest/workflows", json=payload)
    return r

# ── Load all workflow JSONs from the data directory ──
DATA_DIR = Path(__file__).parent / "02-modular" / "workflow-data"

if not DATA_DIR.exists():
    print(f"ERROR: {DATA_DIR} not found. Run save_workflow_data.py first.")
    sys.exit(1)

workflow_files = sorted(DATA_DIR.glob("*.json"))
print(f"Found {len(workflow_files)} workflow data files")

# ── Check existing ──
existing = get_existing()
print(f"Existing workflows: {list(existing.keys())}")

# ── Import each ──
imported, skipped, failed = 0, 0, 0
for f in workflow_files:
    with open(f) as fh:
        wf = json.load(fh)
    
    name = wf.get("name", f.stem)
    if name in existing:
        print(f"  ⏭  {name} — already exists")
        skipped += 1
        continue
    
    resp = import_workflow(wf)
    if resp.status_code in (200, 201):
        print(f"  [OK] {name}")
        imported += 1
    else:
        print(f"  [FAIL] {name}: {resp.status_code} {resp.text[:200]}")
        failed += 1
    
    time.sleep(SLEEP)

print(f"\n{'='*40}")
print(f"Imported: {imported}  |  Skipped: {skipped}  |  Failed: {failed}")
if failed:
    sys.exit(1)
