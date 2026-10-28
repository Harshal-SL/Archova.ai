"""Validator Engine Master Facade.

Consolidates and orchestrates all validation subsystems (structural, requirement,
cross-artifact, NFR, red-team, real-world evidence, explainability, scoring, remediation)
into a unified execution pipeline producing validated_architecture.json.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from Validator_Engine.explainability.provenance_service import DecisionProvenanceService
from Validator_Engine.knowledge.knowledge_retriever import KnowledgeRetriever
from Validator_Engine.knowledge.real_world_assessor import RealWorldAssessor
from Validator_Engine.models.finding_models import FindingSeverity, ValidationFinding
from Validator_Engine.models.input_models import ArchitecturePackageInput
from Validator_Engine.models.output_models import (
    ExplainabilityBlock,
    ValidatedArchitectureResponse,
    ValidationBlock,
    ValidationSummary,
    ValidatorMetadata,
)
from Validator_Engine.models.report_models import (
    ArchitectureCorrectionFeedback,
    CorrectionAttemptRecord,
)
from Validator_Engine.remediation.remediation_engine import RemediationEngine
from Validator_Engine.scoring.scoring_engine import ScoringEngine
from Validator_Engine.validators.cross_artifact_validator import CrossArtifactValidator
from Validator_Engine.validators.nfr_quality_validator import NFRQualityValidator
from Validator_Engine.validators.red_team_reviewer import RedTeamReviewer
from Validator_Engine.validators.requirement_aligner import RequirementAligner
from Validator_Engine.validators.structural_validator import StructuralValidator

logger = logging.getLogger(__name__)

_validator_redis_client = None


def _get_validator_redis():
    """Returns singleton synchronous Redis client for validation result caching."""
    global _validator_redis_client
    if _validator_redis_client is not None:
        return _validator_redis_client
    try:
        from Validator_Engine.config import REDIS_URL
        if not REDIS_URL:
            return None
        import redis
        client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=3,
            socket_connect_timeout=3,
            retry_on_timeout=True,
        )
        client.ping()
        _validator_redis_client = client
        logger.info(f"[Validator:Redis] Connected to Redis cluster for caching: {REDIS_URL.split('@')[-1]}")
        return _validator_redis_client
    except Exception as exc:
        logger.debug(f"[Validator:Redis] Redis connection not available ({exc}). Continuing without cache.")
        return None


class ValidatorEngine:
    """Master Architecture Validation Engine orchestrating end-to-end verification."""

    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
    ) -> None:
        self.retriever = retriever or KnowledgeRetriever()
        self.structural_validator = StructuralValidator()
        self.requirement_aligner = RequirementAligner()
        self.cross_artifact_validator = CrossArtifactValidator()
        self.nfr_validator = NFRQualityValidator()
        self.red_team_reviewer = RedTeamReviewer()
        self.real_world_assessor = RealWorldAssessor(retriever=self.retriever)
        self.provenance_service = DecisionProvenanceService()
        self.scoring_engine = ScoringEngine()
        self.remediation_engine = RemediationEngine()

    def validate(
        self,
        input_data: Union[Dict[str, Any], str, Path, ArchitecturePackageInput],
        attempt: int = 1,
        max_retries: int = 2,
        correction_history: Optional[List[CorrectionAttemptRecord]] = None,
    ) -> ValidatedArchitectureResponse:
        """Execute complete architectural validation lifecycle over the input package.

        Args:
            input_data: A parsed dictionary, JSON string, Path to JSON file, or ArchitecturePackageInput.
            attempt: Current iteration / attempt index (1-based).
            max_retries: Configured retry limit for AI correction loops.
            correction_history: Cumulative audit list of correction attempt records.

        Returns:
            ValidatedArchitectureResponse: Complete validated architecture envelope.
        """
        start_time = time.perf_counter()

        # 1. Normalize Input
        package = self._normalize_input(input_data)
        logger.info(f"Starting architectural validation for package '{package.package_id}' ({package.get_system_name()})...")

        # Fast Fingerprint & Redis Cache Check
        fingerprint = hashlib.sha256(json.dumps(package.data, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
        cache_key = f"val:cache:{fingerprint}"
        r_client = _get_validator_redis()
        if r_client:
            try:
                cached_raw = r_client.get(cache_key)
                if cached_raw:
                    cached_duration = round((time.perf_counter() - start_time) * 1000, 2)
                    logger.info(f"[Validator:Redis] Cache HIT for '{package.package_id}' (fingerprint: {fingerprint}, {cached_duration}ms)")
                    cached_response = ValidatedArchitectureResponse.model_validate_json(cached_raw)
                    return cached_response
            except Exception:
                pass

        # 2. Phase 1: Structural Integrity & Schema Validation
        structural_report = self.structural_validator.validate(package)

        # 3. Phase 2: Requirement Traceability & Alignment
        requirement_report = self.requirement_aligner.validate(package)

        # 4. Phase 3: Cross-Artifact Consistency
        consistency_report = self.cross_artifact_validator.validate(package)

        # 5. Phase 4: NFR & Quality Attribute Feasibility
        nfr_report = self.nfr_validator.validate(package)

        # 6. Phase 5: Red-Team Adversarial & Resilience Review
        red_team_report = self.red_team_reviewer.review(
            package=package,
            structural_report=structural_report,
            consistency_report=consistency_report,
        )

        # 7. Phase 6: Real-World Evidence & Archetype Benchmarking
        real_world_report = self.real_world_assessor.assess(package)

        # 8. Aggregate All Findings
        all_findings: List[ValidationFinding] = []
        all_findings.extend(structural_report.findings)
        all_findings.extend(requirement_report.findings)
        all_findings.extend(consistency_report.findings)
        all_findings.extend(nfr_report.findings)
        all_findings.extend(red_team_report.findings)
        all_findings.extend(real_world_report.findings)

        # 9. Phase 7: Decision Provenance & Explainability Matrix
        provenance_items = self.provenance_service.build_provenance_matrix(
            package=package,
            findings=all_findings,
            real_world_report=real_world_report,
        )

        # 10. Phase 8: Unified Scoring & Quality Gating
        scorecard = self.scoring_engine.evaluate(
            structural_report=structural_report,
            requirement_report=requirement_report,
            consistency_report=consistency_report,
            nfr_report=nfr_report,
            real_world_report=real_world_report,
            red_team_report=red_team_report,
            all_findings=all_findings,
        )

        # 11. Phase 9: Actionable Remediation Plan
        remediation_plan = self.remediation_engine.build_remediation_plan(
            findings=all_findings,
            verdict=red_team_report.verdict,
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 12. Assemble Validation Block
        critical_count = len([f for f in all_findings if f.severity == FindingSeverity.CRITICAL])
        high_count = len([f for f in all_findings if f.severity == FindingSeverity.HIGH])
        medium_count = len([f for f in all_findings if f.severity == FindingSeverity.MEDIUM])
        low_count = len([f for f in all_findings if f.severity == FindingSeverity.LOW])

        validation_summary = ValidationSummary(
            overall_score=scorecard.overall_composite_score,
            verdict=red_team_report.verdict,
            total_findings_count=len(all_findings),
            critical_findings_count=critical_count,
            high_findings_count=high_count,
            medium_findings_count=medium_count,
            low_findings_count=low_count,
            is_valid=scorecard.status in ("HEALTHY", "DEGRADED"),
        )

        validation_block = ValidationBlock(
            status=scorecard.status,
            summary=validation_summary,
            scorecard=scorecard,
            structural_validation=structural_report,
            requirement_alignment=requirement_report,
            cross_artifact_consistency=consistency_report,
            nfr_validation=nfr_report,
            red_team_review=red_team_report,
            findings=all_findings,
        )

        explainability_block = ExplainabilityBlock(
            decisions_provenance=provenance_items,
            architecture_overview_rationale=f"Architecture for {package.get_system_name()} ({package.get_domain()}) with {len(provenance_items)} traced decisions.",
        )

        metadata = ValidatorMetadata(
            validator_version="1.0.0",
            package_id=package.package_id,
            system_name=package.get_system_name(),
            domain=package.get_domain(),
            validated_at=datetime.now(timezone.utc).isoformat(),
            input_fingerprint=fingerprint,
            execution_duration_ms=duration_ms,
        )

        # 13. Determine strict full validation status
        is_fully_validated = bool(
            scorecard.status in ("HEALTHY", "DEGRADED")
            and red_team_report.verdict in ("APPROVED", "APPROVED_WITH_CONDITIONS")
            and critical_count == 0
            and high_count == 0
        )

        # 14. Build Final Response Envelope
        response = ValidatedArchitectureResponse(
            architecture=package.data,
            validation=validation_block,
            evidence=real_world_report,
            explainability=explainability_block,
            remediation=remediation_plan,
            metadata=metadata,
            is_fully_validated=is_fully_validated,
            attempt=attempt,
            max_retries=max_retries,
            correction_history=correction_history or [],
        )

        # Cache validated response in Redis
        if r_client:
            try:
                r_client.set(cache_key, response.model_dump_json(), ex=86400)
            except Exception:
                pass

        logger.info(
            f"Validation completed for '{package.package_id}' (Attempt {attempt}): Status={response.status}, "
            f"Verdict={red_team_report.verdict}, FullyValidated={is_fully_validated}, "
            f"Composite Score={scorecard.overall_composite_score}, Total Findings={len(all_findings)}, Duration={duration_ms}ms"
        )
        return response

    def build_correction_feedback(
        self,
        input_data: Union[Dict[str, Any], str, Path, ArchitecturePackageInput, ValidatedArchitectureResponse],
        attempt: int = 1,
    ) -> ArchitectureCorrectionFeedback:
        """Derive structured correction feedback instructing the AI Engine on targeted repairs."""
        if isinstance(input_data, ValidatedArchitectureResponse):
            package = self._normalize_input(input_data.architecture)
            findings = input_data.validation.findings
            real_world_report = input_data.evidence
        else:
            package = self._normalize_input(input_data)
            validated = self.validate(package, attempt=attempt)
            findings = validated.validation.findings
            real_world_report = validated.evidence

        return self.remediation_engine.build_correction_feedback(
            package=package,
            findings=findings,
            real_world_report=real_world_report,
            attempt=attempt,
        )

    def _normalize_input(
        self,
        input_data: Union[Dict[str, Any], str, Path, ArchitecturePackageInput],
    ) -> ArchitecturePackageInput:
        """Convert various input formats into a validated ArchitecturePackageInput."""
        if isinstance(input_data, ArchitecturePackageInput):
            return input_data

        if isinstance(input_data, (str, Path)):
            path_obj = Path(input_data)
            if path_obj.exists() and path_obj.is_file():
                raw = path_obj.read_text(encoding="utf-8")
                parsed = json.loads(raw)
            else:
                parsed = json.loads(str(input_data))
        elif isinstance(input_data, dict):
            parsed = input_data
        else:
            raise ValueError(f"Unsupported input type for ValidatorEngine: {type(input_data)}")

        pkg_id = (
            parsed.get("package_id")
            or parsed.get("generation_id")
            or parsed.get("id")
            or "arch_pkg_unknown"
        )
        return ArchitecturePackageInput(package_id=str(pkg_id), data=parsed)
