"""Test all 7 user-provided free models."""
import asyncio
import json
import os
import time
from pathlib import Path
import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")

MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-31b-it:free",
    "poolside/laguna-s-2.1:free",
    "nvidia/nemotron-3.5-lightning:free",
]

async def check(model: str):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Respond with strict JSON: {\"status\": \"ok\", \"agent\": \"ready\"}"},
            {"role": "user", "content": "Ping test for system architecture readiness."}
        ],
        "temperature": 0.1,
        "max_tokens": 150,
    }
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
            lat = round(time.perf_counter() - t0, 2)
            if resp.status_code == 200:
                print(f"[HEALTHY] {model:<50} | Latency: {lat:>5.2f}s")
                return model, True, lat
            else:
                print(f"[FAILED]  {model:<50} | HTTP {resp.status_code}: {resp.text[:80]}")
                return model, False, lat
    except Exception as e:
        lat = round(time.perf_counter() - t0, 2)
        print(f"[TIMEOUT] {model:<50} | Latency: {lat:>5.2f}s | {e}")
        return model, False, lat

async def main():
    print("Testing all 7 user candidate models...")
    tasks = [check(m) for m in MODELS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
