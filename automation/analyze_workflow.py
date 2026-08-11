import json, re, sys

# Read the saved file
with open('C:/Users/Kawshik Khan/AppData/Local/hermes/cache/terminal/hermes-results/call_00_WOauC9Aup5O0eKeeqZYj5801.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Find node entries
nodes = re.findall(r'\{\"parameters\":\{.*?\},\"id\":\"[^\"]+\",\"name\":\"([^\"]+)\",\"type\":\"([^\"]+)\"', text)

print(f'Total nodes: {len(nodes)}')

# Group by workstream prefix
workstreams = {}
all_types = {}
for name, ntype in nodes:
    short = ntype.replace('n8n-nodes-base.', '')
    all_types[short] = all_types.get(short, 0) + 1
    parts = name.split('|')
    if len(parts) >= 2:
        ws_key = parts[0].strip()
        ws_name = parts[1].strip()
        if ws_key not in workstreams:
            workstreams[ws_key] = {'name': ws_name, 'count': 0, 'types': {}}
        workstreams[ws_key]['count'] += 1
        workstreams[ws_key]['types'][short] = workstreams[ws_key]['types'].get(short, 0) + 1

# Find URLs
urls = re.findall(r'\"url\":\"([^\"]+?)\"', text)
unique_urls = {}
for u in urls:
    unique_urls[u] = unique_urls.get(u, 0) + 1

# Check auth
auth_count = text.count('httpHeaderAuth')
noauth_count = text.count('"authentication":"none"')

print(f'\n=== ALL NODE TYPES ===')
for t, c in sorted(all_types.items(), key=lambda x: -x[1]):
    print(f'  {t}: {c}')

print(f'\n=== WORKSTREAMS ({len(workstreams)}) ===')
for ws_key in sorted(workstreams.keys(), key=lambda x: int(x) if x.isdigit() else 999):
    ws = workstreams[ws_key]
    types_str = ', '.join([f'{k}x{v}' if v>1 else k for k,v in sorted(ws['types'].items(), key=lambda x: -x[1])])
    print(f'  {ws_key} | {ws["name"]}: {ws["count"]} nodes [{types_str}]')

print(f'\n=== URL TARGETS ({len(unique_urls)}) ===')
for u, c in sorted(unique_urls.items(), key=lambda x: -x[1]):
    print(f'  [{c}x] {u}')

print(f'\n=== AUTH ===')
print(f'  httpHeaderAuth appearances: {auth_count}')
print(f'  authentication:none appearances: {noauth_count}')
