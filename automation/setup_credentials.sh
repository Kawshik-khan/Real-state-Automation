#!/bin/bash
# Create credential in local n8n using docker exec CLI
# Then wire it to all workflow HTTP nodes using the REST API with explicit auth header

N8N_URL="http://localhost:5678"

# Login and capture the auth cookie value
LOGIN_RESP=$(curl -s -c - -X POST "$N8N_URL/rest/login" \
  -H "Content-Type: application/json" \
  -d '{"emailOrLdapLoginId":"admin@glgassets.local","password":"Admin123!"}')
AUTH_TOKEN=$(echo "$LOGIN_RESP" | grep n8n-auth | awk '{print $NF}')
echo "✅ Logged in (token: ${AUTH_TOKEN:0:20}...)"

# Create credential via API with explicit auth header
echo "Creating credential..."
CRED_RESP=$(curl -s -X POST "$N8N_URL/rest/credentials" \
  -H "Content-Type: application/json" \
  -H "Cookie: n8n-auth=$AUTH_TOKEN" \
  -d '{
    "name": "Backend Automation Secret",
    "type": "httpHeaderAuth",
    "data": {
      "name": "X-Automation-Secret",
      "value": "3322af281a2b117d0694f8ff14c7c13c4115759904b6d3884f39b59ab51f3aa8"
    }
  }')
echo "  $CRED_RESP" | head -c 500
echo ""

CRED_ID=$(echo "$CRED_RESP" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$CRED_ID" ]; then
  echo "✅ Credential ID: $CRED_ID"
  
  # Now check if any existing credential was returned instead
  # Try to find it if the response format differs
else
  # Maybe the credential already exists - find it
  echo "  Checking existing credentials..."
  CREDS_RESP=$(curl -s -X GET "$N8N_URL/rest/credentials" \
    -H "Cookie: n8n-auth=$AUTH_TOKEN")
  CRED_ID=$(echo "$CREDS_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('data', []):
    if c.get('type') == 'httpHeaderAuth':
        print(c['id'])
        break
" 2>/dev/null)
  if [ -n "$CRED_ID" ]; then
    echo "✅ Found existing credential: $CRED_ID"
  else
    echo "❌ Cannot find/create credential"
    echo "Response: $CREDS_RESP" | head -c 300
    exit 1
  fi
fi

# Get all workflows
echo ""
echo "Fetching workflows..."
curl -s -X GET "$N8N_URL/rest/workflows?limit=50" \
  -H "Cookie: n8n-auth=$AUTH_TOKEN" > /tmp/n8n_workflows.json

# Process each workflow
echo ""
echo "=== Wiring credentials to HTTP nodes ==="
python3 -c "
import json, requests

BASE = '$N8N_URL'
CRED_ID = '$CRED_ID'
HEADERS = {'Content-Type': 'application/json', 'Cookie': 'n8n-auth=$AUTH_TOKEN'}

with open('/tmp/n8n_workflows.json') as f:
    data = json.load(f)

updated = 0
for wf in data.get('data', []):
    wf_id = wf['id']
    name = wf['name']
    
    r = requests.get(f'{BASE}/rest/workflows/{wf_id}', headers=HEADERS)
    if r.status_code != 200:
        continue
    full = r.json().get('data', {})
    nodes = full.get('nodes', [])
    
    changed = False
    for node in nodes:
        if node.get('type') != 'n8n-nodes-base.httpRequest':
            continue
        creds = node.get('credentials', {})
        if 'httpHeaderAuth' not in creds:
            node['credentials'] = {
                'httpHeaderAuth': {
                    'id': CRED_ID,
                    'name': 'Backend Automation Secret'
                }
            }
            changed = True
    
    if not changed:
        continue
    
    r2 = requests.patch(f'{BASE}/rest/workflows/{wf_id}', 
        headers=HEADERS, json={'nodes': nodes})
    if r2.status_code in (200, 201):
        http_count = sum(1 for n in nodes if n.get('type') == 'n8n-nodes-base.httpRequest')
        print(f'  🔌  {name} — wired {http_count} HTTP nodes')
        updated += 1
    else:
        print(f'  ❌  {name}: {r2.status_code} {r2.text[:100]}')

print(f\"\\n=== Updated {updated} workflows ===\")
"
