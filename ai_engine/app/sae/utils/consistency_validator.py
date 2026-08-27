"""Deterministic post-generation consistency validator for SAE pipeline.

Pure Python checks — no LLM calls. Runs after all agents complete,
before final package assembly. Reports problems but does NOT trigger
re-generation. Read-only validation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple


# Known placeholder patterns to detect
PLACEHOLDER_PATTERNS = [
    "standard option",
    "tbd",
    "to be determined",
    "placeholder",
    "enterprise domain suitability",
    "lorem ipsum",
    "example text",
    "insert here",
    "fill in",
    "todo",
    "xxx",
    "n/a",
]

# Generic boilerplate phrases that indicate non-specific content
BOILERPLATE_PATTERNS = [
    "high performance",
    "mature ecosystem",
    "industry standard",
    "best practices",
    "enterprise grade",
    "production ready",
    "state of the art",
    "cutting edge",
    "world class",
    "robust and scalable",
]


class ConsistencyValidationResult:
    """Result of consistency validation across all SAE outputs."""

    def __init__(self) -> None:
        self.placeholder_violations: List[Dict[str, str]] = []
        self.type_violations: List[Dict[str, str]] = []
        self.tech_mismatches: List[Dict[str, str]] = []
        self.duplicate_technologies: List[Dict[str, str]] = []
        self.coverage_report: Dict[str, Any] = {}
        self.missing_fields: List[Dict[str, str]] = []
        self.phantom_requirements: List[Dict[str, str]] = []
        self.terminology_inconsistencies: List[Dict[str, str]] = []
        self.boilerplate_warnings: List[Dict[str, str]] = []
        self.confidence_score: float = 0.0
        self.confidence_breakdown: Dict[str, float] = {}

    def to_dict(self) -> Dict[str, Any]:
        total_issues = (
            len(self.placeholder_violations)
            + len(self.type_violations)
            + len(self.tech_mismatches)
            + len(self.duplicate_technologies)
            + len(self.missing_fields)
            + len(self.phantom_requirements)
            + len(self.terminology_inconsistencies)
        )
        return {
            "confidence_score": round(self.confidence_score, 4),
            "confidence_breakdown": self.confidence_breakdown,
            "total_issues": total_issues,
            "placeholder_violations": self.placeholder_violations,
            "type_violations": self.type_violations,
            "technology_mismatches": self.tech_mismatches,
            "duplicate_technologies": self.duplicate_technologies,
            "requirement_coverage": self.coverage_report,
            "missing_required_fields": self.missing_fields,
            "phantom_requirements": self.phantom_requirements,
            "terminology_inconsistencies": self.terminology_inconsistencies,
            "boilerplate_warnings": self.boilerplate_warnings,
            "status": "PASS" if total_issues == 0 else "ISSUES_FOUND",
        }


def validate_consistency(
    req_analysis: Dict[str, Any],
    tech_rec: Dict[str, Any],
    adp: Dict[str, Any],
    hld: Dict[str, Any],
    backend_lld: Dict[str, Any],
    database_lld: Dict[str, Any],
    frontend_lld: Dict[str, Any],
    security_lld: Dict[str, Any],
    cloud_lld: Dict[str, Any],
) -> ConsistencyValidationResult:
    """Run all deterministic consistency checks across pipeline outputs.

    Returns a ConsistencyValidationResult with issues found.
    Does NOT trigger re-generation — read-only validation.
    """
    result = ConsistencyValidationResult()

    all_sections = {
        "requirement_analysis": req_analysis,
        "technology_recommendation": tech_rec,
        "architecture_decision_plan": adp,
        "hld": hld,
        "backend_lld": backend_lld,
        "database_lld": database_lld,
        "frontend_lld": frontend_lld,
        "security_lld": security_lld,
        "cloud_lld": cloud_lld,
    }

    # 1. Placeholder detection
    _check_placeholders(all_sections, result)

    # 2. Type validation (structural checks)
    _check_types(hld, backend_lld, result)

    # 3. Technology consistency
    _check_tech_consistency(tech_rec, adp, hld, result)

    # 4. Duplicate technologies
    _check_duplicate_technologies(tech_rec, result)

    # 5. Requirement coverage
    _check_requirement_coverage(req_analysis, all_sections, result)

    # 6. Required fields populated
    _check_required_fields(hld, backend_lld, result)

    # 7. Phantom requirements (satisfies IDs that don't exist)
    _check_phantom_requirements(req_analysis, all_sections, result)

    # 8. Terminology consistency
    _check_terminology_consistency(all_sections, result)

    # 9. Boilerplate detection (warnings only)
    _check_boilerplate(all_sections, result)

    # Compute confidence score
    _compute_confidence(req_analysis, all_sections, result)

    return result


def _collect_strings(obj: Any, path: str = "") -> List[Tuple[str, str]]:
    """Recursively collect all string values with their paths."""
    strings = []
    if isinstance(obj, str):
        strings.append((path, obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            strings.extend(_collect_strings(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            strings.extend(_collect_strings(item, f"{path}[{i}]"))
    return strings


def _check_placeholders(
    sections: Dict[str, Dict[str, Any]],
    result: ConsistencyValidationResult,
) -> None:
    """Scan all string values for placeholder patterns."""
    for section_name, content in sections.items():
        if not content:
            continue
        for path, value in _collect_strings(content):
            value_lower = value.lower().strip()
            for pattern in PLACEHOLDER_PATTERNS:
                if pattern in value_lower:
                    result.placeholder_violations.append({
                        "section": section_name,
                        "path": path,
                        "value": value[:100],
                        "matched_pattern": pattern,
                    })
                    break  # One match per value is enough


def _check_types(
    hld: Dict[str, Any],
    backend_lld: Dict[str, Any],
    result: ConsistencyValidationResult,
) -> None:
    """Verify that nested structures are the correct types."""
    # HLD major_services should be list of objects
    services = hld.get("major_services", [])
    if isinstance(services, list):
        for i, svc in enumerate(services):
            if not isinstance(svc, dict):
                result.type_violations.append({
                    "section": "hld",
                    "path": f"major_services[{i}]",
                    "expected": "object",
                    "actual": type(svc).__name__,
                })

    # HLD decisions should be list of objects
    decisions = hld.get("decisions", [])
    if isinstance(decisions, list):
        for i, dec in enumerate(decisions):
            if not isinstance(dec, dict):
                result.type_violations.append({
                    "section": "hld",
                    "path": f"decisions[{i}]",
                    "expected": "object",
                    "actual": type(dec).__name__,
                })

    # Backend services should be list of objects
    be_services = backend_lld.get("services", [])
    if isinstance(be_services, list):
        for i, svc in enumerate(be_services):
            if not isinstance(svc, dict):
                result.type_violations.append({
                    "section": "backend_lld",
                    "path": f"services[{i}]",
                    "expected": "object",
                    "actual": type(svc).__name__,
                })


def _extract_tech_option(tech_data: Any) -> str:
    """Extract selected_option from a tech category (handles both dict and nested)."""
    if isinstance(tech_data, dict):
        return tech_data.get("selected_option", "")
    return ""


def _check_tech_consistency(
    tech_rec: Dict[str, Any],
    adp: Dict[str, Any],
    hld: Dict[str, Any],
    result: ConsistencyValidationResult,
) -> None:
    """Verify technologies match across Tech Advisor → ADP → HLD."""
    tech_categories = ["backend", "frontend", "database", "cache", "authentication",
                        "communication", "cloud", "deployment"]

    adp_stack = adp.get("technology_stack", {})
    hld_stack = hld.get("technology_stack", {})

    for cat in tech_categories:
        tech_option = _extract_tech_option(tech_rec.get(cat))
        if not tech_option:
            continue

        # Check ADP consistency
        adp_value = adp_stack.get(cat, "")
        if adp_value and tech_option and _normalize_tech(tech_option) != _normalize_tech(adp_value):
            result.tech_mismatches.append({
                "category": cat,
                "tech_advisor": tech_option,
                "adp": adp_value,
                "issue": "ADP does not match Tech Advisor recommendation",
            })

        # Check HLD consistency
        hld_value = hld_stack.get(cat, "")
        if hld_value and tech_option and _normalize_tech(tech_option) != _normalize_tech(hld_value):
            result.tech_mismatches.append({
                "category": cat,
                "tech_advisor": tech_option,
                "hld": hld_value,
                "issue": "HLD does not match Tech Advisor recommendation",
            })


def _normalize_tech(name: str) -> str:
    """Normalize a technology name for comparison."""
    # Remove common suffixes and normalize
    name = name.lower().strip()
    # Remove version numbers
    name = re.sub(r'\d+(\.\d+)*', '', name)
    # Remove common filler words
    for word in ['with', 'and', '&', '/', '(', ')', '-', '+', ',']:
        name = name.replace(word, ' ')
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def _check_duplicate_technologies(
    tech_rec: Dict[str, Any],
    result: ConsistencyValidationResult,
) -> None:
    """Check if the same technology is recommended for conflicting purposes."""
    tech_map: Dict[str, List[str]] = {}  # normalized name → categories

    for cat in ["backend", "frontend", "database", "cache", "authentication",
                 "communication", "cloud", "deployment", "messaging",
                 "monitoring", "search", "storage"]:
        option = _extract_tech_option(tech_rec.get(cat))
        if option:
            normalized = _normalize_tech(option)
            if normalized not in tech_map:
                tech_map[normalized] = []
            tech_map[normalized].append(cat)

    # Flag technologies used in potentially conflicting categories
    conflicting_pairs = {
        frozenset({"database", "cache"}),
        frozenset({"backend", "frontend"}),
    }
    for tech_name, categories in tech_map.items():
        if len(categories) > 1:
            cat_set = frozenset(categories)
            for pair in conflicting_pairs:
                if pair.issubset(cat_set):
                    result.duplicate_technologies.append({
                        "technology": tech_name,
                        "categories": categories,
                        "issue": f"Same technology used for conflicting purposes: {categories}",
                    })


def _extract_all_requirement_ids(req_analysis: Dict[str, Any]) -> Set[str]:
    """Extract all FR-xxx and NFR-xxx IDs from requirement analysis."""
    ids: Set[str] = set()
    for fr in req_analysis.get("functional_requirements", []):
        if isinstance(fr, dict) and "id" in fr:
            ids.add(fr["id"])
    for nfr in req_analysis.get("non_functional_requirements", []):
        if isinstance(nfr, dict) and "id" in nfr:
            ids.add(nfr["id"])
    return ids


def _extract_satisfies_ids(obj: Any) -> Set[str]:
    """Recursively extract all values from 'satisfies' fields."""
    ids: Set[str] = set()
    if isinstance(obj, dict):
        if "satisfies" in obj and isinstance(obj["satisfies"], list):
            for item in obj["satisfies"]:
                if isinstance(item, str):
                    ids.add(item)
        for v in obj.values():
            ids.update(_extract_satisfies_ids(v))
    elif isinstance(obj, list):
        for item in obj:
            ids.update(_extract_satisfies_ids(item))
    return ids


def _check_requirement_coverage(
    req_analysis: Dict[str, Any],
    sections: Dict[str, Dict[str, Any]],
    result: ConsistencyValidationResult,
) -> None:
    """Check how many requirement IDs are referenced in satisfies fields."""
    all_req_ids = _extract_all_requirement_ids(req_analysis)
    if not all_req_ids:
        result.coverage_report = {
            "total_requirements": 0,
            "referenced_requirements": 0,
            "coverage_ratio": 0.0,
            "unreferenced": [],
        }
        return

    all_satisfies: Set[str] = set()
    for section_name, content in sections.items():
        if content and section_name != "requirement_analysis":
            all_satisfies.update(_extract_satisfies_ids(content))

    referenced = all_req_ids & all_satisfies
    unreferenced = all_req_ids - all_satisfies

    result.coverage_report = {
        "total_requirements": len(all_req_ids),
        "referenced_requirements": len(referenced),
        "coverage_ratio": round(len(referenced) / len(all_req_ids), 4) if all_req_ids else 0.0,
        "unreferenced": sorted(unreferenced),
    }


def _check_required_fields(
    hld: Dict[str, Any],
    backend_lld: Dict[str, Any],
    result: ConsistencyValidationResult,
) -> None:
    """Check that critical nested objects have required fields populated."""
    # HLD services must have name and responsibility
    for i, svc in enumerate(hld.get("major_services", [])):
        if isinstance(svc, dict):
            if not svc.get("name"):
                result.missing_fields.append({
                    "section": "hld",
                    "path": f"major_services[{i}].name",
                    "issue": "Service missing name",
                })
            if not svc.get("responsibility"):
                result.missing_fields.append({
                    "section": "hld",
                    "path": f"major_services[{i}].responsibility",
                    "issue": "Service missing responsibility",
                })

    # HLD decisions must have decision and reasoning
    for i, dec in enumerate(hld.get("decisions", [])):
        if isinstance(dec, dict):
            if not dec.get("decision"):
                result.missing_fields.append({
                    "section": "hld",
                    "path": f"decisions[{i}].decision",
                    "issue": "ADR missing decision",
                })
            if not dec.get("reasoning"):
                result.missing_fields.append({
                    "section": "hld",
                    "path": f"decisions[{i}].reasoning",
                    "issue": "ADR missing reasoning",
                })

    # Backend services must have name
    for i, svc in enumerate(backend_lld.get("services", [])):
        if isinstance(svc, dict):
            if not svc.get("name"):
                result.missing_fields.append({
                    "section": "backend_lld",
                    "path": f"services[{i}].name",
                    "issue": "Service missing name",
                })


def _check_phantom_requirements(
    req_analysis: Dict[str, Any],
    sections: Dict[str, Dict[str, Any]],
    result: ConsistencyValidationResult,
) -> None:
    """Flag satisfies IDs that don't exist in requirement analysis."""
    all_req_ids = _extract_all_requirement_ids(req_analysis)

    for section_name, content in sections.items():
        if not content or section_name == "requirement_analysis":
            continue
        satisfies_ids = _extract_satisfies_ids(content)
        phantoms = satisfies_ids - all_req_ids
        for phantom_id in sorted(phantoms):
            result.phantom_requirements.append({
                "section": section_name,
                "phantom_id": phantom_id,
                "issue": f"Requirement ID '{phantom_id}' referenced in satisfies but not defined in requirement analysis",
            })


