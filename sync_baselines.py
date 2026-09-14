import json
import os

root = os.path.dirname(os.path.abspath(__file__))

report_path = os.path.join(root, ".benchmarks/reports/latest_report.json")
with open(report_path, "r", encoding="utf-8") as f:
    data = json.load(f)

if "release_gates" in data and "gates" not in data:
    data["gates"] = data["release_gates"]

destinations = [
    os.path.join(root, ".benchmarks/reports/latest_report.json"),
    os.path.join(root, "backend/app/evals/latest_report_baseline.json"),
    os.path.join(root, "frontend/src/assets/baseline_eval_report.json"),
]

for dest in destinations:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Synced {os.path.relpath(dest, root)} ({os.path.getsize(dest)} bytes)")
