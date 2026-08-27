"""FastAPI Main Application Entrypoint for AI Engine."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api_router

app = FastAPI(
    title="AI Architecture Engine — Unified REE & SAE",
    description=(
        "Unified Requirements Engineering Engine (REE) and "
        "Software Architecture Engine (SAE) — transforms stakeholder input "
        "into complete, enterprise-grade Software Architecture Packages."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

import os

from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Parse configurable CORS origins (comma-separated or wildcard '*')
_cors_origins_raw = os.getenv("CORS_ORIGINS", "*").strip()
if _cors_origins_raw == "*" or not _cors_origins_raw:
    _allow_origins = ["*"]
else:
    _allow_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount master aggregated router
app.include_router(api_router)

# Mount test-frontend directory at /ui
_frontend_dir = Path(__file__).resolve().parent.parent / "test-frontend"
if _frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dir), html=True), name="ui")


@app.get("/", tags=["System Health"])
def health():
    return {
        "status": "AI Engine Running",
        "version": "2.0.0",
        "ui_url": "http://localhost:8000/ui",
        "docs_url": "http://localhost:8000/docs",
        "engines": [
            "Requirements Engineering Engine (REE)",
            "Software Architecture Engine (SAE)",
        ],
    }