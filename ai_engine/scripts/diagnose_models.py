import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

test_key = os.getenv("OPENROUTER_API_KEY_1", "").strip()

models_to_test = [
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "liquid/lfm-2.5-2.6b:free",
    "poolside/laguna-xs-2.1:free",
    "thinkingmachines/inkling-small:free",
    "thinkingmachines/inkling:free",
    "openrouter/free",
]

print("=== BENCHMARKING ALL ACTIVE FREE MODELS ===")
for model in models_to_test:
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
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a JSON assistant. Output valid JSON only."},
                    {"role": "user", "content": "Return a JSON object with key 'status' equal to 'success' and 'message' equal to 'hello'."}
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 100,
                "temperature": 0.1,
            },
            timeout=15,
        )
        dt = time.time() - t0
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            print(f"[SUCCESS] {model:<46} | {dt:5.2f}s | {content.strip()[:70]}")
        else:
            print(f"[FAIL]    {model:<46} | {dt:5.2f}s | HTTP {r.status_code}: {r.text[:100]}")
    except requests.Timeout:
        print(f"[TIMEOUT] {model:<46} | > 15s TIMEOUT")
    except Exception as e:
        print(f"[ERROR]   {model:<46} | {e}")
