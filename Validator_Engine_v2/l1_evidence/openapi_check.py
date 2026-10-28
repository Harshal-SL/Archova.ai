"""Layer 1: OpenAPI specification check against Backend LLD endpoints."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml
from openapi_spec_validator import validate
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from Validator_Engine_v2.schemas import Finding, NormalizedEndpoint


def _clean_path(path: str) -> str:
    p = str(path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/+", "/", p)
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p


def check_openapi(
    openapi_yaml_content: Optional[str],
    backend_endpoints: List[NormalizedEndpoint],
) -> Tuple[List[Finding], Dict[str, Any]]:
    """Validate OpenAPI YAML with openapi-spec-validator and compare operations to Backend LLD.

    Returns:
        findings: List[Finding] with rule_id starting with 'L1.OPENAPI_'
        meta: status and metrics summary
    """
    findings: List[Finding] = []
    meta: Dict[str, Any] = {
        "status": "ok",
        "total_operations": 0,
        "matched_operations": 0,
        "missing_in_spec": 0,
        "extra_in_spec": 0,
    }

    if openapi_yaml_content is None:
        meta["status"] = "not_evaluated"
        meta["message"] = "not evaluated: no scaffold provided"
        return findings, meta

    if not openapi_yaml_content.strip():
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.OPENAPI_SPEC_MISSING",
                artifact="backend",
                severity="critical",
                message="OpenAPI specification (openapi.yaml) is missing or empty.",
                evidence_path="scaffolds/openapi.yaml",
                source="IEEE1016",
                suggested_fix="Generate openapi.yaml documenting all backend endpoints.",
            )
        )
        meta["status"] = "missing"
        return findings, meta

    # 1. Parse YAML
    try:
        spec_dict = yaml.safe_load(openapi_yaml_content)
        if not isinstance(spec_dict, dict):
            raise ValueError("OpenAPI content does not parse as a YAML dictionary.")
    except Exception as exc:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.OPENAPI_SYNTAX_ERROR",
                artifact="backend",
                severity="critical",
                message=f"OpenAPI YAML syntax error: {str(exc)}",
                evidence_path="scaffolds/openapi.yaml",
                source="IEEE1016",
                suggested_fix="Correct YAML syntax formatting in openapi.yaml.",
            )
        )
        meta["status"] = "syntax_error"
        return findings, meta

    # 2. Validate OpenAPI Schema
    try:
        validate(spec_dict)
    except OpenAPIValidationError as val_err:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.OPENAPI_SPEC_INVALID",
                artifact="backend",
                severity="critical",
                message=f"OpenAPI schema validation failed: {val_err.message if hasattr(val_err, 'message') else str(val_err)}",
                evidence_path="scaffolds/openapi.yaml",
                source="IEEE1016",
                suggested_fix="Ensure OpenAPI spec complies with OpenAPI 3.0 / 3.1 specification schema.",
            )
        )
        meta["status"] = "schema_invalid"
    except Exception as exc:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.OPENAPI_SPEC_INVALID",
                artifact="backend",
                severity="high",
                message=f"OpenAPI validation error: {str(exc)}",
                evidence_path="scaffolds/openapi.yaml",
                source="IEEE1016",
                suggested_fix="Review openapi.yaml schema structure.",
            )
        )
        meta["status"] = "validation_error"

    # 3. Compare operations against Backend LLD
    spec_paths = spec_dict.get("paths", {}) or {}
    spec_ops: Set[Tuple[str, str]] = set()

    http_methods = {"get", "post", "put", "delete", "patch", "options", "head"}
    for path, path_item in spec_paths.items():
        if isinstance(path_item, dict):
            cpath = _clean_path(path)
            for m in path_item.keys():
                if m.lower() in http_methods:
                    spec_ops.add((m.upper(), cpath))

    meta["total_operations"] = len(spec_ops)

    backend_ops: Set[Tuple[str, str]] = {
        (ep.method.upper(), _clean_path(ep.path)) for ep in backend_endpoints
    }

    # Missing in OpenAPI spec (in Backend LLD but not in spec)
    for method, path in backend_ops:
        # Exact or normalized match
        matched = False
        for s_method, s_path in spec_ops:
            if method == s_method:
                # Compare parametric equivalents: /books/{id} matches /books/{book_id}
                p1 = re.sub(r"\{[^}]+\}", "{var}", path)
                p2 = re.sub(r"\{[^}]+\}", "{var}", s_path)
                if p1 == p2:
                    matched = True
                    break
        if not matched:
            meta["missing_in_spec"] += 1
            findings.append(
                Finding.create(
                    layer="L1",
                    rule_id="L1.OPENAPI_MISSING_ENDPOINT",
                    artifact="backend",
                    severity="high",
                    message=f"Endpoint '{method} {path}' defined in Backend LLD is missing from openapi.yaml.",
                    evidence_path=f"scaffolds/openapi.yaml/paths/{path}",
                    source="IEEE1016",
                    suggested_fix=f"Add path '{path}' with method '{method}' to openapi.yaml.",
                )
            )
        else:
            meta["matched_operations"] += 1

    # Extra in OpenAPI spec (in spec but not in Backend LLD) - if backend_endpoints is not empty
    if backend_ops:
        for s_method, s_path in spec_ops:
            matched = False
            for b_method, b_path in backend_ops:
                if s_method == b_method:
                    p1 = re.sub(r"\{[^}]+\}", "{var}", s_path)
                    p2 = re.sub(r"\{[^}]+\}", "{var}", b_path)
                    if p1 == p2:
                        matched = True
                        break
            if not matched and s_path != "/health" and s_path != "/docs":
                meta["extra_in_spec"] += 1
                findings.append(
                    Finding.create(
                        layer="L1",
                        rule_id="L1.OPENAPI_EXTRA_ENDPOINT",
                        artifact="backend",
                        severity="medium",
                        message=f"Operation '{s_method} {s_path}' in openapi.yaml is not documented in Backend LLD endpoints.",
                        evidence_path=f"scaffolds/openapi.yaml/paths/{s_path}",
                        source="IEEE1016",
                        suggested_fix=f"Document '{s_method} {s_path}' in Backend LLD api_endpoints.",
                    )
                )

    return findings, meta
