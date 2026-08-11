"""Automated script to update FASTAPI_BASE_URL across all Cloud n8n workflows for 100% FREE (No Enterprise Plan required)."""

import re
import sys
import json
import requests

MCP_URL = "https://glg-ai.app.n8n.cloud/mcp-server/http"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkOTE3ZmU3Ni1kNDg0LTQ3ZGYtYmUyMy1iMmYxZjIyMzdiOGIiLCJpc3MiOiJuOG4iLCJhdWQiOiJtY3Atc2VydmVyLWFwaSIsImp0aSI6ImVhOWFkNTM1LTk2ZjYtNDJhYS1hZWY3LTUxZDUyZjU1ZjY3NSIsImlhdCI6MTc4NjQyNTUyMn0.xg85vsK2U_YELYHste2tX8ENVt9KQXkYspcHBBoi1E0"

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


def update_target_url(render_url):
    # Ensure no trailing slash
    render_url = render_url.rstrip("/")
    print(f"[*] Target Render Backend URL: {render_url}")
    
    # Get all workflows from Cloud n8n
    res = call_mcp("search_workflows", {})
    workflows = res.get("data", [])
    print(f"[+] Found {len(workflows)} workflows on Cloud n8n.")

    updated_count = 0

    for wf in workflows:
        wf_id = wf["id"]
        wf_name = wf["name"]

        # Get workflow details
        details_res = call_mcp("get_workflow_details", {"workflowId": wf_id})
        wf_data = details_res.get("workflow", details_res)
        nodes = wf_data.get("nodes", [])

        modified = False
        for node in nodes:
            params = node.get("parameters", {})
            url_param = params.get("url")
            
            if isinstance(url_param, str) and ("$env.FASTAPI_BASE_URL" in url_param or "localhost:8000" in url_param):
                # Replace $env.FASTAPI_BASE_URL or localhost with render_url
                new_url = url_param.replace("={{ $env.FASTAPI_BASE_URL }}", render_url)
                new_url = new_url.replace("={{$env.FASTAPI_BASE_URL}}", render_url)
                new_url = new_url.replace("http://localhost:8000", render_url)
                new_url = new_url.replace("http://backend:8000", render_url)
                
                params["url"] = new_url
                modified = True
                print(f"   [+] Updated node '{node.get('name')}' in '{wf_name}' --> URL: {new_url[:70]}")

        if modified:
            # Save updated workflow back to Cloud n8n
            update_op = {
                "workflowId": wf_id,
                "operations": [
                    {
                        "type": "setWorkflowMetadata",
                        "name": wf_name
                    }
                ],
                "versionName": "Update Render backend URL"
            }
            res_up = call_mcp("update_workflow", update_op)
            if not res_up.get("error"):
                updated_count += 1
                # Re-publish
                call_mcp("publish_workflow", {"workflowId": wf_id})

    print(f"\n[+] Successfully updated {updated_count} workflows on Cloud n8n to point to '{render_url}'!")


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://glg-realestate-backend.onrender.com"
    update_target_url(target_url)
