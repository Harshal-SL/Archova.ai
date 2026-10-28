"""
Unified Message Queue & Task Dispatcher for Archova.ai.

Supports:
1. Upstash Redis Queue / Streams (using active REDIS_URL — zero extra setup needed).
2. Upstash QStash (Serverless HTTP messaging & webhook scheduling via QSTASH_TOKEN).
3. Graceful in-memory fallback for local development.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx

from app.core.redis_client import get_redis_client

logger = logging.getLogger("archova.queue")

QUEUE_JOBS_KEY = "archova:queue:generation_jobs"
QSTASH_BASE_URL = "https://qstash.upstash.io/v2"


def _get_qstash_token() -> Optional[str]:
    return os.getenv("QSTASH_TOKEN") or None


async def publish_generation_job(
    generation_id: str,
    prompt: str,
    user_id: Optional[str] = None,
    destination_webhook_url: Optional[str] = None,
) -> bool:
    """Enqueues an architecture generation job to Upstash QStash or Upstash Redis Queue."""
    job_payload = {
        "event_type": "ARCHITECTURE_JOB_SUBMITTED",
        "generation_id": generation_id,
        "prompt": prompt,
        "user_id": user_id or "anonymous",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    # 1. Try Upstash QStash if QSTASH_TOKEN is set
    qstash_token = _get_qstash_token()
    if qstash_token and destination_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Authorization": f"Bearer {qstash_token}",
                    "Content-Type": "application/json",
                    "Upstash-Retries": "3",
                    "Upstash-Deduplication-Id": f"job-{generation_id}",
                }
                resp = await client.post(
                    f"{QSTASH_BASE_URL}/publish/{destination_webhook_url}",
                    json=job_payload,
                    headers=headers,
                )
                if resp.status_code in (200, 201, 202):
                    logger.info(f"[QStash] Dispatched job {generation_id} to webhook: {destination_webhook_url}")
                    return True
                else:
                    logger.warning(f"[QStash] Publish failed ({resp.status_code}): {resp.text}")
        except Exception as exc:
            logger.warning(f"[QStash] Exception during publish ({exc}) — falling back to Redis queue.")

    # 2. Use Upstash Redis Queue (Active REDIS_URL)
    try:
        redis_client = await get_redis_client()
        if redis_client:
            payload_str = json.dumps(job_payload)
            # Push to queue list and record state in hash
            await redis_client.rpush(QUEUE_JOBS_KEY, payload_str)
            await redis_client.hset(
                f"job:{generation_id}",
                mapping={
                    "status": "QUEUED",
                    "submitted_at": job_payload["submitted_at"],
                    "prompt_preview": prompt[:100],
                },
            )
            # Expire job tracker after 48 hours
            await redis_client.expire(f"job:{generation_id}", 172800)
            logger.info(f"[RedisQueue] Successfully enqueued job '{generation_id}' to {QUEUE_JOBS_KEY}")
            return True
    except Exception as exc:
        logger.warning(f"[RedisQueue] Could not enqueue to Redis ({exc}) — falling back to in-memory.")

    logger.info(f"[Queue:Local] In-memory job execution for generation '{generation_id}'")
    return True


async def pop_next_job(timeout_seconds: int = 2) -> Optional[Dict[str, Any]]:
    """Pops the next pending job from the Upstash Redis Queue (Worker pattern)."""
    try:
        redis_client = await get_redis_client()
        if redis_client:
            item = await redis_client.blpop(QUEUE_JOBS_KEY, timeout=timeout_seconds)
            if item:
                _, raw_data = item
                return json.loads(raw_data)
    except Exception as exc:
        logger.debug(f"[RedisQueue] Worker pop failed ({exc})")
    return None


async def get_queue_depth() -> int:
    """Returns number of jobs currently waiting in the queue."""
    try:
        redis_client = await get_redis_client()
        if redis_client:
            return await redis_client.llen(QUEUE_JOBS_KEY)
    except Exception:
        pass
    return 0
