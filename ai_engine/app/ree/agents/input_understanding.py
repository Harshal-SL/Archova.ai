"""
Input Understanding Agent

Responsibility:
  Transform raw stakeholder input into a Normalized Project Context (NPC)
  and write it into the Shared Requirement Context (SRC).

Pipeline (entirely deterministic — no AI calls):
  1. Receive raw_input and input_sources from SRC
  2. Split into per-source blocks
  3. Normalize each block (whitespace, encoding, structure)
  4. Detect and preserve document sections
  5. Deduplicate across sources
  6. Merge into a single normalized string
  7. Estimate tokens, flag if chunking is required
  8. Build NormalizedProjectContext
  9. Write NPC into SRC via apply_project_context()

Reuses unchanged:
  - file_parser.py (OCR, PDF, DOCX parsing) — called upstream by input_router
  - tokenizer.py   (estimate_tokens, is_within_limit)
  - chunker.py     (chunk_text) — used for the requires_chunking flag only;
                    actual chunking at LLM call time is still the extractor's job

Does NOT:
  - Call any LLM or AI service
  - Extract structured requirements (that is AI Engineering territory)
  - Modify downstream modules
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

from app.ree.models import (
    InputSourceRecord,
    NormalizedProjectContext,
    REEStatus,
    SharedRequirementContext,
)
from app.ree.agents.text_normalizer import TextNormalizer
from app.services.requirement_extractor.tokenizer import (
    estimate_tokens,
    is_within_limit,
    MAX_DIRECT_TOKENS,
)

logger = logging.getLogger(__name__)

_AGENT_NAME = "InputUnderstandingAgent"


class InputUnderstandingAgent:
    """
    Parses, normalizes, and merges all stakeholder inputs into a single
    Normalized Project Context, then writes it into the SRC.

    This agent is the only consumer of the text normalization layer.
    All other agents read from SRC.project_context, never from raw inputs.
    """

    def __init__(self) -> None:
        self._normalizer = TextNormalizer()

    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """
        Execute the input understanding stage.

        Args:
            src: Shared Requirement Context with raw_input populated.

        Returns:
            Updated SRC with project_context fully populated and
            raw_input set to the normalized merged text.
        """
        src.status = REEStatus.INPUT_UNDERSTANDING
        logger.info("%s: starting", _AGENT_NAME)

        # ── Guard: skip if already processed ─────────────────────────────────
        # On multi-turn resume flows the project_context is already populated.
        # We never re-process input that's already been normalized.
        if src.project_context.normalized_text.strip():
            logger.info("%s: project_context already populated — skipping", _AGENT_NAME)
            src.add_note(
                "input_understanding", _AGENT_NAME,
                "Skipped re-processing: project_context already populated."
            )
            return src

        # ── Guard: empty input ────────────────────────────────────────────────
        if not src.raw_input.strip():
            msg = "raw_input is empty — cannot build NormalizedProjectContext."
            logger.warning("%s: %s", _AGENT_NAME, msg)
            src.errors.append(msg)
            src.add_note("input_understanding", _AGENT_NAME, f"WARNING: {msg}")
            return src

        # ── Step 1: build (source_label, text) blocks ─────────────────────────
        blocks, source_records = self._build_blocks(src)

        # ── Step 2: normalize + section-detect + deduplicate ──────────────────
        sections, dedup_count = self._normalizer.process(blocks)

        # ── Step 3: merge sections into a single string ───────────────────────
        merged_text = self._normalizer.merge_sections(sections)

        # Fallback: if section merging produced nothing, use raw_input normalized
        if not merged_text.strip():
            logger.warning(
                "%s: section merging produced empty text — falling back to normalized raw_input",
                _AGENT_NAME,
            )
            merged_text = self._normalizer._normalize_text(src.raw_input)

        # ── Step 4: token estimation ──────────────────────────────────────────
        token_count = estimate_tokens(merged_text)
        needs_chunking = not is_within_limit(merged_text, MAX_DIRECT_TOKENS)

        # ── Step 5: collect warnings ──────────────────────────────────────────
        warnings: List[str] = []
        if dedup_count > 0:
            warnings.append(
                f"{dedup_count} duplicate text block(s) removed across sources."
            )
        if needs_chunking:
            warnings.append(
                f"Input is large (~{token_count} tokens). "
                "It will be chunked before LLM extraction."
            )
        for rec in source_records:
            if rec.parse_error:
                warnings.append(
                    f"Source '{rec.label}' had a parse warning: {rec.parse_error}"
                )

        # ── Step 6: build NormalizedProjectContext ────────────────────────────
        npc = NormalizedProjectContext(
            full_text=merged_text,
            sections=sections,
            estimated_tokens=token_count,
            requires_chunking=needs_chunking,
            sources=source_records,
            duplicate_blocks_removed=dedup_count,
            warnings=warnings,
        )

        # ── Step 7: write NPC into SRC ────────────────────────────────────────
        src.apply_project_context(npc)

        # ── Step 8: add discussion note ───────────────────────────────────────
        note = (
            f"Input processing complete. "
            f"Sources: {len(source_records)}. "
            f"Sections: {len(sections)}. "
            f"Tokens: ~{token_count}. "
            f"Duplicates removed: {dedup_count}. "
            f"Chunking required: {needs_chunking}."
        )
        src.add_note("input_understanding", _AGENT_NAME, note)

        logger.info(
            "%s: complete — sources=%d, sections=%d, tokens=%d, "
            "dedup=%d, chunking=%s",
            _AGENT_NAME,
            len(source_records),
            len(sections),
            token_count,
            dedup_count,
            needs_chunking,
        )

        return src

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_blocks(
        self,
        src: SharedRequirementContext,
    ) -> Tuple[List[Tuple[str, str]], List[InputSourceRecord]]:
        """
        Build (source_label, text) blocks and source records from the SRC.

        The raw_input in the SRC is always the combined merged string from
        /api/input (built by prompt_builder.build_prompt). We split it back
        into per-source blocks by looking at the input_sources list.

        If there is only one source (or if sources are unknown), the full
        raw_input is treated as one block.
        """
        records: List[InputSourceRecord] = []
        blocks: List[Tuple[str, str]] = []

        sources = src.input_sources if src.input_sources else ["text"]

        if len(sources) == 1:
            # Single source — entire raw_input belongs to this source
            label = sources[0]
            text = src.raw_input
            source_type = TextNormalizer.detect_source_type(label)
            records.append(InputSourceRecord(
                label=label,
                source_type=source_type,
                char_count=len(text),
            ))
            blocks.append((label, text))
        else:
            # Multiple sources.
            # The combined prompt from prompt_builder joins blocks with "\n\n".
            # We split it back heuristically: we know sources[0..n-1] correspond
            # to the blocks that were originally concatenated.
            # Since we cannot perfectly split without the original blocks, we try
            # to split by double-newlines into N parts.
            raw = src.raw_input
            split_blocks = self._split_combined_prompt(raw, len(sources))

            for i, label in enumerate(sources):
                text = split_blocks[i] if i < len(split_blocks) else ""
                source_type = TextNormalizer.detect_source_type(label)
                records.append(InputSourceRecord(
                    label=label,
                    source_type=source_type,
                    char_count=len(text),
                    parse_error=(
                        "Could not isolate this source's text from combined prompt"
                        if not text.strip() else None
                    ),
                ))
                if text.strip():
                    blocks.append((label, text))

        return blocks, records

    @staticmethod
    def _split_combined_prompt(combined: str, n_sources: int) -> List[str]:
        """
        Split a combined prompt back into roughly N per-source blocks.

        The combined prompt was built by joining blocks with "\n\n".
        We split on double newlines and group the resulting paragraphs
        evenly across the expected number of sources.

        This is a best-effort heuristic. Since we can't perfectly recover
        the original split, we prefer to keep all content rather than
        risk losing it. If splitting is ambiguous we return the whole
        text as one block (source 0) and empty strings for the rest.
        """
        if n_sources <= 1:
            return [combined]

        # Try splitting on the double-newline separator used by prompt_builder
        paragraphs = re.split(r"\n{2,}", combined.strip())

        if len(paragraphs) < n_sources:
            # Not enough paragraph breaks — can't split cleanly.
            # Return all text as first block.
            result = [combined] + [""] * (n_sources - 1)
            return result

        # Distribute paragraphs across sources as evenly as possible
        per_source = max(1, len(paragraphs) // n_sources)
        blocks: List[str] = []
        for i in range(n_sources):
            start = i * per_source
            end = start + per_source if i < n_sources - 1 else len(paragraphs)
            blocks.append("\n\n".join(paragraphs[start:end]))

        return blocks

    # ── Backward-compat helpers (used by Orchestrator skip-logic) ─────────────

    @staticmethod
    def _has_confirmed_values(parameters: dict) -> bool:
        """Return True if at least one parameter has a non-null confirmed value."""
        for val in parameters.values():
            if isinstance(val, dict) and val.get("value") is not None:
                return True
            if val is not None and not isinstance(val, dict):
                return True
        return False
