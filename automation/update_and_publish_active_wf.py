"""Update and activate active Cloud n8n workflow with HTTP POST Webhook support."""

import json
import requests

MCP_URL = "https://glg-ai.app.n8n.cloud/mcp-server/http"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkOTE3ZmU3Ni1kNDg0LTQ3ZGYtYmUyMy1iMmYxZjIyMzdiOGIiLCJpc3MiOiJuOG4iLCJhdWQiOiJtY3Atc2VydmVyLWFwaSIsImp0aSI6ImVhOWFkNTM1LTk2ZjYtNDJhYS1hZWY3LTUxZDUyZjU1ZjY3NSIsImlhdCI6MTc4NjQyNTUyMn0.xg85vsK2U_YELYHste2tX8ENVt9KQXkYspcHBBoi1E0"

headers = {
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
    r = requests.post(MCP_URL, headers=headers, json=payload)
    text = r.text
    if "event: message\ndata: " in text:
        text = text.replace("event: message\ndata: ", "", 1).strip()
    return json.loads(text)


def update_and_publish():
    code = """
import { workflow, node, trigger } from '@n8n/workflow-sdk';

const triggerNode = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 1,
  config: {
    name: 'Incoming Email Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'glg-email-webhook',
      responseMode: 'onReceived',
      options: {}
    }
  }
});

const backendNode = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 3,
  config: {
    name: 'Send to GLG AI Backend',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "https://realstate-automation.onrender.com" }}/api/v1/email/incoming',
      sendHeaders: true,
      specifyHeaders: 'json',
      jsonHeaders: '={"X-Automation-Secret": "{{ $env.AUTOMATION_SHARED_SECRET || "3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8" }}", "Content-Type": "application/json"}',
      sendBody: true,
      specifyBody: 'json',
      jsonBody: '={{ JSON.stringify({ message_id: $json.id || $json.messageId, thread_id: $json.threadId, in_reply_to: $json.inReplyTo, sender_email: $json.from || $json.sender_email, sender_name: $json.sender_name || "Lead", subject: $json.subject, body_text: $json.body_text || $json.snippet, body_html: $json.body_html }) }}'
    }
  }
});

const switchNode = node({
  type: 'n8n-nodes-base.switch',
  version: 1,
  config: {
    name: 'Check Action Type',
    parameters: {
      dataType: 'string',
      value1: '={{ $json.action }}',
      rules: {
        values: [
          { value2: 'AUTO_SEND', output: 0 },
          { value2: 'REQUIRES_APPROVAL', output: 1 }
        ]
      }
    }
  }
});

const sendEmailNode = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 3,
  config: {
    name: 'Send Outbound Email (Backend Relay)',
    parameters: {
      method: 'POST',
      url: '={{ $env.FASTAPI_BASE_URL || "https://realstate-automation.onrender.com" }}/api/v1/email/threads/dispatch-outbound',
      sendHeaders: true,
      specifyHeaders: 'json',
      jsonHeaders: '={"X-Automation-Secret": "{{ $env.AUTOMATION_SHARED_SECRET || "3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8" }}", "Content-Type": "application/json"}',
      sendBody: true,
      specifyBody: 'json',
      jsonBody: '={{ JSON.stringify({ thread_id: $json.thread_id, recipient_email: $json.sender_email, subject: $json.ai_draft.subject, body: $json.ai_draft.body }) }}'
    }
  }
});

const telegramNotifyNode = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 3,
  config: {
    name: 'Notify Agent via Telegram (.env Auth)',
    parameters: {
      method: 'POST',
      url: '=https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN || "8098076051:AAFiC-Qf4w37dRLvC40gfzJj6nrpBu8NkKU" }}/sendMessage',
      sendHeaders: true,
      specifyHeaders: 'json',
      jsonHeaders: '={"Content-Type": "application/json"}',
      sendBody: true,
      specifyBody: 'json',
      jsonBody: '={{ JSON.stringify({ chat_id: $env.TELEGRAM_SUPPORT_CHAT_ID || "6761679294", text: "📩 *GLG Email Draft Pending Approval*\\n*Lead*: " + $json.sender_email + "\\n*Subject*: " + $json.ai_draft?.subject + "\\n*Priority*: " + $json.lead_priority + "\\n*Confidence*: " + Math.round(($json.confidence_score || 0.9) * 100) + "%\\n\\nPlease review in GLG Dashboard.", parse_mode: "Markdown" }) }}'
    }
  }
});

export default workflow('wf-email-reply-automation', 'GLG Email Reply Automation Workflow')
  .add(triggerNode)
  .add(backendNode)
  .add(switchNode)
  .add(sendEmailNode)
  .add(telegramNotifyNode)
  .to(triggerNode, backendNode)
  .to(backendNode, switchNode)
  .to(switchNode, sendEmailNode)
  .to(switchNode, telegramNotifyNode);
"""

    res = call_mcp("create_workflow_from_code", {
        "code": code,
        "name": "GLG Email Reply Automation Workflow",
        "versionName": "1.4.0-post-webhook"
    })

    print("Creation Result:", json.dumps(res, indent=2))
    content_txt = res.get("result", {}).get("content", [{}])[0].get("text", "{}")
    try:
        parsed = json.loads(content_txt)
        wf_id = parsed.get("workflowId")
        if wf_id:
            print(f"\n[*] Publishing workflow {wf_id} on Cloud n8n...")
            pub_res = call_mcp("publish_workflow", {"workflowId": wf_id})
            print("Publish Result:", json.dumps(pub_res, indent=2))
    except Exception as e:
        print("Error parsing result:", e)


if __name__ == "__main__":
    update_and_publish()
