"""Pydantic schemas for Multi-Model Architecture Benchmarking."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BenchmarkModelConfig(BaseModel):
    """Configuration for an individual LLM model benchmarked against Archova."""

    id: str = Field(description="Unique local identifier, e.g. 'gpt-4o' or 'claude-3-5-sonnet'")
    name: str = Field(description="Human-readable display name, e.g. 'OpenAI GPT-4o'")
    model_id: str = Field(description="Provider model slug, e.g. 'openai/gpt-4o' or 'anthropic/claude-3.5-sonnet'")
    api_key: Optional[str] = Field(default=None, description="Custom API key (if provided by user)")
    provider: Optional[str] = Field(default="openrouter", description="Provider type, e.g. 'openrouter' or 'direct'")
    base_url: Optional[str] = Field(default=None, description="Custom API base URL (if any)")


class BenchmarkRequest(BaseModel):
    """Payload to initiate direct LLM generation and comparative validation."""

    prompt: str = Field(description="User architecture problem statement / requirements prompt")
    generation_id: Optional[str] = Field(default=None, description="Existing Archova generation ID to link with")
    models: List[BenchmarkModelConfig] = Field(
        default_factory=list,
        description="List of external LLM models to benchmark (single 1-shot call each)",
    )


class ModelBenchmarkResult(BaseModel):
    """Results of a single direct LLM generation and verification pass."""

    model_id: str
    model_name: str
    is_archova: bool = False
    status: str = "COMPLETED"  # COMPLETED | FAILED
    error: Optional[str] = None
    latency_ms: float = 0.0
    package: Dict[str, Any] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)


class QualityGateComparison(BaseModel):
    """Comparative gate status across models."""

    gate_name: str
    archova: bool
    models: Dict[str, bool] = Field(default_factory=dict)


class MetricComparison(BaseModel):
    """Individual comparative score dimension."""

    metric_name: str
    archova_score: float
    model_scores: Dict[str, float] = Field(default_factory=dict)


class BenchmarkComparisonSummary(BaseModel):
    """Aggregated comparison report between Archova AI Engine and benchmarked LLMs."""

    system_name: str
    timestamp: str
    archova_verdict: str
    archova_score: float
    models_evaluated: int
    quality_gates: List[QualityGateComparison] = Field(default_factory=list)
    metrics_matrix: List[MetricComparison] = Field(default_factory=list)
    component_counts: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    findings_summary: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    key_findings_differentiators: List[str] = Field(default_factory=list)


class BenchmarkResponse(BaseModel):
    """Complete response returned by the benchmark engine."""

    generation_id: Optional[str] = None
    prompt: str
    archova: Optional[ModelBenchmarkResult] = None
    models: List[ModelBenchmarkResult] = Field(default_factory=list)
    comparison: BenchmarkComparisonSummary
