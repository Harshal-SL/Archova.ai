"""Live health check for user's exact 5 models."""
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
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "poolside/laguna-s-2.1:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
]

async def check(model: str):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Respond with valid JSON: {\"status\": \"ok\"}"},
            {"role": "user", "content": "Ping"}
        ],
        "temperature": 0.1,
        "max_tokens": 50,
    }
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
            lat = round(time.perf_counter() - t0, 2)
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    print(f"[ERROR 200] {model:<52} | Msg: {data['error']}")
                else:
                    print(f"[HEALTHY]   {model:<52} | Latency: {lat:>5.2f}s")
            elif resp.status_code == 429:
                print(f"[UPSTREAM 429] {model:<50} | {resp.text[:120]}")
            else:
                print(f"[HTTP {resp.status_code}]  {model:<50} | {resp.text[:120]}")
    except Exception as e:
        lat = round(time.perf_counter() - t0, 2)
        print(f"[TIMEOUT]   {model:<52} | Latency: {lat:>5.2f}s | {e}")

async def main():
    print("=" * 70)
    print(" LIVE STATUS CHECK ON USER'S 5 MODELS")
    print("=" * 70)
    for m in MODELS:
        await check(m)
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
