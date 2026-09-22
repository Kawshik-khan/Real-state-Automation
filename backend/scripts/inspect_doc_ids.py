import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {"apikey": key, "Authorization": f"Bearer {key}"}

r = requests.get(f"{url}/rest/v1/knowledge_chunks?select=doc_id,filename&limit=2000", headers=headers)
if r.status_code in (200, 206):
    rows = r.json()
    doc_map = {}
    for row in rows:
        d = row.get("doc_id")
        f = row.get("filename")
        if d not in doc_map:
            doc_map[d] = {"filename": f, "count": 0}
        doc_map[d]["count"] += 1
    print(f"Total distinct doc_ids in Supabase ({len(doc_map)}):")
    for d, info in sorted(doc_map.items()):
        cnt = info['count']
        fname = info['filename']
        print(f"  • {d:<25}: {cnt:>4} chunks | {fname}")
