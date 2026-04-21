import argparse
import json
import random
import time
from pathlib import Path

import requests


GOALS = [
    "Build a scalable order management platform",
    "Design a secure telemedicine appointment system",
    "Create a high-throughput IoT analytics backend",
    "Develop a multi-tenant e-learning platform",
    "Build a resilient digital banking service",
    "Design an event-driven travel booking system",
]

SYSTEM_TYPES = [
    "web platform",
    "mobile and web platform",
    "microservices backend",
    "real-time distributed system",
    "multi-tenant SaaS",
]

ACTORS = [
    "customer",
    "admin",
    "operator",
    "partner",
    "support engineer",
    "finance team",
    "auditor",
    "content creator",
    "delivery agent",
]

FUNCTIONAL_REQUIREMENTS = [
    "user registration and login",
    "real-time notifications",
    "audit log export",
    "role based access control",
    "dashboard analytics",
    "workflow approval",
    "file upload and processing",
    "search and filtering",
    "payment processing",
    "webhook handling",
]

NFRS = [
    "99.9 availability",
    "p95 latency under 300ms",
    "horizontal scalability",
    "disaster recovery readiness",
    "observability and tracing",
    "data encryption in transit and at rest",
    "compliance friendly audit trails",
]

INPUTS = [
    "api requests",
    "event stream records",
    "csv uploads",
    "image metadata",
    "payment callbacks",
    "location updates",
]

OUTPUTS = [
    "status updates",
    "analytics reports",
    "billing records",
    "alerts",
    "email notifications",
    "webhook events",
]

EXTERNAL_SERVICES = [
    "payment gateway",
    "email provider",
    "sms gateway",
    "maps api",
    "identity provider",
    "object storage",
    "cache service",
]

OBJECTIVES = [
    "improve reliability",
    "reduce response time",
    "support global users",
    "enable secure integrations",
    "minimize operational overhead",
    "improve developer velocity",
]

BEHAVIORS = [
    "Asynchronous processing with eventual consistency for non-critical workflows",
    "Synchronous API path for user actions and async path for background workloads",
    "Real-time status updates with event-driven retries for failed operations",
]


def _pick_many(rng: random.Random, items: list[str], min_count: int, max_count: int) -> list[str]:
    count = rng.randint(min_count, max_count)
    return rng.sample(items, k=min(count, len(items)))


def generate_random_parameters(rng: random.Random) -> dict:
    return {
        "goal": {
            "value": rng.choice(GOALS),
            "ai_suggestion": None,
        },
        "core_objectives": {
            "value": _pick_many(rng, OBJECTIVES, 2, 4),
            "ai_suggestion": [],
        },
        "system_type": {
            "value": rng.choice(SYSTEM_TYPES),
            "ai_suggestion": None,
        },
        "actors": {
            "value": _pick_many(rng, ACTORS, 3, 6),
            "ai_suggestion": [],
        },
        "functional_requirements": {
            "value": _pick_many(rng, FUNCTIONAL_REQUIREMENTS, 4, 7),
            "ai_suggestion": [],
        },
        "inputs": {
            "value": _pick_many(rng, INPUTS, 2, 4),
            "ai_suggestion": [],
        },
        "outputs": {
            "value": _pick_many(rng, OUTPUTS, 2, 4),
            "ai_suggestion": [],
        },
        "external_services": {
            "value": _pick_many(rng, EXTERNAL_SERVICES, 2, 4),
            "ai_suggestion": [],
        },
        "system_behaviour": {
            "value": rng.choice(BEHAVIORS),
            "ai_suggestion": None,
        },
        "non_functional_requirements": {
            "value": _pick_many(rng, NFRS, 3, 5),
            "ai_suggestion": [],
        },
        "free_constraint": {
            "value": rng.choice([True, False]),
            "ai_suggestion": [],
        },
    }


def run_cases(base_url: str, cases: int, timeout: int, seed: int | None, reindex_first: bool) -> dict:
    rng = random.Random(seed)

    summary: dict = {
        "base_url": base_url,
        "cases": cases,
        "seed": seed,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": [],
    }

    health = requests.get(f"{base_url}/", timeout=15)
    health.raise_for_status()
    summary["health"] = health.json()

    if reindex_first:
        reindex_resp = requests.post(f"{base_url}/api/design/reindex", timeout=300)
        reindex_resp.raise_for_status()
        summary["reindex"] = reindex_resp.json()

    for case_id in range(1, cases + 1):
        parameters = generate_random_parameters(rng)
        payload = {"parameters": parameters, "design_output": {}}

        started = time.time()
        status_code = None
        response_data = None
        error = None

        try:
            response = requests.post(
                f"{base_url}/api/design",
                json=payload,
                timeout=timeout,
            )
            status_code = response.status_code
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"raw": response.text}
        except Exception as exc:
            error = str(exc)

        elapsed = round(time.time() - started, 2)

        result = {
            "case_id": case_id,
            "elapsed_seconds": elapsed,
            "status_code": status_code,
            "payload": payload,
            "response": response_data,
            "error": error,
        }
        summary["results"].append(result)

        if status_code == 200 and isinstance(response_data, dict):
            design_output = response_data.get("design_output", {})
            hld = design_output.get("high_level_design", {})
            architecture = hld.get("architecture", {}) if isinstance(hld, dict) else {}
            references = design_output.get("references", [])
            assumptions = design_output.get("assumptions", [])
            print(
                f"case {case_id}: status=200 elapsed={elapsed}s "
                f"architecture_type={architecture.get('type', 'N/A')} "
                f"references={len(references)} assumptions={len(assumptions)}"
            )
        else:
            print(f"case {case_id}: status={status_code} elapsed={elapsed}s error={error}")

    summary["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run randomized /api/design tests and save outputs.")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base API URL")
    parser.add_argument("--cases", type=int, default=3, help="Number of randomized test cases")
    parser.add_argument("--timeout", type=int, default=420, help="Per-request timeout in seconds")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    parser.add_argument(
        "--output",
        default="random_design_test_output.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--skip-reindex",
        action="store_true",
        help="Skip /api/design/reindex before tests",
    )

    args = parser.parse_args()

    report = run_cases(
        base_url=args.url.rstrip("/"),
        cases=max(1, args.cases),
        timeout=max(30, args.timeout),
        seed=args.seed,
        reindex_first=not args.skip_reindex,
    )

    output_path = Path(args.output)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"saved report to {output_path}")


if __name__ == "__main__":
    main()
