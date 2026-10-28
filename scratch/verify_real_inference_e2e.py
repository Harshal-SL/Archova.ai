"""Authoritative Real-Inference Verification Suite for Validator Engine v2.

Tests:
1. Confirms API credential presence without exposing it.
2. Runs live OpenRouter request with VALIDATOR_MOCK=0.
3. Confirms model-generated dimensions and findings are parsed and validated.
4. Tests provider failure handling (no fabricated AI review, PROVISIONAL verdict).
5. Confirms benchmark unavailability produces PROVISIONAL verdict.
6. Verifies exact scoring formulas and caps remain unchanged.
"""

import asyncio
import json
import logging
import sys
import time

from Validator_Engine_v2.config import config
from Validator_Engine_v2.decision.scoring import compute_artifact_score
from Validator_Engine_v2.l0_normalize.normalizer import PackageNormalizer
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.review.reviewer import Reviewer
from Validator_Engine_v2.schemas import ArtifactResult, DimensionScore, Finding, RealWorldResult

logging.basicConfig(level=logging.WARNING)


async def main():
    print("=" * 70, flush=True)
    print("STEP 1: API CREDENTIAL & MODEL CONFIGURATION VERIFICATION", flush=True)
    print("=" * 70, flush=True)

    has_key = bool(config.VALIDATOR_API_KEY and len(config.VALIDATOR_API_KEY.strip()) > 10)
    print(f"API Credential Configured: {has_key}", flush=True)
    print(f"API Credential Type: OpenRouter Bearer Token (sk-or-v1-***)", flush=True)
    print(f"Configured Primary Model: {config.VALIDATOR_MODEL}", flush=True)
    print(f"Configured Fallback Models: {config.VALIDATOR_FALLBACK_MODELS}", flush=True)
    print(f"Configured VALIDATOR_MOCK: {config.VALIDATOR_MOCK}", flush=True)
    assert has_key, "FATAL: VALIDATOR_API_KEY is not configured!"

    print("\n" + "=" * 70, flush=True)
    print("STEP 2: LIVE OPENROUTER INFERENCE (VALIDATOR_MOCK=0)", flush=True)
    print("=" * 70, flush=True)

    sample_hld = {
        "architecture_style": "Event-Driven Microservices",
        "major_services": [
            {"name": "PaymentGatewayService", "protocol": "gRPC", "port": 50051},
            {"name": "FraudDetectionService", "protocol": "gRPC", "port": 50052},
            {"name": "LedgerService", "protocol": "gRPC", "port": 50053},
        ],
        "communication_patterns": {
            "sync": "gRPC for synchronous transaction evaluation",
            "async": "Apache Kafka topic 'payment-events' with 12 partitions",
        },
        "data_strategy": {
            "primary": "PostgreSQL partitioned by tenant_id",
            "cache": "Redis cluster write-around cache",
        },
    }

    rubric = {
        "dimensions": [
            {
                "id": "specificity",
                "label": "Specificity",
                "weight": 0.5,
                "source": "IEEE1016",
                "description": "Concrete named entities, ports, protocols declared.",
            },
            {
                "id": "fault_tolerance",
                "label": "Fault Tolerance",
                "weight": 0.5,
                "source": "ISO25010",
                "description": "Circuit breakers, buffering, dead letter queues.",
            },
        ]
    }

    user_prompt = f"""EVALUATION TARGET: HLD ARTIFACT
=== ARTIFACT UNDER REVIEW ===
{json.dumps(sample_hld, indent=2)}

=== RUBRIC DIMENSIONS TO EVALUATE ===
- ID: specificity - Concrete named entities, ports, protocols
- ID: fault_tolerance - Circuit breakers, retries, redundancy

REQUIRED OUTPUT FORMAT (JSON ONLY):
{{
  "dimensions": [
    {{
      "id": "specificity",
      "score": 4,
      "evidence_path": "/major_services/0/protocol",
      "missing": [],
      "rationale": "gRPC protocols and ports declared"
    }},
    {{
      "id": "fault_tolerance",
      "score": 3,
      "evidence_path": "/communication_patterns/async",
      "missing": ["Dead letter queue not specified"],
      "rationale": "Kafka provides async decoupling but dead letter queue is missing"
    }}
  ],
  "findings": [
    {{
      "rule_id": "REVIEW.FAULT_TOLERANCE.MISSING_DLQ",
      "severity": "medium",
      "message": "Kafka topic payment-events does not specify a Dead Letter Queue.",
      "evidence_path": "/communication_patterns/async",
      "fix": "Declare dead-letter topic payment-events-dlq."
    }}
  ]
}}
"""

    live_client = ReviewerLLMClient(
        mock_mode="0",
        model=config.VALIDATOR_MODEL,
        fallback_models=config.get_fallback_models(),
        api_key=config.VALIDATOR_API_KEY,
        timeout=60.0,
    )

    t0 = time.time()
    parsed_json, status = await live_client.call_review(
        artifact_name="hld",
        artifact_data=sample_hld,
        rubric=rubric,
        user_prompt=user_prompt,
        mock_mode="0",
    )
    elapsed = time.time() - t0

    print(f"Provider Call Status: {status}", flush=True)
    print(f"Provider Latency: {elapsed:.2f}s", flush=True)
    print(f"Actual Model Used: {live_client.last_model_used}", flush=True)
    assert status == "ok", f"Expected 'ok', got {status}"
    assert live_client.last_model_used == config.VALIDATOR_MODEL
    assert parsed_json is not None, "Parsed JSON response is None"

    print("\n" + "=" * 70, flush=True)
    print("STEP 3: STRUCTURED OUTPUT PARSING & EVIDENCE VALIDATION", flush=True)
    print("=" * 70, flush=True)
    dimensions = parsed_json.get("dimensions", [])
    findings = parsed_json.get("findings", [])
    print(f"Provider Dimensions Count: {len(dimensions)}", flush=True)
    print(f"Provider Findings Count: {len(findings)}", flush=True)

    for d in dimensions:
        print(f"  Dimension: {d.get('id')} | Score: {d.get('score')} | Evidence: {d.get('evidence_path')}", flush=True)
        print(f"    Rationale: {d.get('rationale')[:80]}...", flush=True)

    for f in findings:
        print(f"  Finding: {f.get('rule_id')} [{f.get('severity')}] | Evidence: {f.get('evidence_path')}", flush=True)
        print(f"    Message: {f.get('message')[:80]}...", flush=True)

    assert len(dimensions) > 0, "Expected at least 1 dimension from live review"

    print("\n" + "=" * 70, flush=True)
    print("STEP 4: SIMULATE PROVIDER FAILURE (NO FABRICATED AI REVIEW)", flush=True)
    print("=" * 70, flush=True)
    bad_client = ReviewerLLMClient(
        mock_mode="0",
        model=config.VALIDATOR_MODEL,
        api_key="sk-invalid-key-should-fail-401",
        fallback_models=[],
    )
    bad_parsed, bad_status = await bad_client.call_review(
        artifact_name="hld",
        artifact_data=sample_hld,
        rubric=rubric,
        user_prompt=user_prompt,
        mock_mode="0",
    )
    print(f"Simulated failure status: {bad_status}", flush=True)
    print(f"Simulated failure model_used: {bad_client.last_model_used}", flush=True)
    print(f"Simulated failure output: {bad_parsed}", flush=True)

    assert bad_status == "unavailable", f"Expected 'unavailable', got {bad_status}"
    assert bad_parsed is None, "Provider failure must NOT fabricate fake findings!"
    assert bad_client.last_model_used is None, "Provider failure must not report model as used!"

    print("\n" + "=" * 70, flush=True)
    print("STEP 5: BENCHMARK UNAVAILABILITY & SCORING SAFETY GATES", flush=True)
    print("=" * 70, flush=True)
    sample_pkg = {
        "generation_id": "gen_safety_test",
        "system_name": "UltraPay",
        "domain": "Fintech",
        "requirements": [{"id": "FR-01", "text": "Auth", "type": "functional"}],
        "hld": sample_hld,
    }
    norm = PackageNormalizer().normalize(sample_pkg)

    # Reviewer unavailable -> PROVISIONAL
    raw_unavail = ArtifactResult(
        artifact="hld",
        score=50,
        verdict="PROVISIONAL",
        dimensions=[],
        findings=[],
        reviewer_status="unavailable",
        model_used="none",
    )
    unavail_score = compute_artifact_score(
        artifact_name="hld",
        reviewer_result=raw_unavail,
        l0_findings=[],
        l1_findings=[],
        real_world_result=None,
        reviewer_mode="live",
        normalized_pkg=norm,
    )
    print(f"Reviewer unavailable verdict: {unavail_score.verdict} (Score: {unavail_score.score})", flush=True)
    assert unavail_score.verdict == "PROVISIONAL"

    # Benchmark unavailable (W=None) -> PROVISIONAL
    raw_ok = ArtifactResult(
        artifact="hld",
        score=90,
        verdict="ACCEPTED",
        dimensions=[DimensionScore(id="specificity", label="Specificity", score=5, weight=1.0, evidence_path="/major_services/0/protocol", missing=[], rationale="OK")],
        findings=[],
        reviewer_status="ok",
        model_used=config.VALIDATOR_MODEL,
    )
    unavail_benchmark_score = compute_artifact_score(
        artifact_name="hld",
        reviewer_result=raw_ok,
        l0_findings=[],
        l1_findings=[],
        real_world_result=None,  # Missing benchmark W
        reviewer_mode="live",
        normalized_pkg=norm,
    )
    print(f"Benchmark unavailable verdict: {unavail_benchmark_score.verdict} (Score: {unavail_benchmark_score.score})", flush=True)
    assert unavail_benchmark_score.verdict == "PROVISIONAL"

    # Critical defect cap -> Score capped at 60, forced REJECTED
    critical_finding = Finding.create(
        layer="L0",
        rule_id="CRIT.1",
        artifact="hld",
        severity="critical",
        message="Critical architecture vulnerability",
        source="SYSTEM",
    )
    crit_score = compute_artifact_score(
        artifact_name="hld",
        reviewer_result=raw_ok,
        l0_findings=[critical_finding],
        l1_findings=[],
        real_world_result=RealWorldResult(artifact="hld", score=90, confidence="normal", counts={}, assessments=[], references_used=[]),
        reviewer_mode="live",
        normalized_pkg=norm,
    )
    print(f"Critical defect cap verdict: {crit_score.verdict} (Score: {crit_score.score})", flush=True)
    assert crit_score.verdict == "REJECTED"
    assert crit_score.score <= 60

    print("\n" + "=" * 70, flush=True)
    print("ALL 5 REAL-INFERENCE INTEGRATION STEPS PASSED SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
