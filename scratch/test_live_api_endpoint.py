import urllib.request
import json
import time
from pathlib import Path

def main():
    pkg_path = Path("Validator_Engine_v2/tests/fixtures/sample_package.json")
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))

    req_data = json.dumps(pkg).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8002/v1/validate",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    print("Sending real HTTP POST to http://127.0.0.1:8002/v1/validate with VALIDATOR_MOCK=0...")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            dur = time.time() - t0
            res = json.loads(resp.read().decode("utf-8"))
            print(f"HTTP Status: {resp.status} (elapsed: {dur:.2f}s)")
            print(f"Status: {res.get('status')}")
            print(f"Verdict: {res.get('verdict')}")
            print(f"Scores: {res.get('scores')}")
            artifacts = res.get("artifacts", {})
            print(f"Artifacts evaluated ({len(artifacts)}): {list(artifacts.keys())}")
            print(f"Total findings: {len(res.get('findings', []))}")
            for k, art in artifacts.items():
                print(f"  Artifact {k}: Score={art.get('score')}, Verdict={art.get('verdict')}, Findings={len(art.get('findings', []))}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
