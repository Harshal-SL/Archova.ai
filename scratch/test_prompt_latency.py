import httpx
import json
import time
from Validator_Engine_v2.config import config
from Validator_Engine_v2.review.prompts import SYSTEM_PROMPT, build_review_user_prompt
from Validator_Engine_v2.review.reviewer import Reviewer

rev = Reviewer()
rubric = rev.rubrics.get("hld", {})

sample_hld = {
    "architecture_style": "Microservices",
    "major_services": [{"name": "AuthService", "protocol": "gRPC", "port": 50051}],
}

prompt, _ = build_review_user_prompt(
    artifact_name="hld",
    artifact_data=sample_hld,
    requirements_summary=[{"id": "FR-01", "text": "Authorize payment", "type": "functional"}],
    cac_summary={},
    reference_excerpts="",
    rubric=rubric,
)

models = [
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3.5-lightning:free",
    "openrouter/free",
    "liquid/lfm-2.5-2.6b:free",
]

headers = {
    "Authorization": f"Bearer {config.VALIDATOR_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://archova.ai",
    "X-Title": "Archova Validator Test",
}

for m in models:
    print(f"\n--- Testing model: {m} ---", flush=True)
    payload = {
        "model": m,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    t0 = time.time()
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            elapsed = time.time() - t0
            print(f"Status: {resp.status_code} in {elapsed:.2f}s", flush=True)
            if resp.status_code == 200:
                body = resp.json()
                content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"Response length: {len(content)} chars", flush=True)
                print(f"Preview:\n{content[:250]}...", flush=True)
                # Check if parseable as JSON
                try:
                    from Validator_Engine_v2.review.llm_client import _extract_first_json
                    parsed = _extract_first_json(content)
                    print(f"JSON parsed successfully: {parsed is not None and 'dimensions' in parsed}", flush=True)
                    if parsed:
                        print(f"Dimensions returned: {len(parsed.get('dimensions', []))}", flush=True)
                        print(f"Findings returned: {len(parsed.get('findings', []))}", flush=True)
                except Exception as pe:
                    print(f"Parse error: {pe}", flush=True)
            else:
                print(f"Error: {resp.text[:200]}", flush=True)
    except Exception as e:
        print(f"Exception after {time.time() - t0:.2f}s: {e}", flush=True)
