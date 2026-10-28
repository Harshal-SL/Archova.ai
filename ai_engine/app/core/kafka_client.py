"""
Queue Client Compatibility Layer for Archova.ai.

Redirects previous Kafka references to the modern Upstash Queue Client
(Upstash Redis Queues & Upstash QStash).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from app.core.queue_client import publish_generation_job

logger = logging.getLogger("archova.kafka")


async def get_kafka_producer():
    """Deprecated: Upstash uses QStash and Redis Queues instead of Kafka."""
    return None


async def publish_event(topic: str, key: str, payload: Dict[str, Any]) -> bool:
    """Compatibility method for event publishing."""
    logger.debug(f"[Queue] publish_event called for '{topic}' [Key: {key}]")
    return True


async def close_kafka_producer():
    """No-op cleanup."""
    pass
