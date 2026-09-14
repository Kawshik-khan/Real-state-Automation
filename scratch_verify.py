import json
import os

root = os.path.dirname(os.path.abspath(__file__))

def check():
    with open(os.path.join(root, "frontend/src/assets/baseline_eval_report.json"), "r", encoding="utf-8") as f:
        rep = json.load(f)
    print("Baseline report gates keys:", list(rep.get("gates", {}).keys()))
    print("Baseline report release_gates keys:", list(rep.get("release_gates", {}).keys()))
    print("Baseline report suites keys:", list(rep.get("suites", {}).keys()))
    print("All passed:", rep.get("all_passed"))
    print("Gate status:", rep.get("gate_status"))
    print("Summary:", rep.get("summary"))

    with open(os.path.join(root, "frontend/src/assets/benchmark_suites.json"), "r", encoding="utf-8") as f:
        suites = json.load(f)
    print("Suites loaded:", len(suites))
    for s in suites:
        print(f"  Suite {s['id']}: {len(s.get('cases', []))} cases")

if __name__ == "__main__":
    check()
