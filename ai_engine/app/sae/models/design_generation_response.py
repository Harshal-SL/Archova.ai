"""Models for unified design generation request and API response payload."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DesignGenerationRequest(BaseModel):
    """Payload model for unified design generation API request."""

    input_type: str = Field(default="text", description="Input type: text, markdown, pdf, docx, image, user_story")
    content: Optional[str] = Field(default=None, description="Direct text or markdown content string")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata context")


class GeneratedOutputsManifest(BaseModel):
    """Manifest of generated output files and directories."""

    output_directory: str = ""
    json_files: List[str] = Field(default_factory=list)
    markdown_files: List[str] = Field(default_factory=list)
    html_report: str = ""


class DesignGenerationResponse(BaseModel):
    """Unified production API response containing complete REE ARSRS and SAE Architecture Package."""

    status: str = Field(default="SUCCESS", description="Execution status: SUCCESS or FAILED")
    request_id: str = Field(default="", description="Unique request execution identifier")
    stage: Optional[str] = Field(default=None, description="Stage identifier if failed (e.g. REE, SAE)")
    message: Optional[str] = Field(default=None, description="Summary or error message")
    arsrs: Dict[str, Any] = Field(default_factory=dict, description="Generated ARSRS specification from REE")
    software_architecture_package: Dict[str, Any] = Field(default_factory=dict, description="Complete Software Architecture Package from SAE")
    generated_outputs: GeneratedOutputsManifest = Field(default_factory=GeneratedOutputsManifest)
    quality_report: Dict[str, Any] = Field(default_factory=dict, description="7-dimension architectural quality report")
    decision_traceability: List[Dict[str, Any]] = Field(default_factory=list, description="Requirement and RAG decision provenance mapping")
    reference_architecture: Dict[str, Any] = Field(default_factory=dict, description="Weighted RAG production reference system analysis")
    execution_metrics: Dict[str, Any] = Field(default_factory=dict, description="REE, SAE, and total execution duration and resource metrics")
    errors: List[str] = Field(default_factory=list, description="Detailed error trace if execution failed")
