"""Delta Prompt Builder: Constructs token-efficient compact baseline summaries and evolution prompts for the LLM."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from app.versioning.contracts import VerificationViolation


class DeltaPromptBuilder:
    """Builds token-compact prompts instructing the LLM to output ONLY additive ArchitecturePatch JSON."""

    @staticmethod
    def build_compact_baseline_summary(baseline: Dict[str, Any]) -> str:
        """Extracts a high-density, token-efficient summary of the existing architecture baseline."""
        lines: List[str] = []

        # System Header
        hld = baseline.get("hld", {}) or {}
        sys_name = baseline.get("prompt") or hld.get("system_name") or "Enterprise Distributed System"
        arch_style = hld.get("architecture_style", "Microservices Architecture")
        lines.append(f"SYSTEM: {sys_name}")
        lines.append(f"STYLE: {arch_style}")
        lines.append("")

        # Nodes Summary - extract from explicit nodes or major_services
        nodes = hld.get("nodes", []) or []
        extracted_nodes: List[Dict[str, Any]] = []

        if nodes:
            for n in nodes:
                if isinstance(n, dict):
                    extracted_nodes.append(n)
        else:
            # Fallback to major_services from SAE HLD
            major_services = hld.get("major_services", []) or hld.get("services", []) or []
            if major_services:
                # Add default API gateway node if not present
                extracted_nodes.append({
                    "id": "api-gateway",
                    "type": "gateway",
                    "data": {"label": "API Gateway", "role": "Ingress Routing & Auth Guard"},
                })
                for idx, svc in enumerate(major_services):
                    if not isinstance(svc, dict):
                        continue
                    s_name = svc.get("name") or f"Service-{idx + 1}"
                    s_id = str(svc.get("service_id") or s_name.lower().replace(" ", "-")).strip()
                    s_role = svc.get("responsibility") or svc.get("role") or ""
                    extracted_nodes.append({
                        "id": s_id,
                        "type": "service",
                        "data": {"label": s_name, "role": s_role},
                    })
                # Add primary database from data_strategy if present
                data_strat = hld.get("data_strategy", {})
                if isinstance(data_strat, dict) and data_strat.get("primary_database"):
                    extracted_nodes.append({
                        "id": "primary-db",
                        "type": "database",
                        "data": {"label": str(data_strat["primary_database"]), "role": "Core Relational Persistence"},
                    })

        lines.append(f"EXISTING NODES ({len(extracted_nodes)} components):")
        for n in extracted_nodes:
            if not isinstance(n, dict):
                continue
            nid = n.get("id", "")
            ntype = n.get("type", "service")
            nlabel = n.get("data", {}).get("label") or n.get("label") or nid
            nrole = n.get("data", {}).get("role") or ""
            role_snippet = f" - {nrole[:80]}..." if len(nrole) > 80 else f" - {nrole}" if nrole else ""
            lines.append(f"  • [{nid}] ({ntype}) \"{nlabel}\"{role_snippet}")
        lines.append("")

        # Edges Summary
        edges = hld.get("edges", []) or []
        lines.append(f"EXISTING EDGES ({len(edges)} connections):")
        for e in edges:
            if not isinstance(e, dict):
                continue
            src = e.get("source")
            tgt = e.get("target")
            proto = e.get("label") or e.get("data", {}).get("protocol") or "TCP"
            lines.append(f"  • {src} ──[{proto}]──► {tgt}")
        lines.append("")

        # Database Tables Summary
        db_lld = baseline.get("llds", {}).get("database", {}) or {}
        if isinstance(db_lld, dict) and "data" in db_lld:
            db_lld = db_lld["data"]
        tables = db_lld.get("tables", []) if isinstance(db_lld, dict) else []
        lines.append(f"EXISTING DATABASE TABLES ({len(tables)} tables):")
        for t in tables:
            if not isinstance(t, dict):
                continue
            tname = t.get("name", "")
            cols = [c.get("name", "") for c in t.get("columns", []) if isinstance(c, dict) and c.get("name")]
            lines.append(f"  • {tname} (columns: {', '.join(cols[:8])}{', ...' if len(cols) > 8 else ''})")
        lines.append("")

        # Backend Endpoints Summary - support both 'path' and 'route'
        b_lld = baseline.get("llds", {}).get("backend", {}) or {}
        if isinstance(b_lld, dict) and "data" in b_lld:
            b_lld = b_lld["data"]
        endpoints = b_lld.get("api_endpoints", []) if isinstance(b_lld, dict) else []
        lines.append(f"EXISTING API ENDPOINTS ({len(endpoints)} endpoints):")
        for ep in endpoints[:10]:
            if not isinstance(ep, dict):
                continue
            m = ep.get("method", "GET")
            p = ep.get("path") or ep.get("route") or ""
            lines.append(f"  • {m} {p}")
        if len(endpoints) > 10:
            lines.append(f"  • ... ({len(endpoints) - 10} more endpoints)")

        return "\n".join(lines)

    @classmethod
    def build_evolution_prompt(
        cls,
        baseline: Dict[str, Any],
        feature_prompt: str,
        violations: Optional[List[VerificationViolation]] = None,
    ) -> str:
        """Constructs the full prompt instructing the LLM to output ONLY an additive ArchitecturePatch."""
        compact_summary = cls.build_compact_baseline_summary(baseline)

        retry_block = ""
        if violations:
            violation_msgs = [f"- [{v.rule}] {v.target}: {v.message}" for v in violations]
            retry_block = (
                "\n\n⚠️ PREVIOUS ATTEMPT FAILED THE VERIFIER. YOU MUST FIX THESE VIOLATIONS:\n"
                + "\n".join(violation_msgs)
                + "\n"
            )

        return f"""You are a Principal Software Architect performing an ADDITIVE FEATURE EVOLUTION on an existing, running production system.

