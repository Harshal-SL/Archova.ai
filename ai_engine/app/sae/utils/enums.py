"""Enumerations for Design Engine roles, statuses, section types, and validation severities."""

from enum import Enum


class AgentRole(str, Enum):
    """Enumeration of agent roles in the Design Engine pipeline DAG."""

    REQUIREMENT_ANALYSIS = "REQUIREMENT_ANALYSIS"
    TECHNOLOGY_ADVISOR = "TECHNOLOGY_ADVISOR"
    ARCHITECTURE_PLANNER = "ARCHITECTURE_PLANNER"
    HLD = "HLD"
    HLD_VALIDATOR = "HLD_VALIDATOR"
    BACKEND = "BACKEND"
    BACKEND_VALIDATOR = "BACKEND_VALIDATOR"
    DATABASE = "DATABASE"
    DATABASE_VALIDATOR = "DATABASE_VALIDATOR"
    FRONTEND = "FRONTEND"
    FRONTEND_VALIDATOR = "FRONTEND_VALIDATOR"
    SECURITY = "SECURITY"
    SECURITY_VALIDATOR = "SECURITY_VALIDATOR"
    CLOUD = "CLOUD"
    CLOUD_VALIDATOR = "CLOUD_VALIDATOR"
    ARCHITECTURE_VALIDATOR = "ARCHITECTURE_VALIDATOR"
    VALIDATOR = "VALIDATOR"
    MERGE = "MERGE"
    EVOLUTION = "EVOLUTION"
    ORCHESTRATOR = "ORCHESTRATOR"
    ADMIN = "ADMIN"


class ExecutionStatus(str, Enum):
    """Execution status for agents and orchestrator pipeline steps."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRYING = "RETRYING"


class SectionType(str, Enum):
    """Enumeration of SharedDesignContext section types."""

    REQUIREMENT_ANALYSIS = "requirement_analysis"
    TECHNOLOGY_RECOMMENDATIONS = "technology_recommendations"
    ARCHITECTURE_DECISION_PLAN = "architecture_decision_plan"
    ARCHITECTURE_KNOWLEDGE = "architecture_knowledge"
    CONFIDENCE_REPORT = "confidence_report"
    ADRS = "adrs"
    HLD = "hld"
    BACKEND_LLD = "backend_lld"
    DATABASE_LLD = "database_lld"
    FRONTEND_LLD = "frontend_lld"
    SECURITY_LLD = "security"
    CLOUD_LLD = "cloud"
    VALIDATION_RESULTS = "validation_results"
    ARCHITECTURE_PACKAGE = "architecture_package"
    EVOLUTION_HISTORY = "evolution_history"
    CUSTOM = "custom"


class SectionStatus(str, Enum):
    """Lifecycle status of a section in SharedDesignContext."""

    EMPTY = "EMPTY"
    PENDING = "PENDING"
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ValidationSeverity(str, Enum):
    """Severity levels for validation errors and feedback items."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
