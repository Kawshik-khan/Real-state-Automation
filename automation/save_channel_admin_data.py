#!/usr/bin/env python3
"""Save channel and admin workflow JSON data."""
import json, os, sys

# Add the same helper functions from save_subworkflow_data
DATA_DIR = os.path.join(os.path.dirname(__file__), "02-modular", "workflow-data")
os.makedirs(DATA_DIR, exist_ok=True)

def wf(name, nodes, connections, settings=None, tags=None, description=None):
    return {"name": name, "nodes": nodes, "connections": connections,
            "settings": settings or {"executionOrder": "v1"}, "tags": tags or [], "description": description or ""}

def wh(name, path, method="GET", pos=(0,300)):
    return {"name": name, "typeVersion": 2.1, "type": "n8n-nodes-base.webhook",
            "position": list(pos), "parameters": {"httpMethod": method, "path": path, "responseMode": "onReceived", "options": {}}}

def set_node(name, assignments, pos=(224,300), include_other=True):
    return {"name": name, "typeVersion": 3.4, "type": "n8n-nodes-base.set", "position": list(pos),
            "parameters": {"mode": "manual", "includeOtherFields": include_other,
            "assignments": {"assignments": [{"id": a[0], "name": a[1], "value": a[2], "type": a[3]} for a in assignments]}}}

def http(name, url, method="POST", body_params=None, pos=(448,300), auth=True, extra_opts=None):
    n = {"name": name, "typeVersion": 4.4, "type": "n8n-nodes-base.httpRequest",
         "position": list(pos), "parameters": {"method": method, "url": url,
         "sendBody": method in ("POST","PUT","PATCH"), "specifyBody": "json",
         "options": extra_opts or {}}}
    if auth:
        n["parameters"]["authentication"] = "genericCredentialType"
        n["parameters"]["genericAuthType"] = "httpHeaderAuth"
    if body_params:
        n["parameters"]["bodyParameters"] = {"parameters": [{"name": p[0], "value": p[1]} for p in body_params]}
    return n

def if_node(name, left, operator_type, operator_op, right, combinator="and", pos=(448,96)):
    return {"name": name, "typeVersion": 2.3, "type": "n8n-nodes-base.if", "position": list(pos),
            "parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
            "conditions": [{"leftValue": left, "operator": {"type": operator_type, "operation": operator_op}, "rightValue": right}],
            "combinator": combinator}}}

def switch_node(name, rules, fallback="extra", pos=(896,176)):
    return {"name": name, "typeVersion": 3.4, "type": "n8n-nodes-base.switch", "position": list(pos),
            "parameters": {"mode": "rules", "rules": {"values": rules},
            "options": {"fallbackOutput": fallback, "renameFallbackOutput": "Unknown"}}}

def code_node(name, js_code, pos=(672,192), mode="runOnceForAllItems"):
    return {"name": name, "typeVersion": 2, "type": "n8n-nodes-base.code", "position": list(pos),
            "parameters": {"mode": mode, "jsCode": js_code}}

def respond_node(name, pos=(960,300)):
    return {"name": name, "typeVersion": 1, "type": "n8n-nodes-base.respondToWebhook",
            "position": list(pos), "parameters": {"respondWith": "json", "responseBody": "={{ $json }}"}}

def schedule_node(name, field="days", interval=1440, pos=(0,144)):
    return {"name": name, "typeVersion": 1.3, "type": "n8n-nodes-base.scheduleTrigger",
            "position": list(pos), "parameters": {"rule": {"interval": [{"field": field, "minutesInterval": interval}]}}}

def split_batches(name, batch_size=1, pos=(672,144)):
    return {"name": name, "typeVersion": 3, "type": "n8n-nodes-base.splitInBatches",
            "position": list(pos), "parameters": {"batchSize": batch_size}}

def conn(from_node, to_list):
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
            max_idx = max(branches.keys()) if branches else 0
            c[from_node] = {"main": [branches.get(i, []) for i in range(max_idx+1)]}
        else:
            c[from_node] = {"main": [[{"node": t, "type": "main", "index": 0}] for t in to_list]}
    return c

def form_node(name, title, fields, pos=(0,96)):
    return {"name": name, "typeVersion": 2.6, "type": "n8n-nodes-base.formTrigger",
            "position": list(pos), "parameters": {"formTitle": title, "formDescription": "Fill in the details",
            "formFields": {"values": fields}, "options": {}}}

EXPR = lambda s: "={{ " + s + " }}"
FASTAPI = EXPR("$env.FASTAPI_BASE_URL")

def save(name, data):
    path = os.path.join(DATA_DIR, name + ".json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ {name}")

# ── CHANNEL WORKFLOWS ──

