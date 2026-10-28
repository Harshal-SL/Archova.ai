"""Centralized FastAPI Router Aggregator for AI Engine.

Aggregates input processing, Requirements Engineering Engine (REE), and Software Architecture Engine (SAE) routers.
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter

from app.routers.input_router import router as input_router
from app.routers.ree_router import router as ree_router
from app.routers.sae_router import router as sae_router
from app.api.routes.generations import router as generations_router
from app.routers.version_router import router as version_router
from app.routers.benchmark_router import router as benchmark_router
from app.routers.correction_router import router as correction_router

api_router = APIRouter()

# Register active domain routers
api_router.include_router(input_router)
api_router.include_router(ree_router)
api_router.include_router(sae_router)
api_router.include_router(generations_router)
api_router.include_router(version_router)
api_router.include_router(benchmark_router)
api_router.include_router(correction_router)


