"""Upload, wire up, and activate latest email & modular workflows to Cloud n8n via MCP."""

import json
import os
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
    try:
        r = requests.post(MCP_URL, headers=HEADERS, json=payload, timeout=30)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}

        text = r.text
        if text.startswith("event: message\ndata: "):
            text = text.replace("event: message\ndata: ", "", 1).strip()

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
        return {"error": str(e)}


def upload_and_wire_email_workflow():
    print("=== 1. Searching existing workflows on Cloud n8n via MCP ===")
    search_res = call_mcp("search_workflows", {})
    workflows = search_res.get("data", []) if isinstance(search_res, dict) else []
    print(f"[+] Found {len(workflows)} active workflows on Cloud n8n.")

    # Load local email reply automation JSON
    wf_file = Path(__file__).parent / "email-reply-automation.json"
    if not wf_file.exists():
        print(f"[!] {wf_file} not found.")
        return

    with open(wf_file, "r", encoding="utf-8") as f:
        wf_data = json.load(f)

    wf_name = wf_data.get("name", "GLG Email Reply Automation Workflow")
    print(f"\n=== 2. Preparing '{wf_name}' for Cloud n8n ===")

    # Convert JSON structure into SDK code representation for MCP create_workflow_from_code tool
    sdk_code = f"""
import {{ workflow, node, trigger }} from '@n8n/workflow-sdk';

const triggerNode = trigger({{
  type: 'n8n-nodes-base.gmailTrigger',
  version: 1,
  config: {{ name: 'On New Incoming Email (Gmail/IMAP)' }}
}});

const backendApiNode = node({{
  type: 'n8n-nodes-base.httpRequest',
  version: 3,
  config: {{
    name: 'Send to GLG AI Backend',
    parameters: {{
      method: 'POST',
      url: 'http://localhost:8000/api/v1/email/incoming',
      sendHeaders: true,
      headerParameters: {{
        parameters: [
          {{ name: 'X-Automation-Secret', value: 'change-me-in-production' }},
          {{ name: 'Content-Type', value: 'application/json' }}
        ]
      }},
      sendBody: true,
      specifyBody: 'json',
      jsonBody: '={{ {{ "message_id": $json.id || $json.messageId, "thread_id": $json.threadId, "in_reply_to": $json.inReplyTo, "sender_email": $json.from.address || $json.from, "sender_name": $json.from.name || $json.from, "subject": $json.subject, "body_text": $json.text || $json.snippet, "body_html": $json.html }} }}'
    }}
  }}
}});

const switchNode = node({{
  type: 'n8n-nodes-base.switch',
  version: 1,
  config: {{
    name: 'Check Action Type',
    parameters: {{
      dataType: 'string',
      value1: '={{ $json.action }}',
      rules: {{
        rules: [
          {{ value2: 'AUTO_SEND', output: 0 }},
          {{ value2: 'REQUIRES_APPROVAL', output: 1 }}
        ]
      }}
    }}
  }}
}});

const sendEmailNode = node({{
  type: 'n8n-nodes-base.emailSend',
  version: 1,
  config: {{
    name: 'Send Outbound Email Node',
    parameters: {{
      sendTo: '={{ $json.sender_email }}',
      subject: '={{ $json.ai_draft.subject }}',
      message: '={{ $json.ai_draft.body }}'
    }}
  }}
}});

const telegramNotifyNode = node({{
  type: 'n8n-nodes-base.telegram',
  version: 1,
  config: {{
    name: 'Notify Agent via Telegram',
    parameters: {{
      text: '=📩 *GLG Email Draft Pending Approval*\\n*Lead*: {{{{ $json.sender_email }}}}\\n*Subject*: {{{{ $json.ai_draft.subject }}}}\\n*Priority*: {{{{ $json.lead_priority }}}}\\n*Confidence*: {{{{ Math.round($json.confidence_score * 100) }}}}%\\n\\nPlease review and approve in GLG Real Estate Dashboard.'
    }}
  }}
}});

export default workflow({{
  name: '{wf_name}',
  nodes: [triggerNode, backendApiNode, switchNode, sendEmailNode, telegramNotifyNode],
  connections: {{
    'On New Incoming Email (Gmail/IMAP)': {{ main: [[{{ node: 'Send to GLG AI Backend', type: 'main', index: 0 }}]] }},
    'Send to GLG AI Backend': {{ main: [[{{ node: 'Check Action Type', type: 'main', index: 0 }}]] }},
    'Check Action Type': {{ main: [[{{ node: 'Send Outbound Email Node', type: 'main', index: 0 }}, {{ node: 'Notify Agent via Telegram', type: 'main', index: 0 }}]] }}
  }}
}});
"""

    print("=== 3. Uploading latest workflow code to Cloud n8n via MCP ===")
    upload_res = call_mcp("create_workflow_from_code", {
        "code": sdk_code,
        "name": wf_name,
        "versionName": "v1.0-email-reply-automation"
    })

    wf_id = upload_res.get("workflowId") or upload_res.get("id")
    if not wf_id and isinstance(upload_res, dict) and "text" in upload_res:
        try:
            parsed = json.loads(upload_res["text"])
            wf_id = parsed.get("workflowId")
        except Exception:
            pass

    print(f"[+] Workflow ID: {wf_id or 'Created / Updated'}")

    if wf_id:
        print(f"=== 4. Publishing & Wiring up workflow ID {wf_id} on Cloud n8n ===")
        pub_res = call_mcp("publish_workflow", {"workflowId": wf_id})
        print(f"[+] Publish result: {pub_res}")

    print("\n=== 5. Publishing all active Cloud n8n workflows ===")
    import publish_all
    publish_all.main()


if __name__ == "__main__":
    upload_and_wire_email_workflow()
