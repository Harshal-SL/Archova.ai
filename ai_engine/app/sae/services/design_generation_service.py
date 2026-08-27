"""Master Design Generation Service orchestrating end-to-end REE to SAE workflow."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.sae.context.design_generation_context import DesignGenerationContext
from app.sae.models.design_generation_response import (
    DesignGenerationRequest,
    DesignGenerationResponse,
    GeneratedOutputsManifest,
)
from app.sae.services.ree_service import REEGenerationService
from app.sae.services.sae_service import SAEGenerationService

logger = logging.getLogger(__name__)


class DesignGenerationService:
    """Master orchestrator executing end-to-end requirement extraction and architecture design generation."""

    def __init__(
        self,
        ree_service: Optional[REEGenerationService] = None,
        sae_service: Optional[SAEGenerationService] = None,
    ) -> None:
        self.ree_service = ree_service or REEGenerationService()
        self.sae_service = sae_service or SAEGenerationService()

    def generate_design(
        self, request: DesignGenerationRequest
    ) -> DesignGenerationResponse:
        """Execute full pipeline: Input -> REE -> ARSRS -> SAE -> Architecture Package -> Response."""
        t0 = time.time()
        context = DesignGenerationContext(
            input_type=request.input_type,
            raw_input=request.content or "",
            normalized_input=request.content or "",
            metadata=request.metadata or {},
        )

        logger.info(f"Starting Unified Design Generation [Request ID: {context.request_id}]")

        # Step 1: Execute REE Pipeline
        context = self.ree_service.process_requirements(context)

        if context.status == "FAILED":
            logger.error(f"REE Stage Failed [Request ID: {context.request_id}]")
            return DesignGenerationResponse(
                status="FAILED",
                request_id=context.request_id,
                stage="REE",
                message="Requirement extraction failed.",
                errors=context.errors,
                execution_metrics=context.execution_metrics,
            )

        # Step 2: Execute SAE Pipeline
        context = self.sae_service.process_architecture(context)

        if context.status == "FAILED":
            logger.error(f"SAE Stage Failed [Request ID: {context.request_id}]")
            return DesignGenerationResponse(
                status="FAILED",
                request_id=context.request_id,
                stage="SAE",
                message="Architecture generation failed.",
                errors=context.errors,
                arsrs=context.arsrs,
                execution_metrics=context.execution_metrics,
            )

        total_time = round(time.time() - t0, 2)
        context.execution_metrics["total_execution_time"] = total_time

        # Filter generated output files into JSONs, Markdown, and HTML report
        json_files = [f for f in context.generated_files if f.endswith(".json")]
        markdown_files = [f for f in context.generated_files if f.endswith(".md")]
        html_report = next((f for f in context.generated_files if f.endswith(".html")), "report.html")

        manifest = GeneratedOutputsManifest(
            output_directory=context.output_directory,
            json_files=json_files,
            markdown_files=markdown_files,
            html_report=html_report,
        )

        logger.info(f"Unified Design Generation Completed Successfully [Request ID: {context.request_id}] in {total_time}s")

        return DesignGenerationResponse(
            status="SUCCESS",
            request_id=context.request_id,
            message="End-to-end architecture design generated successfully.",
            arsrs=context.arsrs,
            software_architecture_package=context.software_architecture_package,
            generated_outputs=manifest,
            quality_report=context.quality_report,
            decision_traceability=context.decision_traceability,
            reference_architecture=context.reference_architecture,
            execution_metrics=context.execution_metrics,
        )
