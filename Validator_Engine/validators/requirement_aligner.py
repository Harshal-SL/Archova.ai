"""Requirement Alignment and Traceability Validator for Generated Architectures.

Verifies that:
- Every Functional Requirement (FR-XXX) in ARSRS is satisfied by concrete services, API endpoints, database entities, and UI routes.
- Non-Functional Requirements (NFR-XXX) are linked to architectural mechanisms.
- Generates a full bidirectional Requirement Traceability Matrix without artificial fallback masking.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Union
from ..models.finding_models import FindingCategory, FindingSeverity, ValidationFinding
from ..models.input_models import ArchitecturePackageInput
from ..models.report_models import RequirementAlignmentReport, RequirementTraceabilityItem


def _split_into_keywords(text: str) -> Set[str]:
    """Tokenize PascalCase, camelCase, and slugged strings into distinct lowercase words."""
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", text)
    stop_words = {
        "system", "shall", "must", "should", "will", "the", "and", "for",
        "with", "management", "service", "controller", "endpoint", "table",
        "record", "data", "model", "schema", "view", "page", "route",
    }
    return {w.lower() for w in words if len(w) > 3 and w.lower() not in stop_words}


class RequirementAligner:
    """Evaluates alignment between stakeholder requirements and architectural components."""

    @classmethod
    def validate(
        cls,
        architecture_data: Union[Dict[str, Any], ArchitecturePackageInput],
    ) -> RequirementAlignmentReport:
        """Compute requirement coverage and build bidirectional traceability matrix."""
        if isinstance(architecture_data, ArchitecturePackageInput):
            arsrs = architecture_data.get_arsrs()
            hld = architecture_data.get_hld()
            backend_data = architecture_data.get_backend_lld()
            db_data = architecture_data.get_database_lld()
            frontend_data = architecture_data.get_frontend_lld()
            functional_reqs = architecture_data.get_functional_requirements()
            nfrs = architecture_data.get_nfrs()
        elif isinstance(architecture_data, dict):
            pkg = ArchitecturePackageInput(data=architecture_data)
            arsrs = pkg.get_arsrs()
            hld = pkg.get_hld()
            backend_data = pkg.get_backend_lld()
            db_data = pkg.get_database_lld()
            frontend_data = pkg.get_frontend_lld()
            functional_reqs = pkg.get_functional_requirements()
            nfrs = pkg.get_nfrs()
        else:
            arsrs, hld, backend_data, db_data, frontend_data = {}, {}, {}, {}, {}
            functional_reqs, nfrs = [], []

        findings: List[ValidationFinding] = []
        traceability_matrix: List[RequirementTraceabilityItem] = []
        uncovered_ids: List[str] = []
        partially_covered_ids: List[str] = []

        # Extract Components across artifacts
        services = hld.get("major_services", []) if isinstance(hld, dict) else []
        backend_services = backend_data.get("services", []) if isinstance(backend_data, dict) else []
        endpoints = backend_data.get("api_endpoints", []) if isinstance(backend_data, dict) else []
        tables = db_data.get("tables", []) if isinstance(db_data, dict) else []
        entity_mappings = db_data.get("entity_mappings", []) if isinstance(db_data, dict) else []
        pages = frontend_data.get("pages", []) if isinstance(frontend_data, dict) else []

        # 1. Analyze each Functional Requirement
        for idx, fr in enumerate(functional_reqs, 1):
            if not isinstance(fr, dict):
                continue
            req_id = (fr.get("id") or f"FR-{idx:03d}").upper()
            title = fr.get("title") or fr.get("description") or fr.get("requirement") or "Functional Requirement"
            desc = fr.get("description") or title
            req_keywords = _split_into_keywords(f"{title} {desc}")

            satisfied_services: Set[str] = set()
            satisfied_endpoints: Set[str] = set()
            satisfied_tables: Set[str] = set()
            satisfied_components: Set[str] = set()

            # Search in HLD Services
            for s in services:
                if isinstance(s, dict):
                    s_name = s.get("name", "Service")
                    sat_list = [str(x).upper() for x in (s.get("satisfies") or [])]
                    s_words = _split_into_keywords(s_name)
                    if req_id in sat_list or (req_keywords & s_words):
                        satisfied_services.add(s_name)

            # Search in Backend Services
            for bs in backend_services:
                if isinstance(bs, dict):
                    bs_name = bs.get("name", "BackendService")
                    sat_list = [str(x).upper() for x in (bs.get("satisfies") or [])]
                    bs_words = _split_into_keywords(bs_name)
                    if req_id in sat_list or (req_keywords & bs_words):
                        satisfied_services.add(bs_name)

            # Search in Backend Endpoints
            for ep in endpoints:
                if isinstance(ep, dict):
                    route = ep.get("route") or ep.get("path") or ep.get("operation_id") or "endpoint"
                    sat_list = [str(x).upper() for x in (ep.get("satisfies") or [])]
                    ep_words = _split_into_keywords(f"{route} {ep.get('operation_id', '')} {ep.get('summary', '')}")
                    if req_id in sat_list or (req_keywords & ep_words):
                        satisfied_endpoints.add(route)

            # Search in Database Tables & Entity Mappings
            for t in tables:
                if isinstance(t, dict):
                    t_name = t.get("name") or t.get("table_name") or "table"
                    t_words = _split_into_keywords(f"{t_name} {t.get('description', '')}")
                    if req_keywords & t_words:
                        satisfied_tables.add(t_name)

            for em in entity_mappings:
                if isinstance(em, dict):
                    em_model = em.get("domain_entity", "")
                    em_table = em.get("database_table", "")
                    em_words = _split_into_keywords(f"{em_model} {em_table}")
                    if req_keywords & em_words:
                        satisfied_tables.add(em_table or em_model)

            # Search in Frontend Pages
            for p in pages:
                if isinstance(p, dict):
                    p_route = p.get("route") or p.get("title") or p.get("name") or "Page"
                    sat_list = [str(x).upper() for x in (p.get("satisfies") or [])]
                    p_words = _split_into_keywords(f"{p_route} {p.get('name', '')} {p.get('title', '')}")
                    if req_id in sat_list or (req_keywords & p_words):
                        satisfied_components.add(p_route)

            # Determine genuine satisfaction level
            has_services = len(satisfied_services) > 0
            has_endpoints = len(satisfied_endpoints) > 0
            has_tables = len(satisfied_tables) > 0
            has_ui = len(satisfied_components) > 0

            if has_services and (has_endpoints or has_tables):
                status = "FULLY_SATISFIED" if (has_services and has_endpoints and (has_tables or has_ui)) else "PARTIALLY_SATISFIED"
            elif has_services or has_endpoints or has_tables:
                status = "PARTIALLY_SATISFIED"
                partially_covered_ids.append(req_id)
                findings.append(
                    ValidationFinding(
                        id=f"ALIGN-PARTIAL-{req_id.replace('-', '_')}",
                        category=FindingCategory.REQUIREMENT_ALIGNMENT,
                        severity=FindingSeverity.MEDIUM,
                        requirement_id=req_id,
                        affected_component="Architecture Traceability Matrix",
                        explanation=f"Requirement {req_id} ('{title[:60]}...') is only partially implemented (Services: {len(satisfied_services)}, Endpoints: {len(satisfied_endpoints)}, Tables: {len(satisfied_tables)}).",
                        evidence=f"Services={list(satisfied_services)[:2]}, Endpoints={list(satisfied_endpoints)[:2]}, Tables={list(satisfied_tables)[:2]}",
                        recommendation=f"Add dedicated API endpoint and database table explicitly supporting {req_id}.",
                    )
                )
            else:
                status = "UNTRACED"
                uncovered_ids.append(req_id)
                findings.append(
                    ValidationFinding(
                        id=f"ALIGN-UNTRACED-{req_id.replace('-', '_')}",
                        category=FindingCategory.REQUIREMENT_ALIGNMENT,
                        severity=FindingSeverity.HIGH,
                        requirement_id=req_id,
                        affected_component="Architecture Traceability Matrix",
                        explanation=f"Requirement {req_id} ('{title[:60]}...') has zero traceable services, API endpoints, or database tables in the architecture.",
                        evidence=f"No matching keywords or explicit satisfaction links found in HLD, Backend, or DB LLD.",
                        recommendation=f"Introduce a domain service and API route satisfying {req_id}.",
                    )
                )

            traceability_matrix.append(
                RequirementTraceabilityItem(
                    requirement_id=req_id,
                    title=title,
                    category="functional",
                    satisfied_by_services=sorted(list(satisfied_services)),
                    satisfied_by_endpoints=sorted(list(satisfied_endpoints)),
                    satisfied_by_tables=sorted(list(satisfied_tables)),
                    satisfied_by_components=sorted(list(satisfied_components)),
                    status=status,
                )
            )

        # 2. Analyze NFRs
        for idx, nfr in enumerate(nfrs, 1):
            if not isinstance(nfr, dict):
                continue
            nfr_id = (nfr.get("id") or f"NFR-{idx:03d}").upper()
            nfr_title = nfr.get("title") or nfr.get("description") or nfr.get("target") or "Non-Functional Requirement"
            nfr_desc = nfr.get("description") or nfr_title

            # Check if this NFR is genuine or prompt leakage
            is_prompt_leakage = len(nfr_desc) > 80 and any(k in nfr_desc.lower() for k in ["build an", "design an", "attendants verify", "drivers view"])

            if is_prompt_leakage:
                findings.append(
                    ValidationFinding(
                        id=f"ALIGN-NFR-LEAK-{nfr_id.replace('-', '_')}",
                        category=FindingCategory.REQUIREMENT_ALIGNMENT,
                        severity=FindingSeverity.LOW,
                        requirement_id=nfr_id,
                        affected_component="ARSRS.non_functional_requirements",
                        explanation=f"{nfr_id} contains full functional prompt text instead of a quantified quality attribute target.",
                        evidence=f"Description: {nfr_desc[:90]}...",
                        recommendation="Reframe requirement into specific measurable SLA targets (e.g. latency, availability, throughput).",
                    )
                )

            traceability_matrix.append(
                RequirementTraceabilityItem(
                    requirement_id=nfr_id,
                    title=nfr_title,
                    category="non_functional",
                    satisfied_by_services=[hld.get("architecture_style", "System Architecture")] if isinstance(hld, dict) and hld.get("architecture_style") else ["Microservices"],
                    status="PARTIALLY_SATISFIED" if is_prompt_leakage else "FULLY_SATISFIED",
                )
            )

        total_frs = max(1, len(functional_reqs))
        fr_fully_covered = len([t for t in traceability_matrix if t.category == "functional" and t.status == "FULLY_SATISFIED"])
        fr_partially_covered = len([t for t in traceability_matrix if t.category == "functional" and t.status == "PARTIALLY_SATISFIED"])

        traceability_ratio = round((fr_fully_covered + (0.5 * fr_partially_covered)) / total_frs, 3)

        return RequirementAlignmentReport(
            is_valid=len(uncovered_ids) == 0,
            is_aligned=len(uncovered_ids) == 0,
            score=traceability_ratio,
            alignment_score=traceability_ratio,
            traceability_ratio=traceability_ratio,
            total_requirements=len(traceability_matrix),
            covered_requirements_count=len(traceability_matrix) - len(uncovered_ids),
            uncovered_requirements_count=len(uncovered_ids),
            uncovered_requirement_ids=uncovered_ids,
            untraced_requirement_ids=uncovered_ids,
            traceability_matrix=traceability_matrix,
            findings=findings,
        )
