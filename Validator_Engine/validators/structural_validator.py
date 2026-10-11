"""Structural and Schema Integrity Validator for Generated Architectures.

Performs deterministic Python checks:
- Presence of required architecture sections (ARSRS, HLD, LLDs)
- Detection of non-specific placeholder text (TBD, xxx, placeholder, standard option)
- Detection of excessive generic boilerplate
- Malformed dictionaries or list elements
- Verification of component identifiers
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Union
from ..models.finding_models import FindingCategory, FindingSeverity, ValidationFinding
from ..models.input_models import ArchitecturePackageInput
from ..models.report_models import StructuralValidationReport


PLACEHOLDER_PATTERNS = [
    r"\btbd\b",
    r"\bto be determined\b",
    r"\bplaceholder\b",
    r"\blorem ipsum\b",
    r"\bexample text\b",
    r"\binsert here\b",
    r"\bfill in\b",
    r"\btodo\b",
    r"\bxxx+\b",
    r"\bstandard option\b",
    r"\bgeneric option\b",
]

BOILERPLATE_PATTERNS = [
    r"state of the art",
    r"cutting edge",
    r"world class",
    r"best in class",
    r"industry standard solution",
]


class StructuralValidator:
    """Evaluates the structural integrity and content cleanliness of architecture JSON."""

    REQUIRED_TOP_LEVEL = ["arsrs", "hld", "llds"]
    REQUIRED_LLD_KEYS = ["backend", "database", "frontend", "security", "cloud"]

    @classmethod
    def validate(
        cls,
        architecture_data: Union[Dict[str, Any], ArchitecturePackageInput],
    ) -> StructuralValidationReport:
        """Run comprehensive structural integrity verification."""
        if isinstance(architecture_data, ArchitecturePackageInput):
            data = architecture_data.data
        elif isinstance(architecture_data, dict):
            data = architecture_data
        else:
            data = {}

        findings: List[ValidationFinding] = []
        missing_sections: List[str] = []
        malformed_elements: List[str] = []
        placeholder_violations: List[Dict[str, str]] = []
        placeholder_items: List[Dict[str, Any]] = []
        boilerplate_warnings: List[str] = []
        orphan_components: List[str] = []

        if not isinstance(data, dict) or not data:
            finding = ValidationFinding(
                id="STRUCT-000",
                category=FindingCategory.STRUCTURAL,
                severity=FindingSeverity.CRITICAL,
                affected_component="root",
                explanation="Architecture JSON is empty or not a valid dictionary.",
                evidence="Input payload is empty or non-dict",
                recommendation="Ensure the AI Engine generates a complete, non-empty architecture JSON payload.",
            )
            return StructuralValidationReport(
                is_valid=False,
                score=0.0,
                missing_sections=["all"],
                malformed_elements=["Root payload is not a valid dictionary"],
                findings=[finding],
            )

        # 1. Top-Level Section Check
        for sec in cls.REQUIRED_TOP_LEVEL:
            if sec not in data or not data[sec]:
                missing_sections.append(sec)
                findings.append(
                    ValidationFinding(
                        id=f"STRUCT-MISSING-{sec.upper()}",
                        category=FindingCategory.STRUCTURAL,
                        severity=FindingSeverity.CRITICAL,
                        affected_component=sec,
                        explanation=f"Required top-level architecture section '{sec}' is missing or empty.",
                        evidence=f"Key '{sec}' is absent in architecture root",
                        recommendation=f"Ensure the AI Engine pipeline populates '{sec}' before finalizing output.",
                    )
                )

        # 2. Check LLD Sub-sections
        llds = data.get("llds", {})
        if isinstance(llds, dict):
            for lld_key in cls.REQUIRED_LLD_KEYS:
                # check both "backend" and "backend_lld"
                lld_obj = llds.get(lld_key) or llds.get(f"{lld_key}_lld")
                if not lld_obj:
                    missing_sections.append(f"llds.{lld_key}")
                    findings.append(
                        ValidationFinding(
                            id=f"STRUCT-MISSING-LLD-{lld_key.upper()}",
                            category=FindingCategory.STRUCTURAL,
                            severity=FindingSeverity.HIGH,
                            affected_component=f"llds.{lld_key}",
                            explanation=f"Required Low-Level Design section '{lld_key}' is missing or empty.",
                            evidence=f"llds.{lld_key} is not populated",
                            recommendation=f"Run the {lld_key} LLD generation agent to complete this tier.",
                        )
                    )
                elif isinstance(lld_obj, dict):
                    if lld_obj.get("status") == "FAILED":
                        malformed_elements.append(f"llds.{lld_key} status is FAILED: {lld_obj.get('error')}")
                        findings.append(
                            ValidationFinding(
                                id=f"STRUCT-FAILED-LLD-{lld_key.upper()}",
                                category=FindingCategory.STRUCTURAL,
                                severity=FindingSeverity.HIGH,
                                affected_component=f"llds.{lld_key}",
                                explanation=f"LLD '{lld_key}' generation failed during pipeline execution.",
                                evidence=str(lld_obj.get("error", "Unknown agent error")),
                                recommendation=f"Re-execute the {lld_key} generation agent to regenerate valid schema.",
                            )
                        )

        # 3. Check for Placeholder Text Across JSON
        json_str = json.dumps(data, default=str).lower()
        for pat in PLACEHOLDER_PATTERNS:
            matches = list(re.finditer(pat, json_str))
            if matches:
                matched_text = pat.replace(r"\b", "")
                placeholder_violations.append({
                    "pattern": matched_text,
                    "occurrences": str(len(matches)),
                })
                placeholder_items.append({
                    "pattern": matched_text,
                    "count": len(matches),
                })
                findings.append(
                    ValidationFinding(
                        id=f"STRUCT-PLACEHOLDER-{matched_text[:10].upper().replace(' ', '_')}",
                        category=FindingCategory.STRUCTURAL,
                        severity=FindingSeverity.MEDIUM,
                        affected_component="Architecture Specifications",
                        explanation=f"Detected {len(matches)} placeholder occurrence(s) of '{matched_text}' in architecture specifications.",
                        evidence=f"Matches regex pattern: {pat}",
                        recommendation="Replace generic placeholder tokens with concrete architectural parameters.",
                    )
                )

        # 4. Check for Generic Boilerplate
        for pat in BOILERPLATE_PATTERNS:
            if re.search(pat, json_str):
                boilerplate_warnings.append(f"Contains generic marketing phrase: '{pat}'")

        # 5. Check HLD Major Services
        hld = data.get("hld", {})
        if isinstance(hld, dict):
            services = hld.get("major_services", [])
            if isinstance(services, list) and len(services) == 0:
                malformed_elements.append("hld.major_services array is empty")
                findings.append(
                    ValidationFinding(
                        id="STRUCT-HLD-EMPTY-SERVICES",
                        category=FindingCategory.STRUCTURAL,
                        severity=FindingSeverity.CRITICAL,
                        affected_component="hld.major_services",
                        explanation="HLD does not define any major services.",
                        evidence="major_services array length is 0",
                        recommendation="Decompose domain into at least 1-2 core services with explicit responsibilities.",
                    )
                )

        is_valid = len(missing_sections) == 0 and not any(
            f.severity == FindingSeverity.CRITICAL for f in findings
        )

        critical_count = len([f for f in findings if f.severity == FindingSeverity.CRITICAL])
        high_count = len([f for f in findings if f.severity == FindingSeverity.HIGH])
        score = round(max(0.0, min(1.0, 1.0 - (0.25 * critical_count) - (0.10 * high_count) - (0.02 * len(placeholder_violations)))), 2)

        return StructuralValidationReport(
            is_valid=is_valid,
            score=score,
            missing_sections=missing_sections,
            malformed_elements=malformed_elements,
            placeholder_items=placeholder_items,
            placeholder_violations=placeholder_violations,
            orphan_components=orphan_components,
            boilerplate_warnings=boilerplate_warnings,
            findings=findings,
            details={
                "total_structural_findings": len(findings),
                "has_critical_failures": critical_count > 0,
            },
        )
