import os
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)
key = os.getenv("OPENROUTER_API_KEY_1", "").strip()

def test_call(model, json_mode=False, max_tokens=1500):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a software architect. Output ONLY a valid JSON object with keys: 'summary', 'actors', 'components'. Do not use markdown fences."},
            {"role": "user", "content": "Analyze an IoT Smart Parking system. Keep it concise."}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    t0 = time.time()
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        dt = time.time() - t0
        print(f"\nModel: {model} (json_mode={json_mode}) -> HTTP {r.status_code} in {dt:.2f}s")
        if r.status_code == 200:
            data = r.json()
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = msg.get("content") or msg.get("reasoning") or choice.get("text") or ""
            print(f"Content preview ({len(content)} chars): {content[:150]}...")
            s = content.find("{")
            e = content.rfind("}")
            if s != -1 and e != -1:
                try:
                    p = json.loads(content[s:e+1])
                    print(f"Parsed JSON successfully! Keys: {list(p.keys())}")
                    return True
                except Exception as ex:
                    print(f"JSON load failed: {ex}")
            else:
                print("No JSON brackets found!")
        else:
            print(f"Error body: {r.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    return False

print("--- Testing cohere/north-mini-code:free ---")
test_call("cohere/north-mini-code:free", json_mode=False)
test_call("cohere/north-mini-code:free", json_mode=True)

print("--- Testing nvidia/nemotron-3-super-120b-a12b:free ---")
test_call("nvidia/nemotron-3-super-120b-a12b:free", json_mode=False)
test_call("nvidia/nemotron-3-super-120b-a12b:free", json_mode=True)

print("--- Testing openrouter/free ---")
test_call("openrouter/free", json_mode=False)
test_call("openrouter/free", json_mode=True)

print("--- Testing liquid/lfm-2.5-2.6b:free ---")
test_call("liquid/lfm-2.5-2.6b:free", json_mode=False)
test_call("liquid/lfm-2.5-2.6b:free", json_mode=True)
