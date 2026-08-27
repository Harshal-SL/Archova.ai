"""LLM Connectivity & Health Check Test Suite.

Tests whether the configured LLM provider (OpenRouter) is working correctly
across both REE (LLMGateway / OpenRouterClient) and SAE (OpenRouterProvider) pipelines.

Usage:
    Direct execution:
        python tests/test_llm.py

    Via pytest:
        pytest tests/test_llm.py -v
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

# Ensure project root is in Python module search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.model_config import MODEL_CONFIG, get_model_for_capability
from app.ree.llm import llm_gateway, OpenRouterClient
from app.sae.providers.llm_provider import OpenRouterProvider


class LLMHealthCheckResponse(BaseModel):
    """Pydantic model for structured response testing."""
    status: str = Field(description="Operational status, e.g. OK")
    message: str = Field(description="Brief health check message")
    echo_test: str = Field(description="Echo payload to verify reasoning accuracy")


def mask_api_key(key: str) -> str:
    """Safely mask API key for console output."""
    if not key:
        return "[NOT SET]"
    if len(key) <= 8:
        return "****"
    return f"{key[:6]}...{key[-4:]}"


def test_01_environment_config() -> bool:
    """Test 1: Check environment variables and model configuration loading."""
    print("\n" + "=" * 60)
    print(" [TEST 1] Environment & LLM Configuration Check")
    print("=" * 60)

    api_key = MODEL_CONFIG.api_key
    provider = MODEL_CONFIG.provider
    default_model = MODEL_CONFIG.default_model

    print(f"  • Provider            : {provider}")
    print(f"  • API Key             : {mask_api_key(api_key)}")
    print(f"  • Default Model       : {default_model}")
    print(f"  • Timeout (sec)       : {MODEL_CONFIG.timeout}")
    print(f"  • Reasoning Model     : {get_model_for_capability('reasoning')}")
    print(f"  • Architecture Model  : {get_model_for_capability('hld')}")

    if not api_key:
        print("\n  ❌ FAIL: OPENROUTER_API_KEY is not set in environment or .env file.")
        print("     Please set OPENROUTER_API_KEY in your .env file to enable LLM features.")
        return False

    print("  ✓ PASS: Configuration and API key detected.")
    return True


def test_02_openrouter_client_ping() -> bool:
    """Test 2: Direct ping to OpenRouter API via OpenRouterClient."""
    print("\n" + "=" * 60)
    print(" [TEST 2] OpenRouter Direct Client Ping Test")
    print("=" * 60)

    api_key = MODEL_CONFIG.api_key
    if not api_key:
        print("  ⚠️ SKIP: API Key missing.")
        return False

    model = MODEL_CONFIG.default_model
    client = OpenRouterClient()

    prompt = "Respond with exactly one word: PONG"
    print(f"  • Target Model : {model}")
    print(f"  • Prompt       : '{prompt}'")

    start_time = time.time()
    try:
        response_text = client.complete(
            prompt=prompt,
            model=model,
            temperature=0.0,
            max_tokens=20,
            json_mode=False,
        )
        elapsed = round(time.time() - start_time, 2)
        cleaned_resp = response_text.strip()
        print(f"  • Response     : '{cleaned_resp}'")
        print(f"  • Latency      : {elapsed}s")

        assert len(cleaned_resp) > 0, "Response string was empty"
        print("  ✓ PASS: Direct OpenRouterClient ping succeeded.")
        return True

    except Exception as exc:
        elapsed = round(time.time() - start_time, 2)
        print(f"  ❌ FAIL: OpenRouter API call failed after {elapsed}s.")
        print(f"     Error details: {exc}")
        return False


def test_03_ree_llm_gateway() -> bool:
    """Test 3: REE LLMGateway capability resolution and completion."""
    print("\n" + "=" * 60)
    print(" [TEST 3] REE LLM Gateway Capability Completion Test")
    print("=" * 60)

    api_key = MODEL_CONFIG.api_key
    if not api_key:
        print("  ⚠️ SKIP: API Key missing.")
        return False

    capability = "reasoning"
    prompt = """Return a valid JSON object with the following schema:
{
  "status": "OK",
  "message": "REE Gateway operational",
  "echo_test": "hello_ree"
}"""

    print(f"  • Capability : '{capability}'")
    start_time = time.time()

    try:
        res = llm_gateway.complete(
            capability=capability,
            prompt=prompt,
            max_tokens=150,
        )
        elapsed = round(time.time() - start_time, 2)
        print(f"  • Result     : {json.dumps(res, indent=2)}")
        print(f"  • Latency    : {elapsed}s")

        assert res is not None, "Gateway returned None"
        assert isinstance(res, dict), "Result is not a dictionary"
        print("  ✓ PASS: REE LLMGateway completion succeeded.")
        return True

    except Exception as exc:
        elapsed = round(time.time() - start_time, 2)
        print(f"  ❌ FAIL: REE LLMGateway failed after {elapsed}s.")
        print(f"     Error details: {exc}")
        return False


def test_04_sae_provider_structured() -> bool:
    """Test 4: SAE OpenRouterProvider structured completion test."""
    print("\n" + "=" * 60)
    print(" [TEST 4] SAE OpenRouterProvider Structured Completion Test")
    print("=" * 60)

    api_key = MODEL_CONFIG.api_key
    if not api_key:
        print("  ⚠️ SKIP: API Key missing.")
        return False

    provider = OpenRouterProvider()
    model = get_model_for_capability("hld")
    prompt = "Perform a self health check. Return status as OK, message as SAE Provider operational, and echo_test as hello_sae."

    print(f"  • Target Model : {model}")
    start_time = time.time()

    try:
        structured_resp: LLMHealthCheckResponse = provider.generate_structured(
            prompt=prompt,
            model_name=model,
            response_model=LLMHealthCheckResponse,
            temperature=0.1,
            system_prompt="You are a system diagnostic bot.",
        )
        elapsed = round(time.time() - start_time, 2)

        print(f"  • Parsed Model : {structured_resp}")
        print(f"  • Status       : {structured_resp.status}")
        print(f"  • Message      : {structured_resp.message}")
        print(f"  • Echo Test    : {structured_resp.echo_test}")
        print(f"  • Latency      : {elapsed}s")

        assert structured_resp.status.upper() in ["OK", "SUCCESS", "PASS", "HEALTHY", "TRUE"], (
            f"Unexpected status: {structured_resp.status}"
        )
        print("  ✓ PASS: SAE OpenRouterProvider structured response succeeded.")
        return True

    except Exception as exc:
        elapsed = round(time.time() - start_time, 2)
        print(f"  ❌ FAIL: SAE OpenRouterProvider failed after {elapsed}s.")
        print(f"     Error details: {exc}")
        return False


def main() -> int:
    """Run all LLM diagnostic test steps."""
    print("\n" + "#" * 60)
    print("      AI ENGINE - LLM HEALTH & CONNECTIVITY TEST SUITE")
    print("#" * 60)

    results = []

    # Step 1: Config
    c1 = test_01_environment_config()
    results.append(("Config & Key Detection", c1))

    if not c1:
        print("\n❌ ABORTING: Fix environment configuration / OPENROUTER_API_KEY before running live tests.")
        return 1

    # Step 2: OpenRouter Client Ping
    c2 = test_02_openrouter_client_ping()
    results.append(("OpenRouter Direct Ping", c2))

    # Step 3: REE Gateway
    c3 = test_03_ree_llm_gateway()
    results.append(("REE LLM Gateway", c3))

    # Step 4: SAE Provider
    c4 = test_04_sae_provider_structured()
    results.append(("SAE Structured Provider", c4))

    # Summary Table
    print("\n" + "=" * 60)
    print(" TEST SUMMARY RESULT")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status_str = "✓ PASSED" if passed else "❌ FAILED"
        if not passed:
            all_passed = False
        print(f"  {name:<30}: {status_str}")

    print("=" * 60)
    if all_passed:
        print(" SUCCESS: All LLM connectivity tests passed! LLM is fully working.")
        return 0
    else:
        print(" FAILURE: One or more LLM connectivity tests failed. Check logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
