"""Layer 0 Normalizer: Transforms raw architecture packages into NormalizedPackage.

Extracts:
- Requirements (FR, NFR)
- Components (HLD, Backend, Frontend, Cloud)
- Endpoints (Backend API operations)
- Tables (Database schemas, columns, PKs, FKs)
- Routes (Frontend views and navigation)
- Security Controls
- Scaffold file contents

Discovers orphan references as low-severity findings with rule_id "L0.ORPHAN_REF".
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from Validator_Engine_v2.schemas import (
    Finding,
    NormalizedComponent,
    NormalizedEndpoint,
    NormalizedPackage,
    NormalizedRequirement,
    NormalizedRoute,
    NormalizedSecurityControl,
    NormalizedTable,
)


def _unwrap_lld(raw: Any) -> Dict[str, Any]:
    """Handles both wrapped {status, data, error} and bare dict forms."""
    if not isinstance(raw, dict):
        return {}
    if "data" in raw and isinstance(raw["data"], dict):
        return raw["data"]
    return raw


def _clean_path(path: str) -> str:
    """Normalize path by removing trailing slash and normalizing parameters like {id}."""
    p = str(path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/+", "/", p)
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    # Replace variable names like {slot_id} with {*} for comparison if needed
    return p


class PackageNormalizer:
    """Normalizes an architecture package and detects orphan cross-references."""

    def normalize(self, package: Dict[str, Any]) -> NormalizedPackage:
        raw_pkg = package or {}
        generation_id = str(raw_pkg.get("generation_id", raw_pkg.get("id", "gen_unknown")))

        arsrs = raw_pkg.get("arsrs") or {}
        if not isinstance(arsrs, dict):
            arsrs = {}
        hld = raw_pkg.get("hld") or {}
        if not isinstance(hld, dict):
            hld = {}
        llds = raw_pkg.get("llds") or {}
        if not isinstance(llds, dict):
            llds = {}

        system_name = (
            arsrs.get("system_name")
            or hld.get("system_name")
            or raw_pkg.get("system_name")
            or "Architecture System"
        )
        domain = (
            arsrs.get("domain")
            or arsrs.get("domain_context", {}).get("industry")
            or raw_pkg.get("domain")
            or "Enterprise Software"
        )

        l0_findings: List[Finding] = []

        # ── 1. Requirements (FR & NFR) ──────────────────────────────────────────
        requirements: List[NormalizedRequirement] = []
        raw_frs = arsrs.get("functional_requirements", [])
        if isinstance(raw_frs, list):
            for i, fr in enumerate(raw_frs):
                if isinstance(fr, dict):
                    r_id = str(fr.get("id") or f"FR-{i+1:03d}")
                    text = str(fr.get("description") or fr.get("title") or fr.get("text") or "")
                    target = fr.get("target") or fr.get("module") or fr.get("priority")
                    requirements.append(NormalizedRequirement(id=r_id, text=text, type="FR", target=str(target) if target else None))
                elif isinstance(fr, str):
                    requirements.append(NormalizedRequirement(id=f"FR-{i+1:03d}", text=fr, type="FR"))

        raw_nfrs = arsrs.get("non_functional_requirements", [])
        if isinstance(raw_nfrs, list):
            for i, nfr in enumerate(raw_nfrs):
                if isinstance(nfr, dict):
                    r_id = str(nfr.get("id") or f"NFR-{i+1:03d}")
                    text = str(nfr.get("description") or nfr.get("title") or nfr.get("text") or "")
                    category = nfr.get("category") or nfr.get("type")
                    requirements.append(NormalizedRequirement(id=r_id, text=text, type="NFR", target=str(category) if category else None))
                elif isinstance(nfr, str):
                    requirements.append(NormalizedRequirement(id=f"NFR-{i+1:03d}", text=nfr, type="NFR"))

        # ── 2. Components ───────────────────────────────────────────────────────
        components: List[NormalizedComponent] = []
        comp_names: Set[str] = set()

        # From HLD major_services
        for svc in hld.get("major_services", []):
            if isinstance(svc, dict):
                sname = str(svc.get("name") or "").strip()
                sresp = str(svc.get("responsibility") or svc.get("description") or "").strip()
                if sname:
                    components.append(NormalizedComponent(name=sname, responsibility=sresp, artifact="hld"))
                    comp_names.add(sname.lower())

        # From Backend services
        backend_lld = _unwrap_lld(llds.get("backend", {}))
        for svc in backend_lld.get("services", []):
            if isinstance(svc, dict):
                sname = str(svc.get("name") or "").strip()
                sresp = str(svc.get("responsibility") or svc.get("description") or "").strip()
                if sname and sname.lower() not in comp_names:
                    components.append(NormalizedComponent(name=sname, responsibility=sresp, artifact="backend"))
                    comp_names.add(sname.lower())

        # From Frontend components
        frontend_lld = _unwrap_lld(llds.get("frontend", {}))
        for cmp in frontend_lld.get("components", []):
            if isinstance(cmp, dict):
                cname = str(cmp.get("name") or "").strip()
                cresp = str(cmp.get("responsibility") or cmp.get("purpose") or "").strip()
                if cname:
                    components.append(NormalizedComponent(name=cname, responsibility=cresp, artifact="frontend"))

        # ── 3. Endpoints (Backend API) ──────────────────────────────────────────
        endpoints: List[NormalizedEndpoint] = []
        endpoint_paths: Set[str] = set()
        endpoint_patterns: List[Tuple[str, str]] = []  # (method, path)

        for ep in backend_lld.get("api_endpoints", []):
            if isinstance(ep, dict):
                method = str(ep.get("method") or "GET").upper().strip()
                path = _clean_path(str(ep.get("path") or ep.get("route") or ""))
                svc = ep.get("service")
                auth = bool(ep.get("auth_required", False))
                if path:
                    endpoints.append(NormalizedEndpoint(method=method, path=path, service=str(svc) if svc else None, auth_required=auth))
                    endpoint_paths.add(path)
                    endpoint_patterns.append((method, path))

                    # Orphan check: Does endpoint specify a service that isn't defined?
                    if svc and str(svc).strip().lower() not in comp_names and len(comp_names) > 0:
                        l0_findings.append(
                            Finding.create(
                                layer="L0",
                                rule_id="L0.ORPHAN_REF",
                                artifact="backend",
                                severity="low",
                                message=f"Backend endpoint '{method} {path}' references unknown service '{svc}'.",
                                evidence_path=f"/llds/backend/api_endpoints/{path}",
                                source="IEEE1016",
                                suggested_fix=f"Register service '{svc}' in HLD or Backend LLD services list.",
                            )
                        )

        # ── 4. Tables (Database) ────────────────────────────────────────────────
        tables: List[NormalizedTable] = []
        table_names: Set[str] = set()
        database_lld = _unwrap_lld(llds.get("database", {}))

        for tbl in database_lld.get("tables", []):
            if isinstance(tbl, dict):
                tname = str(tbl.get("name") or "").strip().lower()
                if not tname:
                    continue
                table_names.add(tname)

                cols: List[str] = []
                pks: List[str] = []
                fks: List[Dict[str, str]] = []

                for col in tbl.get("columns", []):
                    if isinstance(col, dict):
                        cname = str(col.get("name") or "").strip()
                        if cname:
                            cols.append(cname)
                            if col.get("primary_key") or col.get("pk"):
                                pks.append(cname)
                            if col.get("foreign_key"):
                                fks.append({"column": cname, "references": str(col["foreign_key"])})
                    elif isinstance(col, str):
                        cols.append(col)

                tables.append(NormalizedTable(name=tname, columns=cols, pks=pks, fks=fks))

        # Check for orphan foreign keys
        for tbl in tables:
            for fk in tbl.fks:
                ref = fk.get("references", "")
                ref_tbl = ref.split(".")[0].strip().lower() if "." in ref else ref.strip().lower()
                if ref_tbl and ref_tbl not in table_names and len(table_names) > 0:
                    l0_findings.append(
                        Finding.create(
                            layer="L0",
                            rule_id="L0.ORPHAN_REF",
                            artifact="database",
                            severity="low",
                            message=f"Table '{tbl.name}' has foreign key referencing non-existent table '{ref_tbl}'.",
                            evidence_path=f"/llds/database/tables/{tbl.name}",
                            source="ISO25012",
                            suggested_fix=f"Define referenced table '{ref_tbl}' in Database LLD.",
                        )
                    )

        # ── 5. Routes (Frontend) ────────────────────────────────────────────────
        routes: List[NormalizedRoute] = []
        for p in frontend_lld.get("pages", []):
            if isinstance(p, dict):
                rpath = _clean_path(str(p.get("path") or p.get("route") or ""))
                cmp = p.get("component") or p.get("name")
                linked_ep = p.get("api_endpoint") or p.get("endpoint")
                routes.append(NormalizedRoute(path=rpath, component=str(cmp) if cmp else None, linked_endpoint=str(linked_ep) if linked_ep else None))

        # Check frontend api_integration bindings against backend endpoints
        api_int = frontend_lld.get("api_integration", {})
        if isinstance(api_int, dict):
            calls = api_int.get("endpoints_consumed") or api_int.get("endpoints") or []
            if isinstance(calls, list):
                for call in calls:
                    cpath = _clean_path(str(call.get("path") or call.get("route") if isinstance(call, dict) else call))
                    if cpath and endpoint_paths:
                        # Check if matches any endpoint path or parametric match
                        matched = any(
                            cpath == ep or re.sub(r"\{[^}]+\}", "[^/]+", ep) == cpath or re.match(re.sub(r"\{[^}]+\}", "[^/]+", ep), cpath)
                            for ep in endpoint_paths
                        )
                        if not matched:
                            l0_findings.append(
                                Finding.create(
                                    layer="L0",
                                    rule_id="L0.ORPHAN_REF",
                                    artifact="frontend",
                                    severity="low",
                                    message=f"Frontend api_integration references endpoint '{cpath}' which is not in Backend LLD endpoints.",
                                    evidence_path="/llds/frontend/api_integration",
                                    source="IEEE1016",
                                    suggested_fix=f"Add backend endpoint '{cpath}' to Backend LLD.",
                                )
                            )

        # ── 6. Security Controls ────────────────────────────────────────────────
        security_controls: List[NormalizedSecurityControl] = []
        security_lld = _unwrap_lld(llds.get("security", {}))
        for ctrl in security_lld.get("security_controls", []):
            if isinstance(ctrl, dict):
                cid = str(ctrl.get("id") or ctrl.get("control_id") or f"SEC-{len(security_controls)+1}")
                cat = str(ctrl.get("category") or ctrl.get("type") or "general")
                desc = str(ctrl.get("description") or ctrl.get("name") or "")
                security_controls.append(NormalizedSecurityControl(control_id=cid, category=cat, description=desc))

        # ── 7. Scaffold Files ───────────────────────────────────────────────────
        scaffolds_dict: Dict[str, str] = {}
        raw_scaffolds = raw_pkg.get("scaffolds") or raw_pkg.get("scaffold_files") or {}
        if isinstance(raw_scaffolds, dict):
            for path_key, content in raw_scaffolds.items():
                if isinstance(content, str):
                    scaffolds_dict[str(path_key).strip()] = content

        return NormalizedPackage(
            generation_id=generation_id,
            system_name=system_name,
            domain=domain,
            requirements=requirements,
            components=components,
            endpoints=endpoints,
            tables=tables,
            routes=routes,
            security_controls=security_controls,
            scaffold_files=scaffolds_dict,
            raw_package=raw_pkg,
            l0_findings=l0_findings,
        )
