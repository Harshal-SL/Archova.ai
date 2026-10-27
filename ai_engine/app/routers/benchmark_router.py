"""FastAPI Router for Multi-Model Architecture Benchmarking.

Allows generating architectures directly via single-shot baseline LLMs,
validating each through the independent Validator Engine, and returning
in-detail comparative scorecards and metric matrices against Archova AI Engine.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status

from app.schemas.benchmark_schemas import (
    BenchmarkModelConfig,
    BenchmarkRequest,
    BenchmarkResponse,
)
from app.services.direct_llm_generator import direct_llm_generator
from app.services.generation_service import generation_service

logger = logging.getLogger(__name__)

import os

router = APIRouter(prefix="/api/v1/benchmark", tags=["Benchmark & Comparison"])


def get_env_benchmark_models() -> List[BenchmarkModelConfig]:
    """Retrieve exactly the 3 baseline LLM models configured in .env for comparison with Archova."""
    m1_name = os.getenv("BENCHMARK_MODEL_1_NAME", "Gemini").strip()
    m1_id = os.getenv("BENCHMARK_MODEL_1_ID", "gemini-3.5-flash").strip()
    m1_key = os.getenv("BENCHMARK_MODEL_1_API_KEY", "").strip() or None
    m1_base = os.getenv("BENCHMARK_MODEL_1_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai").strip() or None

    m2_name = os.getenv("BENCHMARK_MODEL_2_NAME", "ChatGPT").strip()
    m2_id = os.getenv("BENCHMARK_MODEL_2_ID", "openai/gpt-oss-120b").strip()
    m2_key = os.getenv("BENCHMARK_MODEL_2_API_KEY", "").strip() or None
    m2_base = os.getenv("BENCHMARK_MODEL_2_BASE_URL", "https://api.groq.com/openai/v1").strip() or None

    m3_name = os.getenv("BENCHMARK_MODEL_3_NAME", "Nvidia").strip()
    m3_id = os.getenv("BENCHMARK_MODEL_3_ID", "nvidia/nemotron-3.5-lightning:free").strip()
    m3_key = os.getenv("BENCHMARK_MODEL_3_API_KEY", "").strip() or None
    m3_base = os.getenv("BENCHMARK_MODEL_3_BASE_URL", "https://openrouter.ai/api/v1").strip() or None

    return [
        BenchmarkModelConfig(id="model-gemini", name=m1_name, model_id=m1_id, api_key=m1_key, base_url=m1_base, provider="gemini"),
        BenchmarkModelConfig(id="model-chatgpt", name=m2_name, model_id=m2_id, api_key=m2_key, base_url=m2_base, provider="groq"),
        BenchmarkModelConfig(id="model-nvidia", name=m3_name, model_id=m3_id, api_key=m3_key, base_url=m3_base, provider="openrouter"),
    ]


@router.get("/presets", response_model=List[BenchmarkModelConfig], summary="Get candidate LLM models from .env")
def get_benchmark_presets() -> List[BenchmarkModelConfig]:
    """Retrieve the 3 baseline models configured in .env for direct 1-shot benchmarking."""
    return get_env_benchmark_models()


@router.post("/generate", response_model=BenchmarkResponse, summary="Execute direct 1-shot LLM generation and comparative audit")
async def generate_benchmark(payload: BenchmarkRequest) -> BenchmarkResponse:
    """Accepts a prompt and list of LLM models. Executes strictly 1 single-shot LLM call per model,
    audits all models with the Validator Engine, and synthesizes a head-to-head comparison against Archova.
    """
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requirements prompt cannot be empty.",
        )

    # Use specified models or fallback to the 3 models configured in .env
    env_models = get_env_benchmark_models()
    if payload.models and len(payload.models) > 0:
        target_models = []
        for i, m in enumerate(payload.models):
            # If API key is omitted in payload, populate from .env counterpart if available
            env_key = env_models[i].api_key if i < len(env_models) else None
            m_copy = m.model_copy()
            if not m_copy.api_key:
                m_copy.api_key = env_key
            target_models.append(m_copy)
    else:
        target_models = env_models


    # Attempt to retrieve Archova package if generation_id is provided
    archova_pkg: Optional[Dict[str, Any]] = None
    archova_val: Optional[Dict[str, Any]] = None

    if payload.generation_id:
        try:
            archova_pkg = generation_service.get_package(payload.generation_id)
            context = generation_service.get_context(payload.generation_id)
            # Retrieve validated architecture if already run
            out_dir = generation_service._get_output_dir(payload.generation_id)
            val_file = out_dir / "11_validated_architecture.json"
            if val_file.exists():
                import json
                with open(val_file, "r", encoding="utf-8") as f:
                    archova_val = json.load(f)
        except Exception as exc:
            logger.warning("Could not fetch existing generation package for '%s': %s", payload.generation_id, exc)

    try:
        response = await direct_llm_generator.run_benchmark(
            prompt=payload.prompt,
            models=target_models,
            archova_package=archova_pkg,
            archova_validation=archova_val,
        )
        response.generation_id = payload.generation_id
        return response
    except Exception as exc:
        logger.exception("Benchmark execution failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark generation failed: {str(exc)}",
        ) from exc
