import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import StartGenerationRequest, SubmitAnswerRequest
from app.schemas.responses import (
    ArtifactResponse,
    GenerateArchitectureResponse,
    GenerationLogsResponse,
    GenerationStatusResponse,
    InterviewQuestionSchema,
    LLDDetailResponse,
    LogEntrySchema,
    StartGenerationResponse,
    SubmitAnswerResponse,
)
from app.services.generation_service import generation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/generations", tags=["Generations"])


# ── 1. Start Generation ───────────────────────────────────────────────────────


@router.post(
    "",
    response_model=StartGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Start generation from problem statement and receive first interview question",
)
async def start_generation(payload: StartGenerationRequest) -> StartGenerationResponse:
    """Accepts a stakeholder problem statement, starts the REE pipeline to extract requirements,
    detect ambiguities, generates clarification questions, and returns the first question.
    """
    try:
        context = generation_service.start_generation(payload.prompt)
        first_q = None
        if context.interview_questions:
            q_data = context.interview_questions[0]
            first_q = InterviewQuestionSchema(
                question_id=q_data["question_id"],
                question=q_data["question"],
                options=q_data.get("options", []),
                default_option=q_data.get("default_option"),
                rationale=q_data.get("rationale"),
                target_section=q_data.get("target_section"),
                target_field=q_data.get("target_field"),
                priority=q_data.get("priority"),
            )

        return StartGenerationResponse(
            generation_id=context.generation_id,
            status=context.status,
            current_question=first_q,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Error in start_generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start generation workflow: {str(exc)}",
        ) from exc


# ── 2. Submit Interview Answer ───────────────────────────────────────────────


@router.post(
    "/{generation_id}/answers",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit answer to current interview question",
)
async def submit_interview_answer(
    generation_id: str,
    payload: SubmitAnswerRequest,
) -> SubmitAnswerResponse:
    """Submit an answer to an interview question. Returns the next question or indicates
    that all questions have been completed.
    """
    try:
        context, next_q_data = generation_service.submit_answer(
            generation_id=generation_id,
            question_id=payload.question_id,
            answer=payload.answer,
        )

        next_q = None
        if next_q_data:
            next_q = InterviewQuestionSchema(
                question_id=next_q_data["question_id"],
                question=next_q_data["question"],
                options=next_q_data.get("options", []),
                default_option=next_q_data.get("default_option"),
                rationale=next_q_data.get("rationale"),
                target_section=next_q_data.get("target_section"),
                target_field=next_q_data.get("target_field"),
                priority=next_q_data.get("priority"),
            )

        return SubmitAnswerResponse(
            generation_id=context.generation_id,
            status=context.status,
            next_question=next_q,
        )
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Error in submit_interview_answer: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process interview answer: {str(exc)}",
        ) from exc


# ── 3. Generate ARSRS + HLD ───────────────────────────────────────────────────


@router.post(
    "/{generation_id}/generate",
    response_model=GenerateArchitectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate ARSRS and HLD, and trigger background parallel LLD tasks",
)
async def generate_architecture(generation_id: str) -> GenerateArchitectureResponse:
    """Finalizes requirements into ARSRS and executes High Level Design (HLD).
    Immediately returns ARSRS and HLD while initiating parallel background LLD generation.
    """
    try:
        context = await generation_service.generate_arsrs_and_hld(generation_id)
        return GenerateArchitectureResponse(
            generation_id=context.generation_id,
            status=context.status,
            arsrs=context.arsrs or {},
            hld=context.hld or {},
        )
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except ValueError as val_err:
        err_msg = str(val_err)
        status_code = (
            status.HTTP_409_CONFLICT
            if "already in progress" in err_msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=err_msg,
        ) from val_err
    except Exception as exc:
        logger.exception("Error in generate_architecture: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Architecture generation failed: {str(exc)}",
        ) from exc


# ── 4. Get Generation Status ─────────────────────────────────────────────────


