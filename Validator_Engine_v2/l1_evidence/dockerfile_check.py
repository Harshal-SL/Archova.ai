"""Layer 1: Dockerfile executable evidence check.

Uses hadolint if available on PATH; otherwise executes deterministic static checks:
- Non-root USER instruction
- Pinned base image tag (no :latest or unpinned tags)
- HEALTHCHECK probe instruction
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from Validator_Engine_v2.schemas import Finding


def check_dockerfile(
    dockerfile_content: Optional[str],
) -> Tuple[List[Finding], Dict[str, Any]]:
    """Validate Dockerfile contents with hadolint or static analysis.

    Returns:
        findings: List[Finding] with rule_id starting with 'L1.DOCKERFILE_'
        meta: status and tool execution metadata
    """
    findings: List[Finding] = []
    meta: Dict[str, Any] = {
        "status": "ok",
        "tool_used": "static",
        "hadolint_available": False,
    }

    if dockerfile_content is None:
        meta["status"] = "not_evaluated"
        meta["message"] = "not evaluated: no scaffold provided"
        return findings, meta

    if not dockerfile_content.strip():
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.DOCKERFILE_MISSING",
                artifact="cloud",
                severity="critical",
                message="Dockerfile is missing or empty.",
                evidence_path="scaffolds/Dockerfile",
                source="NIST-SSDF",
                suggested_fix="Create a production multi-stage Dockerfile.",
            )
        )
        meta["status"] = "missing"
        return findings, meta

    hadolint_bin = shutil.which("hadolint")
    if hadolint_bin:
        meta["hadolint_available"] = True
        meta["tool_used"] = "hadolint"
        try:
            res = subprocess.run(
                [hadolint_bin, "--format", "json", "-"],
                input=dockerfile_content,
                text=True,
                capture_output=True,
                timeout=10,
            )
            raw_out = res.stdout.strip()
            if raw_out:
                records = json.loads(raw_out)
                for item in records:
                    level = str(item.get("level", "warning")).lower()
                    code = item.get("code", "HADOLINT")
                    msg = item.get("message", "Hadolint rule violation")
                    line = item.get("line", 1)
                    sev = "high" if level == "error" else ("medium" if level == "warning" else "low")
                    findings.append(
                        Finding.create(
                            layer="L1",
                            rule_id=f"L1.DOCKERFILE_{code}",
                            artifact="cloud",
                            severity=sev,
                            message=f"Hadolint [{code}]: {msg} (line {line})",
                            evidence_path=f"scaffolds/Dockerfile#L{line}",
                            source="NIST-SSDF",
                            suggested_fix=f"Adhere to Hadolint rule {code}.",
                        )
                    )
            meta["status"] = "hadolint_executed"
            return findings, meta
        except Exception:
            # Fall back to static checks if hadolint execution errors
            pass

    # Tool missing or failed -> Record status 'skipped_tool_missing' and run static checks
    meta["status"] = "skipped_tool_missing"
    meta["tool_used"] = "static"

    lines = [line.strip() for line in dockerfile_content.splitlines()]

    # 1. Base image pinned check
    from_lines = [l for l in lines if re.match(r"^FROM\s+", l, re.IGNORECASE)]
    if not from_lines:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.DOCKERFILE_SYNTAX_NO_FROM",
                artifact="cloud",
                severity="critical",
                message="Dockerfile contains no FROM instruction.",
                evidence_path="scaffolds/Dockerfile",
                source="NIST-SSDF",
                suggested_fix="Add a valid FROM base image instruction.",
            )
        )
    else:
        # Check the final FROM stage for image tag pinning
        final_from = from_lines[-1]
        m = re.match(r"^FROM\s+([^\s]+)", final_from, re.IGNORECASE)
        if m:
            img_ref = m.group(1).split("AS")[0].strip()
            if ":" not in img_ref:
                findings.append(
                    Finding.create(
                        layer="L1",
                        rule_id="L1.DOCKERFILE_UNPINNED_BASE",
                        artifact="cloud",
                        severity="medium",
                        message=f"Base image '{img_ref}' has no version tag specified.",
                        evidence_path=final_from,
                        source="NIST-SSDF",
                        suggested_fix="Pin base image to an explicit version tag (e.g. python:3.11-slim).",
                    )
                )
            elif img_ref.endswith(":latest"):
                findings.append(
                    Finding.create(
                        layer="L1",
                        rule_id="L1.DOCKERFILE_LATEST_TAG",
                        artifact="cloud",
                        severity="medium",
                        message=f"Base image '{img_ref}' uses ':latest' tag instead of an immutable version tag.",
                        evidence_path=final_from,
                        source="NIST-SSDF",
                        suggested_fix="Replace ':latest' with a specific semantic version tag.",
                    )
                )

    # 2. Non-root USER check
    user_lines = [l for l in lines if re.match(r"^USER\s+", l, re.IGNORECASE)]
    if not user_lines:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.DOCKERFILE_ROOT_USER",
                artifact="cloud",
                severity="high",
                message="Dockerfile lacks a non-root USER instruction; container runs as root.",
                evidence_path="scaffolds/Dockerfile",
                source="NIST-SSDF",
                suggested_fix="Add a non-root USER instruction (e.g. USER appuser) before CMD/ENTRYPOINT.",
            )
        )
    else:
        final_user = re.sub(r"^USER\s+", "", user_lines[-1], flags=re.IGNORECASE).strip().lower()
        if final_user in ("root", "0"):
            findings.append(
                Finding.create(
                    layer="L1",
                    rule_id="L1.DOCKERFILE_ROOT_USER",
                    artifact="cloud",
                    severity="high",
                    message="Dockerfile explicitly sets USER to root.",
                    evidence_path=user_lines[-1],
                    source="NIST-SSDF",
                    suggested_fix="Create and switch to a non-privileged user.",
                )
            )

    # 3. HEALTHCHECK check
    has_healthcheck = any(re.match(r"^HEALTHCHECK\s+", l, re.IGNORECASE) for l in lines)
    if not has_healthcheck:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.DOCKERFILE_MISSING_HEALTHCHECK",
                artifact="cloud",
                severity="medium",
                message="Dockerfile lacks a HEALTHCHECK instruction for container liveness detection.",
                evidence_path="scaffolds/Dockerfile",
                source="ISO25010",
                suggested_fix="Add HEALTHCHECK instruction verifying the application HTTP /health probe.",
            )
        )

    return findings, meta
