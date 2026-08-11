"""Upload and publish all modular n8n workflows to Cloud n8n MCP Server."""

import re
import sys
import json
import time
import requests
from pathlib import Path

MCP_URL = "https://glg-ai.app.n8n.cloud/mcp-server/http"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkOTE3ZmU3Ni1kNDg0LTQ3ZGYtYmUyMy1iMmYxZjIyMzdiOGIiLCJpc3MiOiJuOG4iLCJhdWQiOiJtY3Atc2VydmVyLWFwaSIsImp0aSI6ImVhOWFkNTM1LTk2ZjYtNDJhYS1hZWY3LTUxZDUyZjU1ZjY3NSIsImlhdCI6MTc4NjQyNTUyMn0.xg85vsK2U_YELYHste2tX8ENVt9KQXkYspcHBBoi1E0"

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}


def call_mcp(method, arguments, req_id=1):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": method,
            "arguments": arguments
        },
        "id": req_id
    }
    r = requests.post(MCP_URL, headers=HEADERS, json=payload, timeout=30)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    
    text = r.text
    if text.startswith("event: message\ndata: "):
        text = text.replace("event: message\ndata: ", "", 1).strip()
    
    try:
        data = json.loads(text)
        res = data.get("result", {})
        content = res.get("content", [])
        if content and isinstance(content, list) and len(content) > 0:
            raw_txt = content[0].get("text", "")
            try:
                return json.loads(raw_txt)
            except Exception:
                return {"text": raw_txt}
        return res
    except Exception as e:
        return {"error": f"JSON parse error: {e}"}


def clean_sdk_code(code: str) -> str:
    """Clean unsupported SDK method calls such as .description(...) or .onError(...) chaining on workflow()."""
    # Remove .description('...') chaining
    cleaned = re.sub(r"\.description\([^)]*\)\s*", "", code)
    # Remove .onError('...') chaining if present on workflow(...) root
    cleaned = re.sub(r"\.onError\(['\"][^'\"]*['\"]\)\s*", "", cleaned)
    return cleaned


def main():
    base_dir = Path(__file__).resolve().parent / "02-modular"
    
    files_to_process = []
    for category in ["admin-workflows", "channel-workflows", "subworkflows"]:
        cat_dir = base_dir / category
        if cat_dir.exists():
            for f in cat_dir.glob("*.ts"):
                files_to_process.append(f)
            for f in cat_dir.glob("*.js"):
                # Avoid duplicates if both .ts and .js exist
                if not (cat_dir / f"{f.stem}.ts").exists():
                    files_to_process.append(f)

    files_to_process = sorted(files_to_process)
    print(f"[*] Found {len(files_to_process)} workflow SDK code files to process.")

    uploaded_count = 0
    published_count = 0

    for idx, filepath in enumerate(files_to_process, 1):
        wf_name = filepath.stem
        print(f"\n[{idx}/{len(files_to_process)}] Processing '{wf_name}' ({filepath.name})...")
        
        with open(filepath, "r", encoding="utf-8") as fh:
            code = fh.read()
        
        cleaned_code = clean_sdk_code(code)

        # 1. Create Workflow from Code
        print(f"   [*] Uploading code to Cloud n8n MCP...")
        res = call_mcp("create_workflow_from_code", {
            "code": cleaned_code,
            "name": wf_name,
            "versionName": "Initial cloud import"
        }, req_id=idx)

        wf_id = res.get("workflowId") or res.get("id")
        if not wf_id and isinstance(res, dict) and "text" in res:
            try:
                parsed = json.loads(res["text"])
                wf_id = parsed.get("workflowId")
            except Exception:
                pass

        if wf_id:
            uploaded_count += 1
            print(f"   [+] Created workflow '{wf_name}' (ID: {wf_id})")

            # 2. Publish/Activate Workflow
            print(f"   [*] Publishing workflow {wf_id}...")
            pub_res = call_mcp("publish_workflow", {
                "workflowId": wf_id
            }, req_id=idx + 100)
            
            if not pub_res.get("error"):
                published_count += 1
                print(f"   [+] Published successfully!")
            else:
                print(f"   [!] Publish warning: {pub_res.get('error')}")
        else:
            print(f"   [!] Upload failed: {json.dumps(res, indent=2)[:300]}")

        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"[+] SUMMARY: Uploaded {uploaded_count}/{len(files_to_process)} workflows | Published {published_count} workflows to Cloud n8n!")


if __name__ == "__main__":
    main()
