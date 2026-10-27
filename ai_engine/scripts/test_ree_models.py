import os
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

test_key = os.getenv("OPENROUTER_API_KEY_1", "").strip()

models = [
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "liquid/lfm-2.5-2.6b:free",
    "openrouter/free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]

sample_prompt = """PROJECT DESCRIPTION:
Build an Online Event Management System for university hackathons with registration, submission judging, and live notifications.

Extract business_goals, business_rules, constraints, stakeholders, kpis, pain_points, priorities.
Return valid JSON:
{
  "business_goals": {"value": ["..."], "ai_suggestion": []},
  "business_rules": {"value": ["..."], "ai_suggestion": []},
  "constraints": {"value": ["..."], "ai_suggestion": []},
  "stakeholders": {"value": ["..."], "ai_suggestion": []},
  "kpis": {"value": ["..."], "ai_suggestion": []},
  "pain_points": {"value": ["..."], "ai_suggestion": []},
  "priorities": {"value": ["..."], "ai_suggestion": []}
}
"""

print("=== TESTING MODELS ON REE BUSINESS ANALYST PROMPT ===")
for m in models:
    t0 = time.time()
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {test_key}",
                "HTTP-Referer": "https://archova.ai",
                "X-Title": "Archova",
            },
            json={
                "model": m,
                "messages": [
                    {"role": "system", "content": "You are a Business Analyst. Return raw JSON only."},
                    {"role": "user", "content": sample_prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.1,
            },
            timeout=25,
        )
        dt = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = msg.get("content") or msg.get("reasoning") or choice.get("text") or ""
            # verify JSON
            clean = content.replace("```json", "").replace("```", "").strip()
            # find first { and last }
            s = clean.find("{")
            e = clean.rfind("}")
            if s != -1 and e != -1:
                try:
                    parsed = json.loads(clean[s:e+1])
                    keys_found = list(parsed.keys())
                    print(f"[OK] {m:<45} | {dt:5.2f}s | Parsed JSON keys: {keys_found[:4]}")
                except Exception as je:
                    print(f"[WARN] {m:<45} | {dt:5.2f}s | JSON parse error: {je} | Raw: {clean[:80]}")
            else:
                print(f"[NO_JSON] {m:<45} | {dt:5.2f}s | Raw: {clean[:80]}")
        else:
            print(f"[FAIL] {m:<45} | {dt:5.2f}s | HTTP {r.status_code}: {r.text[:100]}")
    except requests.Timeout:
        print(f"[TIMEOUT] {m:<45} | >25s TIMEOUT")
    except Exception as e:
        print(f"[ERR]  {m:<45} | {e}")
