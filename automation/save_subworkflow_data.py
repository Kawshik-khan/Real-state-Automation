#!/usr/bin/env python3
"""Save all 22 modular workflow files as cleansed JSON ready for local n8n import."""
import json, os

DATA_DIR = os.path.join(os.path.dirname(__file__), "02-modular", "workflow-data")
os.makedirs(DATA_DIR, exist_ok=True)

def wf(name, nodes, connections, settings=None, tags=None, description=None):
    return {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": settings or {"executionOrder": "v1"},
        "tags": tags or [],
        "description": description or "",
    }

def wh(name, path, method="GET", pos=(0,300)):
    return {"name": name, "typeVersion": 2.1, "type": "n8n-nodes-base.webhook",
            "position": list(pos), "parameters": {"httpMethod": method, "path": path, "responseMode": "onReceived", "options": {}}}

def set_node(name, assignments, pos=(224,300), include_other=True):
    return {"name": name, "typeVersion": 3.4, "type": "n8n-nodes-base.set",
            "position": list(pos), "parameters": {"mode": "manual", "includeOtherFields": include_other,
            "assignments": {"assignments": [{"id": a[0], "name": a[1], "value": a[2], "type": a[3]} for a in assignments]}}}

def http(name, url, method="POST", body_params=None, pos=(448,300), auth=True):
    n = {"name": name, "typeVersion": 4.4, "type": "n8n-nodes-base.httpRequest",
         "position": list(pos), "parameters": {"method": method, "url": url,
         "sendBody": method in ("POST","PUT","PATCH"), "specifyBody": "json", "options": {}}}
    if auth:
        n["parameters"]["authentication"] = "genericCredentialType"
        n["parameters"]["genericAuthType"] = "httpHeaderAuth"
    if body_params:
        n["parameters"]["bodyParameters"] = {"parameters": [{"name": p[0], "value": p[1]} for p in body_params]}
    return n

def if_node(name, left, operator, right, combinator="and", pos=(448,96)):
    return {"name": name, "typeVersion": 2.3, "type": "n8n-nodes-base.if",
            "position": list(pos), "parameters": {"conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
            "conditions": [{"leftValue": left, "operator": {"type": operator.get("type","string"), "operation": operator.get("op","equals")}, "rightValue": right}],
            "combinator": combinator}}}

def switch_node(name, rules, fallback="extra", pos=(896,176)):
    return {"name": name, "typeVersion": 3.4, "type": "n8n-nodes-base.switch",
            "position": list(pos), "parameters": {"mode": "rules",
            "rules": {"values": rules}, "options": {"fallbackOutput": fallback, "renameFallbackOutput": "Unknown"}}}

def code_node(name, js_code, pos=(672,192), mode="runOnceForAllItems"):
    return {"name": name, "typeVersion": 2, "type": "n8n-nodes-base.code",
            "position": list(pos), "parameters": {"mode": mode, "jsCode": js_code}}

def respond_node(name, pos=(960,300)):
    return {"name": name, "typeVersion": 1, "type": "n8n-nodes-base.respondToWebhook",
            "position": list(pos), "parameters": {"respondWith": "json", "responseBody": "={{ $json }}"}}

def schedule_node(name, field="days", interval=1440, pos=(0,144)):
    return {"name": name, "typeVersion": 1.3, "type": "n8n-nodes-base.scheduleTrigger",
            "position": list(pos), "parameters": {"rule": {"interval": [{"field": field, "minutesInterval": interval}]}}}

def form_node(name, title, fields, pos=(0,96)):
    return {"name": name, "typeVersion": 2.6, "type": "n8n-nodes-base.formTrigger",
            "position": list(pos), "parameters": {"formTitle": title, "formDescription": "Fill in the details",
            "formFields": {"values": fields}, "options": {}}}

def split_batches(name, batch_size=1, pos=(672,144)):
    return {"name": name, "typeVersion": 3, "type": "n8n-nodes-base.splitInBatches",
            "position": list(pos), "parameters": {"batchSize": batch_size}}

def conn(from_node, to_list):
    """Build connection map. to_list is a list of (node_name, output_index) or single string.
    output_index 0 = true branch, 1 = false branch for IF nodes.
    """
    c = {}
    if isinstance(to_list, str):
        c[from_node] = {"main": [[{"node": to_list, "type": "main", "index": 0}]]}
    elif isinstance(to_list, list):
        if all(isinstance(t, str) for t in to_list):
            c[from_node] = {"main": [[{"node": t, "type": "main", "index": 0}] for t in to_list]}
        elif all(isinstance(t, tuple) for t in to_list):
            branches = {}
            for t in to_list:
                branch_idx = t[1] if len(t) > 1 else 0
                if branch_idx not in branches:
                    branches[branch_idx] = []
                branches[branch_idx].append({"node": t[0], "type": "main", "index": 0})
            c[from_node] = {"main": [branches.get(i, []) for i in range(max(branches.keys())+1)]}
        else:
            c[from_node] = {"main": [[{"node": t, "type": "main", "index": 0}] for t in to_list]}
    return c

