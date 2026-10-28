"""AI Engine HTTP Client and Regeneration Adapter.

Communicates with AI Engine strictly through its discovered HTTP endpoints:
- GET /api/v1/generations/{generation_id}/package
- GET /api/v1/generations/{generation_id}/status
- POST /api/v1/generations/{generation_id}/generate
- GET /api/v1/generations/{generation_id}/lld/{type}

STOP CONDITION 1 COMPLIANCE:
Because the AI Engine does not expose an HTTP endpoint to accept feedback for individual artifact regeneration,
the feedback loop is abstracted behind `RegenerationAdapter`:
- HttpRegenerationAdapter: calls AI Engine endpoints with fallback, marking `regenerated_with_feedback: false`.
- SimulationRegenerationAdapter: applies targeted corrections in-memory for testing and offline scenarios.
"""

from __future__ import annotations

import abc
import asyncio
import copy
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx

from Validator_Engine_v2.config import config

logger = logging.getLogger(__name__)


class RegenerationAdapter(abc.ABC):
    """Abstract interface for artifact regeneration."""

    @abc.abstractmethod
    async def regenerate(
        self,
        generation_id: str,
        rejected_artifacts: List[str],
        feedback: Dict[str, Any],
        current_package: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], bool]:
        """Regenerate affected artifacts.

        Returns:
            updated_package: The new or modified architecture package
            regenerated_with_feedback: True if feedback was consumed by generator, False otherwise
        """
        pass


class HttpRegenerationAdapter(RegenerationAdapter):
    """Production adapter calling existing AI Engine HTTP endpoints without modifying ai_engine.

    Since existing endpoints do not accept feedback, it re-requests generation and
    marks the iteration regenerated_with_feedback: false.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or config.AI_ENGINE_URL).rstrip("/")

    async def regenerate(
        self,
        generation_id: str,
        rejected_artifacts: List[str],
        feedback: Dict[str, Any],
        current_package: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], bool]:
        logger.info(
            "[%s] Triggering HTTP re-generation for artifacts: %s (no feedback endpoint available)",
            generation_id,
            rejected_artifacts,
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Re-trigger generation if HLD was rejected
                if "hld" in rejected_artifacts:
                    await client.post(f"{self.base_url}/api/v1/generations/{generation_id}/generate")

                # Fetch updated package
                res = await client.get(f"{self.base_url}/api/v1/generations/{generation_id}/package")
                if res.status_code == 200:
                    return res.json(), False
            except Exception as exc:
                logger.warning("[%s] HTTP regeneration call failed: %s", generation_id, exc)

        return current_package, False


class SimulationRegenerationAdapter(RegenerationAdapter):
    """Simulation adapter applying targeted fixes to package in-memory for testing."""

    async def regenerate(
        self,
        generation_id: str,
        rejected_artifacts: List[str],
        feedback: Dict[str, Any],
        current_package: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], bool]:
        pkg = copy.deepcopy(current_package)
        llds = pkg.get("llds", {})
        if not isinstance(llds, dict):
            llds = {}
            pkg["llds"] = llds

        for art in rejected_artifacts:
            art_clean = art.lower().replace("_lld", "")
            if art_clean in ("backend", "database"):
                # Apply concurrency fixes if concurrency was flagged
                raw_be = llds.get("backend", {})
                be_data = raw_be.get("data", raw_be) if isinstance(raw_be, dict) else {}
                if isinstance(be_data, dict):
                    be_data["reservation_concurrency_policy"] = {
                        "lock_type": "Redis Redlock Distributed Locking with 10-minute hold TTL",
                        "database_fallback": "SELECT id, status FROM resources WHERE id = :id FOR UPDATE NOWAIT",
                        "hold_duration_seconds": 600,
                        "concurrency_guarantee": "Strict mutual exclusion preventing double-booking.",
                    }
                    endpoints = be_data.get("api_endpoints", [])
                    if isinstance(endpoints, list):
                        for ep in endpoints:
                            if isinstance(ep, dict):
                                ep["concurrency_lock"] = "Redis Redlock with SELECT FOR UPDATE"
                    if "data" in raw_be and isinstance(raw_be, dict):
                        raw_be["data"] = be_data
                    else:
                        llds["backend"] = be_data

                raw_db = llds.get("database", {})
                db_data = raw_db.get("data", raw_db) if isinstance(raw_db, dict) else {}
                if isinstance(db_data, dict):
                    db_data["locking_and_concurrency"] = {
                        "row_level_locking": "SELECT FOR UPDATE row-level lock during transactions",
                        "isolation_level": "READ COMMITTED with pessimistic row locks",
                    }
                    if "data" in raw_db and isinstance(raw_db, dict):
                        raw_db["data"] = db_data
                    else:
                        llds["database"] = db_data

            if art_clean == "cloud":
                raw_cl = llds.get("cloud", {})
                cl_data = raw_cl.get("data", raw_cl) if isinstance(raw_cl, dict) else {}
                if isinstance(cl_data, dict):
                    cl_data["networking"] = {"vpc": "10.0.0.0/16", "multi_az": True}
                    if "data" in raw_cl and isinstance(raw_cl, dict):
                        raw_cl["data"] = cl_data
                    else:
                        llds["cloud"] = cl_data

        return pkg, True


class AIEngineClient:
    """Client for fetching packages and status from AI Engine."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        regeneration_adapter: Optional[RegenerationAdapter] = None,
    ) -> None:
        self.base_url = (base_url or config.AI_ENGINE_URL).rstrip("/")
        self.regeneration_adapter = regeneration_adapter or HttpRegenerationAdapter(self.base_url)

    async def fetch_package(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full architecture package from AI Engine."""
        url = f"{self.base_url}/api/v1/generations/{generation_id}/package"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(url)
                if res.status_code == 200:
                    return res.json()
            except Exception as exc:
                logger.warning("[%s] Failed to fetch package from AI Engine: %s", generation_id, exc)
        return None

    async def check_health(self) -> bool:
        """Check if AI Engine is responding."""
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                res = await client.get(f"{self.base_url}/")
                return res.status_code == 200
            except Exception:
                return False
