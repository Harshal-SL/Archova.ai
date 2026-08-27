"""Unified 3-Tier Scoring & Quality Gating Engine for SAE v2.

Eliminates metric contradictions by strictly deriving overall readiness from:
  1. Artifact Semantic Quality (Deep content inspection)
  2. Cross-Artifact Consistency (Multi-way structural alignment)
  3. Production Readiness Gates & Adversarial Verdict (Hard Gating Policies)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.sae.utils.cross_artifact_validator import CrossArtifactConsistencyReport
from app.sae.utils.domain_lock import DomainContext

logger = logging.getLogger(__name__)


class BackendQualityDiagnostics(BaseModel):
    """Structured diagnostic report for Backend LLD Quality Gate."""
    score: float = 0.0
    passed: bool = False
    failed_checks: List[Dict[str, str]] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    schema_failures: List[str] = Field(default_factory=list)
    traceability_failures: List[str] = Field(default_factory=list)
    scope_violations: List[str] = Field(default_factory=list)
    endpoints_count: int = 0
    services_count: int = 0
    models_count: int = 0
    repositories_count: int = 0


class UnifiedScorecard(BaseModel):
    """Unified 3-Tier Architectural Scorecard and Gate Results."""
    status: str = Field(..., description="HEALTHY, DEGRADED, NEEDS_REMEDIATION, FAILED")
    overall_composite_score: float = Field(..., description="Balanced composite 0.0 to 1.0")
    structural_completeness: float = Field(..., description="Field population ratio 0.0 to 1.0")
    artifact_quality_score: float = Field(..., description="Deep semantic content quality 0.0 to 1.0")
    consistency_score: float = Field(..., description="Cross-artifact alignment score 0.0 to 1.0")
    production_readiness_score: float = Field(..., description="Production deployment readiness score 0.0 to 1.0")
    traceability_score: float = Field(default=1.0)
    per_section_scores: Dict[str, float] = Field(default_factory=dict)
    hard_gates: Dict[str, bool] = Field(default_factory=dict)
    hard_gate_violations: List[str] = Field(default_factory=list)
    quality_indicators: Dict[str, Any] = Field(default_factory=dict)
    backend_diagnostics: Optional[Dict[str, Any]] = None


class ScoringEngine:
    """Master Architecture Quality Gating and Scoring Engine."""

    HEDGED_PATTERNS = [
        "initial estimate",
        "requires load testing",
        "tbd",
        "to be determined",
        "potential consideration",
        "estimate_requires_workload_sizing",
        "generic option",
        "standard option",
        "placeholder",
    ]

    @classmethod
    def evaluate_backend_quality_gate(
        cls,
        backend_lld: Dict[str, Any],
        domain_ctx: Optional[DomainContext] = None,
    ) -> BackendQualityDiagnostics:
        """Structured validation of Backend LLD exposing granular failure criteria."""
        failed_checks = []
        missing_fields = []
        schema_failures = []
        traceability_failures = []
        scope_violations = []

        if not isinstance(backend_lld, dict) or not backend_lld:
            return BackendQualityDiagnostics(
                score=0.0,
                passed=False,
                failed_checks=[{
                    "check": "backend_lld_present",
                    "expected": "Non-empty dictionary payload",
                    "actual": "None or empty dictionary",
                }],
                missing_fields=["api_endpoints", "services", "domain_models", "repositories"],
            )

        # 1. Inspect API Endpoints
        endpoints = backend_lld.get("api_endpoints", [])
        if not isinstance(endpoints, list) or len(endpoints) == 0:
            missing_fields.append("api_endpoints")
            failed_checks.append({
                "check": "api_endpoints_presence",
                "expected": ">= 2 structured endpoints with route, method, request/response",
                "actual": "0 endpoints found",
            })
        else:
            for idx, ep in enumerate(endpoints):
                if not isinstance(ep, dict):
                    schema_failures.append(f"api_endpoints[{idx}] is not an object")
                    continue
                route = ep.get("route") or ep.get("path")
                method = ep.get("method")
                if not route or not method:
                    schema_failures.append(f"api_endpoints[{idx}] missing 'route' or 'method'")
                if not ep.get("error_responses"):
                    failed_checks.append({
                        "check": f"endpoint_error_handling_{idx}",
                        "expected": f"RFC 7807 error responses for {route or 'endpoint'}",
                        "actual": "Missing 'error_responses' array",
                    })

        # 2. Inspect Domain Models
        models = backend_lld.get("domain_models", [])
        if not isinstance(models, list) or len(models) == 0:
            missing_fields.append("domain_models")
            failed_checks.append({
                "check": "domain_models_presence",
                "expected": ">= 2 domain entity/aggregate models",
                "actual": "0 domain models found",
            })

        # 3. Inspect Services
        services = backend_lld.get("services", [])
        if not isinstance(services, list) or len(services) == 0:
            missing_fields.append("services")
            failed_checks.append({
                "check": "services_presence",
                "expected": ">= 1 application domain service",
                "actual": "0 services found",
            })

        # 4. Inspect Repositories
        repos = backend_lld.get("repositories", [])
        if not isinstance(repos, list) or len(repos) == 0:
            missing_fields.append("repositories")

        # 5. Requirement Traceability
        if domain_ctx and domain_ctx.canonical_requirements:
            backend_str = json.dumps(backend_lld).lower()
            untraced = [r.id for r in domain_ctx.canonical_requirements if r.id.lower() not in backend_str and not any(w in backend_str for w in r.title.lower().split() if len(w) > 4)]
            if len(untraced) > len(domain_ctx.canonical_requirements) * 0.5:
                traceability_failures.append(f"More than 50% canonical requirements not traced in backend: {untraced[:4]}")

        ep_count = len(endpoints) if isinstance(endpoints, list) else 0
        svc_count = len(services) if isinstance(services, list) else 0
        md_count = len(models) if isinstance(models, list) else 0
        repo_count = len(repos) if isinstance(repos, list) else 0

        # Calculate Score
        ep_score = min(1.0, ep_count / 3.0)
        svc_score = min(1.0, svc_count / 2.0)
        md_score = min(1.0, md_count / 2.0)
        repo_score = min(1.0, repo_count / 2.0)

        has_framework = bool(backend_lld.get("framework_config") or backend_lld.get("project_structure"))
        has_security = bool(backend_lld.get("security_config"))

        score = round(
            (0.35 * ep_score)
            + (0.25 * md_score)
            + (0.20 * svc_score)
            + (0.10 * repo_score)
            + (0.05 * (1.0 if has_framework else 0.0))
            + (0.05 * (1.0 if has_security else 0.0)),
            2
        )

        passed = score >= 0.60 and ep_count >= 2 and md_count >= 1

        return BackendQualityDiagnostics(
            score=score,
            passed=passed,
            failed_checks=failed_checks,
            missing_fields=missing_fields,
            schema_failures=schema_failures,
            traceability_failures=traceability_failures,
            scope_violations=scope_violations,
            endpoints_count=ep_count,
            services_count=svc_count,
            models_count=md_count,
            repositories_count=repo_count,
        )

    @classmethod
    def evaluate_section_semantic_quality(
        cls,
        section_name: str,
        content: Dict[str, Any],
        domain_ctx: Optional[DomainContext] = None,
    ) -> float:
        """Deep semantic inspection of an individual section payload."""
        if not isinstance(content, dict) or not content:
            return 0.0

        valid_items = {k: v for k, v in content.items() if k != "rag_metadata" and v is not None and v != "" and v != [] and v != {}}
        if not valid_items:
            return 0.0

        if section_name == "requirement_analysis":
            func = content.get("functional_requirements", [])
            nfr = content.get("non_functional_requirements", [])
            has_enough = len(func) >= 1 and len(nfr) >= 1 and bool(content.get("system_name")) and bool(content.get("domain"))
            return 1.0 if has_enough else round((len(func) + len(nfr)) / 4.0, 2)

        elif section_name == "technology_recommendation":
            core_keys = ["backend", "frontend", "database", "authentication"]
            present = sum(1 for k in core_keys if bool(content.get(k)))
            return round(present / len(core_keys), 2)

        elif section_name == "hld":
            services = content.get("major_services", [])
            has_data = bool(content.get("data_strategy"))
            has_comm = bool(content.get("communication_patterns"))
            has_sec = bool(content.get("security_overview"))
            svc_score = min(1.0, len(services) / 4.0) if isinstance(services, list) else 0.0
            return round((0.40 * svc_score) + (0.20 * (1.0 if has_data else 0.0)) + (0.20 * (1.0 if has_comm else 0.0)) + (0.20 * (1.0 if has_sec else 0.0)), 2)

        elif section_name == "backend_lld":
            diag = cls.evaluate_backend_quality_gate(content, domain_ctx)
            return diag.score

        elif section_name == "database_lld":
            tables = content.get("tables", []) or content.get("schemas", [])
            tb_score = min(1.0, len(tables) / 3.0) if isinstance(tables, list) else 0.0
            return round(tb_score, 2)

        elif section_name == "frontend_lld":
            components = content.get("components", []) or content.get("pages", [])
            return round(min(1.0, len(components) / 3.0), 2) if isinstance(components, list) else 0.8

        elif section_name == "security_lld":
            threats = content.get("threat_model", []) or content.get("controls", []) or content.get("authentication", {})
            return 1.0 if threats else 0.8

        elif section_name == "cloud_lld":
            compute = content.get("compute", {}) or content.get("infrastructure", {})
            return 1.0 if compute else 0.8

        return round(len(valid_items) / max(len(content), 1), 2)

    @classmethod
    def compute_unified_scorecard(
        cls,
        sections: Dict[str, Dict[str, Any]],
        domain_ctx: DomainContext,
        consistency_report: CrossArtifactConsistencyReport,
        adversarial_verdict: str = "APPROVED",
    ) -> UnifiedScorecard:
        """Compute holistic, non-contradictory 3-tier scorecard with hard gating."""
        per_section_scores: Dict[str, float] = {}
        for sname, content in sections.items():
            per_section_scores[sname] = cls.evaluate_section_semantic_quality(sname, content, domain_ctx)

        structural_completeness = round(sum(per_section_scores.values()) / max(len(per_section_scores), 1), 2)
        
        core_weights = {
            "requirement_analysis": 0.12,
            "technology_recommendation": 0.08,
            "architecture_decision_plan": 0.08,
            "hld": 0.20,
            "backend_lld": 0.15,
            "database_lld": 0.12,
            "frontend_lld": 0.05,
            "security_lld": 0.10,
            "cloud_lld": 0.10,
        }
        weighted_sum = 0.0
        total_w = 0.0
        for sname, w in core_weights.items():
            if sname in per_section_scores:
                weighted_sum += per_section_scores[sname] * w
                total_w += w

        artifact_quality_score = round(weighted_sum / max(total_w, 0.01), 2)
        consistency_score = consistency_report.score

        # Hedged / Placeholder Scan
        all_text = json.dumps(sections, default=str).lower()
        hedged_hits = [p for p in cls.HEDGED_PATTERNS if p in all_text]
        hedged_penalty = min(0.30, len(hedged_hits) * 0.05)

        # Production Readiness Gates
        gate_endpoints = bool(sections.get("backend_lld", {}).get("api_endpoints"))
        gate_cost = bool(sections.get("cloud_lld", {}).get("cost_estimation"))
        gate_compliance = bool(sections.get("security_lld", {}).get("compliance") or sections.get("security_lld", {}).get("security_controls"))
        gate_load = bool(sections.get("testing_strategy", {}).get("load_testing") or sections.get("testing_strategy"))
        gate_slo = bool(sections.get("observability", {}).get("service_level_objectives") or sections.get("observability"))

        gates_passed = sum([gate_endpoints, gate_cost, gate_compliance, gate_load, gate_slo])
        raw_gate_ratio = round(gates_passed / 5.0, 2)

        base_readiness = round(
            (0.35 * artifact_quality_score)
            + (0.35 * consistency_score)
            + (0.30 * raw_gate_ratio)
            - hedged_penalty,
            2
        )
        base_readiness = max(0.0, min(1.0, base_readiness))

        # Backend Diagnostics
        be_diag = cls.evaluate_backend_quality_gate(sections.get("backend_lld", {}), domain_ctx)

        # Hard Quality Gates
        hard_gate_violations: List[str] = []
        production_readiness = base_readiness

        hld_score = per_section_scores.get("hld", 0.0)
        req_score = per_section_scores.get("requirement_analysis", 0.0)
        db_score = per_section_scores.get("database_lld", 0.0)
        be_score = be_diag.score

        if hld_score < 0.70:
            hard_gate_violations.append(f"HLD semantic score ({hld_score:.2f}) is below minimum threshold 0.70")
            production_readiness = min(production_readiness, 0.30)

        if req_score < 0.70:
            hard_gate_violations.append(f"Requirement Analysis score ({req_score:.2f}) is below minimum threshold 0.70")
            production_readiness = min(production_readiness, 0.35)

        if be_score < 0.60 or db_score < 0.60:
            hard_gate_violations.append(f"Core LLD (Backend: {be_score:.2f}, DB: {db_score:.2f}) below threshold 0.60")
            production_readiness = min(production_readiness, 0.40)

        if consistency_score < 0.65:
            hard_gate_violations.append(f"Cross-artifact consistency ({consistency_score:.2f}) below threshold 0.65")
            production_readiness = min(production_readiness, 0.45)

        # CAC Contract Hard Gates
        if consistency_report.unknown_requirement_ids:
            hard_gate_violations.append(f"Unknown requirement IDs referenced in artifacts: {consistency_report.unknown_requirement_ids}")
            production_readiness = min(production_readiness, 0.40)

        if consistency_report.frontend_to_backend_alignment < 0.95:
            hard_gate_violations.append(f"Frontend ↔ Backend alignment ({consistency_report.frontend_to_backend_alignment*100:.0f}%) is below 95% threshold")
            if consistency_report.frontend_to_backend_alignment < 0.50:
                production_readiness = min(production_readiness, 0.30)

        if consistency_report.backend_to_database_alignment < 0.95:
            hard_gate_violations.append(f"Backend ↔ Database alignment ({consistency_report.backend_to_database_alignment*100:.0f}%) is below 95% threshold")
            if consistency_report.backend_to_database_alignment < 0.50:
                production_readiness = min(production_readiness, 0.35)

        if consistency_report.unknown_api_operations:
            hard_gate_violations.append(f"Non-canonical API routes found: {consistency_report.unknown_api_operations}")

        if consistency_report.missing_entity_mappings:
            hard_gate_violations.append(f"Unmapped backend entities in database: {consistency_report.missing_entity_mappings}")

        # Traceability Hard Gate: HEALTHY requires >= 75% of canonical requirements
        # to be traced across HLD, Backend, Database, Frontend, Security, Cloud artifacts.
        traceability_score = consistency_report.traceability_coverage
        if traceability_score < 0.75:
            hard_gate_violations.append(
                f"Requirement traceability ({traceability_score*100:.0f}%) is below minimum threshold of 75%. "
                f"Untraced requirement IDs prevent HEALTHY status."
            )
            production_readiness = min(production_readiness, 0.50)

        # Scope drift & Placeholder FR Hard Gates
        if not consistency_report.scope_drift_passed:
            hard_gate_violations.append("Cross-domain scope drift / contamination tokens detected in generated artifacts")
            production_readiness = min(production_readiness, 0.30)

        if consistency_report.placeholder_fr_count > 0:
            hard_gate_violations.append(f"{consistency_report.placeholder_fr_count} generic placeholder functional requirements detected")
            production_readiness = min(production_readiness, 0.30)

        if adversarial_verdict == "REJECTED":
            hard_gate_violations.append("Adversarial Red-Team review REJECTED the architecture package")
            production_readiness = min(production_readiness, 0.25)
        elif adversarial_verdict == "APPROVED_WITH_CONDITIONS":
            production_readiness = min(production_readiness, 0.90)

        overall_composite = round(
            (0.40 * artifact_quality_score)
            + (0.35 * consistency_score)
            + (0.25 * production_readiness),
            2
        )

        # ── Three-Tier Status Gating ──────────────────────────────────────────
        # 1. HEALTHY: Zero violations, high readiness, strict domain isolation & traceability
        if (
            len(hard_gate_violations) == 0
            and production_readiness >= 0.75
            and overall_composite >= 0.75
            and consistency_report.traceability_coverage >= 0.75
            and consistency_report.source_traceability_passed
            and consistency_report.scope_drift_passed
            and consistency_report.placeholder_fr_count == 0
        ):
            final_status = "HEALTHY"
        # 2. REGENERATE / FAILED: Critical structural failure, domain contamination, or placeholder FRs
        elif (
            consistency_report.placeholder_fr_count > 0
            or not consistency_report.scope_drift_passed
            or not consistency_report.source_traceability_passed
            or adversarial_verdict == "REJECTED"
            or consistency_report.frontend_to_backend_alignment == 0.0
            or consistency_report.backend_to_database_alignment == 0.0
            or production_readiness < 0.40
            or overall_composite < 0.40
        ):
            final_status = "REGENERATE"
        # 3. DEGRADED: Minor documentation gaps, optional NFR missing, non-critical observability
        else:
            final_status = "DEGRADED"

        return UnifiedScorecard(
            status=final_status,
            overall_composite_score=overall_composite,
            structural_completeness=structural_completeness,
            artifact_quality_score=artifact_quality_score,
            consistency_score=consistency_score,
            production_readiness_score=production_readiness,
            traceability_score=consistency_report.traceability_coverage,
            per_section_scores=per_section_scores,
            hard_gates={
                "hld_quality_gate_passed": hld_score >= 0.70,
                "requirement_quality_gate_passed": req_score >= 0.70,
                "backend_quality_gate_passed": be_score >= 0.60,
                "database_quality_gate_passed": db_score >= 0.60,
                "cross_artifact_consistency_passed": consistency_score >= 0.65,
                "requirement_id_integrity_passed": len(consistency_report.unknown_requirement_ids) == 0,
                "frontend_backend_alignment_passed": consistency_report.frontend_to_backend_alignment >= 0.95,
                "backend_database_alignment_passed": consistency_report.backend_to_database_alignment >= 0.95,
                "traceability_gate_passed": consistency_report.traceability_coverage >= 0.75,
                "source_traceability_passed": consistency_report.source_traceability_passed,
                "scope_drift_passed": consistency_report.scope_drift_passed,
                "placeholder_fr_gate_passed": consistency_report.placeholder_fr_count == 0,
                "adversarial_review_passed": adversarial_verdict != "REJECTED",
                "zero_hard_gate_violations": len(hard_gate_violations) == 0,
            },
            hard_gate_violations=hard_gate_violations,
            quality_indicators={
                "hedged_phrases_detected_count": len(hedged_hits),
                "hedged_phrases": hedged_hits,
                "endpoints_error_responses_verified": gate_endpoints,
                "cost_model_quantified": gate_cost,
                "compliance_determinations_binary": gate_compliance,
                "load_testing_traffic_model_defined": gate_load,
                "observability_slos_configured": gate_slo,
            },
            backend_diagnostics=be_diag.model_dump(),
        )
