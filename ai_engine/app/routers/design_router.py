from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict

from app.services.design_service import reindex_corpus, run_design_pipeline, run_design_pipeline_from_arsrs

router = APIRouter()


class DesignRequest(BaseModel):
    parameters: dict
    design_output: dict = Field(default_factory=dict)


class ARSRSDesignRequest(BaseModel):
    """Request body for POST /api/design/arsrs — ARSRS-driven design generation."""
    arsrs: Dict[str, Any] = Field(
        ...,
        description="Serialised ARSRS dict from the REE pipeline (/api/ree/run response.arsrs).",
    )


@router.post("/api/design")
def generate_system_design(body: DesignRequest):
    if not body.parameters:
        raise HTTPException(status_code=400, detail="parameters is empty.")

    try:
        return run_design_pipeline(body.parameters)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/design/arsrs")
def generate_design_from_arsrs(body: ARSRSDesignRequest):
    """
    Generate system architecture (HLD + LLD) from an ARSRS.

    The ARSRS is the output of the REE pipeline (/api/ree/run when
    status == 'complete'). Pass response.arsrs here to generate the
    full architecture design.

    This is the primary entry point for architecture generation in the
    REE-integrated workflow:

        /api/ree/run → arsrs → /api/design/arsrs → HLD + LLD
    """
    if not body.arsrs:
        raise HTTPException(status_code=400, detail="arsrs is empty.")

    try:
        return run_design_pipeline_from_arsrs(body.arsrs)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/design/reindex")
def rebuild_design_index():
    try:
        stats = reindex_corpus()
        return {
            "status": "ok",
            "index": stats,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
