"""Fetch recent runs from LangSmith project to verify trace logging."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
load_dotenv(backend_dir / ".env")

from langsmith import Client  # noqa: E402

client = Client()
project_name = os.getenv("LANGSMITH_PROJECT", "glg-assets-ai-os")

print(f"Fetching recent traces from LangSmith project: '{project_name}'...\n")
try:
    runs = list(client.list_runs(project_name=project_name, limit=5))
    print(f"Total traces recorded in '{project_name}': {len(runs)}\n")
    for idx, r in enumerate(runs, 1):
        print(f"[{idx}] Trace Run ID: {r.id}")
        print(f"    Name: {r.name}")
        print(f"    Run Type: {r.run_type}")
        print(f"    Status: {r.status}")
        print(f"    Execution Time: {r.end_time - r.start_time if r.end_time and r.start_time else 'N/A'}")
        if r.error:
            print(f"    Error: {r.error}")
        print(f"    Direct Run Link: https://smith.langchain.com/o/b24ab78d-5b5d-4140-8b1b-275e5f37f1da/projects/p/{project_name}/r/{r.id}")
        print("-" * 60)
except Exception as e:
    print(f"Error fetching runs: {e}")
