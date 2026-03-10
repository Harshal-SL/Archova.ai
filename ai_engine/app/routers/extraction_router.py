from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.requirement_extractor.pipeline import run_extraction_pipeline

router = APIRouter()


class ExtractionRequest(BaseModel):
    combined_prompt: str


@router.post("/api/extract")
def extract_requirements(body: ExtractionRequest):
    if not body.combined_prompt.strip():
        raise HTTPException(status_code=400, detail="combined_prompt is empty.")

    try:
        requirements = run_extraction_pipeline(body.combined_prompt)
        return {"parameters": requirements}
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
