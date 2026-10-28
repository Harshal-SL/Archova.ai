"""
Redis Client Manager for Archova.ai.

Provides high-performance distributed caching, LLM response caching,
real-time generation state tracking, and pub/sub streaming.
Compatible with Upstash Redis (Serverless TLS) and self-hosted Redis.
Supports both async and synchronous execution with in-memory fallbacks.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("archova.redis")

_async_redis_client = None
_sync_redis_client = None
_in_memory_cache: Dict[str, Any] = {}
_in_memory_state: Dict[str, Any] = {}


def _get_redis_url() -> Optional[str]:
    url = os.getenv("REDIS_URL") or os.getenv("UPSTASH_REDIS_URL")
    if not url:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            candidates = [
                Path(__file__).resolve().parent.parent.parent / ".env",
                Path(__file__).resolve().parent.parent / ".env",
                Path.cwd() / ".env",
                Path.cwd() / "ai_engine" / ".env",
            ]
            for p in candidates:
                if p.exists():
                    load_dotenv(p)
                    break
            url = os.getenv("REDIS_URL") or os.getenv("UPSTASH_REDIS_URL")
        except Exception:
            pass
    return url


def hash_key(prefix: str, content: str) -> str:
    """Creates a deterministic SHA-256 hash key for caching."""
    digest = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:32]
    return f"{prefix}:{digest}"


# ── Synchronous Client (For sync workers and REE agents) ───────────────────────

def get_sync_redis():
    """Returns the singleton synchronous Redis client, or None."""
    global _sync_redis_client
    if _sync_redis_client is not None:
        return _sync_redis_client

    redis_url = _get_redis_url()
    if not redis_url:
        return None

    try:
        import redis
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=3,
            socket_connect_timeout=3,
            retry_on_timeout=True,
        )
        client.ping()
        _sync_redis_client = client
        logger.info(f"[Redis:Sync] Connected to remote Redis: {redis_url.split('@')[-1]}")
        return _sync_redis_client
    except Exception as exc:
        logger.debug(f"[Redis:Sync] Remote connection failed ({exc}) — using in-memory.")
        return None


def get_cached_llm_sync(prompt: str, model: str) -> Optional[str]:
    """Synchronous LLM cache lookup."""
    key = hash_key(f"llm:{model}", prompt)
    client = get_sync_redis()
    if client:
        try:
            val = client.get(key)
            if val:
                logger.info(f"[Redis] LLM Cache HIT ({model})")
                return val
        except Exception:
            pass
    return _in_memory_cache.get(key)


def set_cached_llm_sync(prompt: str, model: str, completion: str, ttl_seconds: int = 86400) -> bool:
    """Synchronous LLM cache write."""
    if not completion or len(completion) < 10:
        return False
    key = hash_key(f"llm:{model}", prompt)
    client = get_sync_redis()
    if client:
        try:
            client.set(key, completion, ex=ttl_seconds)
            return True
        except Exception:
            pass

    _in_memory_cache[key] = completion
    return True


# ── Asynchronous Client (For FastAPI endpoints & async routers) ───────────────

async def get_redis_client():
    """Returns the singleton async Redis client, or None."""
    global _async_redis_client
    if _async_redis_client is not None:
        return _async_redis_client

    redis_url = _get_redis_url()
    if not redis_url:
        return None

    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        await client.ping()
        _async_redis_client = client
        logger.info(f"[Redis:Async] Connected to remote Redis cluster: {redis_url.split('@')[-1]}")
        return _async_redis_client
    except Exception as exc:
        logger.debug(f"[Redis:Async] Remote connection failed ({exc}) — using in-memory.")
        return None


async def get_cached_llm(prompt: str, model: str) -> Optional[str]:
    """Retrieve cached LLM response asynchronously."""
    key = hash_key(f"llm:{model}", prompt)
    client = await get_redis_client()
    if client:
        try:
            val = await client.get(key)
            if val:
                logger.info(f"[Redis] LLM Cache HIT ({model})")
                return val
        except Exception:
            pass
    return _in_memory_cache.get(key)


async def set_cached_llm(prompt: str, model: str, completion: str, ttl_seconds: int = 86400) -> bool:
    """Cache LLM response asynchronously."""
    if not completion or len(completion) < 10:
        return False
    key = hash_key(f"llm:{model}", prompt)
    client = await get_redis_client()
    if client:
        try:
            await client.set(key, completion, ex=ttl_seconds)
            return True
        except Exception:
            pass

    _in_memory_cache[key] = completion
    return True


# ── Generation State & Real-Time Progress ─────────────────────────────────────

async def set_generation_progress(
    generation_id: str,
    stage: str,
    status: str,
    message: str = "",
    extra: Optional[Dict[str, Any]] = None,
    ttl_seconds: int = 7200,
) -> None:
    """Record current pipeline stage and broadcast via Pub/Sub."""
    payload = {
        "generation_id": generation_id,
        "stage": stage,
        "status": status,
        "message": message,
        **(extra or {}),
    }
    payload_str = json.dumps(payload)
    key = f"gen:{generation_id}:status"

    client = await get_redis_client()
    if client:
        try:
            await client.set(key, payload_str, ex=ttl_seconds)
            await client.publish(f"channel:{generation_id}", payload_str)
            return
        except Exception:
            pass

    _in_memory_state[key] = payload


async def get_generation_progress(generation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve active status of a running generation pipeline."""
    key = f"gen:{generation_id}:status"
    client = await get_redis_client()
    if client:
        try:
            val = await client.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass

    return _in_memory_state.get(key)


async def close_redis():
    """Explicitly closes Redis connections to free sockets."""
    global _async_redis_client, _sync_redis_client
    if _async_redis_client is not None:
        try:
            await _async_redis_client.aclose()
        except Exception:
            pass
        _async_redis_client = None

    if _sync_redis_client is not None:
        try:
            _sync_redis_client.close()
        except Exception:
            pass
        _sync_redis_client = None
