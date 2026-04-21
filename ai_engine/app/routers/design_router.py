from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag_design import reindex_corpus, run_design_pipeline

router = APIRouter()


class DesignRequest(BaseModel):
    parameters: dict
    design_output: dict = Field(default_factory=dict)


@router.post("/api/design")
def generate_system_design(body: DesignRequest):
    if not body.parameters:
        raise HTTPException(status_code=400, detail="parameters is empty.")

    try:
        return run_design_pipeline(body.parameters)
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