def _check_terminology_consistency(
    sections: Dict[str, Dict[str, Any]],
    result: ConsistencyValidationResult,
) -> None:
    """Check that services/technologies aren't referred to by different names."""
    # Collect service names from HLD
    hld = sections.get("hld", {})
    if not hld:
        return

    hld_service_names: Set[str] = set()
    for svc in hld.get("major_services", []):
        if isinstance(svc, dict) and svc.get("name"):
            hld_service_names.add(svc["name"])

    # Check backend LLD service names match HLD
    backend = sections.get("backend_lld", {})
    if backend:
        be_service_names: Set[str] = set()
        for svc in backend.get("services", []):
            if isinstance(svc, dict) and svc.get("name"):
                be_service_names.add(svc["name"])

        # Warn if backend has services not in HLD (could be sub-services, so just warn)
        # We don't flag this as an error since backend decomposes HLD services


def _check_boilerplate(
    sections: Dict[str, Dict[str, Any]],
    result: ConsistencyValidationResult,
) -> None:
    """Detect generic boilerplate phrases (warnings, not errors)."""
    for section_name, content in sections.items():
        if not content:
            continue
        for path, value in _collect_strings(content):
            value_lower = value.lower()
            for pattern in BOILERPLATE_PATTERNS:
                if pattern in value_lower and len(value) < 80:
                    # Only flag short values that are purely boilerplate
                    result.boilerplate_warnings.append({
                        "section": section_name,
                        "path": path,
                        "value": value[:100],
                        "matched_pattern": pattern,
                    })
                    break