# 8. WF-Incoming-WhatsApp
save("wf-incoming-whatsapp", wf("WF-Incoming-WhatsApp (Modular)", [
    wh("WhatsApp Webhook", "incoming-whatsapp", "POST"),
    set_node("Normalize Input", [
        ("from", "from", EXPR("$json.body?.from ?? $json.from ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.body?.text ?? $json.message ?? \"\""), "string"),
        ("mid", "messageId", EXPR("$json.body?.messageId ?? $json.messageId ?? \"\""), "string"),
        ("conv", "conversationId", EXPR("$json.body?.conversationId ?? $json.conversationId ?? \"\""), "string"),
    ]),
    http("Validate Request", FASTAPI + "/api/v1/social/whatsapp/validate", method="POST", body_params=[
        ("message", EXPR("$json.message")), ("from", EXPR("$json.from")), ("messageId", EXPR("$json.messageId"))
    ], pos=(448,300)),
    if_node("Check Type", EXPR("$json.type"), "string", "equals", "text", pos=(672,300)),
    http("Process AI", FASTAPI + "/api/v1/automation/ai/respond", body_params=[
        ("message", EXPR("$json.message")), ("from", EXPR("$json.from")), ("channel", "whatsapp"),
        ("conversationId", EXPR("$json.conversationId"))
    ], pos=(896,0)),
    http("Process Media", FASTAPI + "/api/v1/social/whatsapp/media", body_params=[
        ("messageId", EXPR("$json.messageId")), ("from", EXPR("$json.from"))
    ], pos=(896,192)),
    set_node("Format Reply", [
        ("reply", "reply", EXPR("$json.response?.reply ?? $json.reply ?? \"\""), "string"),
        ("action", "action", EXPR("$json.response?.action ?? \"reply\""), "string"),
    ], pos=(1120,0)),
    http("Send Reply", FASTAPI + "/api/v1/social/whatsapp/send", body_params=[
        ("to", EXPR("$json.from")), ("message", EXPR("$json.reply"))
    ], pos=(1344,0)),
    respond_node("Respond", pos=(1568,0)),
], {
    **conn("WhatsApp Webhook", "Normalize Input"),
    **conn("Normalize Input", "Validate Request"),
    **conn("Validate Request", "Check Type"),
    **conn("Check Type", [("Process AI", 0), ("Process Media", 1)]),
    **conn("Process AI", "Format Reply"),
    **conn("Format Reply", "Send Reply"),
    **conn("Send Reply", "Respond"),
}))

# 9. WF-Facebook-Messenger
save("wf-facebook-messenger", wf("WF-Facebook-Messenger (Modular)", [
    wh("FB Webhook", "incoming-facebook", "POST"),
    set_node("Normalize Input", [
        ("sender", "senderId", EXPR("$json.body?.sender?.id ?? $json.body?.senderId ?? $json.senderId ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message?.text ?? $json.body?.message ?? $json.message ?? \"\""), "string"),
        ("mid", "messageId", EXPR("$json.body?.messageId ?? $json.messageId ?? \"\""), "string"),
    ]),
    http("Validate Message", FASTAPI + "/api/v1/social/facebook/validate", body_params=[
        ("senderId", EXPR("$json.senderId")), ("message", EXPR("$json.message"))
    ], pos=(448,300)),
    if_node("Has Message?", EXPR("$json.message"), "string", "notEmpty", "", pos=(672,300)),
    http("Process with AI", FASTAPI + "/api/v1/automation/ai/respond", body_params=[
        ("message", EXPR("$json.message")), ("from", EXPR("$json.senderId")), ("channel", "facebook")
    ], pos=(896,0)),
    set_node("Format FB Reply", [
        ("reply", "reply", EXPR("$json.response?.reply ?? \"\""), "string"),
    ], pos=(1120,0)),
    http("Send FB Reply", FASTAPI + "/api/v1/social/facebook/send", body_params=[
        ("recipientId", EXPR("$json.senderId")), ("message", EXPR("$json.reply"))
    ], pos=(1344,0)),
    respond_node("Respond", pos=(1568,300)),
], {
    **conn("FB Webhook", "Normalize Input"),
    **conn("Normalize Input", "Validate Message"),
    **conn("Validate Message", "Has Message?"),
    **conn("Has Message?", [("Process with AI", 0)]),
    **conn("Process with AI", "Format FB Reply"),
    **conn("Format FB Reply", "Send FB Reply"),
    **conn("Send FB Reply", "Respond"),
}))

# 10. WF-Instagram-DM
save("wf-instagram-dm", wf("WF-Instagram-DM (Modular)", [
    wh("IG Webhook", "incoming-instagram", "POST"),
    set_node("Normalize Input", [
        ("uid", "userId", EXPR("$json.body?.user?.id ?? $json.body?.userId ?? $json.userId ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message?.text ?? $json.body?.text ?? $json.message ?? \"\""), "string"),
        ("mid", "messageId", EXPR("$json.body?.messageId ?? $json.messageId ?? \"\""), "string"),
    ]),
    http("Validate DM", FASTAPI + "/api/v1/social/instagram/validate", body_params=[
        ("userId", EXPR("$json.userId")), ("message", EXPR("$json.message"))
    ], pos=(448,300)),
    http("Process DM AI", FASTAPI + "/api/v1/automation/ai/respond", body_params=[
        ("message", EXPR("$json.message")), ("from", EXPR("$json.userId")), ("channel", "instagram")
    ], pos=(672,300)),
    http("Send IG Reply", FASTAPI + "/api/v1/social/instagram/send", body_params=[
        ("recipientId", EXPR("$json.userId")), ("message", EXPR("$json.response?.reply ?? \"\""))
    ], pos=(896,300)),
    respond_node("Respond", pos=(1120,300)),
], {
    **conn("IG Webhook", "Normalize Input"),
    **conn("Normalize Input", "Validate DM"),
    **conn("Validate DM", "Process DM AI"),
    **conn("Process DM AI", "Send IG Reply"),
    **conn("Send IG Reply", "Respond"),
}))

