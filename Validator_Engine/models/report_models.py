"""Report Data Models for Multi-Dimensional Validation Subsystems."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from .finding_models import ValidationFinding


class StructuralValidationReport(BaseModel):
    """Report for structural integrity, missing sections, and formatting checks."""
    model_config = ConfigDict(extra="allow")

    is_valid: bool = Field(default=True)
    score: float = Field(default=1.0)
    missing_sections: List[str] = Field(default_factory=list)
    malformed_elements: List[str] = Field(default_factory=list)
    placeholder_items: List[Dict[str, Any]] = Field(default_factory=list)
    placeholder_violations: List[Dict[str, str]] = Field(default_factory=list)
    orphan_components: List[str] = Field(default_factory=list)
    boilerplate_warnings: List[str] = Field(default_factory=list)
    findings: List[ValidationFinding] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class RequirementTraceabilityItem(BaseModel):
    """Traceability mapping for an individual requirement."""
    model_config = ConfigDict(extra="allow")

    requirement_id: str
    title: str = ""
    category: str = "functional"  # functional | non_functional | constraint
    satisfied_by_services: List[str] = Field(default_factory=list)
    satisfied_by_endpoints: List[str] = Field(default_factory=list)
    satisfied_by_tables: List[str] = Field(default_factory=list)
    satisfied_by_components: List[str] = Field(default_factory=list)
    status: str = "FULLY_SATISFIED"  # FULLY_SATISFIED | PARTIALLY_SATISFIED | UNTRACED
    notes: Optional[str] = None


class RequirementAlignmentReport(BaseModel):
    """Report measuring requirement-to-architecture satisfaction."""
    model_config = ConfigDict(extra="allow")

    is_valid: bool = Field(default=True)
    is_aligned: bool = Field(default=True)
    score: float = Field(default=1.0)
    alignment_score: float = Field(default=1.0)
    total_requirements: int = 0
    covered_requirements_count: int = 0
    uncovered_requirements_count: int = 0
    uncovered_requirement_ids: List[str] = Field(default_factory=list)
    untraced_requirement_ids: List[str] = Field(default_factory=list)
    traceability_ratio: float = Field(default=1.0)
    traceability_matrix: List[Any] = Field(default_factory=list)
    findings: List[ValidationFinding] = Field(default_factory=list)


class CrossArtifactConsistencyReport(BaseModel):
    """Multi-artifact consistency verification report."""
    model_config = ConfigDict(extra="allow")

    is_valid: bool = Field(default=True)
    is_consistent: bool = Field(default=True)
    score: float = Field(default=1.0)
    consistency_score: float = Field(default=1.0)
    hld_to_backend_alignment: float = 1.0
    backend_to_database_alignment: float = 1.0
    frontend_to_backend_alignment: float = 1.0
    security_to_backend_alignment: float = 1.0
    cloud_to_architecture_alignment: float = 1.0
    inconsistencies: List[Dict[str, Any]] = Field(default_factory=list)
    missing_links: List[str] = Field(default_factory=list)
    unknown_requirement_ids: List[str] = Field(default_factory=list)
    unknown_api_operations: List[str] = Field(default_factory=list)
    missing_entity_mappings: List[str] = Field(default_factory=list)
    findings: List[ValidationFinding] = Field(default_factory=list)


class NFRValidationItem(BaseModel):
    """Validation evaluation for a specific NFR category."""
    model_config = ConfigDict(extra="allow")

    nfr_category: str = ""  # latency, throughput, availability, scalability, security, compliance
    declared_target: str = ""
    architectural_support: str = "SUPPORTED"  # SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | AT_RISK
    mechanisms_identified: List[str] = Field(default_factory=list)
    evaluation_notes: str = ""


class NFRValidationReport(BaseModel):
    """Report evaluating non-functional requirements against architectural choices."""
    model_config = ConfigDict(extra="allow")

    is_valid: bool = Field(default=True)
    score: float = Field(default=1.0)
    feasibility_score: float = Field(default=1.0)
    total_nfrs: int = 0
    supported_nfrs_count: int = 0
    partially_supported_count: int = 0
    unsupported_nfrs_count: int = 0
    nfr_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    evaluated_nfrs: List[Any] = Field(default_factory=list)
    identified_bottlenecks: List[str] = Field(default_factory=list)
    findings: List[ValidationFinding] = Field(default_factory=list)


class RealWorldArchetypeMatch(BaseModel):
    """Evidence comparison against a Category 10 real-world production system."""
    model_config = ConfigDict(extra="allow")

    reference_system: str = ""
    domain: str = ""
    relevance_reason: str = ""
    structural_comparison: str = ""
    supporting_patterns: List[str] = Field(default_factory=list)
    cautionary_failure_modes: List[str] = Field(default_factory=list)
    recommended_guardrails: List[str] = Field(default_factory=list)


class RealWorldEvidenceReport(BaseModel):
    """Contextual evidence report benchmarking against real-world production designs."""
    model_config = ConfigDict(extra="allow")

    is_valid: bool = Field(default=True)
    has_evidence: bool = Field(default=True)
    score: float = Field(default=0.85)
    evidence_quality_score: float = Field(default=0.85)
    primary_archetype: str = "Standard Distributed Architecture"
    matched_systems: List[Dict[str, Any]] = Field(default_factory=list)
    matched_archetypes: List[Any] = Field(default_factory=list)
    trade_off_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    failure_mode_risks: List[Dict[str, Any]] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    findings: List[ValidationFinding] = Field(default_factory=list)


class RedTeamReviewReport(BaseModel):
    """Adversarial Red-Team audit of vulnerabilities, single points of failure, and risks."""
    model_config = ConfigDict(extra="allow")

    is_valid: bool = Field(default=True)
    score: float = Field(default=1.0)
    verdict: str = "APPROVED"  # APPROVED | APPROVED_WITH_CONDITIONS | NEEDS_REMEDIATION | REJECTED
    review_status: str = "PASSED"  # PASSED | PASSED_WITH_CONDITIONS | REJECTED
    single_points_of_failure: List[Dict[str, Any]] = Field(default_factory=list)
    scalability_bottlenecks: List[Dict[str, Any]] = Field(default_factory=list)
    untested_assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_risks: List[Dict[str, Any]] = Field(default_factory=list)
    security_vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    production_readiness_verdict: str = "APPROVED"
    findings: List[ValidationFinding] = Field(default_factory=list)


class DecisionProvenanceItem(BaseModel):
    """Explainability record explaining why an architectural decision was made."""
    model_config = ConfigDict(extra="allow")

    decision_id: str
    topic: str = ""
    decision_title: str = ""
    decision_type: str = "style"  # style | database | cache | auth | cloud | messaging
    chosen_option: str = ""
    selected_option: str = ""
    rationale: str = ""
    why_chosen: str = ""
    traced_requirements: List[str] = Field(default_factory=list)
    driving_requirements: List[str] = Field(default_factory=list)
    driving_constraints: List[str] = Field(default_factory=list)
    trade_offs_considered: List[str] = Field(default_factory=list)
    rejected_alternatives: List[str] = Field(default_factory=list)
    alternatives_considered: List[str] = Field(default_factory=list)
    real_world_precedent: str = ""
    supporting_real_world_evidence: str = ""
    validation_status: str = "VALIDATED"  # VALIDATED | WARNING | DEFICIENT
    trade_offs: Dict[str, Any] = Field(default_factory=dict)


class RemediationAction(BaseModel):
    """Targeted corrective action addressing a validation finding."""
    model_config = ConfigDict(extra="allow")

    action_id: str
    priority: str = "P1"  # P0 | P1 | P2
    finding_id: str = ""
    category: str = ""
    severity: str = "HIGH"
    target_component: str = ""
    target_artifact: str = ""  # hld | backend_lld | database_lld | security_lld | cloud_lld
    issue_summary: str = ""
    title: str = ""
    description: str = ""
    recommendation: str = ""
    revalidation_criteria: str = ""
    recommended_patch: Dict[str, Any] = Field(default_factory=dict)


class RemediationPlan(BaseModel):
    """Actionable remediation plan addressing all actionable findings."""
    model_config = ConfigDict(extra="allow")

    verdict: str = "APPROVED"
    total_findings: int = 0
    total_findings_count: int = 0
    critical_findings_count: int = 0
    affected_components: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    remediation_actions: List[Any] = Field(default_factory=list)
    suggested_patches: Dict[str, Any] = Field(default_factory=dict)
    remediation_summary: str = ""


class UnifiedScorecard(BaseModel):
    """Unified multi-tier architectural quality and readiness scorecard."""
    model_config = ConfigDict(extra="allow")

    status: str = Field(..., description="HEALTHY | DEGRADED | NEEDS_REMEDIATION | FAILED")
    overall_composite_score: float = Field(..., description="Balanced composite 0.0 to 1.0")
    structural_completeness: float = Field(..., description="Field population ratio 0.0 to 1.0")
    artifact_quality_score: float = Field(..., description="Semantic content quality 0.0 to 1.0")
    consistency_score: float = Field(..., description="Cross-artifact alignment score 0.0 to 1.0")
    requirement_alignment_score: float = Field(default=1.0, description="Requirement satisfaction ratio 0.0 to 1.0")
    production_readiness_score: float = Field(..., description="Production readiness score 0.0 to 1.0")
    traceability_score: float = Field(default=1.0)
    evidence_support_score: float = Field(default=0.85)
    hard_gates: Dict[str, bool] = Field(default_factory=dict)
    hard_gates_passed: bool = Field(default=True)
    hard_gate_violations: List[str] = Field(default_factory=list)
    per_section_scores: Dict[str, float] = Field(default_factory=dict)
    quality_indicators: Dict[str, Any] = Field(default_factory=dict)


class CorrectionFeedbackItem(BaseModel):
    """Structured defect feedback instructing the AI Engine on targeted architectural correction."""
    model_config = ConfigDict(extra="allow")

    issue_id: str = Field(..., description="Unique ID of the finding or defect")
    issue_identified: str = Field(..., description="Summary of the issue identified")
    missing_or_incorrect_detail: str = Field(..., description="Specific missing component or incorrect detail")
    affected_artifact: str = Field(..., description="Target artifact: backend_lld | database_lld | security_lld | cloud_lld | frontend_lld | hld")
    affected_requirement_id: Optional[str] = Field(default=None, description="Affected FR or NFR if traceable")
    affected_component: str = Field(..., description="Component or module name")
    severity: str = Field(default="HIGH", description="Severity: CRITICAL | HIGH | MEDIUM | LOW")
    recommended_correction: str = Field(..., description="Concrete, actionable correction guidance")
    rag_evidence: Optional[str] = Field(default=None, description="Relevant evidence retrieved from RAG")
    suggested_patch: Optional[Dict[str, Any]] = Field(default=None, description="Structured patch dictionary")


class ArchitectureCorrectionFeedback(BaseModel):
    """Feedback payload bundle passed to the AI Engine for targeted architecture correction."""
    model_config = ConfigDict(extra="allow")

    package_id: str
    generation_id: Optional[str] = None
    attempt: int = 1
    total_issues: int = 0
    critical_issues_count: int = 0
    high_issues_count: int = 0
    items: List[CorrectionFeedbackItem] = Field(default_factory=list)
    affected_artifacts: List[str] = Field(default_factory=list)
    summary: str = ""


class CorrectionAttemptRecord(BaseModel):
    """Audit record of a single validation & correction iteration."""
    model_config = ConfigDict(extra="allow")

    attempt: int
    timestamp: str
    findings_count_before: int
    findings_count_after: int
    resolved_issue_ids: List[str] = Field(default_factory=list)
    unresolved_issue_ids: List[str] = Field(default_factory=list)
    regenerated_artifacts: List[str] = Field(default_factory=list)
    summary: str = ""

