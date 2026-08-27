"""Benchmark script to test candidate models with high context and measure latency/health."""

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

CANDIDATE_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "cohere/north-mini-code:free",
    "poolside/laguna-s-2.1:free",
    "google/gemma-4-31b-it:free",
]

# Generate realistic high-context system & architecture text (~12,000 characters)
HIGH_CONTEXT_DATA = """
The enterprise system is an Education & College Library Management System with multi-campus circulation, automated book reservations, barcode and RFID scanner integration, role-based access control (Student, Faculty, Librarian, System Administrator), overdue fines management with online payment gateway integration, digital asset access (e-books, journals, research publications), audit logging, reporting dashboards, and real-time inventory tracking.

Key Functional Modules:
1. User Authentication & Profile Management: OAuth2 / OpenID Connect, JWT issuance, MFA for administrators, LDAP / Active Directory sync for college students and faculty members.
2. Catalog Management & Multi-Faceted Search: Elasticsearch or PostgreSQL full-text search indexing title, ISBN, author, Dewey Decimal class, subject tags, physical branch location, shelf ID, availability count.
3. Circulation & Borrowing Engine: Check-out, check-in, loan renewals, maximum borrowing limits per user category, due-date calculations excluding university holidays, reservation queues with automated notification triggers.
4. Fines & Penalty Management: Daily accrual calculation, waiver requests, Stripe / Razorpay payment gateway webhooks, automated receipt generation.
5. Digital Repository & Media Server: Secure presigned URL streaming for PDF e-books, watermarking, DRM enforcement, concurrent read limits.
6. System Analytics & Reporting: Borrowing trends, lost/damaged book rates, acquisition recommendations, monthly circulation summaries.

Non-Functional Requirements:
- Availability: 99.9% uptime with Multi-AZ RDS failover and container auto-scaling.
- Performance: p95 API response time <= 200ms for catalog search and <= 150ms for check-out operations.
- Security: End-to-end TLS 1.3, AES-256 encryption at rest for PII, OWASP Top 10 compliance, immutable audit logs.
- Scalability: Support up to 50,000 active concurrent students during exam seasons.
"""

USER_PROMPT = f"""
Given the following architecture requirements context:
{HIGH_CONTEXT_DATA * 3}

Generate a structured JSON response with:
1. "model_name": Name of the model
2. "status": "HEALTHY"
3. "system_name": Name of the system
4. "key_services": Array of 4 major backend service names
5. "recommended_database": Recommended DB engine and 2-sentence rationale
6. "architecture_pattern": Name of the architecture pattern

Respond strictly with valid JSON only. No markdown fences, no conversational prose.
"""

SYSTEM_PROMPT = "You are a Principal Software Architect. Always respond with strict, well-formed JSON matching the requested structure."

async def test_model(model: str) -> dict:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-architecture-platform.local",
        "X-Title": "Model Benchmark Test",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
    }

    t0 = time.perf_counter()
    status = "UNKNOWN"
    err = None
    char_len = 0
    parsed_json = None

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
            latency = round(time.perf_counter() - t0, 2)
            
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    status = "ERROR"
                    err = data["error"].get("message", str(data["error"]))
                else:
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        char_len = len(content)
                        try:
                            clean = content.strip()
                            if clean.startswith("```json"):
                                clean = clean[7:]
                            if clean.startswith("```"):
                                clean = clean[3:]
                            if clean.endswith("```"):
                                clean = clean[:-3]
                            parsed_json = json.loads(clean.strip())
                            status = "HEALTHY"
                        except Exception as parse_e:
                            status = "DEGRADED (JSON Parse Error)"
                            err = str(parse_e)
                    else:
                        status = "EMPTY_CHOICES"
            else:
                status = f"HTTP_{resp.status_code}"
                err = resp.text[:200]

    except Exception as exc:
        latency = round(time.perf_counter() - t0, 2)
        status = "EXCEPTION"
        err = str(exc)

    return {
        "model": model,
        "status": status,
        "latency_sec": latency,
        "output_chars": char_len,
        "chars_per_sec": round(char_len / max(latency, 0.01), 1),
        "error": err,
        "parsed_json": parsed_json,
    }

async def main():
    print("=" * 75)
    print(f" TESTING CANDIDATE MODELS WITH HIGH CONTEXT (~{len(USER_PROMPT)} chars)")
    print("=" * 75)
    
    results = []
    for model in CANDIDATE_MODELS:
        print(f"\n[*] Testing model: {model} ...", flush=True)
        res = await test_model(model)
        print(f"   Status     : {res['status']}")
        print(f"   Latency    : {res['latency_sec']}s")
        print(f"   Throughput : {res['chars_per_sec']} chars/sec ({res['output_chars']} chars)")
        if res['error']:
            print(f"   Error/Note : {res['error']}")
        results.append(res)

    print("\n" + "=" * 75)
    print(" BENCHMARK SUMMARY & RANKING")
    print("=" * 75)
    
    healthy = [r for r in results if r["status"] == "HEALTHY"]
    others = [r for r in results if r["status"] != "HEALTHY"]
    healthy.sort(key=lambda x: x["latency_sec"])

    print(f"{'Model':<52} | {'Status':<10} | {'Latency':<8} | {'Throughput'}")
    print("-" * 85)
    for r in healthy:
        print(f"{r['model']:<52} | {r['status']:<10} | {r['latency_sec']:>6.2f}s | {r['chars_per_sec']:>6.1f} c/s")
    for r in others:
        print(f"{r['model']:<52} | {r['status']:<10} | {r['latency_sec']:>6.2f}s | {r['chars_per_sec']:>6.1f} c/s")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(main())