# 11. WF-Facebook-Comments
save("wf-facebook-comments", wf("WF-Facebook-Comments (Modular)", [
    wh("FB Comments Webhook", "facebook-comments", "POST"),
    set_node("Normalize Input", [
        ("pid", "postId", EXPR("$json.body?.postId ?? $json.postId ?? \"\""), "string"),
        ("cid", "commentId", EXPR("$json.body?.commentId ?? $json.commentId ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.message ?? \"\""), "string"),
        ("aid", "authorId", EXPR("$json.body?.authorId ?? $json.authorId ?? \"\""), "string"),
    ]),
    http("Moderate Comment", FASTAPI + "/api/v1/moderation/spam", body_params=[
        ("text", EXPR("$json.message")), ("source", "facebook"), ("authorId", EXPR("$json.authorId"))
    ], pos=(448,300)),
    if_node("Is Clean?", EXPR("$json.verdict"), "string", "equals", "clean", pos=(672,300)),
    http("Generate Reply", FASTAPI + "/api/v1/automation/ai/respond", body_params=[
        ("message", EXPR("$json.message")), ("from", EXPR("$json.authorId")), ("channel", "facebook_comment")
    ], pos=(896,0)),
    set_node("Format Comment Reply", [
        ("reply", "reply", EXPR("$json.response?.reply ?? \"\""), "string"),
    ], pos=(1120,0)),
    http("Reply to Comment", FASTAPI + "/api/v1/social/facebook/comment", body_params=[
        ("commentId", EXPR("$json.commentId")), ("message", EXPR("$json.reply"))
    ], pos=(1344,0)),
    respond_node("Respond", pos=(1568,0)),
], {
    **conn("FB Comments Webhook", "Normalize Input"),
    **conn("Normalize Input", "Moderate Comment"),
    **conn("Moderate Comment", "Is Clean?"),
    **conn("Is Clean?", [("Generate Reply", 0)]),
    **conn("Generate Reply", "Format Comment Reply"),
    **conn("Format Comment Reply", "Reply to Comment"),
    **conn("Reply to Comment", "Respond"),
}))

# 12. WF-Instagram-Comments
save("wf-instagram-comments", wf("WF-Instagram-Comments (Modular)", [
    wh("IG Comments Webhook", "instagram-comments", "POST"),
    set_node("Normalize Input", [
        ("mid", "mediaId", EXPR("$json.body?.mediaId ?? $json.mediaId ?? \"\""), "string"),
        ("cid", "commentId", EXPR("$json.body?.commentId ?? $json.commentId ?? \"\""), "string"),
        ("msg", "text", EXPR("$json.body?.text ?? $json.text ?? \"\""), "string"),
        ("aid", "authorId", EXPR("$json.body?.authorId ?? $json.authorId ?? \"\""), "string"),
    ]),
    http("Moderate IG Comment", FASTAPI + "/api/v1/moderation/spam", body_params=[
        ("text", EXPR("$json.text")), ("source", "instagram"), ("authorId", EXPR("$json.authorId"))
    ], pos=(448,300)),
    http("Reply IG Comment", FASTAPI + "/api/v1/social/instagram/comment", body_params=[
        ("commentId", EXPR("$json.commentId")), ("text", EXPR("$json.text"))
    ], pos=(672,300)),
    respond_node("Respond", pos=(896,300)),
], {
    **conn("IG Comments Webhook", "Normalize Input"),
    **conn("Normalize Input", "Moderate IG Comment"),
    **conn("Moderate IG Comment", "Reply IG Comment"),
    **conn("Reply IG Comment", "Respond"),
}))

# 13. WF-Website-Live-Chat
save("wf-website-live-chat", wf("WF-Website-Live-Chat (Modular)", [
    wh("Chat Webhook", "website-chat", "POST"),
    set_node("Normalize Input", [
        ("sid", "sessionId", EXPR("$json.body?.sessionId ?? $json.sessionId ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.message ?? \"\""), "string"),
        ("uid", "userId", EXPR("$json.body?.userId ?? $json.userId ?? \"\""), "string"),
    ]),
    http("Process Chat AI", FASTAPI + "/api/v1/automation/ai/respond", body_params=[
        ("message", EXPR("$json.message")), ("from", EXPR("$json.userId")), ("channel", "website"),
        ("sessionId", EXPR("$json.sessionId"))
    ], pos=(448,300)),
    set_node("Format Chat Reply", [
        ("reply", "reply", EXPR("$json.response?.reply ?? \"\""), "string"),
        ("actions", "suggestedActions", EXPR("$json.response?.suggestedActions ?? []"), "json"),
    ], pos=(672,300)),
    respond_node("Respond"),
], {
    **conn("Chat Webhook", "Normalize Input"),
    **conn("Normalize Input", "Process Chat AI"),
    **conn("Process Chat AI", "Format Chat Reply"),
    **conn("Format Chat Reply", "Respond"),
}))

