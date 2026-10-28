"""Pydantic Contracts for Targeted AI Architecture Correction (Part 2.2.2)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class CorrectionApprovalRequest(BaseModel):
    """Payload to register an explicit user approval on a correction finding."""
    generation_id: str = Field(..., description="Active generation or session ID")
    finding_id: str = Field(..., description="Original validator finding ID approved by user")
    artifact_type: str = Field(..., description="Target artifact type (e.g. 'hld', 'backend', 'database')")
    source_version: str = Field(default="v1.0", description="Source architecture version tag")
    approved_by: Optional[str] = Field(default="user", description="Authorizing user or role")
    notes: Optional[str] = Field(default=None, description="Optional user approval notes")


class CorrectionApprovalResponse(BaseModel):
    """Response confirming that an approval has been securely recorded on the backend."""
    generation_id: str
    finding_id: str
    artifact_type: str
    source_version: str
    approved: bool = True
    approved_at: str
    message: str = "Finding approval recorded successfully."


class VerificationResult(BaseModel):
    """Automated backend-side verification result for the proposed correction."""
    is_valid: bool = Field(..., description="True if proposed correction passes structural & safety checks")
    checks_passed: List[str] = Field(default_factory=list)
    checks_failed: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    baseline_preservation_score: float = Field(default=1.0, ge=0.0, le=1.0)
    unrelated_keys_preserved: bool = True


class TargetedCorrectionRequest(BaseModel):
    """Payload to request targeted AI correction of an approved architecture defect."""
    model_config = ConfigDict(protected_namespaces=())

    generation_id: str = Field(..., description="Active generation or session ID")
    artifact_type: str = Field(..., description="Affected artifact identifier (e.g. 'backend', 'database', 'hld', 'frontend', 'security', 'cloud', 'arsrs')")
    source_version: str = Field(..., description="Source artifact version (e.g. 'v1.0' or '1.0')")
    finding_id: str = Field(..., description="Approved finding ID from Validator Engine v2")
    finding_description: str = Field(..., description="Description of the defect")
    evidence: str = Field(..., description="Evidence path or anchor from Validator Engine")
    correction_instruction: str = Field(..., description="Specific localized correction instruction")
    reason: Optional[str] = Field(default=None, description="Architectural rationale for the correction")
    affected_target: Optional[str] = Field(default=None, description="Component, service, or table targeted")
    dependencies: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Downstream dependent artifacts")
    baseline_package: Optional[Dict[str, Any]] = Field(default=None, description="Optional full architecture package for context")
    simulated_corrected_artifact: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional pre-formed corrected artifact for deterministic unit testing without external LLM call",
    )


class TargetedCorrectionResponse(BaseModel):
    """Response containing proposed correction draft, change summary, and verification."""
    model_config = ConfigDict(protected_namespaces=())

    operation_id: str
    status: Literal["CORRECTION_PROPOSED", "CORRECTION_VERIFIED", "MANUAL_REVIEW_REQUIRED", "CORRECTION_FAILED"]
    generation_id: str
    source_version: str
    artifact_type: str
    finding_id: str
    change_summary: str
    explanation: str
    original_artifact: Dict[str, Any]
    corrected_artifact: Dict[str, Any]
    verification_result: VerificationResult
    unresolved_issues: Optional[List[str]] = Field(default_factory=list)
    created_at: str


class AcceptCorrectionRequest(BaseModel):
    """Payload to accept a proposed correction draft and commit it as a new version."""
    expected_source_version: Optional[str] = Field(default=None, description="Verification that source version hasn't changed")
    target_version: Optional[str] = Field(default=None, description="Optional explicit version bump (e.g. 'v1.1')")
    generation_id: Optional[str] = Field(default=None, description="Optional generation or session ID validation")


class AcceptCorrectionResponse(BaseModel):
    """Response confirming that the correction was accepted and committed."""
    operation_id: str
    status: Literal["ACCEPTED"] = "ACCEPTED"
    new_version: str
    previous_version: str
    artifact_type: str
    updated_artifact: Dict[str, Any]
    updated_package: Optional[Dict[str, Any]] = None
    accepted_at: str
    message: str = "Correction accepted successfully. New artifact version created."


class RejectCorrectionResponse(BaseModel):
    """Response confirming that the correction was rejected, preserving original artifact."""
    operation_id: str
    status: Literal["REJECTED"] = "REJECTED"
    message: str = "Correction draft rejected by user. Original artifact remains unchanged."
    rejected_at: str
