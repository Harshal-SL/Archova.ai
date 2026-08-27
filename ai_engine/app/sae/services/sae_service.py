"""SAE Generation Service executing Software Architecture Engine pipeline."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from app.sae.context.design_generation_context import DesignGenerationContext
from app.sae.pipeline import SAEPipeline

logger = logging.getLogger(__name__)


class SAEGenerationService:
    """Service executing lean SAE v2 multi-agent pipeline."""

    def __init__(self, fast_mode: bool = True, verbose: bool = False) -> None:
        self.fast_mode = fast_mode
        self.verbose = verbose

    def process_architecture(self, context: DesignGenerationContext) -> DesignGenerationContext:
        """Execute SAE pipeline with ARSRS input payload."""
        t_start = time.time()
        context.status = "SAE_RUNNING"

        if not context.arsrs:
            context.status = "FAILED"
            context.errors.append("Missing ARSRS specification in context.")
            return context

        try:
            import re
            
            # Resolve project title for dedicated output folder
            raw_title = (
                context.metadata.get("title")
                or context.metadata.get("project_title")
                or (context.arsrs.get("project_profile", {}).get("name") if isinstance(context.arsrs, dict) else None)
                or (context.arsrs.get("project_profile", {}).get("goal") if isinstance(context.arsrs, dict) else None)
                or (context.arsrs.get("system_name") if isinstance(context.arsrs, dict) else None)
                or "system_design"
            )
            title_slug = re.sub(r"[^\w\-_]+", "_", str(raw_title).strip().lower()).strip("_")
            if len(title_slug) > 40:
                title_slug = title_slug[:40].rsplit("_", 1)[0]
            title_slug = title_slug or "system_design"
            
            design_id = (
                getattr(context, "design_id", None)
                or context.metadata.get("design_id")
                or (context.arsrs.get("design_id") if isinstance(context.arsrs, dict) else None)
                or (context.arsrs.get("session_id") if isinstance(context.arsrs, dict) else None)
                or context.request_id
            )
            context.design_id = design_id
            context.metadata["title_slug"] = title_slug

            # Structure: outputs/<title_slug>/outputs and outputs/<title_slug>/logs
            project_base_dir = Path("outputs") / title_slug
            out_dir = project_base_dir / "outputs"
            logs_dir = project_base_dir / "logs"
            out_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)

            pipeline = SAEPipeline(
                output_dir=str(out_dir),
                design_id=design_id,
                logs_root=str(logs_dir),
                debug=True,
            )

            # Save incoming ARSRS directly into outputs folder
            pipeline._save_json("arsrs.json", context.arsrs)

            # Run synchronous pipeline (internally executes async parallel)
            package = pipeline.run(context.arsrs, design_id=design_id)

            duration = round(time.time() - t_start, 2)
            context.execution_metrics["sae_execution_time"] = duration
            context.execution_metrics["total_execution_time"] = round(
                context.execution_metrics.get("ree_execution_time", 0.0) + duration, 2
            )

            context.output_directory = str(pipeline.output_dir)
            context.metadata["design_id"] = design_id
            if pipeline.sae_logger:
                context.metadata["debug_log_path"] = str(pipeline.sae_logger.debug_log_path)
                context.metadata["logs_directory"] = str(pipeline.sae_logger.log_dir)

            context.requirement_analysis = package.requirement_analysis
            context.technology_recommendation = package.technology_recommendation
            context.architecture_plan = package.architecture_decision_plan
            context.hld = package.hld
            context.backend_lld = package.backend_lld
            context.database_lld = package.database_lld
            context.frontend_lld = package.frontend_lld
            context.security_lld = package.security_lld
            context.cloud_lld = package.cloud_lld
            context.merged_package = package.model_dump(mode="json")
            context.software_architecture_package = context.merged_package
            context.completeness_report = package.completeness

            if pipeline.output_dir.exists():
                context.generated_files = [
                    str(f.name) for f in pipeline.output_dir.glob("*") if f.is_file()
                ]

            context.status = "SUCCESS"
            return context

        except Exception as e:
            logger.exception(f"SAE Generation Service Error: {e}")
            context.status = "FAILED"
            context.errors.append(f"SAE Architecture Pipeline Error: {str(e)}")
            return context
