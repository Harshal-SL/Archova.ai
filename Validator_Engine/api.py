"""FastAPI Service API for the Validator Engine.

Allows running the Validator Engine as an independent microservice.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from Validator_Engine.engine import ValidatorEngine
from Validator_Engine.models.output_models import ValidatedArchitectureResponse
from Validator_Engine.models.report_models import ArchitectureCorrectionFeedback

app = FastAPI(
    title="Validator Engine API",
    description="Independent Architectural Verification, Quality Assessment, and Evidence Engine.",
    version="1.0.0",
)

# Enable CORS for Next Application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine = ValidatorEngine()


@app.get("/")
@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health status check."""
    return {"status": "ok", "service": "validator_engine", "version": "1.0.0"}


@app.post("/api/v1/validate", response_model=ValidatedArchitectureResponse)
@app.post("/api/v1/validator/validate", response_model=ValidatedArchitectureResponse)
def validate_architecture(payload: Dict[str, Any], attempt: int = 1, max_retries: int = 2) -> ValidatedArchitectureResponse:
    """Validate an architecture package JSON payload and produce validated_architecture.json response."""
    if not payload:
        raise HTTPException(status_code=400, detail="Empty architecture package payload provided.")
    try:
        return _engine.validate(payload, attempt=attempt, max_retries=max_retries)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(exc)}")


@app.post("/api/v1/validator/feedback", response_model=ArchitectureCorrectionFeedback)
def get_correction_feedback(payload: Dict[str, Any], attempt: int = 1) -> ArchitectureCorrectionFeedback:
    """Generate structured correction feedback instructing the AI Engine on targeted repairs."""
    if not payload:
        raise HTTPException(status_code=400, detail="Empty architecture package payload provided.")
    try:
        return _engine.build_correction_feedback(payload, attempt=attempt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Feedback generation failed: {str(exc)}")


@app.get("/api/v1/validator/archetypes")
def list_archetypes() -> List[Dict[str, Any]]:
    """List reference system archetypes available in the knowledge base."""
    cat10_chunks = [
        c.to_dict()
        for c in _engine.retriever._chunks_cache
        if "category_10" in str(c.file_path).lower() or "real_world" in c.category.lower()
    ]
    return cat10_chunks
