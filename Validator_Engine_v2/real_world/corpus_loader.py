"""Corpus loader for Real-World Reference Systems and Failure Modes.

Reads markdown case studies from the configured RAG folders (read-only, no embeddings)
and extracts structured ReferenceDoc objects with section parsing and keyword tags.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from Validator_Engine_v2.config import config

DOMAIN_KEYWORDS: List[str] = [
    "parking",
    "ecommerce",
    "fintech",
    "healthcare",
    "iot",
    "streaming",
    "social",
    "logistics",
    "saas",
    "bookstore",
    "retail",
    "banking",
    "crm",
    "erp",
    "payments",
    "trading",
    "storage",
    "messaging",
    "search",
    "marketplace",
    "collaboration",
    "video",
]

PATTERN_KEYWORDS: List[str] = [
    "caching",
    "sharding",
    "idempotency",
    "queue",
    "saga",
    "circuit breaker",
    "multi-az",
    "cdn",
    "rate limit",
    "event sourcing",
    "cqrs",
    "distributed lock",
    "replication",
    "cdc",
    "edge",
    "waf",
    "ddos",
    "failover",
    "load balancer",
    "retry",
    "outbox",
    "partitioning",
]


class ReferenceDoc(BaseModel):
    """Normalized structured document from the real-world RAG corpus."""

    id: str
    system_name: str
    folder: str
    path: str
    sha256: str
    sections: List[Dict[str, str]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class CorpusLoader:
    """Loads and parses markdown reference documents from the corpus root."""

    def __init__(
        self,
        corpus_path: Optional[str] = None,
        folders: Optional[List[str]] = None,
    ) -> None:
        self.corpus_path = Path(corpus_path or config.REAL_WORLD_CORPUS_PATH)
        if folders:
            self.folders = folders
        else:
            raw = config.REAL_WORLD_FOLDERS
            self.folders = [f.strip() for f in raw.split(",") if f.strip()]

    def load_corpus(self) -> List[ReferenceDoc]:
        """Load and parse all markdown documents in configured folders."""
        if not self.corpus_path.exists():
            return []

        docs: List[ReferenceDoc] = []
        for folder_name in self.folders:
            folder_dir = self.corpus_path / folder_name
            if not folder_dir.exists() or not folder_dir.is_dir():
                continue

            for fname in sorted(os.listdir(folder_dir)):
                if not fname.endswith(".md"):
                    continue

                fpath = folder_dir / fname
                try:
                    doc = self._parse_file(fpath, folder_name)
                    if doc:
                        docs.append(doc)
                except Exception:
                    continue

        return docs

    def _parse_file(self, file_path: Path, folder_name: str) -> Optional[ReferenceDoc]:
        content = file_path.read_text(encoding="utf-8-sig")
        if not content.strip():
            return None

        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        doc_id = file_path.stem

        # Extract system name (from H1 or filename)
        system_name = doc_id.replace("_", " ").title()
        lines = content.splitlines()
        for line in lines:
            if line.startswith("# "):
                system_name = line.replace("# ", "").strip()
                break

        # Parse sections based on ## headings
        sections: List[Dict[str, str]] = []
        current_heading = "overview"
        current_lines: List[str] = []

        for line in lines:
            if line.startswith("## "):
                if current_lines:
                    sections.append({
                        "heading": current_heading,
                        "content": "\n".join(current_lines).strip(),
                    })
                    current_lines = []
                current_heading = line.replace("## ", "").strip().lower()
            elif not line.startswith("# "):
                current_lines.append(line)

        if current_lines:
            sections.append({
                "heading": current_heading,
                "content": "\n".join(current_lines).strip(),
            })

        # Extract sources / internal citations
        sources: List[str] = []
        # Find markdown links: [Title](link)
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        for title, link in md_links:
            sources.append(f"{title}: {link}")

        # Extract tags from folder, system name, headings, and keyword matching
        tags_set = {folder_name.lower()}
        lower_content = content.lower()
        lower_name = system_name.lower()

        for d in DOMAIN_KEYWORDS:
            if d in lower_content or d in lower_name:
                tags_set.add(d)

        for p in PATTERN_KEYWORDS:
            if p in lower_content:
                tags_set.add(p)

        for sec in sections:
            h = sec["heading"]
            if h not in ("chunk_id", "category", "type"):
                tags_set.add(h)

        return ReferenceDoc(
            id=doc_id,
            system_name=system_name,
            folder=folder_name,
            path=str(file_path),
            sha256=sha,
            sections=sections,
            sources=sources,
            tags=sorted(list(tags_set)),
        )
