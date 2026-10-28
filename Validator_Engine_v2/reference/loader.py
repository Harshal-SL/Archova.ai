"""Reference checklist loader.

Discovers markdown checklists in reference/checklists/, parses frontmatter tags,
and performs keyword/tag matching to select relevant excerpts (max ~1500 tokens).
No embeddings or external vector DB required.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set
import yaml

CHECKLISTS_DIR = Path(__file__).resolve().parent / "checklists"


class ReferenceChecklist:
    def __init__(self, filename: str, title: str, tags: List[str], content: str) -> None:
        self.filename = filename
        self.title = title
        self.tags = [t.lower().strip() for t in tags]
        self.content = content


class ReferenceLoader:
    def __init__(self, directory: Optional[Path] = None) -> None:
        self.dir = directory or CHECKLISTS_DIR
        self.checklists: List[ReferenceChecklist] = []
        self._load_all()

    def _load_all(self) -> None:
        if not self.dir.exists():
            return
        for p in self.dir.glob("*.md"):
            raw = p.read_text(encoding="utf-8")
            tags: List[str] = []
            title = p.stem.replace("_", " ").title()
            body = raw

            # Parse frontmatter if present
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1]
                    body = parts[2].strip()
                    try:
                        parsed_fm = yaml.safe_load(fm)
                        if isinstance(parsed_fm, dict):
                            tags = parsed_fm.get("tags", [])
                            title = parsed_fm.get("title", title)
                    except Exception:
                        pass

            self.checklists.append(ReferenceChecklist(p.name, title, tags, body))

    def select_excerpts(
        self,
        query_tags: List[str],
        context_text: str = "",
        max_tokens: int = 1500,
    ) -> str:
        """Score checklists by overlap with query_tags and context_text keywords, returning formatted excerpts."""
        normalized_query_tags: Set[str] = {t.lower().strip() for t in query_tags if t}
        context_words: Set[str] = set(re.findall(r"\b[a-zA-Z]{3,}\b", context_text.lower()))

        scored: List[Tuple[int, ReferenceChecklist]] = []
        for cl in self.checklists:
            score = 0
            # Tag match weight: 5 points
            for t in cl.tags:
                if t in normalized_query_tags:
                    score += 5
                elif any(qt in t or t in qt for qt in normalized_query_tags):
                    score += 3
                # Context match: 1 point per match
                if t in context_words:
                    score += 1

            if score > 0:
                scored.append((score, cl))

        # Sort highest score first
        scored.sort(key=lambda x: x[0], reverse=True)

        selected_sections: List[str] = []
        approx_tokens = 0

        for _, cl in scored:
            # Estimate tokens (~4 chars per token)
            tokens = len(cl.content) // 4
            if approx_tokens + tokens > max_tokens and selected_sections:
                break
            selected_sections.append(f"### Reference Standard: {cl.title}\n{cl.content}")
            approx_tokens += tokens

        return "\n\n".join(selected_sections)


# Global singleton
reference_loader = ReferenceLoader()
