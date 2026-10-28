"""FastAPI Application Entrypoint for Validator Engine v2 (Port 8002).

Endpoints:
- POST /v1/pipeline/run          -> 202 Accepted, initiates background validation & correction loop
- GET  /v1/pipeline/{id}/status  -> Real-time state and iteration progress for polling
- GET  /v1/reports/{id}          -> Full Report and final architecture package snapshot
- POST /v1/validate              -> Direct single-pass validation on package payload (dev mode)
- GET  /health                   -> Health check and service readiness
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import (
    BackgroundTasks,
    FastAPI,
    Header,
    HTTPException,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from Validator_Engine_v2.config import config
from Validator_Engine_v2.pipeline import pipeline_engine
from Validator_Engine_v2.schemas import Report
from Validator_Engine_v2.storage.report_store import report_store

app = FastAPI(
    title="Validator Engine v2",
    description="Independent Architectural Verification & Quality Gate Service for Archova.ai",
    version="2.0.0",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _verify_api_key(x_api_key: Optional[str] = None, authorization: Optional[str] = None) -> None:
    """Simple API-key verification; skipped in dev if VALIDATOR_API_KEY_INBOUND is unset."""
    expected = config.VALIDATOR_API_KEY_INBOUND.strip()
    if not expected:
        return
    provided = (x_api_key or "").strip()
    if not provided and authorization:
        if authorization.lower().startswith("bearer "):
            provided = authorization[7:].strip()
        else:
            provided = authorization.strip()

    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key header (X-API-Key or Authorization).",
        )


class RunPipelineRequest(BaseModel):
    generation_id: str = Field(..., min_length=1, description="AI Engine generation ID to evaluate")
    package: Optional[Dict[str, Any]] = Field(default=None, description="Optional pre-fetched architecture package")


# ── Health Endpoint ───────────────────────────────────────────────────────────

@app.get("/health", tags=["System Health"])
async def health():
    return {
        "status": "healthy",
        "service": "Validator Engine v2",
        "version": "2.0.0",
        "port": config.VALIDATOR_PORT,
        "mock_mode": config.VALIDATOR_MOCK == "1",
        "model": config.VALIDATOR_MODEL,
        "accept_threshold": config.ACCEPT_THRESHOLD,
        "max_rounds": config.MAX_ROUNDS,
    }


# ── Run Background Validation Pipeline ─────────────────────────────────────────

@app.post(
    "/v1/pipeline/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger automated iterative validation pipeline",
    tags=["Validation Pipeline"],
)
async def run_pipeline(
    payload: RunPipelineRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    """Initiates the multi-round validation and AI correction workflow in the background.

    Returns immediately with HTTP 202 Accepted.
    """
    _verify_api_key(x_api_key, authorization)
    gen_id = payload.generation_id.strip()

    async def _runner():
        try:
            await pipeline_engine.execute_pipeline(
                generation_id=gen_id,
                initial_package=payload.package,
            )
        except Exception as exc:
            st = pipeline_engine.task_states.get(gen_id)
            if st:
                st.state = "error"
                st.error = str(exc)

    # Launch background task
    background_tasks.add_task(_runner)

    return {
        "message": f"Validation pipeline started for generation '{gen_id}'",
        "generation_id": gen_id,
        "status_url": f"/v1/pipeline/{gen_id}/status",
        "report_url": f"/v1/reports/{gen_id}",
    }


# ── Pipeline Status Polling Endpoint ───────────────────────────────────────────

@app.get(
    "/v1/pipeline/{generation_id}/status",
    summary="Poll real-time validation and correction status",
    tags=["Validation Pipeline"],
)
async def get_pipeline_status(
    generation_id: str,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    _verify_api_key(x_api_key, authorization)
    stat = pipeline_engine.get_status(generation_id)
    return {
        "generation_id": generation_id,
        **stat,
    }


# ── Report Retrieval Endpoint ──────────────────────────────────────────────────

@app.get(
    "/v1/reports/{generation_id}",
    summary="Retrieve complete validation report and final package snapshot",
    tags=["Reports"],
)
async def get_report(
    generation_id: str,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    _verify_api_key(x_api_key, authorization)
    data = report_store.load_report(generation_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for generation '{generation_id}' not found.",
        )
    return data


@app.get(
    "/v1/pipeline/{generation_id}/report",
    summary="Retrieve complete validation report via pipeline alias",
    tags=["Reports"],
)
async def get_pipeline_report(
    generation_id: str,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    return await get_report(generation_id, x_api_key, authorization)


# ── Direct Single-Pass Validation (Dev Mode) ───────────────────────────────────

@app.post(
    "/v1/validate",
    summary="Direct single-pass validation without generation loop",
    tags=["Direct Validation"],
)
async def validate_direct(
    package: Dict[str, Any],
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    """Directly evaluates a supplied architecture package in a single pass without re-generation."""
    _verify_api_key(x_api_key, authorization)
    if not package:
        raise HTTPException(status_code=400, detail="Empty package payload provided.")

    gen_id = str(package.get("generation_id", package.get("id", "direct_validate")))

    from Validator_Engine_v2.real_world.corpus_loader import CorpusLoader
    from Validator_Engine_v2.real_world.selector import SystemSelector
    from Validator_Engine_v2.real_world.profile_extractor import ProfileExtractor
    from Validator_Engine_v2.schemas import ReferenceSystemUsed

    # Real-World Benchmark evaluation for direct validation
    corpus_loader = CorpusLoader()
    corpus_docs = corpus_loader.load_corpus()
    corpus_status = "ok" if corpus_docs else "unavailable"
    all_patterns = []
    system_names_by_pattern = {}
    references_used = []

    if corpus_docs:
        selector = SystemSelector(top_k=config.REAL_WORLD_TOP_K)
        selected_systems = selector.select(
            docs=corpus_docs,
            arsrs=package.get("arsrs", {}),
            hld=package.get("hld", {}),
        )
        extractor = ProfileExtractor(llm_client=pipeline_engine.reviewer.llm_client)
        for s in selected_systems:
            ref_item = ReferenceSystemUsed(
                id=s.doc.id,
                system_name=s.doc.system_name,
                match_reasons=s.match_reasons,
                scale_note=s.scale_note,
                sources=s.doc.sources,
            )
            references_used.append(ref_item)
            profile = await extractor.extract_profile(s.doc)
            if not profile.extraction_failed:
                for p in profile.patterns:
                    all_patterns.append(p)
                    system_names_by_pattern[p.id] = s.doc.system_name

    reviewer_mode = "mock" if config.VALIDATOR_MOCK in ("1", "true", "mock") else "live"
    model_used = "mock" if reviewer_mode == "mock" else config.VALIDATOR_MODEL

    results, all_findings, normalized = await pipeline_engine.run_single_pass(
        package=package,
        iteration_num=1,
        patterns=all_patterns if corpus_docs else None,
        system_names_by_pattern=system_names_by_pattern,
        references_used=references_used,
        reviewer_mode=reviewer_mode,
    )

    scores = {art: r.score for art, r in results.items()}
    overall_c = int(round(sum(r.c_score for r in results.values()) / len(results)))
    overall_r = int(round(sum(r.r_score for r in results.values()) / len(results)))
    w_scores = [r.w_score for r in results.values() if r.w_score is not None]
    overall_w = int(round(sum(w_scores) / len(w_scores))) if w_scores else None
    overall_d = int(round(sum(r.penalty_d for r in results.values()) / len(results)))
    overall_s = int(round(sum(r.score for r in results.values()) / len(results)))
    scores["overall"] = overall_s
    scores["c"] = overall_c
    scores["r"] = overall_r
    scores["w"] = overall_w
    scores["d"] = overall_d

    all_accepted = all(r.verdict in ("ACCEPTED", "ACCEPTED_WITH_WARNINGS") for r in results.values())
    has_provisional = any(r.verdict == "PROVISIONAL" for r in results.values())
    has_critical = any(
        any(f.severity == "critical" for f in r.findings)
        for r in results.values()
    )
    has_rejected = any(r.verdict == "REJECTED" for r in results.values())

    if has_critical or has_rejected:
        final_status = "REJECTED"
    elif has_provisional:
        final_status = "PROVISIONAL"
    elif all_accepted:
        if reviewer_mode == "mock" and not config.ALLOW_MOCK_ACCEPT:
            final_status = "PROVISIONAL"
        elif any(r.verdict == "ACCEPTED_WITH_WARNINGS" for r in results.values()):
            final_status = "ACCEPTED_WITH_WARNINGS"
        else:
            final_status = "ACCEPTED"
    else:
        final_status = "REJECTED"

    now = datetime.now(timezone.utc).isoformat()
    report = Report(
        generation_id=gen_id,
        iterations=[
            {
                "n": 1,
                "results": results,
                "corrections": [],
                "started_at": now,
                "finished_at": now,
            }
        ],
        final_status=final_status,
        final_scores=scores,
        overall_c=overall_c,
        overall_r=overall_r,
        overall_w=overall_w,
        overall_d=overall_d,
        model_used=model_used,
        reviewer_mode=reviewer_mode,
        corpus_status=corpus_status,
        references_used=references_used,
        config_snapshot={
            "accept_threshold": config.ACCEPT_THRESHOLD,
            "max_rounds": config.MAX_ROUNDS,
            "validator_mock": config.VALIDATOR_MOCK,
            "allow_mock_accept": config.ALLOW_MOCK_ACCEPT,
            "rw_weight": config.RW_WEIGHT,
            "rw_min": config.RW_MIN,
        },
        created_at=now,
        final_package=package,
    )
    return report