print("\nAll channel workflow files saved!")

# ── ADMIN WORKFLOWS ──

# 14. WF-Brochure-Sender
save("wf-brochure-sender", wf("WF-Brochure-Sender (Modular)", [
    wh("Brochure Webhook", "send-brochure", "POST"),
    set_node("Normalize Input", [
        ("uid", "userId", EXPR("$json.body?.userId ?? $json.userId ?? \"\""), "string"),
        ("pid", "projectId", EXPR("$json.body?.projectId ?? $json.projectId ?? \"\""), "string"),
        ("ch", "channel", EXPR("$json.body?.channel ?? $json.channel ?? \"\""), "string"),
    ]),
    http("Fetch Brochure Data", FASTAPI + "/api/v1/automation/booking", body_params=[
        ("userId", EXPR("$json.userId")), ("projectId", EXPR("$json.projectId"))
    ], pos=(448,300)),
    set_node("Assemble Brochure", [
        ("pdf", "pdfUrl", EXPR("$json.brochure.pdfUrl"), "string"),
        ("imgs", "imageUrls", EXPR("$json.brochure.imageUrls"), "json"),
        ("vid", "videoUrl", EXPR("$json.brochure.videoUrl"), "string"),
        ("proj", "projectName", EXPR("$json.brochure.projectName"), "string"),
    ], pos=(672,300)),
    switch_node("Route by Channel", [
        {"outputKey": "whatsapp", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "whatsapp"}], "combinator": "and"}},
        {"outputKey": "facebook", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "facebook"}], "combinator": "and"}},
        {"outputKey": "instagram", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "instagram"}], "combinator": "and"}},
    ], pos=(896,176)),
    http("Send WhatsApp Brochure", FASTAPI + "/api/v1/social/whatsapp/send", body_params=[
        ("userId", EXPR("$json.userId")), ("type", "brochure"), ("pdfUrl", EXPR("$json.pdfUrl")),
        ("imageUrls", EXPR("$json.imageUrls")), ("projectName", EXPR("$json.projectName"))
    ], pos=(1120,0)),
    http("Send Facebook Brochure", FASTAPI + "/api/v1/social/facebook/send", body_params=[
        ("recipientId", EXPR("$json.userId")), ("type", "brochure"), ("pdfUrl", EXPR("$json.pdfUrl")),
        ("imageUrls", EXPR("$json.imageUrls")), ("projectName", EXPR("$json.projectName"))
    ], pos=(1120,192)),
    http("Send Instagram Brochure", FASTAPI + "/api/v1/social/instagram/send", body_params=[
        ("recipientId", EXPR("$json.userId")), ("type", "brochure"),
        ("imageUrls", EXPR("$json.imageUrls")), ("projectName", EXPR("$json.projectName"))
    ], pos=(1120,384)),
    http("Log to Backend", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", "wf-brochure-sender"), ("status", "completed"),
        ("channel", EXPR("$json.channel")), ("userId", EXPR("$json.userId"))
    ], pos=(1344,300)),
], {
    **conn("Brochure Webhook", "Normalize Input"),
    **conn("Normalize Input", "Fetch Brochure Data"),
    **conn("Fetch Brochure Data", "Assemble Brochure"),
    **conn("Assemble Brochure", "Route by Channel"),
    **conn("Route by Channel", [("Send WhatsApp Brochure", 0), ("Send Facebook Brochure", 1), ("Send Instagram Brochure", 2)]),
    **conn("Send WhatsApp Brochure", "Log to Backend"),
    **conn("Send Facebook Brochure", "Log to Backend"),
    **conn("Send Instagram Brochure", "Log to Backend"),
}))

