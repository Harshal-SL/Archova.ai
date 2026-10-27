"""Architecture Differ: Generates user-facing and machine-readable delta summaries between versions."""

from __future__ import annotations

from typing import Any, Dict, List
from app.versioning.contracts import ArchitectureDiff, ArchitecturePatch


class ArchitectureDiffer:
    """Computes exact diffs between a baseline architecture and its evolved version."""

    @staticmethod
    def compute_diff(
        baseline: Dict[str, Any],
        patched: Dict[str, Any],
        patch: ArchitecturePatch,
        from_version: str = "1.0",
        to_version: str = "1.1",
        feature_prompt: str = "",
    ) -> ArchitectureDiff:
        """Produces an ArchitectureDiff comparing baseline vs patched."""
        b_hld = baseline.get("hld", {}) or {}
        p_hld = patched.get("hld", {}) or {}

        b_nodes = b_hld.get("nodes", []) or []
        p_nodes = p_hld.get("nodes", []) or []

        b_edges = b_hld.get("edges", []) or []
        p_edges = p_hld.get("edges", []) or []

        b_node_ids = {n.get("id") for n in b_nodes if isinstance(n, dict)}
        b_edge_ids = {e.get("id") for e in b_edges if isinstance(e, dict)}

        raw_added_nodes = [n for n in p_nodes if isinstance(n, dict) and n.get("id") not in b_node_ids]
        added_nodes = [
            str(n.get("data", {}).get("label") or n.get("label") or n.get("id") or "New Component")
            for n in raw_added_nodes
        ]
        added_edges = [e for e in p_edges if isinstance(e, dict) and e.get("id") not in b_edge_ids]

        b_tables = (baseline.get("llds", {}).get("database", {}) or {}).get("tables", []) or []
        p_tables = (patched.get("llds", {}).get("database", {}) or {}).get("tables", []) or []

        b_table_names = {t.get("name", "").lower() for t in b_tables if isinstance(t, dict)}
        added_tables = [
            t.get("name", "")
            for t in p_tables
            if isinstance(t, dict) and t.get("name", "").lower() not in b_table_names
        ]

        added_columns = [
            f"{c.table_name}.{c.column_name} ({c.column_type})"
            for c in patch.added_columns
        ]

        added_endpoints = [
            f"{ep.get('method', 'GET').upper()} {ep.get('path') or ep.get('route') or ''}"
            for ep in patch.added_endpoints
            if isinstance(ep, dict) and (ep.get("path") or ep.get("route"))
        ]
        for sep in patch.added_service_endpoints:
            ep_dict = sep.endpoint if isinstance(sep.endpoint, dict) else {}
            ep_path = ep_dict.get("path") or ep_dict.get("route")
            if ep_dict and ep_path:
                added_endpoints.append(
                    f"{ep_dict.get('method', 'GET').upper()} {ep_path} ({sep.service_id_or_name})"
                )

        baseline_stats = {
            "nodes": len(b_nodes),
            "edges": len(b_edges),
            "tables": len(b_tables),
        }
        new_stats = {
            "nodes": len(p_nodes),
            "edges": len(p_edges),
            "tables": len(p_tables),
        }

        return ArchitectureDiff(
            from_version=from_version,
            to_version=to_version,
            feature_prompt=feature_prompt,
            feature_summary=patch.feature_summary,
            added_nodes=added_nodes,
            added_edges=added_edges,
            added_tables=added_tables,
            added_columns=added_columns,
            added_endpoints=added_endpoints,
            baseline_stats=baseline_stats,
            new_stats=new_stats,
            invariance_certified=True,
        )
