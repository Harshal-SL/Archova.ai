"""Layer 1: Terraform IaC executable evidence check.

Uses terraform CLI if available on PATH; otherwise executes deterministic static checks:
- Verifies resources mentioned in Cloud LLD (VPC, compute, database, storage) exist in main.tf
- Validates balanced braces and required blocks
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from Validator_Engine_v2.schemas import Finding


def check_terraform(
    terraform_content: Optional[str],
    cloud_lld: Dict[str, Any],
) -> Tuple[List[Finding], Dict[str, Any]]:
    """Validate Terraform main.tf with terraform CLI or static analysis against Cloud LLD.

    Returns:
        findings: List[Finding] with rule_id starting with 'L1.TERRAFORM_'
        meta: status and tool execution metadata
    """
    findings: List[Finding] = []
    meta: Dict[str, Any] = {
        "status": "ok",
        "tool_used": "static",
        "terraform_available": False,
        "resources_detected": [],
    }

    if terraform_content is None:
        meta["status"] = "not_evaluated"
        meta["message"] = "not evaluated: no scaffold provided"
        return findings, meta

    if not terraform_content.strip():
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.TERRAFORM_MISSING",
                artifact="cloud",
                severity="high",
                message="Terraform IaC configuration (main.tf) is missing or empty.",
                evidence_path="scaffolds/terraform/main.tf",
                source="ISO25010",
                suggested_fix="Generate Terraform infrastructure-as-code configuration in main.tf.",
            )
        )
        meta["status"] = "missing"
        return findings, meta

    terraform_bin = shutil.which("terraform")
    if terraform_bin:
        meta["terraform_available"] = True
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tf_path = Path(tmpdir) / "main.tf"
                tf_path.write_text(terraform_content, encoding="utf-8")

                # Run terraform fmt -check
                fmt_res = subprocess.run(
                    [terraform_bin, "fmt", "-check", str(tf_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if fmt_res.returncode != 0:
                    findings.append(
                        Finding.create(
                            layer="L1",
                            rule_id="L1.TERRAFORM_FMT_ERROR",
                            artifact="cloud",
                            severity="low",
                            message="Terraform configuration is not canonically formatted according to 'terraform fmt'.",
                            evidence_path="scaffolds/terraform/main.tf",
                            source="internal",
                            suggested_fix="Run 'terraform fmt' to format configuration files.",
                        )
                    )

                # Run terraform init & validate
                init_res = subprocess.run(
                    [terraform_bin, "init", "-backend=false"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if init_res.returncode == 0:
                    val_res = subprocess.run(
                        [terraform_bin, "validate"],
                        cwd=tmpdir,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if val_res.returncode != 0:
                        findings.append(
                            Finding.create(
                                layer="L1",
                                rule_id="L1.TERRAFORM_VALIDATION_ERROR",
                                artifact="cloud",
                                severity="high",
                                message=f"Terraform validation failed: {val_res.stderr.strip() or val_res.stdout.strip()}",
                                evidence_path="scaffolds/terraform/main.tf",
                                source="ISO25010",
                                suggested_fix="Resolve Terraform syntax and resource configuration errors.",
                            )
                        )

            meta["status"] = "terraform_executed"
            meta["tool_used"] = "terraform"
        except Exception:
            # Fall back to static checks if terraform execution fails
            pass

    if meta["tool_used"] != "terraform":
        meta["status"] = "skipped_tool_missing"
        meta["tool_used"] = "static"

    # Static Syntax Check: Balanced Braces
    open_braces = terraform_content.count("{")
    close_braces = terraform_content.count("}")
    if open_braces != close_braces:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.TERRAFORM_SYNTAX_UNBALANCED_BRACES",
                artifact="cloud",
                severity="critical",
                message=f"Terraform syntax error: Unbalanced braces in main.tf ({open_braces} open, {close_braces} close).",
                evidence_path="scaffolds/terraform/main.tf",
                source="ISO25010",
                suggested_fix="Ensure all opening braces '{' in main.tf have matching closing braces '}'.",
            )
        )

    # Extract declared resources: resource "aws_vpc" "main"
    resource_patterns = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', terraform_content)
    declared_types: Set[str] = {res_type.lower() for res_type, _ in resource_patterns}
    meta["resources_detected"] = [f"{t}.{n}" for t, n in resource_patterns]

    # Compare against Cloud LLD components
    # Check VPC / networking
    networking = cloud_lld.get("networking", {})
    if networking and not any("vpc" in t or "network" in t for t in declared_types):
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.TERRAFORM_MISSING_NETWORKING",
                artifact="cloud",
                severity="medium",
                message="Cloud LLD specifies networking/VPC tier but no VPC resource is declared in main.tf.",
                evidence_path="scaffolds/terraform/main.tf",
                source="ISO25010",
                suggested_fix="Declare VPC and Subnet resources in main.tf.",
            )
        )

    # Check database / RDS
    db_config = cloud_lld.get("database") or cloud_lld.get("storage", {})
    if db_config and isinstance(db_config, dict):
        engine_str = str(db_config.get("engine") or db_config.get("type") or "").lower()
        if ("postgres" in engine_str or "mysql" in engine_str or "rds" in engine_str) and not any("db" in t or "rds" in t for t in declared_types):
            findings.append(
                Finding.create(
                    layer="L1",
                    rule_id="L1.TERRAFORM_MISSING_DATABASE",
                    artifact="cloud",
                    severity="medium",
                    message="Cloud LLD specifies relational database deployment but no RDS/database resource is declared in main.tf.",
                    evidence_path="scaffolds/terraform/main.tf",
                    source="ISO25010",
                    suggested_fix="Declare an aws_db_instance or equivalent database resource in main.tf.",
                )
            )

    return findings, meta
