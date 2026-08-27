"""Software Architecture Engine (SAE) Router

Exposes system architecture generation, ARSRS-driven generation, unified end-to-end execution, and vector index management.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.services.file_parser import parse_file
from app.sae.models.design_generation_response import (
    DesignGenerationRequest,
    DesignGenerationResponse,
)
from app.sae.services.design_generation_service import DesignGenerationService
from app.sae.services.sae_service import SAEGenerationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sae", tags=["Software Architecture Engine (SAE)"])
_generation_service = DesignGenerationService()
_sae_service = SAEGenerationService()


class ARSRSDesignRequest(BaseModel):
    """Request body for POST /api/sae/arsrs — ARSRS-driven design generation."""
    arsrs: Dict[str, Any] = Field(
        ...,
        description="Serialised ARSRS dict from the REE pipeline (/api/ree/run response.arsrs).",
    )


@router.post(
    "/generate",
    response_model=DesignGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate complete architecture specification from user prompt or file payload",
)
async def generate_design_unified(
    input_type: str = Form(default="text"),
    content: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> DesignGenerationResponse:
    """Unified endpoint accepting raw text, Markdown, PDF, DOCX, or Image file upload.

    Executes REE to produce ARSRS and immediately executes SAE to produce Software Architecture Package.
    """
    extracted_text = ""
    if file is not None:
        try:
            extracted_text = await parse_file(file)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse uploaded file: {str(e)}",
            )
    elif content is not None:
        extracted_text = content
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'content' text or 'file' upload must be provided.",
        )

    req = DesignGenerationRequest(
        input_type=input_type,
        content=extracted_text,
    )

    response = _generation_service.generate_design(req)
    if response.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.model_dump(),
        )

    return response


@router.post("/arsrs", summary="Generate architecture from ARSRS specification")
def generate_design_from_arsrs(body: ARSRSDesignRequest):
    """Generate system architecture (HLD + LLD) from an ARSRS specification."""
    if not body.arsrs:
        raise HTTPException(status_code=400, detail="arsrs is empty.")

    try:
        from app.sae.context.design_generation_context import DesignGenerationContext
        ctx = DesignGenerationContext(arsrs=body.arsrs)
        res_ctx = _sae_service.process_architecture(ctx)
        return {
            "status": res_ctx.status,
            "request_id": res_ctx.request_id,
            "output_directory": res_ctx.output_directory,
            "execution_metrics": res_ctx.execution_metrics,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/reindex", summary="Rebuild vector index for architecture knowledge base")
def rebuild_design_index():
    try:
        from app.rag.ingestion import IngestionPipeline
        pipeline = IngestionPipeline()
        stats = pipeline.run()
        return {
            "status": "ok",
            "index": stats,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
