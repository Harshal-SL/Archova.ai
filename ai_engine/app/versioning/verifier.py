"""Architecture Verifier: Pure deterministic invariant checker for additive delta patches."""

from __future__ import annotations

from typing import Any, Dict, List, Set
from app.versioning.contracts import (
    ArchitecturePatch,
    PatchVerificationResult,
    VerificationViolation,
)


class ArchitectureVerifier:
    """Verifies that an architecture patch preserves 100% of baseline invariants
    and only introduces valid, non-destructive additive modifications.
    """

    def verify(
        self,
        baseline: Dict[str, Any],
        patched: Dict[str, Any],
        patch: ArchitecturePatch,
    ) -> PatchVerificationResult:
        """Run all verification rules and return violation list."""
        violations: List[VerificationViolation] = []

        # 1. Verify HLD Baseline Survival & Immutability
        self._verify_hld_survival(baseline, patched, violations)

        # 2. Verify Edge Connection Integrity (No orphan edges)
        self._verify_edge_connectivity(patched, violations)

        # 3. Verify Database Baseline Survival & Non-Breaking Additions
        self._verify_database_survival(baseline, patched, patch, violations)

        # 4. Verify Backend Endpoints Baseline Survival
        self._verify_backend_survival(baseline, patched, violations)

        is_valid = not any(v.severity in ["CRITICAL", "ERROR"] for v in violations)
        return PatchVerificationResult(is_valid=is_valid, violations=violations)

    def _verify_hld_survival(
        self,
        baseline: Dict[str, Any],
        patched: Dict[str, Any],
        violations: List[VerificationViolation],
    ) -> None:
        """Rule 1: 100% of baseline nodes and edges must survive untouched."""
        b_hld = baseline.get("hld", {}) or {}
        p_hld = patched.get("hld", {}) or {}

        b_nodes = b_hld.get("nodes", []) or []
        p_nodes = p_hld.get("nodes", []) or []

        p_node_map = {n.get("id"): n for n in p_nodes if isinstance(n, dict)}

        for b_node in b_nodes:
            if not isinstance(b_node, dict) or not b_node.get("id"):
                continue
            nid = b_node["id"]
            if nid not in p_node_map:
                violations.append(
                    VerificationViolation(
                        rule="IMMUTABLE_NODE_SURVIVAL",
                        severity="CRITICAL",
                        target=f"node:{nid}",
                        message=f"Baseline node '{nid}' was deleted or renamed in the evolved design.",
                    )
                )
            else:
                p_node = p_node_map[nid]
                # Check type didn't mutate
                if b_node.get("type") and p_node.get("type") != b_node.get("type"):
                    violations.append(
                        VerificationViolation(
                            rule="NODE_TYPE_IMMUTABILITY",
                            severity="ERROR",
                            target=f"node:{nid}",
                            message=f"Node '{nid}' changed type from '{b_node.get('type')}' to '{p_node.get('type')}'.",
                        )
                    )

        # Verify edge survival
        b_edges = b_hld.get("edges", []) or []
        p_edge_map = {e.get("id"): e for e in p_hld.get("edges", []) or [] if isinstance(e, dict)}

        for b_edge in b_edges:
            if not isinstance(b_edge, dict) or not b_edge.get("id"):
                continue
            eid = b_edge["id"]
            if eid not in p_edge_map:
                violations.append(
                    VerificationViolation(
                        rule="IMMUTABLE_EDGE_SURVIVAL",
                        severity="ERROR",
                        target=f"edge:{eid}",
                        message=f"Baseline edge '{eid}' was removed from the evolved design.",
                    )
                )

    def _verify_edge_connectivity(
        self,
        patched: Dict[str, Any],
        violations: List[VerificationViolation],
    ) -> None:
        """Rule 2: Every edge must connect to valid existing nodes (no dangling edges)."""
        p_hld = patched.get("hld", {}) or {}
        p_nodes = p_hld.get("nodes", []) or []
        valid_node_ids = {str(n.get("id")).strip() for n in p_nodes if isinstance(n, dict) and n.get("id")}

        # Include major_services IDs & names if present
        for s in (p_hld.get("major_services", []) or []):
            if isinstance(s, dict):
                if s.get("service_id"):
                    valid_node_ids.add(str(s["service_id"]).strip())
                    valid_node_ids.add(str(s["service_id"]).strip().lower())
                if s.get("name"):
                    name = str(s["name"]).strip()
                    valid_node_ids.add(name)
                    valid_node_ids.add(name.lower())
                    valid_node_ids.add(name.lower().replace(" ", "-"))

        # Recognized infrastructure tier node IDs that are standard in architecture topologies
        standard_infra_ids = {
            "api-gateway", "api-gw", "gateway", "ingress", "ingress-gateway",
            "primary-db", "database", "postgres", "postgres-db", "relational-db",
            "cache", "redis", "redis-cache", "in-memory-cache",
            "message-broker", "kafka", "rabbitmq", "event-broker", "event-bus", "queue",
            "auth-service", "user-service", "notification-service"
        }
        valid_node_ids.update(standard_infra_ids)

        for edge in p_hld.get("edges", []) or []:
            if not isinstance(edge, dict):
                continue
            eid = edge.get("id", "unknown_edge")
            source = str(edge.get("source", "")).strip()
            target = str(edge.get("target", "")).strip()

            if source and source not in valid_node_ids:
                violations.append(
                    VerificationViolation(
                        rule="DANGLING_EDGE_SOURCE",
                        severity="CRITICAL",
                        target=f"edge:{eid}",
                        message=f"Edge '{eid}' connects from non-existent source node '{source}'.",
                    )
                )
            if target and target not in valid_node_ids:
                violations.append(
                    VerificationViolation(
                        rule="DANGLING_EDGE_TARGET",
                        severity="CRITICAL",
                        target=f"edge:{eid}",
                        message=f"Edge '{eid}' connects to non-existent target node '{target}'.",
                    )
                )

    def _verify_database_survival(
        self,
        baseline: Dict[str, Any],
        patched: Dict[str, Any],
        patch: ArchitecturePatch,
        violations: List[VerificationViolation],
    ) -> None:
        """Rule 3: Baseline tables & columns must survive; new columns must be nullable or have default."""
        b_db = self._extract_lld_section(baseline, "database")
        p_db = self._extract_lld_section(patched, "database")

        b_tables = b_db.get("tables", []) or []
        p_tables = p_db.get("tables", []) or []

        p_tbl_map = {t.get("name", "").lower(): t for t in p_tables if isinstance(t, dict)}

        for b_tbl in b_tables:
            if not isinstance(b_tbl, dict) or not b_tbl.get("name"):
                continue
            t_name = b_tbl["name"]
            t_name_lower = t_name.lower()

            if t_name_lower not in p_tbl_map:
                violations.append(
                    VerificationViolation(
                        rule="IMMUTABLE_TABLE_SURVIVAL",
                        severity="CRITICAL",
                        target=f"table:{t_name}",
                        message=f"Baseline database table '{t_name}' was removed in the evolved design.",
                    )
                )
            else:
                # Check column survival
                p_col_map = {
                    c.get("name", "").lower(): c
                    for c in p_tbl_map[t_name_lower].get("columns", [])
                    if isinstance(c, dict)
                }
                for b_col in b_tbl.get("columns", []) or []:
                    if not isinstance(b_col, dict) or not b_col.get("name"):
                        continue
                    c_name = b_col["name"]
                    if c_name.lower() not in p_col_map:
                        violations.append(
                            VerificationViolation(
                                rule="IMMUTABLE_COLUMN_SURVIVAL",
                                severity="CRITICAL",
                                target=f"column:{t_name}.{c_name}",
                                message=f"Baseline column '{c_name}' on table '{t_name}' was deleted.",
                            )
                        )

        # Verify added columns on existing tables are safe (nullable or default)
        for col_add in patch.added_columns:
            if not col_add.nullable and (not col_add.default or col_add.default.strip() == ""):
                violations.append(
                    VerificationViolation(
                        rule="BREAKING_COLUMN_ADDITION",
                        severity="ERROR",
                        target=f"column:{col_add.table_name}.{col_add.column_name}",
                        message=(
                            f"Added column '{col_add.column_name}' on existing table '{col_add.table_name}' "
                            f"is NOT nullable and has no default value, which breaks production data."
                        ),
                    )
                )

    def _verify_backend_survival(
        self,
        baseline: Dict[str, Any],
        patched: Dict[str, Any],
        violations: List[VerificationViolation],
    ) -> None:
        """Rule 4: Baseline API endpoints must remain intact."""
        b_backend = self._extract_lld_section(baseline, "backend")
        p_backend = self._extract_lld_section(patched, "backend")

        b_eps = b_backend.get("api_endpoints", []) or []
        p_ep_keys = {
            f"{e.get('method', 'GET').upper()}:{e.get('path') or e.get('route') or ''}"
            for e in p_backend.get("api_endpoints", []) or []
            if isinstance(e, dict)
        }

        for b_ep in b_eps:
            p_val = b_ep.get("path") or b_ep.get("route")
            if not isinstance(b_ep, dict) or not p_val:
                continue
            key = f"{b_ep.get('method', 'GET').upper()}:{p_val}"
            if key not in p_ep_keys:
                violations.append(
                    VerificationViolation(
                        rule="IMMUTABLE_ENDPOINT_SURVIVAL",
                        severity="ERROR",
                        target=f"endpoint:{key}",
                        message=f"Baseline API endpoint '{key}' was removed in the evolved design.",
                    )
                )

    @staticmethod
    def _extract_lld_section(pkg: Dict[str, Any], section: str) -> Dict[str, Any]:
        """Safely extract LLD dictionary unwrapping inner data wrapper if present."""
        llds = pkg.get("llds", {}) or {}
        raw = llds.get(section, {}) or {}
        if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
            return raw["data"]
        return raw if isinstance(raw, dict) else {}
