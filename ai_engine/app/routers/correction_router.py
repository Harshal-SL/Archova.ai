"""FastAPI Router for Targeted AI Architecture Corrections (Part 2.2.2)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status

from app.corrections.contracts import (
    AcceptCorrectionRequest,
    AcceptCorrectionResponse,
    CorrectionApprovalRequest,
    CorrectionApprovalResponse,
    RejectCorrectionResponse,
    TargetedCorrectionRequest,
    TargetedCorrectionResponse,
)
from app.corrections.correction_service import correction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/architecture-corrections", tags=["Architecture Corrections"])


# ── 1. Record Server-Side Approval ─────────────────────────────────────────────

@router.post(
    "/approvals",
    response_model=CorrectionApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Register explicit user approval for an architecture finding",
)
def register_correction_approval(payload: CorrectionApprovalRequest) -> CorrectionApprovalResponse:
    """Records an explicit user approval on the backend.
    Targeted AI corrections are strictly rejected unless prior user approval is verified.
    """
    try:
        return correction_service.register_approval(payload)
    except Exception as exc:
        logger.exception("Error registering correction approval: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record approval: {str(exc)}",
        ) from exc


@router.get(
    "/approvals/{generation_id}",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List all approved findings for a given generation session",
)
def get_generation_approvals(generation_id: str) -> List[Dict[str, Any]]:
    """Retrieve all approved findings for the specified generation session."""
    return correction_service.get_approvals_for_generation(generation_id)


# ── 2. Request Targeted AI Correction ─────────────────────────────────────────

@router.post(
    "",
    response_model=TargetedCorrectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute targeted AI refinement of an approved architecture defect",
)
async def request_targeted_correction(payload: TargetedCorrectionRequest) -> TargetedCorrectionResponse:
    """Executes a surgical, single-finding AI correction against the specified artifact.
    Preserves all unrelated architecture decisions, interfaces, endpoints, and schemas.
    """
    try:
        return await correction_service.execute_targeted_correction(payload)
    except PermissionError as perm_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(perm_err),
        ) from perm_err
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        ) from val_err
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(run_err),
        ) from run_err
    except Exception as exc:
        logger.exception("Error executing targeted correction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Targeted correction execution failed: {str(exc)}",
        ) from exc


# ── 3. Inspect Proposed Correction Draft ──────────────────────────────────────

@router.get(
    "/{operation_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Retrieve details of a proposed correction operation",
)
def get_correction_operation(operation_id: str) -> Dict[str, Any]:
    """Retrieve draft details, verification scores, and change summary for an operation."""
    op = correction_service.get_operation(operation_id)
    if not op:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correction operation '{operation_id}' not found.",
        )
    return op


# ── 4. Accept Correction (Commit New Version) ─────────────────────────────────

@router.post(
    "/{operation_id}/accept",
    response_model=AcceptCorrectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept a proposed correction draft and commit as a new artifact version",
)
async def accept_correction(
    operation_id: str,
    payload: Optional[AcceptCorrectionRequest] = None,
) -> AcceptCorrectionResponse:
    """Commits the proposed correction draft into the architecture package as a new version.
    Preserves the original artifact in historical version records.
    """
    try:
        return await correction_service.accept_correction(operation_id, payload)
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Error accepting correction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept correction: {str(exc)}",
        ) from exc


# ── 5. Reject Correction (Preserve Original) ──────────────────────────────────

@router.post(
    "/{operation_id}/reject",
    response_model=RejectCorrectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a proposed correction draft, preserving original architecture unchanged",
)
def reject_correction(operation_id: str) -> RejectCorrectionResponse:
    """Rejects the proposed correction draft. The original artifact remains completely unchanged."""
    try:
        return correction_service.reject_correction(operation_id)
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Error rejecting correction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject correction: {str(exc)}",
        ) from exc


# ── 6. Historical Versions Audit ──────────────────────────────────────────────

@router.get(
    "/versions/{generation_id}",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List historical version records for a given generation session",
)
def get_historical_versions(generation_id: str) -> List[Dict[str, Any]]:
    """Retrieve all committed version changes for the specified generation session."""
    return correction_service.get_historical_versions(generation_id)

