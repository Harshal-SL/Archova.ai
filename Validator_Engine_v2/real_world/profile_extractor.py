"""Profile Extractor for Real-World Reference Systems.

Extracts transferable architectural patterns from ReferenceDoc markdown documents
via ReviewerLLMClient with local file caching and deterministic offline mock mode.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from Validator_Engine_v2.config import config
from Validator_Engine_v2.real_world.corpus_loader import ReferenceDoc
from Validator_Engine_v2.review.llm_client import ReviewerLLMClient, _extract_first_json

CACHE_DIR = Path(__file__).parent / "cache"


class PatternApplicability(BaseModel):
    conditions: str = ""
    scale_hint: str = ""


class RealWorldPattern(BaseModel):
    """A transferable pattern extracted from a real-world case study."""

    id: str  # RW-<SYSTEM>-NN
    name: str
    description: str
    category: Literal[
        "concurrency",
        "caching",
        "data",
        "messaging",
        "resilience",
        "security",
        "scaling",
        "deployment",
        "observability",
        "api",
    ]
    applies_to_artifacts: List[Literal["hld", "backend", "database", "frontend", "security", "cloud"]] = Field(
        default_factory=list
    )
    applicability: PatternApplicability = Field(default_factory=PatternApplicability)
    source_section: str = ""
    priority: int = Field(..., ge=1, le=3)

    @field_validator("description", mode="before")
    @classmethod
    def enforce_word_limit(cls, v: Any) -> str:
        s = str(v or "").strip()
        words = s.split()
        if len(words) > 25:
            return " ".join(words[:25])
        return s


class ExtractedProfile(BaseModel):
    """Full pattern profile extracted from a reference doc."""

    system: str
    patterns: List[RealWorldPattern] = Field(default_factory=list)
    extraction_failed: bool = False
    error: Optional[str] = None


SYSTEM_PROMPT_PROFILE = """You are a senior enterprise architecture analyst.
Extract transferable architectural patterns from the provided real-world system case study.
Paraphrase all patterns into your own words.
Descriptions MUST NOT exceed 25 words. Do not copy text verbatim.

Required JSON format:
{
  "system": "<System Name>",
  "patterns": [
    {
      "id": "RW-<SYSTEM_CODE>-01",
      "name": "<Pattern Name>",
      "description": "<Concise description, max 25 words in your own words>",
      "category": "concurrency" | "caching" | "data" | "messaging" | "resilience" | "security" | "scaling" | "deployment" | "observability" | "api",
      "applies_to_artifacts": ["hld", "backend", "database", "frontend", "security", "cloud"],
      "applicability": {
        "conditions": "<When this pattern applies>",
        "scale_hint": "<Scale threshold or load signal>"
      },
      "source_section": "<Source section name>",
      "priority": 1 | 2 | 3
    }
  ]
}