EXPR = lambda s: "={{ " + s + " }}"

FASTAPI = EXPR("$env.FASTAPI_BASE_URL")

def save(name, data):
    path = os.path.join(DATA_DIR, name + ".json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {name}")

# ── SUBWORKFLOWS ──

# 1. SWF-AI-API-Caller
save("swf-ai-api-caller", wf("SWF-AI-API-Caller (Modular)", [
    wh("Webhook", "call-ai", "POST"),
    set_node("Normalize Input", [
        ("prompt", "prompt", EXPR("$json.body?.prompt ?? $json.prompt ?? \"\""), "string"),
        ("conv", "conversationId", EXPR("$json.body?.conversationId ?? $json.conversationId ?? \"\""), "string"),
        ("uid", "userId", EXPR("$json.body?.userId ?? $json.userId ?? \"\""), "string"),
        ("ch", "channel", EXPR("$json.body?.channel ?? $json.channel ?? \"\""), "string"),
    ]),
    http("Call AI", FASTAPI + "/api/v1/automation/ai/respond", body_params=[
        ("prompt", EXPR("$json.prompt")), ("conversationId", EXPR("$json.conversationId")),
        ("userId", EXPR("$json.userId")), ("channel", EXPR("$json.channel"))
    ], pos=(480,300)),
    set_node("Parse Response", [
        ("reply", "reply", EXPR("$json.response?.reply ?? $json.reply ?? $json.text ?? \"\""), "string"),
        ("conf", "confidence", EXPR("$json.response?.confidence ?? $json.confidence ?? 1"), "number"),
        ("act", "action", EXPR("$json.response?.action ?? $json.action ?? \"reply\""), "string"),
    ], pos=(720,300)),
    respond_node("Respond to Webhook"),
], {**conn("Webhook", "Normalize Input"), **conn("Normalize Input", "Call AI"),
    **conn("Call AI", "Parse Response"), **conn("Parse Response", "Respond to Webhook")}))

# 2. SWF-WhatsApp-Send
save("swf-whatsapp-send", wf("SWF-WhatsApp-Send (Modular)", [
    wh("Webhook", "send-whatsapp", "POST"),
    set_node("Normalize Input", [
        ("to", "to", EXPR("$json.body?.to ?? $json.to ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.message ?? \"\""), "string"),
        ("type", "type", EXPR("$json.body?.type ?? $json.type ?? \"text\""), "string"),
    ]),
    http("Send WhatsApp", FASTAPI + "/api/v1/social/whatsapp/send", body_params=[
        ("to", EXPR("$json.to")), ("message", EXPR("$json.message")), ("type", EXPR("$json.type"))
    ], pos=(480,300)),
    set_node("Format Response", [
        ("status", "status", EXPR("$json.response?.status ?? $json.status ?? \"sent\""), "string"),
        ("msgId", "messageId", EXPR("$json.response?.messageId ?? $json.messageId ?? \"\""), "string"),
    ], pos=(720,300)),
    respond_node("Respond to Webhook"),
], {**conn("Webhook", "Normalize Input"), **conn("Normalize Input", "Send WhatsApp"),
    **conn("Send WhatsApp", "Format Response"), **conn("Format Response", "Respond to Webhook")}))

# 3. SWF-Facebook-Send
save("swf-facebook-send", wf("SWF-Facebook-Send (Modular)", [
    wh("Webhook", "send-facebook", "POST"),
    set_node("Normalize Input", [
        ("to", "to", EXPR("$json.body?.to ?? $json.to ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.message ?? \"\""), "string"),
        ("type", "type", EXPR("$json.body?.type ?? $json.type ?? \"text\""), "string"),
    ]),
    http("Send Facebook", FASTAPI + "/api/v1/social/facebook/send", body_params=[
        ("to", EXPR("$json.to")), ("message", EXPR("$json.message")), ("type", EXPR("$json.type"))
    ], pos=(480,300)),
    respond_node("Respond to Webhook"),
], {**conn("Webhook", "Normalize Input"), **conn("Normalize Input", "Send Facebook"),
    **conn("Send Facebook", "Respond to Webhook")}))