@router.get(
    "/{generation_id}/status",
    response_model=GenerationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll overall generation and per-LLD background progress",
)
async def get_generation_status(generation_id: str) -> GenerationStatusResponse:
    """Returns the current state of interview, ARSRS, HLD, and background LLD generation."""
    try:
        stat = generation_service.get_status(generation_id)
        return GenerationStatusResponse(**stat)
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except Exception as exc:
        logger.exception("Error in get_generation_status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch status: {str(exc)}",
        ) from exc


# ── 5. Get ARSRS ─────────────────────────────────────────────────────────────


@router.get(
    "/{generation_id}/arsrs",
    response_model=ArtifactResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve generated ARSRS specification",
)
async def get_arsrs(generation_id: str) -> ArtifactResponse:
    """Retrieve the generated ARSRS specification document."""
    try:
        res = generation_service.get_arsrs(generation_id)
        return ArtifactResponse(**res)
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except Exception as exc:
        logger.exception("Error in get_arsrs: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ARSRS: {str(exc)}",
        ) from exc


# ── 6. Get HLD ───────────────────────────────────────────────────────────────


@router.get(
    "/{generation_id}/hld",
    response_model=ArtifactResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve generated High Level Design (HLD)",
)
async def get_hld(generation_id: str) -> ArtifactResponse:
    """Retrieve the generated High Level Design (HLD) document."""
    try:
        res = generation_service.get_hld(generation_id)
        return ArtifactResponse(**res)
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except Exception as exc:
        logger.exception("Error in get_hld: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch HLD: {str(exc)}",
        ) from exc


# ── 7. Get Specific LLD ───────────────────────────────────────────────────────


@router.get(
    "/{generation_id}/lld/{lld_type}",
    response_model=LLDDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve specific Low Level Design (LLD) artifact",
)
async def get_lld(generation_id: str, lld_type: str) -> LLDDetailResponse:
    """Retrieve the status and generated payload of a specific LLD type.
    Supported types: backend, frontend, database, security, cloud.
    """
    try:
        res = generation_service.get_lld(generation_id, lld_type)
        return LLDDetailResponse(**res)
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Error in get_lld: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch LLD: {str(exc)}",
        ) from exc


# ── 8. Get Execution Logs & Live Stream ──────────────────────────────────────


@router.get(
    "/{generation_id}/logs",
    status_code=status.HTTP_200_OK,
    summary="Retrieve all real-time execution logs for a generation session",
)
async def get_generation_logs(generation_id: str) -> Dict[str, Any]:
    """Retrieve full chronological execution log entries for the session."""
    try:
        logs = generation_service.get_logs(generation_id)
        return {
            "generation_id": generation_id,
            "count": len(logs),
            "logs": logs,
        }
    except KeyError as k_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(k_err).strip("'"),
        ) from k_err
    except Exception as exc:
        logger.exception("Error in get_generation_logs: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {str(exc)}",
        ) from exc


@router.get(
    "/{generation_id}/logs/stream",
    summary="Stream real-time pipeline execution logs via Server-Sent Events (SSE)",
)
async def stream_generation_logs(generation_id: str):
    """Server-Sent Events (SSE) stream for real-time console log monitoring."""
    import asyncio
    import json
    from fastapi.responses import StreamingResponse

    context = generation_service.get_context(generation_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation ID '{generation_id}' not found.",
        )

    async def event_generator():
        q: asyncio.Queue = asyncio.Queue()
        context.subscribers.append(q)

        try:
            # Yield any existing historical logs first
            for historical_entry in list(context.logs):
                yield f"data: {json.dumps(historical_entry)}\n\n"

            # Stream incoming live events
            while True:
                try:
                    entry = await asyncio.wait_for(q.get(), timeout=5.0)
                    yield f"data: {json.dumps(entry)}\n\n"
                    # If generation reached terminal state and queue is empty, close gracefully
                    if context.status in ("COMPLETED", "FAILED") and q.empty():
                        break
                except asyncio.TimeoutError:
                    if context.status in ("COMPLETED", "FAILED") and q.empty():
                        break
                    # Send keep-alive comment only once every 5 seconds
                    yield ": keepalive\n\n"
        finally:
            if q in context.subscribers:
                context.subscribers.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
