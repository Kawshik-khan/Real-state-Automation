"""Check subworkflow links and node connections across all Cloud n8n workflows."""

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


def main():
    print("[*] Inspecting all workflows and subworkflow linkage on Cloud n8n...")
    
    # 1. Get all workflows
    res = call_mcp("search_workflows", {})
    workflows = res.get("data", [])
    print(f"[+] Retrieved {len(workflows)} workflows from Cloud n8n.\n")

    id_name_map = {wf["id"]: wf["name"] for wf in workflows}
    name_id_map = {wf["name"]: wf["id"] for wf in workflows}

    # Map sub-workflows
    subworkflows = {name: id_ for name, id_ in name_id_map.items() if name.startswith("swf-")}
    print(f"[*] Sub-workflows discovered ({len(subworkflows)}):")
    for s_name, s_id in subworkflows.items():
        print(f"   - {s_name} (ID: {s_id})")

    print("\n" + "="*60)
    print("[*] CHECKING WORKFLOW-TO-SUBWORKFLOW CONNECTIONS:")
    print("="*60)

    total_sub_calls = 0
    valid_links = 0
    broken_links = 0

    for wf in workflows:
        wf_id = wf["id"]
        wf_name = wf["name"]
        
        # Get workflow details
        details_res = call_mcp("get_workflow_details", {"workflowId": wf_id})
        wf_data = details_res.get("workflow", details_res)
        nodes = wf_data.get("nodes", [])

        exec_nodes = [n for n in nodes if n.get("type") in ("n8n-nodes-base.executeWorkflow", "n8n-nodes-base.workflow")]
        
        if not exec_nodes:
            continue

        print(f"\n[*] Workflow '{wf_name}' (ID: {wf_id}) contains {len(exec_nodes)} sub-workflow calls:")
        for n in exec_nodes:
            total_sub_calls += 1
            node_name = n.get("name")
            params = n.get("parameters", {})
            target_wf_id = params.get("workflowId", {})
            
            # Extract target ID string or object
            target_val = ""
            if isinstance(target_wf_id, dict):
                target_val = target_wf_id.get("value", "")
            elif isinstance(target_wf_id, str):
                target_val = target_wf_id

            target_name = id_name_map.get(target_val) or (target_val if target_val in name_id_map else "Unknown")
            
            if target_val in id_name_map or target_val in name_id_map:
                valid_links += 1
                resolved_name = target_name if target_name != "Unknown" else id_name_map.get(name_id_map.get(target_val))
                print(f"   [+] Node '{node_name}' --> Calls '{resolved_name}' (ID: {target_val}) [VALID]")
            else:
                broken_links += 1
                print(f"   [!] Node '{node_name}' --> References target: '{target_val}' [NEEDS LINKING]")

    print("\n" + "="*60)
    print(f"[*] SUMMARY: Analyzed {total_sub_calls} subworkflow call nodes.")
    print(f"   [+] Verified Valid Connections: {valid_links}")
    print(f"   [!] Unlinked/Legacy Target References: {broken_links}")
    print("="*60)

if __name__ == "__main__":
    main()