=== INCOMING FEATURE REQUEST ===
"{feature_prompt}"

=== IMMUTABLE BASELINE ARCHITECTURE ===
{compact_summary}
{retry_block}
=== STRICT ARCHITECTURAL CONTRACT ===
1. DO NOT recreate or regenerate the existing architecture.
2. The existing nodes, edges, tables, and endpoints are LIVE IN PRODUCTION. You cannot delete or rename them.
3. OUTPUT ONLY A DELTA PATCH (new components to add, and connections to existing components).
4. Every new edge MUST have a valid source and target matching either an existing node ID from the baseline, or a new node ID you are introducing.
5. If adding a column to an existing table, it MUST have nullable: true or a default value.
6. Return strictly valid JSON matching the ArchitecturePatch schema below. No markdown fences, no conversational text.

=== REQUIRED JSON OUTPUT SCHEMA ===
{{
  "version_bump": "minor",
  "feature_summary": "1-sentence technical summary of what was added",
  "added_nodes": [
    {{
      "id": "kebab-case-unique-id",
      "type": "service | database | cache | queue | gateway",
      "data": {{
        "label": "Display Title",
        "tech": "Specific Technology Choice",
        "role": "Single responsibility of this new component",
        "category": "service | database | cache | queue | gateway"
      }}
    }}
  ],
  "added_edges": [
    {{
      "id": "e-source-target-unique",
      "source": "existing-or-new-node-id",
      "target": "existing-or-new-node-id",
      "label": "Protocol / Transport (e.g. gRPC, HTTPS, AMQP, WebSocket)",
      "data": {{ "protocol": "HTTPS" }}
    }}
  ],
  "added_tables": [
    {{
      "name": "new_table_name",
      "description": "Table purpose",
      "columns": [
        {{ "name": "id", "type": "UUID", "is_primary_key": true }},
        {{ "name": "column_name", "type": "VARCHAR(255)", "nullable": false }}
      ]
    }}
  ],
  "added_columns": [
    {{
      "table_name": "existing_table_name",
      "column_name": "new_foreign_key_id",
      "column_type": "UUID",
      "nullable": true,
      "references": "other_table(id)"
    }}
  ],
  "added_endpoints": [
    {{
      "path": "/api/v1/new-feature",
      "method": "POST",
      "service": "target-service-id",
      "description": "Endpoint purpose"
    }}
  ]
}}"""
