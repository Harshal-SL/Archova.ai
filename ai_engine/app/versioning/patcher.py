"""Architecture Patcher: Pure deterministic module to apply an ArchitecturePatch to a baseline package."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional
from app.versioning.contracts import ArchitecturePatch, ColumnAddition, ExistingServiceEndpointAddition


class ArchitecturePatcher:
    """Applies an additive ArchitecturePatch onto an existing immutable baseline package."""

    def __init__(self, target_version: str = "1.1") -> None:
        self.target_version = target_version

    def apply_patch(
        self,
        baseline: Dict[str, Any],
        patch: ArchitecturePatch,
    ) -> Dict[str, Any]:
        """Deep-copies the baseline and applies the patch strictly additively.
        
        Guarantees that all baseline nodes, edges, tables, and endpoints remain intact,
        while embedding the new feature elements tagged with version_added and is_new.
        """
        # 1. Deep copy baseline to guarantee immutability of the original input
        patched: Dict[str, Any] = copy.deepcopy(baseline)

        # 2. Patch HLD (High-Level Design)
        self._patch_hld(patched, patch)

        # 3. Patch LLDs (Low-Level Designs)
        self._patch_llds(patched, patch)

        # 4. Update package version metadata
        patched["version"] = self.target_version
        patched["version_tag"] = f"v{self.target_version}"
        patched["is_evolution"] = True
        patched["feature_summary"] = patch.feature_summary

        return patched

    def _patch_hld(self, pkg: Dict[str, Any], patch: ArchitecturePatch) -> None:
        """Inject newly added nodes and edges into HLD without mutating existing ones."""
        hld = pkg.setdefault("hld", {})
        existing_nodes: List[Dict[str, Any]] = hld.setdefault("nodes", [])
        existing_edges: List[Dict[str, Any]] = hld.setdefault("edges", [])

        existing_node_ids = {n.get("id") for n in existing_nodes if isinstance(n, dict)}
        existing_edge_ids = {e.get("id") for e in existing_edges if isinstance(e, dict)}

        # If baseline nodes were empty but major_services exists, synthesize baseline nodes
        if not existing_nodes and hld.get("major_services"):
            gw_node = {
                "id": "api-gateway",
                "type": "gateway",
                "data": {"label": "API Gateway", "category": "gateway", "role": "Ingress Routing & Auth Guard"},
            }
            existing_nodes.append(gw_node)
            existing_node_ids.add("api-gateway")

            for idx, svc in enumerate(hld.get("major_services", [])):
                if not isinstance(svc, dict):
                    continue
                s_name = svc.get("name") or f"Service-{idx + 1}"
                s_id = str(svc.get("service_id") or s_name.lower().replace(" ", "-")).strip()
                s_role = svc.get("responsibility") or svc.get("role") or ""
                existing_nodes.append({
                    "id": s_id,
                    "type": "service",
                    "data": {"label": s_name, "category": "service", "role": s_role},
                })
                existing_node_ids.add(s_id)

            data_strat = hld.get("data_strategy", {})
            if isinstance(data_strat, dict) and data_strat.get("primary_database"):
                existing_nodes.append({
                    "id": "primary-db",
                    "type": "database",
                    "data": {"label": str(data_strat["primary_database"]), "category": "database"},
                })
                existing_node_ids.add("primary-db")

        # Append new nodes
        for node in patch.added_nodes:
            if not isinstance(node, dict) or not node.get("id"):
                continue
            node_id = str(node["id"]).strip()
            if node_id in existing_node_ids:
                continue  # Skip duplicate or collisions, baseline takes absolute precedence

            node_copy = copy.deepcopy(node)
            data_dict = node_copy.setdefault("data", {})
            if isinstance(data_dict, dict):
                data_dict["version_added"] = self.target_version
                data_dict["is_new"] = True
            node_copy["version_added"] = self.target_version
            node_copy["is_new"] = True

            existing_nodes.append(node_copy)
            existing_node_ids.add(node_id)

        # Also sync new services into major_services if present
        if "major_services" in hld or not existing_nodes:
            major_services = hld.setdefault("major_services", [])
            existing_svc_names = {s.get("name", "").lower() for s in major_services if isinstance(s, dict)}
            for node in patch.added_nodes:
                if not isinstance(node, dict):
                    continue
                ntype = str(node.get("type", "service")).lower()
                if ntype in ("service", "microservice"):
                    nlabel = node.get("data", {}).get("label") or node.get("label") or node.get("id")
                    if nlabel and str(nlabel).lower() not in existing_svc_names:
                        major_services.append({
                            "service_id": str(node.get("id", f"SVC-{len(major_services)+1:02d}")),
                            "name": str(nlabel),
                            "responsibility": str(node.get("data", {}).get("role") or f"Handles {nlabel} capabilities"),
                            "version_added": self.target_version,
                            "is_new": True,
                        })
                        existing_svc_names.add(str(nlabel).lower())

        # Append new edges
        for idx, edge in enumerate(patch.added_edges):
            if not isinstance(edge, dict):
                continue
            edge_copy = copy.deepcopy(edge)
            edge_id = edge_copy.get("id") or f"e-evolved-{self.target_version.replace('.', '_')}-{idx + 1}"
            edge_copy["id"] = str(edge_id)

            if edge_copy["id"] in existing_edge_ids:
                continue

            data_dict = edge_copy.setdefault("data", {})
            if isinstance(data_dict, dict):
                data_dict["version_added"] = self.target_version
                data_dict["is_new"] = True
            edge_copy["version_added"] = self.target_version
            edge_copy["is_new"] = True

            existing_edges.append(edge_copy)
            existing_edge_ids.add(edge_copy["id"])

    def _patch_llds(self, pkg: Dict[str, Any], patch: ArchitecturePatch) -> None:
        """Patch all 5 LLD domains (database, backend, frontend, security, cloud)."""
        llds = pkg.setdefault("llds", {})
        if not isinstance(llds, dict):
            llds = {}
            pkg["llds"] = llds

        self._patch_database_lld(llds, patch)
        self._patch_backend_lld(llds, patch)
        self._patch_frontend_lld(llds, patch)
        self._patch_security_lld(llds, patch)
        self._patch_cloud_lld(llds, patch)

    def _patch_database_lld(self, llds: Dict[str, Any], patch: ArchitecturePatch) -> None:
        """Add new tables, relationships, and additive nullable columns."""
        db_lld = llds.setdefault("database", {})
        if "data" in db_lld and isinstance(db_lld["data"], dict):
            db_target = db_lld["data"]
        else:
            db_target = db_lld

        tables: List[Dict[str, Any]] = db_target.setdefault("tables", [])
        existing_table_names = {t.get("name", "").lower(): t for t in tables if isinstance(t, dict)}

        # 1. Append new tables
        for tbl in patch.added_tables:
            if not isinstance(tbl, dict) or not tbl.get("name"):
                continue
            name_lower = str(tbl["name"]).strip().lower()
            if name_lower in existing_table_names:
                continue  # Invariant: do not overwrite existing baseline tables

            tbl_copy = copy.deepcopy(tbl)
            tbl_copy["version_added"] = self.target_version
            tbl_copy["is_new"] = True
            tables.append(tbl_copy)
            existing_table_names[name_lower] = tbl_copy

        # 2. Add allowed additive columns to existing tables
        for col_add in patch.added_columns:
            target_tbl = existing_table_names.get(col_add.table_name.strip().lower())
            if not target_tbl:
                continue
            col_list: List[Dict[str, Any]] = target_tbl.setdefault("columns", [])
            existing_col_names = {c.get("name", "").lower() for c in col_list if isinstance(c, dict)}

            if col_add.column_name.strip().lower() not in existing_col_names:
                new_col_dict = {
                    "name": col_add.column_name,
                    "type": col_add.column_type,
                    "nullable": col_add.nullable,
                    "default": col_add.default,
                    "references": col_add.references,
                    "version_added": self.target_version,
                    "is_new": True,
                }
                col_list.append(new_col_dict)
                target_tbl["version_added"] = self.target_version
                target_tbl["is_new"] = True

        # 3. Append new relationships
        relationships: List[Dict[str, Any]] = db_target.setdefault("relationships", [])
        for rel in patch.added_relationships:
            if isinstance(rel, dict):
                rel_copy = copy.deepcopy(rel)
                rel_copy["version_added"] = self.target_version
                relationships.append(rel_copy)

    def _patch_backend_lld(self, llds: Dict[str, Any], patch: ArchitecturePatch) -> None:
        """Add new backend services, standalone endpoints, and service endpoints."""
        backend_lld = llds.setdefault("backend", {})
        if "data" in backend_lld and isinstance(backend_lld["data"], dict):
            b_target = backend_lld["data"]
        else:
            b_target = backend_lld

        # 1. Append new services
        services: List[Dict[str, Any]] = b_target.setdefault("services", [])
        existing_services = {s.get("name", "").lower(): s for s in services if isinstance(s, dict)}

        for s in patch.added_services:
            if isinstance(s, dict) and s.get("name"):
                s_name_lower = str(s["name"]).strip().lower()
                if s_name_lower not in existing_services:
                    s_copy = copy.deepcopy(s)
                    s_copy["version_added"] = self.target_version
                    s_copy["is_new"] = True
                    services.append(s_copy)
                    existing_services[s_name_lower] = s_copy

        # 2. Append new endpoints
        endpoints: List[Dict[str, Any]] = b_target.setdefault("api_endpoints", [])
        existing_endpoint_keys = {
            f"{e.get('method', 'GET').upper()}:{e.get('path') or e.get('route') or ''}" for e in endpoints if isinstance(e, dict)
        }

        for ep in patch.added_endpoints:
            ep_path = ep.get("path") or ep.get("route")
            if isinstance(ep, dict) and ep_path:
                method = ep.get("method", "GET").upper()
                key = f"{method}:{ep_path}"
                if key not in existing_endpoint_keys:
                    ep_copy = copy.deepcopy(ep)
                    ep_copy["path"] = ep_path
                    ep_copy["route"] = ep_path
                    ep_copy["version_added"] = self.target_version
                    ep_copy["is_new"] = True
                    endpoints.append(ep_copy)
                    existing_endpoint_keys.add(key)

        # 3. Append endpoints to existing services
        for sep in patch.added_service_endpoints:
            ep_dict = sep.endpoint if isinstance(sep.endpoint, dict) else {}
            ep_path = ep_dict.get("path") or ep_dict.get("route")
            if ep_dict and ep_path:
                method = ep_dict.get("method", "GET").upper()
                key = f"{method}:{ep_path}"
                if key not in existing_endpoint_keys:
                    ep_copy = copy.deepcopy(ep_dict)
                    ep_copy["path"] = ep_path
                    ep_copy["route"] = ep_path
                    ep_copy["service"] = sep.service_id_or_name
                    ep_copy["version_added"] = self.target_version
                    ep_copy["is_new"] = True
                    endpoints.append(ep_copy)
                    existing_endpoint_keys.add(key)

    def _patch_frontend_lld(self, llds: Dict[str, Any], patch: ArchitecturePatch) -> None:
        """Add new pages and UI components to Frontend LLD."""
        frontend_lld = llds.setdefault("frontend", {})
        if "data" in frontend_lld and isinstance(frontend_lld["data"], dict):
            f_target = frontend_lld["data"]
        else:
            f_target = frontend_lld

        pages: List[Dict[str, Any]] = f_target.setdefault("pages", [])
        for p in patch.added_pages:
            if isinstance(p, dict):
                p_copy = copy.deepcopy(p)
                p_copy["version_added"] = self.target_version
                p_copy["is_new"] = True
                pages.append(p_copy)

        components: List[Dict[str, Any]] = f_target.setdefault("components", [])
        for c in patch.added_components:
            if isinstance(c, dict):
                c_copy = copy.deepcopy(c)
                c_copy["version_added"] = self.target_version
                c_copy["is_new"] = True
                components.append(c_copy)

    def _patch_security_lld(self, llds: Dict[str, Any], patch: ArchitecturePatch) -> None:
        """Append new security controls."""
        sec_lld = llds.setdefault("security", {})
        if "data" in sec_lld and isinstance(sec_lld["data"], dict):
            s_target = sec_lld["data"]
        else:
            s_target = sec_lld

        controls: List[Dict[str, Any]] = s_target.setdefault("security_controls", [])
        for sc in patch.added_security_controls:
            if isinstance(sc, dict):
                sc_copy = copy.deepcopy(sc)
                sc_copy["version_added"] = self.target_version
                sc_copy["is_new"] = True
                controls.append(sc_copy)

    def _patch_cloud_lld(self, llds: Dict[str, Any], patch: ArchitecturePatch) -> None:
        """Append new cloud resources."""
        cloud_lld = llds.setdefault("cloud", {})
        if "data" in cloud_lld and isinstance(cloud_lld["data"], dict):
            c_target = cloud_lld["data"]
        else:
            c_target = cloud_lld

        # 1. Sync new cloud services into services list for LLDGraph
        services = c_target.setdefault("services", [])
        for res in patch.added_cloud_resources:
            if isinstance(res, dict) and res.get("name"):
                res_copy = copy.deepcopy(res)
                res_copy["version_added"] = self.target_version
                res_copy["is_new"] = True
                services.append(res_copy)

        compute: Dict[str, Any] = c_target.setdefault("compute", {})
        if isinstance(compute, dict):
            new_res = compute.setdefault("additional_services", [])
            if isinstance(new_res, list):
                for res in patch.added_cloud_resources:
                    if isinstance(res, dict):
                        res_copy = copy.deepcopy(res)
                        res_copy["version_added"] = self.target_version
                        res_copy["is_new"] = True
                        new_res.append(res_copy)
