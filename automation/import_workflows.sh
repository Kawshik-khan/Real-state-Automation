#!/bin/bash
# Simple import using curl only
N8N_URL="http://localhost:5678"
COOKIE_JAR="/tmp/n8n_cookies2.txt"

# Login
curl -s -c "$COOKIE_JAR" -X POST "$N8N_URL/rest/login" \
  -H "Content-Type: application/json" \
  -d '{"emailOrLdapLoginId":"admin@glgassets.local","password":"Admin123!"}' > /dev/null

echo "Logged in."

# Get existing workflow names
EXISTING=$(curl -s -b "$COOKIE_JAR" "$N8N_URL/rest/workflows" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
echo "Existing:"
echo "$EXISTING" | sed 's/^/  /'

DATA_DIR="/d/Softwear Project/Realstate Automation/automation/02-modular/workflow-data"
IMPORTED=0; SKIPPED=0; FAILED=0

echo ""
echo "=== Importing ==="
for f in "$DATA_DIR"/*.json; do
  name=$(python3 -c "import json; print(json.load(open('$f'))['name'])" 2>/dev/null || basename "$f" .json)
  
  # Check if name already exists
  if echo "$EXISTING" | grep -qFx "$name"; then
    echo "  ⏭  $name"
    SKIPPED=$((SKIPPED+1))
    continue
  fi
  
  echo -n "  ● $name ... "
  RESP=$(curl -s -b "$COOKIE_JAR" -X POST "$N8N_URL/rest/workflows" \
    -H "Content-Type: application/json" \
    -d @"$f")
  
  if echo "$RESP" | grep -q '"id"'; then
    id=$(echo "$RESP" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "✓ $id"
    IMPORTED=$((IMPORTED+1))
  else
    echo "✗"
    echo "  $RESP" | head -c 300
    FAILED=$((FAILED+1))
  fi
  
  sleep 0.2
done

echo ""
echo "=== DONE: $IMPORTED imported | $SKIPPED skipped | $FAILED failed ==="