# 4. SWF-Instagram-Send
save("swf-instagram-send", wf("SWF-Instagram-Send (Modular)", [
    wh("Webhook", "send-instagram", "POST"),
    set_node("Normalize Input", [
        ("to", "to", EXPR("$json.body?.to ?? $json.to ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.message ?? \"\""), "string"),
        ("type", "type", EXPR("$json.body?.type ?? $json.type ?? \"text\""), "string"),
    ]),
    http("Send Instagram", FASTAPI + "/api/v1/social/instagram/send", body_params=[
        ("to", EXPR("$json.to")), ("message", EXPR("$json.message")), ("type", EXPR("$json.type"))
    ], pos=(480,300)),
    respond_node("Respond to Webhook"),
], {**conn("Webhook", "Normalize Input"), **conn("Normalize Input", "Send Instagram"),
    **conn("Send Instagram", "Respond to Webhook")}))

# 5. SWF-Notification
save("swf-notification", wf("SWF-Notification (Modular)", [
    wh("Webhook", "notify", "POST"),
    set_node("Normalize Input", [
        ("ch", "channel", EXPR("$json.body?.channel ?? $json.channel ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.message ?? \"\""), "string"),
        ("uid", "userId", EXPR("$json.body?.userId ?? $json.userId ?? \"\""), "string"),
    ]),
    switch_node("Route Channel", [
        {"outputKey": "email", "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "email"}], "combinator": "and"}},
        {"outputKey": "slack", "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "slack"}], "combinator": "and"}},
        {"outputKey": "telegram", "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "telegram"}], "combinator": "and"}},
    ], pos=(448,300)),
    http("Send Email", FASTAPI + "/api/v1/notifications/email", body_params=[
        ("to", EXPR("$env.SUPPORT_EMAIL")), ("subject", "=Notification"), ("body", EXPR("$json.message"))
    ], pos=(672,0)),
    http("Send Slack", FASTAPI + "/api/v1/notifications/slack", body_params=[
        ("channel", "#alerts"), ("text", EXPR("$json.message"))
    ], pos=(672,192)),
    http("Send Telegram", FASTAPI + "/api/v1/notifications/telegram", body_params=[
        ("chatId", EXPR("$env.TELEGRAM_SUPPORT_CHAT_ID")), ("text", EXPR("$json.message"))
    ], pos=(672,384)),
], {**conn("Webhook", "Normalize Input"), **conn("Normalize Input", "Route Channel"),
   **conn("Route Channel", [("Send Email", 0), ("Send Slack", 1), ("Send Telegram", 2)])}))

# 6. SWF-Error-Handler
save("swf-error-handler", wf("SWF-Error-Handler (Modular)", [
    wh("Error Webhook", "error", "POST"),
    set_node("Normalize Input", [
        ("wf", "workflowName", EXPR("$json.body?.workflowName ?? $json.workflowName ?? \"\""), "string"),
        ("err", "error", EXPR("$json.body?.error ?? $json.error ?? \"\""), "string"),
        ("node", "failedNode", EXPR("$json.body?.failedNode ?? $json.failedNode ?? \"\""), "string"),
    ]),
    set_node("Format Alert", [
        ("alert", "alertText", "=Workflow {{ $json.workflowName }} failed at node {{ $json.failedNode }}: {{ $json.error }}", "string"),
    ], pos=(480,300)),
    http("Notify Admin", FASTAPI + "/api/v1/notifications/email", body_params=[
        ("to", EXPR("$env.ADMIN_EMAIL")), ("subject", "=n8n Error: {{ $json.workflowName }}"), ("body", EXPR("$json.alertText"))
    ], pos=(672,300)),
    http("Log Error", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", EXPR("$json.workflowName")), ("status", "error"), ("error", EXPR("$json.error")),
        ("failedNode", EXPR("$json.failedNode"))
    ], pos=(896,300)),
], {**conn("Error Webhook", "Normalize Input"), **conn("Normalize Input", "Format Alert"),
    **conn("Format Alert", "Notify Admin"), **conn("Notify Admin", "Log Error")}))

# 7. SWF-Log
save("swf-log", wf("SWF-Log (Modular)", [
    wh("Log Webhook", "log", "POST"),
    set_node("Normalize Input", [
        ("wf", "workflow", EXPR("$json.body?.workflow ?? $json.workflow ?? \"\""), "string"),
        ("st", "status", EXPR("$json.body?.status ?? $json.status ?? \"\""), "string"),
        ("detail", "details", EXPR("$json.body?.details ?? $json.details ?? \"\""), "string"),
    ]),
    http("Store Log", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", EXPR("$json.workflow")), ("status", EXPR("$json.status")), ("details", EXPR("$json.details"))
    ], pos=(480,300)),
    respond_node("Respond to Webhook"),
], {**conn("Log Webhook", "Normalize Input"), **conn("Normalize Input", "Store Log"),
    **conn("Store Log", "Respond to Webhook")}))

print("\nAll subworkflow files saved!")