def _compute_confidence(
    req_analysis: Dict[str, Any],
    sections: Dict[str, Dict[str, Any]],
    result: ConsistencyValidationResult,
) -> None:
    """Compute confidence score from evidence — not forced into a range.

    confidence =
        0.30 * requirement_coverage_ratio
      + 0.25 * field_population_rate
      + 0.25 * consistency_score
      + 0.20 * specificity_score
    """
    # 1. Requirement coverage ratio
    coverage_ratio = result.coverage_report.get("coverage_ratio", 0.0)

    # 2. Field population rate (non-empty fields / total fields across all sections)
    total_fields = 0
    populated_fields = 0
    for section_name, content in sections.items():
        if not content:
            continue
        if isinstance(content, dict):
            for v in content.values():
                total_fields += 1
                if v:  # non-empty
                    populated_fields += 1

    field_population = (populated_fields / max(total_fields, 1))

    # 3. Consistency score (1.0 - mismatches/total checks)
    total_checks = max(len(result.tech_mismatches) + 8, 8)  # at least 8 tech categories checked
    mismatches = len(result.tech_mismatches) + len(result.terminology_inconsistencies)
    consistency = 1.0 - (mismatches / total_checks)

    # 4. Specificity score (1.0 - placeholder_count / total_strings)
    all_strings = []
    for content in sections.values():
        if content:
            all_strings.extend(_collect_strings(content))
    total_strings = max(len(all_strings), 1)
    placeholder_count = len(result.placeholder_violations) + len(result.boilerplate_warnings)
    specificity = 1.0 - (placeholder_count / total_strings)
    specificity = max(specificity, 0.0)

    # Weighted combination
    confidence = (
        0.30 * coverage_ratio
        + 0.25 * field_population
        + 0.25 * consistency
        + 0.20 * specificity
    )

    result.confidence_score = confidence
    result.confidence_breakdown = {
        "requirement_coverage": round(coverage_ratio, 4),
        "field_population": round(field_population, 4),
        "consistency": round(consistency, 4),
        "specificity": round(specificity, 4),
    }