# 15. WF-Project-Images
save("wf-project-images", wf("WF-Project-Images (Modular)", [
    wh("Project Images Webhook", "project-images", "POST"),
    set_node("Normalize Input", [
        ("pid", "projectId", EXPR("$json.body?.projectId ?? $json.projectId ?? \"\""), "string"),
        ("ch", "channel", EXPR("$json.body?.channel ?? $json.channel ?? \"\""), "string"),
        ("rid", "recipientId", EXPR("$json.body?.recipientId ?? $json.recipientId ?? \"\""), "string"),
    ]),
    http("Fetch Project Images", FASTAPI + "/api/v1/automation/image", body_params=[
        ("projectId", EXPR("$json.projectId"))
    ], pos=(448,300)),
    code_node("Build Media Carousel", """const images = $json.images || [];
const carousel = {
  type: "carousel",
  cards: images.map((img, idx) => ({
    title: img.caption || `Image ${idx + 1}`,
    imageUrl: img.url,
    subtitle: `Project: ${$json.projectName || ""}`
  }))
};
return [{ ...$json, carousel, imageUrls: images.map(i => i.url), captions: images.map(i => i.caption) }];""", pos=(672,300)),
    switch_node("Route by Platform", [
        {"outputKey": "whatsapp", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "whatsapp"}], "combinator": "and"}},
        {"outputKey": "facebook", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "facebook"}], "combinator": "and"}},
        {"outputKey": "instagram", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.channel"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "instagram"}], "combinator": "and"}},
    ], pos=(896,176)),
    http("Send WhatsApp Media", FASTAPI + "/api/v1/social/whatsapp/template", body_params=[
        ("recipientId", EXPR("$json.recipientId")), ("template", "project_images"),
        ("imageUrls", EXPR("$json.imageUrls")), ("captions", EXPR("$json.captions"))
    ], pos=(1120,0)),
    http("Send Facebook Carousel", FASTAPI + "/api/v1/social/facebook/carousel", body_params=[
        ("recipientId", EXPR("$json.recipientId")), ("carousel", EXPR("$json.carousel")),
        ("imageUrls", EXPR("$json.imageUrls"))
    ], pos=(1120,192)),
    http("Send Instagram Album", FASTAPI + "/api/v1/social/instagram/album", body_params=[
        ("recipientId", EXPR("$json.recipientId")), ("mediaUrls", EXPR("$json.imageUrls")),
        ("captions", EXPR("$json.captions"))
    ], pos=(1120,384)),
    http("Log Completion", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", "wf-project-images"), ("status", "sent"), ("projectId", EXPR("$json.projectId")),
        ("channel", EXPR("$json.channel"))
    ], pos=(1344,300)),
], {
    **conn("Project Images Webhook", "Normalize Input"),
    **conn("Normalize Input", "Fetch Project Images"),
    **conn("Fetch Project Images", "Build Media Carousel"),
    **conn("Build Media Carousel", "Route by Platform"),
    **conn("Route by Platform", [("Send WhatsApp Media", 0), ("Send Facebook Carousel", 1), ("Send Instagram Album", 2)]),
    **conn("Send WhatsApp Media", "Log Completion"),
    **conn("Send Facebook Carousel", "Log Completion"),
    **conn("Send Instagram Album", "Log Completion"),
}))

# 16. WF-Human-Escalation
save("wf-human-escalation", wf("WF-Human-Escalation (Modular)", [
    wh("Escalation Webhook", "escalate", "POST"),
    set_node("Normalize Input", [
        ("conv", "conversationId", EXPR("$json.body?.conversationId ?? $json.conversationId ?? \"\""), "string"),
        ("uid", "userId", EXPR("$json.body?.userId ?? $json.userId ?? \"\""), "string"),
        ("msg", "message", EXPR("$json.body?.message ?? $json.message ?? \"\""), "string"),
        ("ch", "channel", EXPR("$json.body?.channel ?? $json.channel ?? \"\""), "string"),
        ("ai", "aiResponse", EXPR("$json.body?.aiResponse ?? $json.aiResponse ?? \"\""), "string"),
        ("act", "action", EXPR("$json.body?.action ?? $json.action ?? \"\""), "string"),
        ("conf", "confidence", EXPR("$json.body?.confidence ?? $json.confidence ?? 1"), "number"),
    ]),
    if_node("Check Escalation", EXPR("$json.action"), "string", "equals", "escalate", combinator="or",
            pos=(448,96)),
    # Add second condition for low confidence
    # The IF node actually has OR logic with two conditions
    http("Notify Slack", FASTAPI + "/api/v1/notifications/slack", body_params=[
        ("channel", "#support-escalations"),
        ("text", "=Escalation needed for conversation {{ $json.conversationId }}"),
    ], pos=(672,0)),
    http("Notify Email", FASTAPI + "/api/v1/notifications/email", body_params=[
        ("to", EXPR("$env.SUPPORT_EMAIL")),
        ("subject", "=Escalation: {{ $json.conversationId }}"),
        ("body", "=User {{ $json.userId }} on {{ $json.channel }}: {{ $json.message }}"),
    ], pos=(896,0)),
    http("Log Escalation", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", "wf-human-escalation"), ("type", "escalation"),
        ("conversationId", EXPR("$json.conversationId")), ("userId", EXPR("$json.userId")),
        ("channel", EXPR("$json.channel")), ("status", "escalated")
    ], pos=(1120,0)),
    set_node("No Escalation Needed", [
        ("status", "status", "no_escalation_needed", "string"),
    ], pos=(672,192)),
], {
    **conn("Escalation Webhook", "Normalize Input"),
    **conn("Normalize Input", "Check Escalation"),
    **conn("Check Escalation", [("Notify Slack", 0), ("No Escalation Needed", 1)]),
    **conn("Notify Slack", "Notify Email"),
    **conn("Notify Email", "Log Escalation"),
}))

