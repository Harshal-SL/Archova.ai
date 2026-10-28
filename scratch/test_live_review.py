import asyncio
import json
import logging
from pathlib import Path

from Validator_Engine_v2.config import config
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.review.prompts import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)

async def test_live_call():
    env_path = Path("Validator_Engine_v2/.env")
    key = None
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("VALIDATOR_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break

    client = ReviewerLLMClient(
        api_base="https://openrouter.ai/api/v1",
        api_key=key,
        model="cohere/north-mini-code:free",
        fallback_models=[
            "nvidia/nemotron-3.5-lightning:free",
            "openrouter/free",
            "liquid/lfm-2.5-2.6b:free",
        ],
        mock_mode="0",
        timeout=45.0,
    )

    artifact_data = {
        "architecture_style": "Event-Driven Microservices",
        "major_services": [
            {"name": "PaymentGatewayService", "protocol": "gRPC", "port": 50051},
            {"name": "FraudDetectionService", "protocol": "gRPC", "port": 50052},
            {"name": "NotificationService", "protocol": "AMQP", "port": 5672},
        ],
        "communication_patterns": {
            "sync": "gRPC for low-latency critical path payment evaluation",
            "async": "Apache Kafka topic 'payment-events' partitioned by account_id",
        },
        "data_strategy": {
            "primary": "PostgreSQL partitioned by tenant_id with Citus extension",
            "cache": "Redis cluster with write-around caching",
        },
    }

    rubric = {
        "dimensions": [
            {
                "id": "specificity",
                "label": "Specificity",
                "weight": 0.25,
                "source": "IEEE1016",
                "description": "Concrete names, ports, protocols, and exact parameters rather than generic statements.",
            },
            {
                "id": "fault_tolerance",
                "label": "Fault Tolerance",
                "weight": 0.25,
                "source": "ISO25010",
                "description": "Circuit breakers, fallbacks, dead letter queues, and partition tolerance.",
            },
        ]
    }

    user_prompt = f"""EVALUATION TARGET: HLD ARTIFACT

=== ARTIFACT UNDER REVIEW ===
{json.dumps(artifact_data, indent=2)}

=== RUBRIC DIMENSIONS TO EVALUATE ===
- ID: specificity (Weight: 0.25) - Concrete named entities, ports, protocols
- ID: fault_tolerance (Weight: 0.25) - Circuit breakers, retries, redundancy

REQUIRED OUTPUT FORMAT (JSON ONLY):
{{
  "dimensions": [
    {{
      "id": "specificity",
      "score": 4,
      "evidence_path": "/major_services/0/protocol",
      "missing": [],
      "rationale": "Clear specific ports and protocols defined."
    }},
    {{
      "id": "fault_tolerance",
      "score": 3,
      "evidence_path": "/communication_patterns/async",
      "missing": ["Dead letter queue for Kafka not mentioned"],
      "rationale": "Kafka event-driven decoupling provides buffering but DLQ is missing."
    }}
  ],
  "findings": [
    {{
      "rule_id": "REVIEW.FAULT_TOLERANCE.MISSING_DLQ",
      "severity": "medium",
      "message": "Kafka topic payment-events does not specify a Dead Letter Queue mechanism.",
      "evidence_path": "/communication_patterns/async",
      "fix": "Declare a dead-letter topic 'payment-events-dlq' with retry policy."
    }}
  ]
}}
"""

    print("Sending live call to ReviewerLLMClient...")
    parsed_out, status = await client.call_review(
        artifact_name="hld",
        artifact_data=artifact_data,
        rubric=rubric,
        user_prompt=user_prompt,
    )

    print(f"Status: {status}")
    print(f"Model used: {client.last_model_used}")
    if parsed_out:
        print("Parsed JSON dimensions count:", len(parsed_out.get("dimensions", [])))
        print("Parsed JSON findings count:", len(parsed_out.get("findings", [])))
        print("Dimensions:", json.dumps(parsed_out.get("dimensions"), indent=2))
        print("Findings:", json.dumps(parsed_out.get("findings"), indent=2))
    else:
        print("Failed to get parsed JSON.")

if __name__ == "__main__":
    asyncio.run(test_live_call())
