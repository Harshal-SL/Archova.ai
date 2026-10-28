import asyncio
import json
import time
from Validator_Engine_v2.config import config
from Validator_Engine_v2.l0_normalize.normalizer import PackageNormalizer
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient
from Validator_Engine_v2.review.reviewer import Reviewer

async def main():
    print(f"Key configured: {bool(config.VALIDATOR_API_KEY)} (len={len(config.VALIDATOR_API_KEY)})", flush=True)
    print(f"Primary model: {config.VALIDATOR_MODEL}", flush=True)
    print(f"Fallbacks: {config.VALIDATOR_FALLBACK_MODELS}", flush=True)

    client = ReviewerLLMClient(
        mock_mode="0",
        model=config.VALIDATOR_MODEL,
        api_key=config.VALIDATOR_API_KEY,
        timeout=35.0,
    )

    sample_package = {
        "generation_id": "gen_live_001",
        "system_name": "PaymentApp",
        "domain": "Fintech",
        "requirements": [
            {"id": "FR-01", "text": "Authorize payment", "type": "functional"}
        ],
        "hld": {
            "architecture_style": "Microservices",
            "major_services": [{"name": "AuthService", "protocol": "gRPC", "port": 50051}],
        },
        "llds": {}
    }

    norm = PackageNormalizer().normalize(sample_package)
    reviewer = Reviewer(llm_client=client)

    print("\nStarting review_artifact for HLD...", flush=True)
    t0 = time.time()
    try:
        res = await asyncio.wait_for(
            reviewer.review_artifact(
                artifact_name="hld",
                artifact_data=sample_package["hld"],
                normalized_pkg=norm,
                reviewer_mode="live",
            ),
            timeout=40.0
        )
        print(f"Completed in {time.time() - t0:.2f}s!", flush=True)
        print(f"Verdict: {res.verdict}", flush=True)
        print(f"Score: {res.score}", flush=True)
        print(f"Model: {res.model_used}", flush=True)
        print(f"Dimensions: {len(res.dimensions)}", flush=True)
        print(f"Findings: {len(res.findings)}", flush=True)
    except asyncio.TimeoutError:
        print(f"review_artifact timed out after {time.time() - t0:.2f}s", flush=True)
    except Exception as e:
        print(f"Exception: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