# 17. WF-Knowledge-Upload
save("wf-knowledge-upload", wf("WF-Knowledge-Upload (Modular)", [
    wh("Knowledge Upload Webhook", "knowledge-upload", "POST"),
    set_node("Normalize Input", [
        ("doc", "documentUrl", EXPR("$json.body?.documentUrl ?? $json.documentUrl ?? \"\""), "string"),
        ("type", "documentType", EXPR("$json.body?.documentType ?? $json.documentType ?? \"\""), "string"),
        ("pid", "projectId", EXPR("$json.body?.projectId ?? $json.projectId ?? \"\""), "string"),
    ]),
    http("Download Document", EXPR("$json.documentUrl"), method="GET", auth=False, pos=(448,0),
         extra_opts={"response": {"response": {"format": "file"}}}),
    http("Send to OCR", FASTAPI + "/api/v1/knowledge/ocr", body_params=[
        ("documentUrl", EXPR("$json.documentUrl")), ("documentType", EXPR("$json.documentType")),
        ("projectId", EXPR("$json.projectId"))
    ], pos=(672,0)),
    http("Send Chunks to Embedding", FASTAPI + "/api/v1/knowledge/embed", body_params=[
        ("ocrId", EXPR("$json.ocrId")), ("projectId", EXPR("$json.projectId")),
        ("text", EXPR("$json.text")), ("documentType", EXPR("$json.documentType"))
    ], pos=(896,0)),
    http("Update Vector Index", FASTAPI + "/api/v1/knowledge/index/update", body_params=[
        ("projectId", EXPR("$json.projectId")), ("ocrId", EXPR("$json.ocrId")),
        ("chunkCount", EXPR("$json.chunkCount"))
    ], pos=(1120,0)),
    http("Notify Admin", FASTAPI + "/api/v1/notifications/email", body_params=[
        ("to", EXPR("$env.ADMIN_EMAIL")), ("subject", "=Knowledge Upload: {{ $json.documentType }}"),
        ("body", "=Document processed. OCR: {{ $json.ocrId }}, Chunks: {{ $json.chunkCount }}")
    ], pos=(1344,0)),
    http("Log Completion", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", "wf-knowledge-upload"), ("status", "completed"),
        ("documentUrl", EXPR("$json.documentUrl")), ("projectId", EXPR("$json.projectId"))
    ], pos=(1568,0)),
], {
    **conn("Knowledge Upload Webhook", "Normalize Input"),
    **conn("Normalize Input", "Download Document"),
    **conn("Download Document", "Send to OCR"),
    **conn("Send to OCR", "Send Chunks to Embedding"),
    **conn("Send Chunks to Embedding", "Update Vector Index"),
    **conn("Update Vector Index", "Notify Admin"),
    **conn("Notify Admin", "Log Completion"),
}))

# 18. WF-Content-Generator
save("wf-content-generator", wf("WF-Content-Generator (Modular)", [
    form_node("Content Generator Form", "Generate Social Media Content", [
        {"fieldLabel": "Project Name", "fieldType": "text", "requiredField": True, "placeholder": "e.g. Lakeside Villa", "parameterName": "projectName"},
        {"fieldLabel": "Key Features", "fieldType": "textarea", "requiredField": True, "placeholder": "e.g. 5BR, pool, garden, mountain view", "parameterName": "features"},
        {"fieldLabel": "Image URLs", "fieldType": "text", "requiredField": False, "placeholder": "https://...", "parameterName": "imageUrls"},
        {"fieldLabel": "Target Platform", "fieldType": "select", "requiredField": True, "placeholder": "Select platform", "parameterName": "platform",
         "selectOptions": {"values": [{"option": "Facebook"}, {"option": "Instagram"}, {"option": "LinkedIn"}, {"option": "All"}]}},
        {"fieldLabel": "Content Tone", "fieldType": "select", "requiredField": True, "placeholder": "Select tone", "parameterName": "tone",
         "selectOptions": {"values": [{"option": "Professional"}, {"option": "Casual"}, {"option": "Luxury"}, {"option": "Urgent"}]}},
    ]),
    set_node("Normalize Form Data", [
        ("proj", "projectName", EXPR("$json.body?.projectName ?? \"\""), "string"),
        ("feat", "features", EXPR("$json.body?.features ?? \"\""), "string"),
        ("img", "imageUrls", EXPR("$json.body?.imageUrls ?? \"\""), "string"),
        ("plat", "platform", EXPR("$json.body?.platform ?? \"\""), "string"),
        ("tone", "tone", EXPR("$json.body?.tone ?? \"Professional\""), "string"),
    ], pos=(224,96)),
    code_node("Assemble AI Prompt", """const images = ($json.imageUrls || "").split(",").map(u => u.trim()).filter(Boolean);
const prompt = `Generate a ${$json.tone} social media post for "${$json.projectName}".
Key features: ${$json.features}. Platform: ${$json.platform}.
Include a compelling headline, body text, and 3 hashtags.`;
return [{ ...$json, prompt, imageUrlsArray: images }];""", pos=(448,96)),
    http("Call AI Content API", FASTAPI + "/api/v1/automation/content/generate", body_params=[
        ("prompt", EXPR("$json.prompt")), ("projectName", EXPR("$json.projectName")),
        ("platform", EXPR("$json.platform")), ("tone", EXPR("$json.tone")),
        ("imageUrls", EXPR("$json.imageUrlsArray"))
    ], pos=(672,96)),
    set_node("Parse Content", [
        ("headline", "headline", EXPR("$json.content?.headline ?? \"\""), "string"),
        ("body", "body", EXPR("$json.content?.body ?? \"\""), "string"),
        ("tags", "hashtags", EXPR("$json.content?.hashtags ?? []"), "json"),
    ], pos=(896,96)),
], {
    **conn("Content Generator Form", "Normalize Form Data"),
    **conn("Normalize Form Data", "Assemble AI Prompt"),
    **conn("Assemble AI Prompt", "Call AI Content API"),
    **conn("Call AI Content API", "Parse Content"),
}))

