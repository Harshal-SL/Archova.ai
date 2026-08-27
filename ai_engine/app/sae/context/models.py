"""Domain section content models and change audit records for Shared Design Context."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.sae.contracts.design_contracts import (
    DatabaseContract,
    DeploymentContract,
    SecurityContract,
    ServiceContract,
)
from app.sae.utils.enums import AgentRole


class ChangeRecord(BaseModel):
    """Audit log entry capturing a specific modification to the Shared Design Context."""

    change_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_role: AgentRole = Field(..., description="Role of agent performing the change")
    section_id: str = Field(..., description="Section identifier modified")
    modified_fields: List[str] = Field(default_factory=list, description="Fields changed in this update")
    previous_version: int = Field(..., description="Section version prior to change")
    new_version: int = Field(..., description="Section version after change")
    description: Optional[str] = Field(default=None, description="Summary explanation of change")


class ProjectMetadataSection(BaseModel):
    """Section content for project metadata."""

    project_id: str = Field(default_factory=lambda: str(uuid4()))
    project_name: str = Field(..., description="Name of the target system")
    description: str = Field(default="", description="High-level description of system")
    owner: str = Field(default="Architect Team")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    version: str = Field(default="1.0.0")


class RequirementAnalysisSection(BaseModel):
    """Section content for structured requirement analysis (ARSRS)."""

    raw_arsrs: Dict[str, Any] = Field(default_factory=dict, description="Raw ARSRS specification payload")
    functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    non_functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    target_scale: Dict[str, Any] = Field(default_factory=dict)
    domain: str = Field(default="General Software")
    risk_assessment: List[Dict[str, Any]] = Field(default_factory=list)


class TechnologyRecommendationsSection(BaseModel):
    """Section content for technology stack recommendations."""

    tech_stack_summary: Dict[str, str] = Field(default_factory=dict)
    recommended_languages: List[str] = Field(default_factory=list)
    recommended_frameworks: List[str] = Field(default_factory=list)
    recommended_databases: List[str] = Field(default_factory=list)
    recommended_infrastructure: List[str] = Field(default_factory=list)
    selection_rationale: Dict[str, str] = Field(default_factory=dict)


class HLDSection(BaseModel):
    """Section content for High Level Design (HLD)."""

    system_overview: str = Field(default="")
    architectural_pattern: str = Field(default="Microservices")
    component_diagram_desc: str = Field(default="")
    module_boundaries: List[Dict[str, Any]] = Field(default_factory=list)
    external_integrations: List[Dict[str, Any]] = Field(default_factory=list)
    data_flow_descriptions: List[str] = Field(default_factory=list)
    service_contracts: List[ServiceContract] = Field(default_factory=list)


class BackendLLDSection(BaseModel):
    """Section content for Backend Low Level Design (LLD)."""

    services: List[ServiceContract] = Field(default_factory=list)
    design_patterns_used: List[str] = Field(default_factory=list)
    error_handling_strategy: str = Field(default="")
    logging_monitoring_strategy: str = Field(default="")
    caching_layer_spec: Dict[str, Any] = Field(default_factory=dict)


class DatabaseLLDSection(BaseModel):
    """Section content for Database Low Level Design (LLD)."""

    databases: List[DatabaseContract] = Field(default_factory=list)
    data_migration_strategy: str = Field(default="")
    indexing_strategy_summary: str = Field(default="")
    data_retention_policy: str = Field(default="")


class FrontendLLDSection(BaseModel):
    """Section content for Frontend Low Level Design (LLD)."""

    ui_architecture: str = Field(default="Single Page Application (SPA)")
    component_hierarchy: List[Dict[str, Any]] = Field(default_factory=list)
    state_management_strategy: str = Field(default="")
    routing_design: List[Dict[str, Any]] = Field(default_factory=list)
    theme_and_design_system: Dict[str, Any] = Field(default_factory=dict)


class SecurityDesignSection(BaseModel):
    """Section content for Security Architecture & Policy."""

    security_contract: Optional[SecurityContract] = Field(default=None)
    threat_model_summary: str = Field(default="")
    vulnerability_mitigations: List[Dict[str, str]] = Field(default_factory=list)
    data_classification: Dict[str, str] = Field(default_factory=dict)


class CloudDesignSection(BaseModel):
    """Section content for Cloud Infrastructure & Deployment."""

    deployments: List[DeploymentContract] = Field(default_factory=list)
    cloud_provider: str = Field(default="AWS")
    infrastructure_as_code: str = Field(default="Terraform")
    ci_cd_pipeline_desc: str = Field(default="")
    disaster_recovery_plan: Dict[str, Any] = Field(default_factory=dict)


class JustificationReportsSection(BaseModel):
    """Section content for Architectural Justification Reports."""

    tradeoff_matrix: List[Dict[str, Any]] = Field(default_factory=list)
    pattern_justifications: Dict[str, str] = Field(default_factory=dict)
    cost_benefit_analysis: Dict[str, Any] = Field(default_factory=dict)
    risk_mitigation_matrix: List[Dict[str, Any]] = Field(default_factory=list)


class ValidationResultsSection(BaseModel):
    """Section content for Architectural Validation & Verification Results."""

    validation_passed: bool = Field(default=True)
    total_checks: int = Field(default=0)
    passed_checks: int = Field(default=0)
    failed_checks: int = Field(default=0)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_score: float = Field(default=1.0, ge=0.0, le=1.0)
