"""FastAPI Router for Architecture Versioning & Non-Destructive Delta Evolution."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.versioning.contracts import ArchitectureDiff, ArchitecturePatch, VersionContext
from app.versioning.differ import ArchitectureDiffer
from app.versioning.version_manager import VersionManager
from app.sae.providers.llm_provider import OpenRouterProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/versioning", tags=["Architecture Versioning"])
_version_manager = VersionManager(llm_provider=OpenRouterProvider())


class EvolveArchitectureRequest(BaseModel):
    """Payload to add a new feature to an existing architecture baseline."""
    session_id: Optional[str] = Field(default=None, description="Chat session ID")
    feature_prompt: str = Field(..., description="Prompt describing the new feature to add")
    baseline_package: Dict[str, Any] = Field(..., description="The previous design JSON (v1.0 / v1.x)")
    target_version: Optional[str] = Field(default=None, description="Explicit target version (e.g. '1.1')")
    simulated_patch: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional pre-formed patch for test/offline simulation without external LLM call",
    )


class EvolveArchitectureResponse(BaseModel):
    """Response returning the merged evolved architecture and the visual diff."""
    status: str = "SUCCESS"
    version: str
    previous_version: str
    feature_summary: str
    evolved_architecture: Dict[str, Any]
    diff: ArchitectureDiff


class DetectModeRequest(BaseModel):
    session_id: Optional[str] = None
    baseline_package: Optional[Dict[str, Any]] = None


@router.post(
    "/detect-mode",
    response_model=VersionContext,
    status_code=status.HTTP_200_OK,
    summary="Detect whether the incoming prompt is INITIAL (v1.0) or EVOLUTION (v1.1+)",
)
def detect_version_mode(payload: DetectModeRequest) -> VersionContext:
    """Returns INITIAL if session has no prior design, or EVOLUTION if baseline exists."""
    return VersionManager.detect_version_context(
        session_id=payload.session_id,
        previous_package=payload.baseline_package,
    )


@router.post(
    "/evolve",
    response_model=EvolveArchitectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Evolve an existing baseline architecture additively with a new feature",
)
async def evolve_architecture(payload: EvolveArchitectureRequest) -> EvolveArchitectureResponse:
    """Non-destructively patches the baseline architecture with the new feature,
    guaranteeing 100% baseline survival and returning the updated package and diff.
    """
    if not payload.baseline_package or not payload.baseline_package.get("hld"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid baseline architecture package containing an 'hld' section is required for evolution.",
        )

    try:
        custom_caller = None
        if payload.simulated_patch:
            custom_caller = lambda _p: payload.simulated_patch

        evolved_pkg, diff = await _version_manager.evolve_architecture(
            baseline=payload.baseline_package,
            feature_prompt=payload.feature_prompt,
            custom_llm_caller=custom_caller,
            target_version=payload.target_version,
            max_retries=2,
        )

        return EvolveArchitectureResponse(
            version=diff.to_version,
            previous_version=diff.from_version,
            feature_summary=diff.feature_summary,
            evolved_architecture=evolved_pkg,
            diff=diff,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Error evolving architecture: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Architecture evolution failed: {str(exc)}",
        ) from exc