Return ONLY valid JSON.
"""


class ProfileExtractor:
    """Extracts and caches architectural patterns from ReferenceDocs."""

    def __init__(self, llm_client: Optional[ReviewerLLMClient] = None, cache_dir: Optional[Path] = None) -> None:
        self.llm_client = llm_client or ReviewerLLMClient()
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, doc: ReferenceDoc) -> Path:
        model_safe = re.sub(r"[^\w\-_]", "_", self.llm_client.model)
        return self.cache_dir / f"{doc.sha256[:16]}_{model_safe}.json"

    async def extract_profile(self, doc: ReferenceDoc) -> ExtractedProfile:
        """Extract patterns with local disk cache and deterministic fallback."""
        cache_path = self._get_cache_path(doc)

        # 1. Check disk cache
        if cache_path.exists():
            try:
                cached_data = json.loads(cache_path.read_text(encoding="utf-8"))
                return ExtractedProfile(**cached_data)
            except Exception:
                pass

        # 2. Check Mock Mode
        if self.llm_client.mock_mode in ("1", "true", "mock"):
            profile = self._generate_mock_profile(doc)
            self._save_cache(cache_path, profile)
            return profile

        # 3. Call LLM with 1 retry
        sys_code = re.sub(r"[^\w]", "", doc.system_name.upper())[:6] or "SYS"
        user_prompt = (
            f"Extract transferable architectural patterns from this case study:\n"
            f"System: {doc.system_name}\n"
            f"Code Prefix: RW-{sys_code}\n\n"
            f"Document Sections:\n"
        )
        for sec in doc.sections:
            if sec["heading"] not in ("chunk_id", "category", "type"):
                user_prompt += f"\n## {sec['heading']}\n{sec['content'][:800]}\n"

        parsed_json, status = await self.llm_client.call_review(
            artifact_name=doc.id,
            artifact_data={"system": doc.system_name},
            rubric={"dimensions": []},
            user_prompt=user_prompt,
        )

        if not parsed_json or "patterns" not in parsed_json:
            # Fallback on extraction failure
            profile = ExtractedProfile(
                system=doc.system_name,
                patterns=[],
                extraction_failed=True,
                error=f"LLM extraction returned status: {status}",
            )
            return profile

        try:
            profile = ExtractedProfile(**parsed_json)
            self._save_cache(cache_path, profile)
            return profile
        except Exception as exc:
            return ExtractedProfile(
                system=doc.system_name,
                patterns=[],
                extraction_failed=True,
                error=f"Pydantic validation error: {exc}",
            )

    def _save_cache(self, path: Path, profile: ExtractedProfile) -> None:
        try:
            path.write_text(json.dumps(profile.model_dump(), indent=2), encoding="utf-8")
        except Exception:
            pass

    def _generate_mock_profile(self, doc: ReferenceDoc) -> ExtractedProfile:
        """Deterministic mock patterns based on system name."""
        sys_name = doc.system_name.lower()
        sys_code = re.sub(r"[^\w]", "", doc.system_name.upper())[:6] or "MOCK"

        patterns: List[RealWorldPattern] = []

        if "stripe" in sys_name or "paypal" in sys_name or "fintech" in sys_name:
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-01",
                    name="Idempotent Ingress Request Locking",
                    description="Guarantees once-only API transaction execution using distributed deduplication keys and reservation holds.",
                    category="concurrency",
                    applies_to_artifacts=["hld", "backend", "database"],
                    applicability=PatternApplicability(
                        conditions="Transaction processing or financial reservation",
                        scale_hint="Any concurrent booking or payment traffic",
                    ),
                    source_section="decision_signals",
                    priority=1,
                )
            )
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-02",
                    name="Double-Entry Audit Ledger Persistence",
                    description="Enforces immutable financial audit logging with append-only ledger and pessimistic row-level locking.",
                    category="data",
                    applies_to_artifacts=["database", "security"],
                    applicability=PatternApplicability(
                        conditions="Financial state mutability",
                        scale_hint="High-integrity transactions",
                    ),
                    source_section="advantages",
                    priority=1,
                )
            )
        elif "cloudflare" in sys_name or "edge" in sys_name:
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-01",
                    name="Edge Perimeter Rate Limiting and WAF",
                    description="Filters malicious traffic and enforces rate limits at ingress boundaries prior to hitting application core.",
                    category="security",
                    applies_to_artifacts=["hld", "security", "cloud"],
                    applicability=PatternApplicability(
                        conditions="Public-facing web or mobile endpoints",
                        scale_hint="Protects origin from request storms",
                    ),
                    source_section="advantages",
                    priority=1,
                )
            )
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-02",
                    name="Hierarchical Static and Response Caching",
                    description="Offloads origin servers via multi-tier caching with deterministic TTL and event-driven invalidation.",
                    category="caching",
                    applies_to_artifacts=["hld", "backend", "cloud"],
                    applicability=PatternApplicability(
                        conditions="High-read traffic ratio",
                        scale_hint=">70% read offload target",
                    ),
                    source_section="decision_signals",
                    priority=2,
                )
            )
        elif "netflix" in sys_name or "streaming" in sys_name or "failure" in sys_name:
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-01",
                    name="Circuit Breaker with Graceful Fallback",
                    description="Isolates downstream microservice dependencies with timeouts and fallback responses to prevent cascading outages.",
                    category="resilience",
                    applies_to_artifacts=["hld", "backend", "cloud"],
                    applicability=PatternApplicability(
                        conditions="Distributed multi-service architecture",
                        scale_hint="Critical service path availability",
                    ),
                    source_section="advantages",
                    priority=1,
                )
            )
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-02",
                    name="Multi-AZ Active-Active Redundancy",
                    description="Maintains redundant compute across availability zones with automatic health-checked traffic failover.",
                    category="scaling",
                    applies_to_artifacts=["hld", "cloud"],
                    applicability=PatternApplicability(
                        conditions="High-availability NFR targets",
                        scale_hint="99.99% uptime requirements",
                    ),
                    source_section="decision_signals",
                    priority=2,
                )
            )
        else:
            # Generic high-assurance production patterns
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-01",
                    name="Distributed Concurrency Lock",
                    description="Prevents race conditions and double-allocation on shared resources using atomic locks.",
                    category="concurrency",
                    applies_to_artifacts=["backend", "database"],
                    applicability=PatternApplicability(
                        conditions="Shared mutable state",
                        scale_hint="Concurrent read/write access",
                    ),
                    source_section="decision_signals",
                    priority=1,
                )
            )
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-02",
                    name="Zero-Trust Boundary RBAC Enforcement",
                    description="Validates cryptographic tokens and least-privilege permissions on all resource endpoints.",
                    category="security",
                    applies_to_artifacts=["backend", "security"],
                    applicability=PatternApplicability(
                        conditions="Multi-tenant or authenticated APIs",
                        scale_hint="All public or internal RPCs",
                    ),
                    source_section="advantages",
                    priority=2,
                )
            )
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-03",
                    name="Structured Observability & Telemetry",
                    description="Correlates distributed traces, metrics, and structured logs across service boundaries.",
                    category="observability",
                    applies_to_artifacts=["hld", "cloud"],
                    applicability=PatternApplicability(
                        conditions="Production monitoring",
                        scale_hint="SLO/SLI verification",
                    ),
                    source_section="decision_signals",
                    priority=3,
                )
            )
            patterns.append(
                RealWorldPattern(
                    id=f"RW-{sys_code}-04",
                    name="Client-Side State Management & Query Caching",
                    description="Caches API queries client-side with optimistic updates and automatic cache invalidation.",
                    category="caching",
                    applies_to_artifacts=["frontend"],
                    applicability=PatternApplicability(
                        conditions="Interactive web or mobile client interfaces",
                        scale_hint="Eliminates redundant network round-trips",
                    ),
                    source_section="advantages",
                    priority=2,
                )
            )

        return ExtractedProfile(
            system=doc.system_name,
            patterns=patterns,
            extraction_failed=False,
        )
