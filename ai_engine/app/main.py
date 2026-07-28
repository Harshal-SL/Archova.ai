from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import input_router, elicitation_router, design_router
from app.routers import ree_router

app = FastAPI(
    title="AI Architecture Engine — REE",
    description=(
        "Requirements Engineering Engine (REE) — "
        "transforms stakeholder input into an Architecture-Ready "
        "Structured Requirement Specification (ARSRS)."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Core input processing (unchanged) ────────────────────────────────────────
app.include_router(input_router.router)

# ── REE Orchestrator endpoints (new primary API) ──────────────────────────────
# Also re-exposes /api/extract for backward compatibility.
app.include_router(ree_router.router)

# ── Elicitation endpoints (kept for direct use / backward compat) ─────────────
app.include_router(elicitation_router.router)

# ── Design generation (unchanged) ─────────────────────────────────────────────
app.include_router(design_router.router)


@app.get("/")
def health():
    return {
        "status": "AI Engine Running",
        "version": "2.0.0",
        "engine": "Requirements Engineering Engine (REE)",
    }