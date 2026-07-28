"""
REE Router

Exposes the Requirements Engineering Engine (REE) via the HTTP API.

New endpoints:
  POST /api/ree/run      — Start or continue a full REE workflow
  POST /api/ree/continue — Continue an existing REE session (submit answers)

Backward-compatible endpoint replacement:
  POST /api/extract      — Still works, but now routes through the REE
                           Orchestrator instead of the bare extraction pipeline.
                           Response shape is unchanged so existing clients
                           continue to work without modification.

Flow overview:
  /api/input  →  /api/ree/run  →  (interview loop via /api/ree/continue)
             →  /api/design
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ree.orchestrator import REEOrchestrator
from app.ree.models import REERequest, REEStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared orchestrator instance — stateless, safe to reuse across requests
_orchestrator = REEOrchestrator()


# ── Pydantic request/response models ─────────────────────────────────────────


class AnswerItem(BaseModel):
    parameter: str
    answer: str


class REERunRequest(BaseModel):
    """
    Request body for POST /api/ree/run

    Supports both fresh starts and continued interview sessions.
    """
    combined_prompt: str = Field(
        ...,
        description="Combined stakeholder input text (from /api/input or provided directly).",
    )
    input_sources: List[str] = Field(
        default_factory=list,
        description="Source labels for the combined_prompt (file names, 'text', etc.).",
    )
    prior_parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Pre-extracted parameters from a prior /api/extract call. "
            "Pass these to skip re-extraction in a resumed session."
        ),
    )
    prior_src: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Full serialised SRC from a previous REEResponse.src. "
            "When provided the Orchestrator restores complete session state "
            "(interview history, review result, etc.) and continues from there."
        ),
    )
    interview_answers: Optional[List[AnswerItem]] = Field(
        default=None,
        description="Answers to the questions from the previous interview round.",
    )
    max_interview_rounds: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum interview rounds before forcing finalization.",
    )


class REEContinueRequest(BaseModel):
    """
    Request body for POST /api/ree/continue

    Used to submit answers in a multi-turn interview session.
    The client POSTs back the ``src`` dict from the prior response
    together with the stakeholder's answers.
    """
    src: Dict[str, Any] = Field(
        ...,
        description="The 'src' dict from the previous REEResponse.",
    )
    answers: List[AnswerItem] = Field(
        ...,
        description="Stakeholder answers to the interview questions.",
    )


# ── /api/ree/run ──────────────────────────────────────────────────────────────


@router.post("/api/ree/run")
def ree_run(body: REERunRequest):
    """
    Start (or continue) a full REE workflow run.

    Returns either:
      - status=complete  → ARSRS ready for /api/design
      - status=interviewing → questions for the stakeholder to answer
      - status=failed → error detail
    """
    if not body.combined_prompt.strip():
        raise HTTPException(status_code=400, detail="combined_prompt must not be empty.")

    # Convert Pydantic AnswerItem models to plain dicts
    answers_raw = (
        [{"parameter": a.parameter, "answer": a.answer} for a in body.interview_answers]
        if body.interview_answers
        else None
    )

    request = REERequest(
        combined_prompt=body.combined_prompt,
        input_sources=body.input_sources,
        prior_parameters=body.prior_parameters,
        prior_src=body.prior_src,
        interview_answers=answers_raw,
        max_interview_rounds=body.max_interview_rounds,
    )

    try:
        response = _orchestrator.run(request)
    except Exception as exc:
        logger.error("REE run failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"REE workflow error: {exc}") from exc

    return response.to_dict()


# ── /api/ree/continue ─────────────────────────────────────────────────────────


@router.post("/api/ree/continue")
def ree_continue(body: REEContinueRequest):
    """
    Continue an existing REE session by submitting interview answers.

    The client should POST back:
      - ``src``:     the exact ``src`` dict from the prior REEResponse
      - ``answers``: stakeholder answers to the interview questions

    Returns the same shape as /api/ree/run.
    """
    if not body.src:
        raise HTTPException(status_code=400, detail="src must not be empty.")
    if not body.answers:
        raise HTTPException(status_code=400, detail="answers list must not be empty.")

    answers_raw = [{"parameter": a.parameter, "answer": a.answer} for a in body.answers]

    try:
        response = _orchestrator.run_from_src(body.src, answers=answers_raw)
    except Exception as exc:
        logger.error("REE continue failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"REE continue error: {exc}") from exc

    return response.to_dict()


# ── Backward-compatible /api/extract ─────────────────────────────────────────


class ExtractionRequest(BaseModel):
    combined_prompt: str


@router.post("/api/extract")
def extract_requirements_ree(body: ExtractionRequest):
    """
    Backward-compatible replacement for the original /api/extract endpoint.

    Routes through the REE Orchestrator but returns the same
    ``{"parameters": {...}}`` shape so existing clients continue to work.

    The REE enriches the extracted parameters via the Engineering Team
    agents (parallel analysis), so the output is richer than the previous
    bare extraction pipeline.
    """
    if not body.combined_prompt.strip():
        raise HTTPException(status_code=400, detail="combined_prompt is empty.")

    request = REERequest(
        combined_prompt=body.combined_prompt,
        max_interview_rounds=0,  # Never start an interview from the compat endpoint
    )

    try:
        response = _orchestrator.run(request)
    except Exception as exc:
        logger.error("REE extract (compat) failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Return in the original shape regardless of REE status
    # (the ARSRS parameters or the SRC parameters are equivalent here)
    if response.arsrs:
        params = response.arsrs.get("parameters", {})
    else:
        params = response.src.get("parameters", {})

    return {"parameters": params}


# ── /api/ree/design ───────────────────────────────────────────────────────────


class REEDesignRequest(BaseModel):
    """
    Request body for POST /api/ree/design

    Convenience endpoint that chains REE finalization → architecture generation
    in a single call. Pass the ARSRS from a completed REE run.
    """
    arsrs: Dict[str, Any] = Field(
        ...,
        description="The 'arsrs' dict from a completed REEResponse (status='complete').",
    )


@router.post("/api/ree/design")
def ree_design(body: REEDesignRequest):
    """
    Generate system architecture (HLD + LLD) from a completed ARSRS.

    Typical client flow:
      1. POST /api/ree/run    → status=complete, response contains arsrs
      2. POST /api/ree/design → pass arsrs from step 1, receive HLD + LLD

    This endpoint delegates to /api/design/arsrs internally.
    """
    if not body.arsrs:
        raise HTTPException(status_code=400, detail="arsrs is empty.")

    from app.services.design_service import run_design_pipeline_from_arsrs
    try:
        return run_design_pipeline_from_arsrs(body.arsrs)
    except RuntimeError as exc:
        logger.error("REE design failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Architecture generation error: {exc}") from exc
