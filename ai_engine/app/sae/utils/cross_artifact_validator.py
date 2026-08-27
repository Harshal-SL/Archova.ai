"""Cross-Artifact Consistency Validator Engine for SAE v2.

Performs deterministic multi-way consistency checks against the Canonical Architecture Contract (CAC):
  1. Requirement ID Integrity: Every referenced requirement ID must exist in the canonical registry (FR-XXX, NFR-XXX). No REQ-* aliases allowed.
  2. Canonical API Operation Alignment: Backend, Frontend, Testing, and Observability must use canonical operation IDs and paths.
  3. Backend <-> Database Entity Mapping: Domain entities and SQL tables must resolve via explicit canonical entity mappings.
  4. Frontend <-> Backend API Integration: Frontend must integrate canonical API operations.
  5. Security <-> Backend / Cloud: Auth mechanisms, RBAC, and TLS enforcement.
  6. Cloud <-> System Architecture: Compute, containers, and database instances deployed.
  7. Observability & Testing <-> Canonical APIs: Monitored SLIs and test scopes must target real canonical endpoints.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.sae.utils.domain_lock import DomainContext
from app.sae.utils.canonical_contract import CanonicalArchitectureContract

logger = logging.getLogger(__name__)


class CrossArtifactConsistencyReport(BaseModel):
    """Multi-artifact consistency verification report."""
    score: float = Field(..., description="Aggregate cross-artifact consistency score 0.0 to 1.0")
    is_valid: bool = Field(..., description="True if score >= 0.70 and no blocking hard violations")
    hld_to_backend_alignment: float = 1.0
    backend_to_database_alignment: float = 1.0
    frontend_to_backend_alignment: float = 1.0
    security_to_backend_alignment: float = 1.0
    cloud_to_architecture_alignment: float = 1.0
    testing_to_api_alignment: float = 1.0
    observability_to_api_alignment: float = 1.0
    requirement_id_integrity: float = 1.0
    traceability_coverage: float = 1.0
    total_issues: int = 0
    inconsistencies: List[Dict[str, str]] = Field(default_factory=list)
    missing_links: List[str] = Field(default_factory=list)
    traced_requirements: List[str] = Field(default_factory=list)
    unknown_requirement_ids: List[str] = Field(default_factory=list)
    unknown_api_operations: List[str] = Field(default_factory=list)
    missing_entity_mappings: List[str] = Field(default_factory=list)
    source_traceability_passed: bool = True
    scope_drift_passed: bool = True
    placeholder_fr_count: int = 0


class CrossArtifactValidator:
    """Deterministic Multi-Way Consistency Engine powered by Canonical Architecture Contract."""

    @classmethod
    def validate_cross_artifacts(
        cls,
        domain_ctx: DomainContext,
        hld: Dict[str, Any],
        backend_lld: Dict[str, Any],
        database_lld: Dict[str, Any],
        frontend_lld: Dict[str, Any],
        security_lld: Dict[str, Any],
        cloud_lld: Dict[str, Any],
        testing_strategy: Optional[Dict[str, Any]] = None,
        observability: Optional[Dict[str, Any]] = None,
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> CrossArtifactConsistencyReport:
        """Execute comprehensive cross-artifact consistency verification against CAC."""
        inconsistencies: List[Dict[str, str]] = []
        missing_links: List[str] = []
        unknown_req_ids: List[str] = []
        unknown_api_ops: List[str] = []
        missing_entity_maps: List[str] = []

        # Canonical requirement IDs set
        canonical_req_ids = set(domain_ctx.get_req_ids())
        if cac and cac.requirement_ids:
            canonical_req_ids.update(cac.requirement_ids)

        # ── 1. Requirement ID Integrity (Strict No-Alias Validation) ──────────
        all_artifacts = {
            "hld": hld,
            "backend_lld": backend_lld,
            "database_lld": database_lld,
            "frontend_lld": frontend_lld,
            "security_lld": security_lld,
            "cloud_lld": cloud_lld,
        }
        if testing_strategy:
            all_artifacts["testing_strategy"] = testing_strategy
        if observability:
            all_artifacts["observability"] = observability

        all_satisfies_refs: Set[Tuple[str, str]] = set()
        for art_name, art_content in all_artifacts.items():
            if not isinstance(art_content, dict):
                continue
            for req_ref in cls._extract_satisfies_values(art_content):
                all_satisfies_refs.add((art_name, req_ref))

        invalid_satisfies_count = 0
        for art_name, req_ref in all_satisfies_refs:
            if req_ref not in canonical_req_ids:
                invalid_satisfies_count += 1
                unknown_req_ids.append(req_ref)
                inconsistencies.append({
                    "type": "UNKNOWN_REQUIREMENT_ID",
                    "severity": "CRITICAL",
                    "detail": f"Artifact '{art_name}' references unknown requirement ID '{req_ref}' not in canonical registry: {sorted(list(canonical_req_ids))}",
                })

        total_satisfies = max(len(all_satisfies_refs), 1)
        req_id_integrity = round(max(0.0, 1.0 - (invalid_satisfies_count / total_satisfies)), 2)

        # ── 2. HLD <-> Backend LLD Alignment ──────────────────────────────────
        hld_services = []
        for s in hld.get("major_services", []):
            if isinstance(s, dict):
                name = s.get("name") or s.get("service_name") or ""
                if name:
                    hld_services.append(name.lower())

        backend_text = json.dumps(backend_lld, default=str).lower()
        matched_services = 0
        for sname in hld_services:
            root_words = [w for w in sname.split() if len(w) > 3 and w not in ("service", "management", "system")]
            if any(rw in backend_text for rw in root_words):
                matched_services += 1
            else:
                inconsistencies.append({
                    "type": "HLD_BACKEND_MISMATCH",
                    "severity": "WARNING",
                    "detail": f"HLD Service '{sname}' has no matching implementation in Backend LLD",
                })
                missing_links.append(f"Backend missing service: {sname}")

        hld_backend_score = round(matched_services / max(len(hld_services), 1), 2) if hld_services else 0.85

        # ── 3. Backend LLD <-> Database LLD Alignment (via Entity Mappings) ───
        domain_models = []
        for dm in backend_lld.get("domain_models", []):
            if isinstance(dm, dict):
                mname = dm.get("name") or dm.get("entity_name") or ""
                if mname:
                    domain_models.append(mname)

        db_text = json.dumps(database_lld, default=str).lower()
        matched_models = 0
        for mname in domain_models:
            # Check if direct name in DB or explicit canonical mapping exists
            has_direct = mname.lower() in db_text or (mname.lower() + "s") in db_text or (mname.lower() + "_records") in db_text
            has_mapped = False
            if cac:
                mapping = cac.get_entity_mapping_by_domain_name(mname)
                if mapping and mapping.database_table.lower() in db_text:
                    has_mapped = True

            if has_direct or has_mapped:
                matched_models += 1
            else:
                missing_entity_maps.append(mname)
                inconsistencies.append({
                    "type": "BACKEND_DB_MISMATCH",
                    "severity": "CRITICAL",
                    "detail": f"Backend Domain Entity '{mname}' has no corresponding Database table or explicit CAC mapping in database_lld",
                })

        backend_db_score = round(matched_models / max(len(domain_models), 1), 2) if domain_models else 0.85

        # ── 3b. Database Relationships Integrity Validation ──────────────────
        db_tables = {t.get("name", "").lower() for t in database_lld.get("tables", []) if isinstance(t, dict) and t.get("name")}
        for rel in database_lld.get("relationships", []):
            if isinstance(rel, dict):
                from_t = rel.get("from_table", "").lower()
                to_t = rel.get("to_table", "").lower()
                if from_t and db_tables and from_t not in db_tables:
                    inconsistencies.append({
                        "type": "INVALID_DB_RELATIONSHIP",
                        "severity": "CRITICAL",
                        "detail": f"Database relationship references non-existent from_table '{from_t}' (Valid tables: {sorted(list(db_tables))})",
                    })
                if to_t and db_tables and to_t not in db_tables:
                    inconsistencies.append({
                        "type": "INVALID_DB_RELATIONSHIP",
                        "severity": "CRITICAL",
                        "detail": f"Database relationship references non-existent to_table '{to_t}' (Valid tables: {sorted(list(db_tables))})",
                    })

        # ── 4. Frontend LLD <-> Backend LLD (Canonical API Operations) ────────
        frontend_text = json.dumps(frontend_lld, default=str).lower()
        backend_endpoints = backend_lld.get("api_endpoints", [])
        
        canonical_paths = []
        if cac and cac.api_operations:
            canonical_paths = [op.path.lower() for op in cac.api_operations]
        else:
            for ep in backend_endpoints:
                if isinstance(ep, dict):
                    p = ep.get("route") or ep.get("path")
                    if p:
                        canonical_paths.append(p.lower())

        matched_fe_endpoints = 0
        if cac and cac.api_operations:
            for op in cac.api_operations:
                op_id = op.operation_id.lower()
                full_path = op.path.lower()
                sub_path = "/" + "/".join(op.path.strip("/").split("/")[2:]) if len(op.path.strip("/").split("/")) > 2 else full_path
                if op_id in frontend_text or full_path in frontend_text or (len(sub_path) > 5 and sub_path in frontend_text):
                    matched_fe_endpoints += 1
            fe_be_score = round(matched_fe_endpoints / max(len(cac.api_operations), 1), 2)
        else:
            for p in canonical_paths:
                sub_path = "/" + "/".join(p.strip("/").split("/")[2:]) if len(p.strip("/").split("/")) > 2 else p
                if p in frontend_text or (len(sub_path) > 5 and sub_path in frontend_text):
                    matched_fe_endpoints += 1
            fe_be_score = (
                round(matched_fe_endpoints / max(len(canonical_paths), 1), 2)
                if canonical_paths else 0.80
            )
        if fe_be_score < 0.50:
            inconsistencies.append({
                "type": "FRONTEND_BACKEND_MISMATCH",
                "severity": "CRITICAL",
                "detail": f"Frontend LLD only aligns with {matched_fe_endpoints}/{len(canonical_paths)} canonical API operations ({fe_be_score*100:.0f}%)",
            })

        # ── 5. Testing Strategy <-> Canonical API Alignment ───────────────────
        test_score = 1.0
        if testing_strategy and isinstance(testing_strategy, dict):
            test_text = json.dumps(testing_strategy, default=str).lower()
            matched_test_ops = 0
            for p in canonical_paths:
                leaf_seg = p.strip("/").split("/")[-1] if p.strip("/") else ""
                if leaf_seg in test_text or p in test_text:
                    matched_test_ops += 1
            test_score = round(matched_test_ops / max(len(canonical_paths), 1), 2) if canonical_paths else 1.0
            if test_score < 0.50:
                inconsistencies.append({
                    "type": "TESTING_API_MISMATCH",
                    "severity": "WARNING",
                    "detail": f"Testing Strategy references non-canonical API operations (alignment: {test_score*100:.0f}%)",
                })

        # ── 6. Observability <-> Canonical API Alignment ──────────────────────
        obs_score = 1.0
        if observability and isinstance(observability, dict):
            obs_text = json.dumps(observability, default=str).lower()
            # Check for non-canonical invented routes in SLOs
            slos = observability.get("service_level_objectives", [])
            for slo in slos:
                if isinstance(slo, dict):
                    sli = slo.get("sli", "") + " " + slo.get("target", "")
                    # Find any /api/v1/xxx patterns
                    found_routes = re.findall(r"/api/v1/[a-zA-Z0-9_/]+", sli)
                    for fr in found_routes:
                        fr_clean = fr.lower().rstrip(".,;)")
                        if canonical_paths and not any(cp in fr_clean or fr_clean in cp for cp in canonical_paths):
                            unknown_api_ops.append(fr)
                            inconsistencies.append({
                                "type": "OBSERVABILITY_API_MISMATCH",
                                "severity": "WARNING",
                                "detail": f"Observability SLO defines SLI on non-canonical route '{fr}' not in API contract",
                            })
            if unknown_api_ops:
                obs_score = round(max(0.0, 1.0 - (len(unknown_api_ops) / max(len(slos), 1))), 2)

        # ── 7. Security LLD <-> Backend/Cloud Alignment ───────────────────────
        sec_text = json.dumps(security_lld, default=str).lower()
        cloud_text = json.dumps(cloud_lld, default=str).lower()
        
        has_auth_in_backend = any(term in backend_text for term in ["jwt", "auth", "token", "security", "bearer"])
        has_tls_in_cloud = any(term in cloud_text for term in ["tls", "ssl", "https", "certificate", "cert-manager", "ingress"])
        has_rbac_in_sec = any(term in sec_text for term in ["rbac", "role", "permission", "authorization"])

        sec_score = 0.0
        if has_auth_in_backend:
            sec_score += 0.40
        else:
            inconsistencies.append({
                "type": "SECURITY_BACKEND_MISMATCH",
                "severity": "WARNING",
                "detail": "Backend LLD lacks explicit JWT / Auth middleware integration",
            })

        if has_tls_in_cloud:
            sec_score += 0.30
        else:
            inconsistencies.append({
                "type": "SECURITY_CLOUD_MISMATCH",
                "severity": "WARNING",
                "detail": "Cloud LLD lacks explicit TLS / Ingress certificate configuration",
            })

        if has_rbac_in_sec:
            sec_score += 0.30

        sec_alignment_score = round(sec_score, 2)

        # ── 8. Cloud LLD <-> System Architecture Alignment ────────────────────
        has_compute = any(term in cloud_text for term in ["kubernetes", "eks", "gke", "ecs", "container", "pod", "node", "vm"])
        has_database_infra = any(term in cloud_text for term in ["rds", "postgres", "mysql", "aurora", "statefulset", "database"])
        has_networking = any(term in cloud_text for term in ["vpc", "subnet", "ingress", "load_balancer", "gateway"])

        cloud_score = 0.0
        if has_compute:
            cloud_score += 0.40
        if has_database_infra:
            cloud_score += 0.30
        if has_networking:
            cloud_score += 0.30
        cloud_alignment_score = round(cloud_score, 2)

        # ── 9. Canonical Requirement Traceability ─────────────────────────────
        # Aggregate all generated architecture artifacts (HLD, Backend, DB, Frontend, Security, Cloud, Testing, Observability)
        test_text = json.dumps(testing_strategy or {})
        obs_text = json.dumps(observability or {})
        all_design_text = f"{json.dumps(hld)} {backend_text} {db_text} {frontend_text} {sec_text} {cloud_text} {test_text} {obs_text}".lower()

        traced_reqs = []
        for req_id in canonical_req_ids:
            # 1. Direct requirement ID presence across any architecture artifact
            if req_id.lower() in all_design_text:
                traced_reqs.append(req_id)
            # 2. Derived traceability via Canonical Architecture Contract
            elif cac:
                # Check if requirement is covered by a canonical service or API operation
                is_derived = any(
                    req_id in op.requirement_ids for op in cac.api_operations if op.path.lower() in all_design_text
                ) or any(
                    req_id in s.requirement_ids for s in cac.services if s.name.lower() in all_design_text
                )
                if is_derived:
                    traced_reqs.append(req_id)

        total_reqs = len(canonical_req_ids)
        traceability_score = (
            round(len(traced_reqs) / max(total_reqs, 1), 2)
            if total_reqs > 0 else 0.85
        )

        # ── 10. Dynamic Cross-Run Scope-Drift / Contamination Scanner ─────────
        # Dynamically queries all OTHER domains from the domain registry.
        # Zero static lists: scales automatically as domains are added.
        from app.sae.utils.domain_fence import get_forbidden_domain_concepts
        from app.ree.agents.answer_merger import is_generic_placeholder

        # Check placeholder FR count
        placeholder_frs: List[str] = []
        for fr in domain_ctx.functional_requirements:
            fr_title = fr.get("title", "") if isinstance(fr, dict) else str(fr)
            fr_desc = fr.get("description", "") if isinstance(fr, dict) else ""
            if is_generic_placeholder(fr_title) or is_generic_placeholder(fr_desc):
                placeholder_frs.append(fr_title or fr_desc)
                inconsistencies.append({
                    "type": "PLACEHOLDER_FUNCTIONAL_REQUIREMENT",
                    "severity": "CRITICAL",
                    "detail": f"Generic placeholder requirement found: '{fr_title}'",
                })

        current_domain = (domain_ctx.domain_key or "").lower()
        scope_drift_penalty = 0.0
        scope_drift_hits: List[str] = []

        forbidden_domains = get_forbidden_domain_concepts(current_domain)
        # Check declared requirements titles (business concepts, not technical code dumps)
        req_titles = " ".join([fr.get("title", "") for fr in domain_ctx.functional_requirements if isinstance(fr, dict)]).lower()
        declared_actors_text = " ".join([
            str(a.get("role", "") if isinstance(a, dict) else a)
            for a in (domain_ctx.actors or [])
        ]).lower()

        for f_key, f_info in forbidden_domains.items():
            f_display = f_info.get("display_name", f_key)
            for kw in f_info.get("keywords", []):
                # Check business keyword strictly in requirement titles
                if len(kw) >= 5 and re.search(rf"\b{re.escape(kw.lower())}(?:s|es)?\b", req_titles):
                    hit_msg = f"Scope-drift: '{kw}' ({f_display}) found in requirement titles for domain '{current_domain}'"
                    if hit_msg not in scope_drift_hits:
                        scope_drift_hits.append(hit_msg)
                        inconsistencies.append({
                            "type": "SCOPE_DRIFT_CONTAMINATION",
                            "severity": "CRITICAL",
                            "detail": hit_msg,
                        })
                        scope_drift_penalty += 0.05

            for actor in f_info.get("default_actors", []):
                if actor and len(actor) >= 4:
                    # Check actor word boundary strictly in declared actors
                    if re.search(rf"\b{re.escape(actor.lower())}\b", declared_actors_text):
                        hit_msg = f"Actor-drift: '{actor}' ({f_display}) found in declared actors for domain '{current_domain}'"
                        if hit_msg not in scope_drift_hits:
                            scope_drift_hits.append(hit_msg)
                            inconsistencies.append({
                                "type": "SCOPE_DRIFT_ACTOR_CONTAMINATION",
                                "severity": "CRITICAL",
                                "detail": hit_msg,
                            })
                            scope_drift_penalty += 0.05

        scope_drift_penalty = min(scope_drift_penalty, 0.40)  # Cap at -40%

        # ── Aggregate Consistency Score ───────────────────────────────────────
        composite_score = round(
            max(0.0, (0.20 * hld_backend_score)
            + (0.20 * backend_db_score)
            + (0.15 * fe_be_score)
            + (0.15 * req_id_integrity)
            + (0.10 * sec_alignment_score)
            + (0.10 * cloud_alignment_score)
            + (0.05 * test_score)
            + (0.05 * traceability_score)
            - scope_drift_penalty),
            2
        )

        source_traceability_passed = (
            len(missing_entity_maps) == 0
            and len(unknown_api_ops) == 0
            and traceability_score >= 0.75
        )
        scope_drift_passed = (len(scope_drift_hits) == 0)

        is_valid = (
            composite_score >= 0.70
            and fe_be_score >= 0.50
            and backend_db_score >= 0.50
            and req_id_integrity >= 0.80
            and len(unknown_api_ops) == 0
            and scope_drift_passed
            and len(placeholder_frs) == 0
        )

        return CrossArtifactConsistencyReport(
            score=composite_score,
            is_valid=is_valid,
            hld_to_backend_alignment=hld_backend_score,
            backend_to_database_alignment=backend_db_score,
            frontend_to_backend_alignment=fe_be_score,
            security_to_backend_alignment=sec_alignment_score,
            cloud_to_architecture_alignment=cloud_alignment_score,
            testing_to_api_alignment=test_score,
            observability_to_api_alignment=obs_score,
            requirement_id_integrity=req_id_integrity,
            traceability_coverage=traceability_score,
            total_issues=len(inconsistencies),
            inconsistencies=inconsistencies,
            missing_links=missing_links,
            traced_requirements=traced_reqs,
            unknown_requirement_ids=unknown_req_ids,
            unknown_api_operations=unknown_api_ops,
            missing_entity_mappings=missing_entity_maps,
            source_traceability_passed=source_traceability_passed,
            scope_drift_passed=scope_drift_passed,
            placeholder_fr_count=len(placeholder_frs),
        )

    @classmethod
    def _extract_satisfies_values(cls, obj: Any) -> List[str]:
        """Recursively extracts all strings in satisfies arrays."""
        results: List[str] = []
        if isinstance(obj, dict):
            if "satisfies" in obj and isinstance(obj["satisfies"], list):
                for item in obj["satisfies"]:
                    if isinstance(item, str) and item.strip():
                        results.append(item.strip())
            for v in obj.values():
                results.extend(cls._extract_satisfies_values(v))
        elif isinstance(obj, list):
            for item in obj:
                results.extend(cls._extract_satisfies_values(item))
        return results