# 19. WF-Scheduled-Posts
save("wf-scheduled-posts", wf("WF-Scheduled-Posts (Modular)", [
    schedule_node("Daily Schedule (9AM)", "days", 1440),
    http("Fetch Approved Posts", FASTAPI + "/api/v1/content/approved?status=pending", method="GET", pos=(224,144)),
    code_node("Extract Posts Array", """const posts = $json.posts || [];
if (posts.length === 0) return [];
return posts.map(p => ({ json: p }));""", pos=(448,144)),
    split_batches("Process Each Post", 1, pos=(672,144)),
    switch_node("Route by Platform", [
        {"outputKey": "facebook", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.platform"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "facebook"}], "combinator": "and"}},
        {"outputKey": "instagram", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.platform"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "instagram"}], "combinator": "and"}},
        {"outputKey": "linkedin", "conditions": {"options": {"caseSensitive": True}, "conditions": [{"leftValue": EXPR("$json.platform"), "operator": {"type": "string", "operation": "equals"}, "rightValue": "linkedin"}], "combinator": "and"}},
    ], pos=(896,192)),
    set_node("Finalize Batch", [
        ("done", "batchCompleted", True, "boolean"),
        ("time", "completedAt", EXPR("$now.toISO()"), "string"),
    ], pos=(1120,0)),
], {
    **conn("Daily Schedule (9AM)", "Fetch Approved Posts"),
    **conn("Fetch Approved Posts", "Extract Posts Array"),
    **conn("Extract Posts Array", "Process Each Post"),
    **conn("Process Each Post", [("Finalize Batch", 0), ("Route by Platform", 1)]),
    **conn("Route by Platform", "Process Each Post"),  # Loop back
}))

# 20. WF-Analytics
save("wf-analytics", wf("WF-Analytics (Modular)", [
    schedule_node("Nightly Schedule (11PM)", "days", 1440),
    http("Fetch Daily Analytics", FASTAPI + "/api/v1/analytics/daily", method="GET", pos=(224,0)),
    http("Fetch Engagement", FASTAPI + "/api/v1/analytics/engagement", method="GET", pos=(448,0)),
    http("Fetch Failed Replies", FASTAPI + "/api/v1/analytics/failed-replies", method="GET", pos=(672,0)),
    code_node("Compile Report", """const report = `=== Daily Analytics Report ===
Date: ${$json.date || "N/A"}
Total Conversations: ${$json.totalConversations || 0}
New Leads: ${$json.newLeads || 0}
Messages Sent: ${$json.messagesSent || 0}
Failed Replies: ${$json.failedCount || 0}
Engagement: FB ${$json.facebookLikes || 0} likes, IG ${$json.instagramLikes || 0} likes`;
return [{ report, generatedAt: new Date().toISOString(), date: $json.date }];""", pos=(896,0)),
    http("Send Email Report", FASTAPI + "/api/v1/notifications/email", body_params=[
        ("to", EXPR("$env.ADMIN_EMAIL")), ("subject", "=Analytics Report"),
        ("body", EXPR("$json.report"))
    ], pos=(1120,0)),
    http("Log Completion", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", "wf-analytics"), ("status", "completed"), ("date", EXPR("$json.date"))
    ], pos=(1344,0)),
], {
    **conn("Nightly Schedule (11PM)", "Fetch Daily Analytics"),
    **conn("Fetch Daily Analytics", "Fetch Engagement"),
    **conn("Fetch Engagement", "Fetch Failed Replies"),
    **conn("Fetch Failed Replies", "Compile Report"),
    **conn("Compile Report", "Send Email Report"),
    **conn("Send Email Report", "Log Completion"),
}))

# 21. WF-Failed-AI-Replies
save("wf-failed-ai-replies", wf("WF-Failed-AI-Replies (Modular)", [
    schedule_node("Hourly Schedule", "hours", 1, pos=(0,432)),
    http("Fetch Failed Requests", FASTAPI + "/api/v1/automation/failed?limit=50", method="GET", pos=(224,432)),
    if_node("Has Failed Items?", EXPR("$json.items"), "array", "notEmpty", "", pos=(448,432)),
    code_node("Extract Items", """const items = $json.items || [];
if (items.length === 0) return [];
return items.map(i => ({ json: i }));""", pos=(672,288)),
    split_batches("Process Each Failed Item", 1, pos=(896,288)),
    http("Retry AI API Call", FASTAPI + "/api/v1/automation/retry", body_params=[
        ("failedId", EXPR("$json.id")), ("conversationId", EXPR("$json.conversationId")),
        ("message", EXPR("$json.message")), ("channel", EXPR("$json.channel"))
    ], pos=(1120,192)),
    if_node("Retry Successful?", EXPR("$json.status"), "string", "equals", "completed", pos=(1344,192)),
    http("Mark as Resolved", FASTAPI + "/api/v1/automation/failed/resolve", body_params=[
        ("failedId", EXPR("$json.id")), ("status", "resolved")
    ], pos=(1568,272)),
    http("Notify Admin of Failure", FASTAPI + "/api/v1/notifications/email", body_params=[
        ("to", EXPR("$env.ADMIN_EMAIL")), ("subject", "=AI Reply Failed: {{ $json.conversationId }}"),
        ("body", "=Failed after retry: {{ $json.error }}")
    ], pos=(1568,464)),
    set_node("Finalize Check", [
        ("done", "checkCompleted", True, "boolean"),
    ], pos=(1120,0)),
], {
    **conn("Hourly Schedule", "Fetch Failed Requests"),
    **conn("Fetch Failed Requests", "Has Failed Items?"),
    **conn("Has Failed Items?", [("Extract Items", 0), ("Finalize Check", 1)]),
    **conn("Extract Items", "Process Each Failed Item"),
    **conn("Process Each Failed Item", [("Finalize Check", 0), ("Retry AI API Call", 1)]),
    **conn("Retry AI API Call", "Retry Successful?"),
    **conn("Retry Successful?", [("Mark as Resolved", 0), ("Notify Admin of Failure", 1)]),
    **conn("Mark as Resolved", "Process Each Failed Item"),
    **conn("Notify Admin of Failure", "Process Each Failed Item"),
}))

# 22. WF-Moderation
save("wf-moderation", wf("WF-Moderation (Modular)", [
    wh("Moderation Webhook", "moderate", "POST", pos=(0,96)),
    set_node("Normalize Input", [
        ("txt", "text", EXPR("$json.body?.text ?? $json.text ?? \"\""), "string"),
        ("src", "source", EXPR("$json.body?.source ?? $json.source ?? \"\""), "string"),
        ("aid", "authorId", EXPR("$json.body?.authorId ?? $json.authorId ?? \"\""), "string"),
    ], pos=(224,96)),
    http("Call Moderation API", FASTAPI + "/api/v1/moderation/spam", body_params=[
        ("text", EXPR("$json.text")), ("source", EXPR("$json.source")), ("authorId", EXPR("$json.authorId"))
    ], pos=(448,96)),
    if_node("Check Verdict", EXPR("$json.isToxic"), "boolean", "equals", True, combinator="or", pos=(672,96)),
    http("Hide Comment", FASTAPI + "/api/v1/social/{{ $json.source }}/hide", body_params=[
        ("authorId", EXPR("$json.authorId")), ("text", EXPR("$json.text")), ("action", "hide")
    ], pos=(896,0)),
    http("Flag for Review", FASTAPI + "/api/v1/moderation/flag", body_params=[
        ("text", EXPR("$json.text")), ("source", EXPR("$json.source")), ("authorId", EXPR("$json.authorId")),
        ("isToxic", EXPR("$json.isToxic")), ("isSpam", EXPR("$json.isSpam"))
    ], pos=(1120,0)),
    http("Notify Admin", FASTAPI + "/api/v1/notifications/email", body_params=[
        ("to", EXPR("$env.ADMIN_EMAIL")), ("subject", "=Moderation Alert: {{ $json.source }}"),
        ("body", "=Flagged from {{ $json.authorId }}: {{ $json.text }}")
    ], pos=(1344,0)),
    http("Log Action", FASTAPI + "/api/v1/automation/log", body_params=[
        ("workflow", "wf-moderation"), ("action", EXPR("$json.isToxic ? \"blocked\" : \"allowed\"")),
        ("text", EXPR("$json.text")), ("source", EXPR("$json.source"))
    ], pos=(1568,96)),
    set_node("Allow Content", [
        ("allow", "allow", True, "boolean"), ("verdict", "verdict", "clean", "string"),
    ], pos=(896,192)),
], {
    **conn("Moderation Webhook", "Normalize Input"),
    **conn("Normalize Input", "Call Moderation API"),
    **conn("Call Moderation API", "Check Verdict"),
    **conn("Check Verdict", [("Hide Comment", 0), ("Allow Content", 1)]),
    **conn("Hide Comment", "Flag for Review"),
    **conn("Flag for Review", "Notify Admin"),
    **conn("Notify Admin", "Log Action"),
    **conn("Allow Content", "Log Action"),
}))

print("\nAll 22 workflow data files saved to:", DATA_DIR)
