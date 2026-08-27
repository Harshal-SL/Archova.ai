"""Unified Design Generation Context shared between REE and SAE."""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DesignGenerationContext(BaseModel):
    """Shared in-memory context carrying state across REE and SAE pipeline execution."""

    request_id: str = Field(default_factory=lambda: f"req_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    design_id: str = Field(default_factory=lambda: f"design_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    input_type: str = "text"
    raw_input: Any = ""
    uploaded_files: List[str] = Field(default_factory=list)
    normalized_input: str = ""

    # REE Outputs
    structured_requirements: Dict[str, Any] = Field(default_factory=dict)
    arsrs: Dict[str, Any] = Field(default_factory=dict)

    # SAE Core Section Outputs
    requirement_analysis: Dict[str, Any] = Field(default_factory=dict)
    technology_recommendation: Dict[str, Any] = Field(default_factory=dict)
    architecture_plan: Dict[str, Any] = Field(default_factory=dict)
    hld: Dict[str, Any] = Field(default_factory=dict)
    backend_lld: Dict[str, Any] = Field(default_factory=dict)
    database_lld: Dict[str, Any] = Field(default_factory=dict)
    frontend_lld: Dict[str, Any] = Field(default_factory=dict)
    security_lld: Dict[str, Any] = Field(default_factory=dict)
    cloud_lld: Dict[str, Any] = Field(default_factory=dict)
    validation_report: Dict[str, Any] = Field(default_factory=dict)
    merged_package: Dict[str, Any] = Field(default_factory=dict)
    evolution_package: Dict[str, Any] = Field(default_factory=dict)
    software_architecture_package: Dict[str, Any] = Field(default_factory=dict)

    # Post-Processing & Quality Outputs
    reference_architecture: Dict[str, Any] = Field(default_factory=dict)
    decision_traceability: List[Dict[str, Any]] = Field(default_factory=list)
    quality_report: Dict[str, Any] = Field(default_factory=dict)
    completeness_report: Dict[str, Any] = Field(default_factory=dict)

    # Metrics, Manifest & Status
    execution_metrics: Dict[str, Any] = Field(default_factory=dict)
    output_directory: str = ""
    generated_files: List[str] = Field(default_factory=list)
    status: str = "PENDING"
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
