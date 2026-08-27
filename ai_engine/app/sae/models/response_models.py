"""Flat SAE Response Models — max 2 levels of nesting.

Design principle: top-level fields are typed for structural validation,
nested content uses Dict[str, Any] / List[Dict[str, Any]] to give the LLM
freedom to generate rich content without fighting field-by-field schema
validation. This keeps the JSON schema under 500 bytes (vs 15KB+ before).

SafeBaseModel safely coerces None values to field defaults so LLM nulls
do not cause validation crashes.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


# ─── Safe Base Model ─────────────────────────────────────────────────────────

class SafeBaseModel(BaseModel):
    """Base model that safely coerces None values to field defaults."""
    rag_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _coerce_none_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = {}
        for k, v in data.items():
            if v is None and k in cls.model_fields:
                field_info = cls.model_fields[k]
                if field_info.default is not None and field_info.default is not ...:
                    cleaned[k] = field_info.default
                elif field_info.default_factory is not None:
                    cleaned[k] = field_info.default_factory()
                else:
                    cleaned[k] = None
            else:
                cleaned[k] = v
        return cleaned


# ─── Requirement Analysis ────────────────────────────────────────────────────

class RequirementAnalysisResponse(SafeBaseModel):
    """Flat requirement analysis extracted from ARSRS."""
    system_name: str = ""
    system_type: str = ""
    domain: str = ""
    functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    non_functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    actors: List[Dict[str, Any]] = Field(default_factory=list)
    modules: List[Any] = Field(default_factory=list)
    constraints: List[Any] = Field(default_factory=list)
    assumptions: List[Any] = Field(default_factory=list)
    key_workflows: List[Dict[str, Any]] = Field(default_factory=list)
    domain_gap_analysis: Dict[str, Any] = Field(default_factory=dict)
    domain_checklist: List[Any] = Field(default_factory=list)


# ─── Technology Advisor ──────────────────────────────────────────────────────

class TechAdvisorResponse(SafeBaseModel):
    """Flat technology recommendation."""
    backend: Dict[str, Any] = Field(default_factory=dict)
    frontend: Dict[str, Any] = Field(default_factory=dict)
    database: Dict[str, Any] = Field(default_factory=dict)
    cache: Dict[str, Any] = Field(default_factory=dict)
    authentication: Dict[str, Any] = Field(default_factory=dict)
    communication: Dict[str, Any] = Field(default_factory=dict)
    cloud: Dict[str, Any] = Field(default_factory=dict)
    deployment: Dict[str, Any] = Field(default_factory=dict)
    rationale: List[Any] = Field(default_factory=list)


# ─── HLD ─────────────────────────────────────────────────────────────────────

class HLDResponse(SafeBaseModel):
    """Flat High Level Design — LLM fills top-level keys, nested content is free-form."""
    architecture_style: str = ""
    executive_summary: str = ""
    business_goals: List[Any] = Field(default_factory=list)
    major_services: List[Dict[str, Any]] = Field(default_factory=list)
    communication_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    data_strategy: Dict[str, Any] = Field(default_factory=dict)
    security_overview: Dict[str, Any] = Field(default_factory=dict)
    deployment_strategy: Dict[str, Any] = Field(default_factory=dict)
    diagrams: List[Dict[str, Any]] = Field(default_factory=list)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    technology_stack: Dict[str, Any] = Field(default_factory=dict)


# ─── Backend LLD ─────────────────────────────────────────────────────────────

class BackendLLDResponse(SafeBaseModel):
    """Flat Backend LLD."""
    api_endpoints: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of API endpoint specs with route, method, request/response shapes"
    )
    services: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Application/domain service specs with methods and responsibilities"
    )
    domain_models: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Domain entities, aggregates, value objects"
    )
    repositories: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Data access layer specs"
    )
    project_structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="Directory/package layout"
    )
    framework_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Framework-specific configuration (Spring Boot, FastAPI, etc.)"
    )
    security_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Auth filters, RBAC, security middleware"
    )
    error_handling: Dict[str, Any] = Field(
        default_factory=dict,
        description="Global error handling strategy"
    )
    api_versioning_policy: Dict[str, Any] = Field(
        default_factory=dict,
        description="API versioning and deprecation strategy"
    )
    data_lifecycle: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data retention, backup verification, and right-to-erasure lifecycle"
    )
    dependencies: List[Any] = Field(
        default_factory=list,
        description="Key library/framework dependencies"
    )
    architecture_patterns: List[Any] = Field(
        default_factory=list,
        description="Applied patterns (Clean Architecture, DDD, CQRS, etc.)"
    )


# ─── Database LLD ────────────────────────────────────────────────────────────

class DatabaseLLDResponse(SafeBaseModel):
    """Flat Database LLD."""
    database_type: str = ""
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    indexes: List[Dict[str, Any]] = Field(default_factory=list)
    migrations_strategy: Dict[str, Any] = Field(default_factory=dict)
    caching_strategy: Dict[str, Any] = Field(default_factory=dict)
    backup_strategy: Dict[str, Any] = Field(default_factory=dict)
    performance_tuning: Dict[str, Any] = Field(default_factory=dict)


# ─── Frontend LLD ────────────────────────────────────────────────────────────

class FrontendLLDResponse(SafeBaseModel):
    """Flat Frontend LLD."""
    framework: str = ""
    pages: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    state_management: Dict[str, Any] = Field(default_factory=dict)
    routing: Dict[str, Any] = Field(default_factory=dict)
    api_integration: Dict[str, Any] = Field(default_factory=dict)
    styling_approach: Dict[str, Any] = Field(default_factory=dict)
    build_config: Dict[str, Any] = Field(default_factory=dict)
    accessibility: Dict[str, Any] = Field(default_factory=dict)


# ─── Security LLD ────────────────────────────────────────────────────

class SecurityLLDResponse(SafeBaseModel):
    """Flat Security LLD."""
    authentication: Dict[str, Any] = Field(default_factory=dict)
    authorization: Dict[str, Any] = Field(default_factory=dict)
    encryption: Dict[str, Any] = Field(default_factory=dict)
    threat_model: List[Dict[str, Any]] = Field(default_factory=list)
    security_controls: List[Dict[str, Any]] = Field(default_factory=list)
    compliance: Any = Field(default_factory=dict)
    secrets_management: Dict[str, Any] = Field(default_factory=dict)
    audit_logging: Dict[str, Any] = Field(default_factory=dict)


# ─── Cloud LLD ───────────────────────────────────────────────────────────────

class CloudLLDResponse(SafeBaseModel):
    """Flat Cloud/Infrastructure LLD."""
    cloud_provider: str = ""
    compute: Dict[str, Any] = Field(default_factory=dict)
    networking: Dict[str, Any] = Field(default_factory=dict)
    storage: Dict[str, Any] = Field(default_factory=dict)
    container_orchestration: Dict[str, Any] = Field(default_factory=dict)
    ci_cd_pipeline: Dict[str, Any] = Field(default_factory=dict)
    monitoring: Dict[str, Any] = Field(default_factory=dict)
    scaling_strategy: Dict[str, Any] = Field(default_factory=dict)
    disaster_recovery: Dict[str, Any] = Field(default_factory=dict)
    cost_estimation: Dict[str, Any] = Field(default_factory=dict)


# ─── Testing Strategy ─────────────────────────────────────────────────────────

class TestingStrategyResponse(SafeBaseModel):
    """Flat Testing Strategy & Quality Assurance Plan."""
    coverage_targets: Dict[str, Any] = Field(default_factory=dict)
    unit_testing: Dict[str, Any] = Field(default_factory=dict)
    integration_testing: Dict[str, Any] = Field(default_factory=dict)
    contract_testing: Dict[str, Any] = Field(default_factory=dict)
    e2e_testing: Dict[str, Any] = Field(default_factory=dict)
    load_testing: Dict[str, Any] = Field(default_factory=dict)
    security_testing: Dict[str, Any] = Field(default_factory=dict)
    ci_cd_test_gates: List[Any] = Field(default_factory=list)


# ─── Observability ──────────────────────────────────────────────────────────

class ObservabilityResponse(SafeBaseModel):
    """Flat Observability & Reliability Plan."""
    service_level_objectives: List[Dict[str, Any]] = Field(default_factory=list)
    error_budgets: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    logging_strategy: Dict[str, Any] = Field(default_factory=dict)
    distributed_tracing: Dict[str, Any] = Field(default_factory=dict)
    alerting_rules: List[Dict[str, Any]] = Field(default_factory=list)
    dashboards: List[Dict[str, Any]] = Field(default_factory=list)
    health_checks: Dict[str, Any] = Field(default_factory=dict)


# ─── Runbooks & Operations ───────────────────────────────────────────────────

class RunbookResponse(SafeBaseModel):
    """Flat Runbooks & Operational Procedures."""
    on_call_escalation: List[Dict[str, Any]] = Field(default_factory=list)
    incident_response_steps: List[Dict[str, Any]] = Field(default_factory=list)
    deployment_rollback_procedure: Dict[str, Any] = Field(default_factory=dict)
    backup_restore_drill: Dict[str, Any] = Field(default_factory=dict)
    failover_procedure: Dict[str, Any] = Field(default_factory=dict)
    common_alerts_playbook: List[Dict[str, Any]] = Field(default_factory=list)
    data_retention_and_purge_flow: Dict[str, Any] = Field(default_factory=dict)


# ─── Adversarial Red-Team Review ─────────────────────────────────────────────

class AdversarialReviewResponse(SafeBaseModel):
    """Flat Adversarial Red-Team Architecture Review."""
    review_status: str = "PASSED"
    single_points_of_failure: List[Dict[str, Any]] = Field(default_factory=list)
    untested_assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_risks: List[Dict[str, Any]] = Field(default_factory=list)
    security_vulnerabilities_identified: List[Dict[str, Any]] = Field(default_factory=list)
    scalability_bottlenecks: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_mitigations: List[Dict[str, Any]] = Field(default_factory=list)
    production_readiness_verdict: str = "APPROVED_WITH_CONDITIONS"


# ─── Unified Architecture Package ─────────────────────────────────────────────

class SoftwareArchitecturePackageResponse(SafeBaseModel):
    """Canonical aggregated Software Architecture Package."""
    system_name: str = ""
    domain: str = ""
    architecture_style: str = ""
    requirement_analysis: Dict[str, Any] = Field(default_factory=dict)
    technology_recommendation: Dict[str, Any] = Field(default_factory=dict)
    architecture_decision_plan: Dict[str, Any] = Field(default_factory=dict)
    hld: Dict[str, Any] = Field(default_factory=dict)
    backend_lld: Dict[str, Any] = Field(default_factory=dict)
    database_lld: Dict[str, Any] = Field(default_factory=dict)
    frontend_lld: Dict[str, Any] = Field(default_factory=dict)
    security_lld: Dict[str, Any] = Field(default_factory=dict)
    cloud_lld: Dict[str, Any] = Field(default_factory=dict)
    testing_strategy: Dict[str, Any] = Field(default_factory=dict)
    observability: Dict[str, Any] = Field(default_factory=dict)
    runbooks: Dict[str, Any] = Field(default_factory=dict)
    adversarial_review: Dict[str, Any] = Field(default_factory=dict)
    generated_artifacts: Dict[str, Any] = Field(default_factory=dict)
    completeness: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

