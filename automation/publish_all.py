"""Publish all uploaded workflows on Cloud n8n."""

import os
import json
import requests

MCP_URL = "https://glg-ai.app.n8n.cloud/mcp-server/http"
AUTH_TOKEN = os.environ["N8N_MCP_TOKEN"]  # never hardcode; rotate if previously committed

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

def call_mcp(method, arguments):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": method, "arguments": arguments},
        "id": 1
    }
    r = requests.post(MCP_URL, headers=HEADERS, json=payload, timeout=30)
    text = r.text.replace("event: message\ndata: ", "", 1).strip()
    try:
        data = json.loads(text)
        content = data.get("result", {}).get("content", [])
        if content and len(content) > 0:
            return json.loads(content[0].get("text", "{}"))
    except Exception:
        pass
    return {}

def main():
    print("[*] Searching existing workflows on Cloud n8n...")
    res = call_mcp("search_workflows", {})
    workflows = res.get("data", [])
    print(f"[+] Found {len(workflows)} workflows on Cloud n8n.")

    pub_count = 0
    for wf in workflows:
        wf_id = wf.get("id")
        wf_name = wf.get("name")
        is_active = wf.get("active", False)
        
        if is_active:
            print(f"   [i] '{wf_name}' ({wf_id}) is already published.")
            pub_count += 1
            continue

        print(f"   [*] Publishing '{wf_name}' ({wf_id})...")
        pub_res = call_mcp("publish_workflow", {"workflowId": wf_id})
        if not pub_res.get("error"):
            print(f"   [+] Published successfully!")
            pub_count += 1
        else:
            print(f"   [!] Note: {pub_res.get('error')[:150]}")

    print(f"\n[+] Total Active / Published Workflows on Cloud n8n: {pub_count}/{len(workflows)}")

if __name__ == "__main__":
    main()
