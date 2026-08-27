"""SAECacheManager module for SHA-256 fingerprint result caching and incremental generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


class SAECacheManager:
    """Manages SHA-256 fingerprint result caching to re-use intact section outputs."""

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or Path(".cache") / "sae_artifact_cache.json"
        self._cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk if available."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        """Persist cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
        except Exception:
            pass

    @classmethod
    def compute_fingerprint(cls, agent_role: str, inputs: Dict[str, Any], prompt_version: str = "1.0.0") -> str:
        """Compute deterministic SHA-256 fingerprint for an agent's execution context."""
        input_str = json.dumps(inputs, sort_keys=True, default=str)
        raw_key = f"{agent_role}:{prompt_version}:{input_str}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, agent_role: str, inputs: Dict[str, Any], prompt_version: str = "1.0.0") -> Optional[Dict[str, Any]]:
        """Retrieve cached output payload if fingerprint matches."""
        fp = self.compute_fingerprint(agent_role, inputs, prompt_version)
        entry = self._cache.get(fp)
        if entry:
            return entry.get("payload")
        return None

    def put(self, agent_role: str, inputs: Dict[str, Any], payload: Dict[str, Any], prompt_version: str = "1.0.0") -> str:
        """Store output payload under SHA-256 fingerprint."""
        fp = self.compute_fingerprint(agent_role, inputs, prompt_version)
        self._cache[fp] = {
            "agent_role": agent_role,
            "fingerprint": fp,
            "payload": payload,
        }
        self._save_cache()
        return fp

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass
