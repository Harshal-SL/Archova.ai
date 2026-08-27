"""
Text Normalizer

Deterministic text processing used by the Input Understanding Agent.

Responsibilities:
  1. Section detection      — identify headings and split text into sections
  2. Text normalization     — normalize whitespace, line endings, encoding
  3. Duplicate removal      — detect and remove repeated text blocks
  4. Multi-source merging   — merge text from multiple input sources
     with source attribution preserved

No AI reasoning. No external calls. Pure string operations.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

from app.ree.models import DocumentSection, InputSourceRecord, InputSourceType


# ── Constants ──────────────────────────────────────────────────────────────────

# Minimum characters for a block to be considered non-trivial
_MIN_BLOCK_CHARS = 30

# Heading patterns: markdown headers, ALL CAPS lines, numbered sections
_HEADING_PATTERNS = [
    # Markdown headers: ## Heading, ### Sub-heading
    re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE),
    # Numbered section headers: 1. Title, 1.2 Title, 2.1.3 Section
    re.compile(r"^(\d+(?:\.\d+)*)[.\)]\s+([A-Z][^\n]{3,60})$", re.MULTILINE),
    # ALL CAPS headings (3+ words or 10+ chars, standalone line)
    re.compile(r"^([A-Z][A-Z\s\-/&]{9,60})$", re.MULTILINE),
    # Title Case standalone lines (likely section headers in plain docs)
    re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,6}):?\s*$", re.MULTILINE),
]

# Section titles that signal specific content types (used for ordering hints)
_REQUIREMENTS_SIGNALS = {
    "requirement", "functional", "feature", "user story", "use case",
    "acceptance criteria", "specification", "spec",
}
_BACKGROUND_SIGNALS = {
    "background", "overview", "introduction", "context", "summary", "about",
    "description", "purpose",
}
_NFR_SIGNALS = {
    "non-functional", "nonfunctional", "performance", "scalability",
    "availability", "security", "reliability", "quality",
}


class TextNormalizer:
    """
    Deterministic text normalizer for multi-source stakeholder inputs.

    Usage::

        normalizer = TextNormalizer()
        sections, dedup_count = normalizer.process(
            blocks=[("text", "Some requirements text..."),
                    ("design.pdf", "PDF content here...")],
        )
        merged = normalizer.merge_sections(sections)
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def process(
        self,
        blocks: List[Tuple[str, str]],
    ) -> Tuple[List[DocumentSection], int]:
        """
        Process multiple (source_label, text) pairs into DocumentSections.

        Pipeline per block:
          1. Normalize whitespace and encoding
          2. Detect and split into sections
          3. Remove duplicate sections across all sources

        Args:
            blocks: List of (source_label, raw_text) pairs.

        Returns:
            (sections, duplicate_blocks_removed) tuple.
        """
        all_sections: List[DocumentSection] = []
        seen_fingerprints: Dict[str, str] = {}  # fingerprint → first source
        dedup_count = 0

        for source_label, raw_text in blocks:
            if not raw_text or not raw_text.strip():
                continue

            # Step 1: normalize the text
            normalized = self._normalize_text(raw_text)

            # Step 2: split into sections
            sections = self._split_into_sections(normalized, source_label)

            # Step 3: deduplicate against already-seen sections
            for section in sections:
                fp = self._fingerprint(section.content)
                if fp in seen_fingerprints:
                    dedup_count += 1
                else:
                    seen_fingerprints[fp] = source_label
                    all_sections.append(section)

        # Re-index section positions after dedup
        for i, section in enumerate(all_sections):
            section.section_index = i

        return all_sections, dedup_count

    def merge_sections(self, sections: List[DocumentSection]) -> str:
        """
        Merge a list of DocumentSections into a single normalized string.

        Sections from different sources are separated clearly.
        Section titles are preserved as lightweight headers.

        Args:
            sections: Ordered list of DocumentSections.

        Returns:
            Single merged string suitable for LLM consumption.
        """
        parts: List[str] = []
        current_source: Optional[str] = None

        for section in sections:
            # Add a source separator when the source changes
            if section.source != current_source:
                if current_source is not None:
                    parts.append("")  # blank line between sources
                current_source = section.source

            # Add section heading if it's not a 'main' catchall
            if section.title and section.title.lower() != "main":
                parts.append(f"# {section.title}")

            parts.append(section.content.strip())

        return "\n\n".join(p for p in parts if p.strip())

    # ── Source type detection ─────────────────────────────────────────────────

    @staticmethod
    def detect_source_type(filename: str) -> InputSourceType:
        """Infer the InputSourceType from a filename or source label."""
        lower = filename.lower()
        if lower == "text" or lower.endswith(".txt"):
            return InputSourceType.TEXT
        if lower.endswith(".pdf"):
            return InputSourceType.PDF
        if lower.endswith(".docx"):
            return InputSourceType.DOCX
        if lower.endswith((".png", ".jpg", ".jpeg")):
            return InputSourceType.IMAGE
        if lower.endswith(".md"):
            return InputSourceType.MARKDOWN
        return InputSourceType.UNKNOWN

    # ── Internal: text normalization ──────────────────────────────────────────

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Apply deterministic text normalization.

        Steps:
          1. Unicode NFC normalization (handles composed/decomposed forms)
          2. Normalize line endings to LF
          3. Strip null bytes and other control chars (keep tab/newline)
          4. Normalize excessive whitespace within lines
          5. Collapse 3+ consecutive blank lines to 2
          6. Strip leading/trailing whitespace
        """
        # 1. Unicode normalization
        text = unicodedata.normalize("NFC", text)

        # 2. Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Remove control characters except tab and newline
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # 4. Normalize whitespace within lines (collapse multiple spaces/tabs)
        lines = []
        for line in text.split("\n"):
            # Preserve leading indentation depth (collapse each indent unit)
            stripped = line.lstrip()
            indent = line[: len(line) - len(stripped)]
            # Normalize indent to at most 2 spaces per level
            indent = re.sub(r"\t", "  ", indent)
            # Collapse internal whitespace
            normalized_line = re.sub(r"[ \t]{2,}", " ", stripped)
            lines.append(indent + normalized_line)

        text = "\n".join(lines)

        # 5. Collapse 3+ consecutive blank lines → 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 6. Strip
        return text.strip()

    # ── Internal: section detection ───────────────────────────────────────────

    def _split_into_sections(
        self, text: str, source: str
    ) -> List[DocumentSection]:
        """
        Split normalized text into DocumentSections.

        Uses heading pattern matching. Falls back to a single 'main'
        section if no headings are detected.
        """
        # Find all heading matches with their positions
        heading_spans: List[Tuple[int, int, str]] = []  # (start, end, title)

        for pattern in _HEADING_PATTERNS:
            for match in pattern.finditer(text):
                title = (match.group(1) if match.lastindex and match.lastindex >= 1
                         else match.group(0)).strip()
                # Clean up title
                title = re.sub(r"^#+\s*", "", title).strip(": ")
                if title and len(title) >= 3:
                    heading_spans.append((match.start(), match.end(), title))

        if not heading_spans:
            # No headings detected — treat entire text as a single section
            cleaned = self._clean_section_body(text)
            if cleaned:
                return [DocumentSection(
                    title="main",
                    content=cleaned,
                    source=source,
                    section_index=0,
                )]
            return []

        # Sort by position, remove overlapping spans
        heading_spans.sort(key=lambda x: x[0])
        heading_spans = self._remove_overlapping(heading_spans)

        sections: List[DocumentSection] = []

        # Text before the first heading → 'preamble' section
        first_start = heading_spans[0][0]
        preamble = text[:first_start].strip()
        if len(preamble) >= _MIN_BLOCK_CHARS:
            sections.append(DocumentSection(
                title="preamble",
                content=self._clean_section_body(preamble),
                source=source,
                section_index=0,
            ))

        # Each heading → next heading (or end of text)
        for idx, (hstart, hend, title) in enumerate(heading_spans):
            next_start = heading_spans[idx + 1][0] if idx + 1 < len(heading_spans) else len(text)
            body = text[hend:next_start]
            cleaned = self._clean_section_body(body)
            if cleaned:
                sections.append(DocumentSection(
                    title=title,
                    content=cleaned,
                    source=source,
                    section_index=len(sections),
                ))

        # If no sections were produced (all bodies were empty), return single section
        if not sections:
            cleaned = self._clean_section_body(text)
            if cleaned:
                return [DocumentSection(
                    title="main",
                    content=cleaned,
                    source=source,
                    section_index=0,
                )]

        return sections

    @staticmethod
    def _clean_section_body(text: str) -> str:
        """
        Strip the heading line and normalize a section body.
        Removes blank lines at start/end, collapses internal runs.
        """
        # Remove leading/trailing blank lines
        text = text.strip()
        if not text:
            return ""
        # Collapse excessive internal blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    @staticmethod
    def _remove_overlapping(
        spans: List[Tuple[int, int, str]],
    ) -> List[Tuple[int, int, str]]:
        """
        Remove overlapping heading spans, keeping the first one at each position.
        """
        result: List[Tuple[int, int, str]] = []
        last_end = -1
        for span in spans:
            if span[0] >= last_end:
                result.append(span)
                last_end = span[1]
        return result

    # ── Deduplication ─────────────────────────────────────────────────────────

    @staticmethod
    def _fingerprint(text: str) -> str:
        """
        Compute a content fingerprint for deduplication.

        Strips whitespace and lowercases before hashing so minor
        formatting differences don't create false negatives.
        """
        canonical = re.sub(r"\s+", " ", text.strip().lower())
        return hashlib.sha1(canonical.encode("utf-8", errors="replace")).hexdigest()


# ── Standalone Semantic Normalization & Classification Helpers ────────────────


def clean_conversational_prefix(text: str) -> str:
    """
    Strip conversational/role prefixes (e.g. Answer:, Response:, User:, AI:, Clarification:, Note:)
    while preserving text content and numbers (e.g., 1,000, 99.9%, 95%, 2 seconds).
    """
    if not text or not isinstance(text, str):
        return ""
    s = text.strip()
    s = re.sub(r"^(?:Answer|Response|User|AI|Clarification|Note):\s*", "", s, flags=re.IGNORECASE)
    return s.strip()


def split_semantic_boundaries(text: str) -> List[str]:
    """
    Split text into list items on semantic boundaries only:
    - Newlines, bullet points (- , * , • , 1. , etc.), semicolons (;)
    - NEVER split on commas alone.
    """
    if not text or not isinstance(text, str):
        return []

    cleaned = clean_conversational_prefix(text)
    if not cleaned:
        return []

    lines = cleaned.splitlines()
    items: List[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Strip bullet/numbering prefix (require space after number prefix so 99.9% isn't stripped)
        line = re.sub(r"^(?:[\-\*\•\>]\s*|\d+[\.\)]\s+)", "", line).strip()
        if not line:
            continue

        # Split on semicolons if present
        if ";" in line:
            sub_parts = [p.strip() for p in line.split(";") if p.strip()]
            for p in sub_parts:
                p = re.sub(r"^(?:[\-\*\•\>]\s*|\d+[\.\)]\s+)", "", p).strip()
                if p:
                    items.append(p)
        else:
            items.append(line)

    return items


def normalize_actor_name(actor: str) -> str:
    """
    Normalize actor/role titles cleanly (e.g. Students -> Student, Librarians -> Librarian).
    """
    if not actor or not isinstance(actor, str):
        return ""

    cleaned = clean_conversational_prefix(actor)
    cleaned = re.sub(r"^(?:The\s+primary\s+actors\s+are|Primary\s+actors|System\s+actor|Actor|Role|User\s+role|The\s+actors\s+are):\s*", "", cleaned, flags=re.IGNORECASE).strip()
    if not cleaned:
        return ""

    mapping = {
        "students": "Student",
        "student": "Student",
        "librarians": "Librarian",
        "librarian": "Librarian",
        "users": "User",
        "user": "User",
        "admins": "System Administrator",
        "administrator": "System Administrator",
        "administrators": "System Administrator",
        "admin": "System Administrator",
        "hospital administrator": "Hospital Administrator",
        "hospital administrators": "Hospital Administrator",
        "doctors": "Doctor",
        "doctor": "Doctor",
        "patients": "Patient",
        "patient": "Patient",
        "receptionists": "Receptionist",
        "receptionist": "Receptionist",
        "nurses": "Nurse",
        "nurse": "Nurse",
        "pharmacists": "Pharmacist",
        "pharmacist": "Pharmacist",
        "lab technician": "Laboratory Technician",
        "lab technicians": "Laboratory Technician",
        "laboratory technician": "Laboratory Technician",
        "laboratory technicians": "Laboratory Technician",
        "end user": "User",
        "end users": "User",
    }

    lower = cleaned.lower().strip()
    if lower in mapping:
        return mapping[lower]

    return cleaned.title()


def extract_discrete_actors(raw_actors: Any) -> List[str]:
    """
    Parse sentence-style actor strings ("The primary actors are Doctor, Patient, Nurse...")
    or raw lists into clean discrete actor titles.
    """
    if not raw_actors:
        return []

    raw_items: List[str] = []
    prefix_pattern = r"^(?:The\s+primary\s+actors\s+(?:are|include)|Primary\s+actors(?:\s+are|\s+include)?|System\s+actors\s+include|The\s+actors\s+are|Actors\s+include):?\s*"

    if isinstance(raw_actors, str):
        cleaned = re.sub(prefix_pattern, "", raw_actors.strip(), flags=re.IGNORECASE)
        # Split on commas, 'and', or semicolons
        parts = re.split(r",|\band\b|;", cleaned, flags=re.IGNORECASE)
        raw_items = [p.strip() for p in parts if p.strip()]
    elif isinstance(raw_actors, list):
        for item in raw_actors:
            if isinstance(item, str):
                cleaned = re.sub(prefix_pattern, "", item.strip(), flags=re.IGNORECASE)
                parts = re.split(r",|\band\b|;", cleaned, flags=re.IGNORECASE)
                raw_items.extend([p.strip() for p in parts if p.strip()])

    norm_actors: List[str] = []
    for item in raw_items:
        norm = normalize_actor_name(item)
        if norm and norm not in norm_actors and len(norm) > 1:
            norm_actors.append(norm)

    return norm_actors


def split_coarse_requirements(items: List[str]) -> List[str]:
    """
    Split coarse requirements (e.g. 'The system should include Patient Management, Appointment Booking, and Billing')
    into atomic, single-capability requirement statements.
    """
    atomic_items: List[str] = []

    for item in items:
        if not item or not isinstance(item, str):
            continue
        cleaned = clean_conversational_prefix(item)
        if not cleaned:
            continue

        # If item contains bullet points or newlines or semicolons, split using semantic boundaries first
        sub_boundaries = split_semantic_boundaries(cleaned)
        for part in sub_boundaries:
            # Check if part contains multiple comma-separated capabilities after verbs like "include", "support", "provides"
            match = re.search(r"(?:should|must|will|to)\s+(?:include|support|provide|manage|allow)\s+(.+)", part, re.IGNORECASE)
            if match and ("," in match.group(1) or " and " in match.group(1)):
                phrase = match.group(1)
                sub_features = re.split(r",|\band\b", phrase, flags=re.IGNORECASE)
                for sf in sub_features:
                    sf_clean = sf.strip().strip(".")
                    if sf_clean:
                        feat_title = sf_clean.title()
                        atomic_items.append(f"System shall support {feat_title}")
            else:
                atomic_items.append(part.strip())

    result: List[str] = []
    for a in atomic_items:
        if a and a not in result:
            result.append(a)

    return result


def merge_fragmented_requirements(fr_list: List[str]) -> List[str]:
    """
    Merge related requirement fragments and remove broken sentences.
    Example:
      ❌ Book Management (Adding
      ❌ Removing Books)
      ✅ Librarian shall manage books (Add, Update, Remove).
    """
    if not fr_list:
        return []

    cleaned_items: List[str] = []
    buffer_fragment: str = ""

    for item in fr_list:
        if not item or not isinstance(item, str):
            continue
        text = clean_conversational_prefix(item).strip()
        if not text:
            continue

        # If previous line was incomplete (open paren or dangling verb/preposition)
        if buffer_fragment:
            text = f"{buffer_fragment} {text}"
            buffer_fragment = ""

        # Check if text ends abruptly with open paren or comma or dangling conjunction
        if re.search(r"\([^)]*$", text) or text.endswith((",", " (", " and", " or", " with")):
            buffer_fragment = text
            continue

        # Ensure paren count is balanced
        if text.count("(") > text.count(")"):
            text += ")"

        # Transform raw feature fragments into clean requirement statements
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 4:
            continue

        cleaned_items.append(text)

    if buffer_fragment:
        text = buffer_fragment.strip()
        if text.count("(") > text.count(")"):
            text += ")"
        cleaned_items.append(text)

    # Merge related requirements sharing similar resources
    merged_map: Dict[str, List[str]] = {}
    standalone: List[str] = []

    for item in cleaned_items:
        lower = item.lower()
        # Detect resource patterns
        res_match = re.search(r"\b(event|registration|attendance|notification|ticket|schedule|participant|item|resource|profile|account|record|book|patient|appointment|order|catalog|file|document)s?\b", lower)
        if res_match:
            res_key = res_match.group(1).title()
            merged_map.setdefault(res_key, []).append(item)
        else:
            standalone.append(item)

    final_reqs: List[str] = []
    for res_key, reqs in merged_map.items():
        if len(reqs) >= 2:
            # Consolidate actions for this resource
            actions = []
            for r in reqs:
                r_clean = re.sub(rf"(?i)\b{res_key}s?\b", "", r).strip("- *•: ")
                if r_clean:
                    actions.append(r_clean)
            merged_statement = f"System shall manage {res_key} operations ({', '.join(dict.fromkeys(actions))})"
            final_reqs.append(merged_statement)
        else:
            final_reqs.extend(reqs)

    final_reqs.extend(standalone)

    # Final deduplication maintaining order
    out: List[str] = []
    for r in final_reqs:
        if r and r not in out:
            out.append(r)
    return out


def clean_actor_role(raw: str) -> Optional[str]:
    """Clean a raw actor string into a concise persona title (1-4 words)."""
    if not raw or not isinstance(raw, str):
        return None
    cleaned = clean_conversational_prefix(raw).strip("- *•: ")
    if not cleaned or len(cleaned) < 2:
        return None

    # Discard pure action verb phrases (e.g. "registers for workshops", "manages items")
    lower = cleaned.lower()
    if re.match(r"^(?:registers?|browses?|manages?|creates?|oversees?|views?|handles?|monitors?|tracks?|updates?|deletes?|searches?)\b", lower):
        return None

    # Cut off at descriptive clauses: "who", "that", "responsible for", "can", "to", ":"
    clause_match = re.search(r"\b(?:who\b|that\b|which\b|responsible for\b|can\b|to\b|shall\b|must\b|allowing\b|is responsible|oversees\b|manages\b|browses\b|registers\b)", cleaned, flags=re.IGNORECASE)
    if clause_match:
        cleaned = cleaned[:clause_match.start()].strip()

    if ":" in cleaned:
        cleaned = cleaned.split(":")[0].strip()
    if " - " in cleaned:
        cleaned = cleaned.split(" - ")[0].strip()

    cleaned = cleaned.strip(" .,;()")
    if not cleaned or len(cleaned.split()) > 5:
        tokens = cleaned.split()
        if len(tokens) > 4:
            cleaned = " ".join(tokens[:3])

    if not cleaned or len(cleaned) < 2:
        return None

    # Normalize plural to singular
    words = cleaned.split()
    singular_words = []
    for w in words:
        if w.lower().endswith("s") and not w.lower().endswith(("ss", "us", "is")):
            singular_words.append(w[:-1])
        else:
            singular_words.append(w)

    return " ".join(singular_words).title()


def deduplicate_and_normalize_actors(actors_list: List[str]) -> List[str]:
    """
    Deduplicate actors and normalize singular vs plural forms.
    Extracts concise, structured role personas without conversational sentences.
    """
    if not actors_list:
        return []

    normalized_set: Dict[str, str] = {}  # lowercase_singular -> canonical_title

    for raw in actors_list:
        if not raw or not isinstance(raw, str):
            continue

        # Split multiple actors separated by comma or slash
        split_candidates = re.split(r",|/|(?:\s+and\s+)", raw, flags=re.IGNORECASE) if len(raw) < 60 else [raw]
        for candidate in split_candidates:
            clean_role = clean_actor_role(candidate)
            if not clean_role:
                continue

            singular_key = clean_role.lower().strip()
            if singular_key not in normalized_set:
                normalized_set[singular_key] = clean_role

    return list(normalized_set.values())


def infer_modules(functional_requirements: List[str], system_type: str = "") -> List[str]:
    """
    Infer business modules dynamically from functional requirements and system type.
    Extracts modules directly from the functional capabilities of the current problem statement.
    """
    modules: List[str] = []
    
    # 1. Dynamically extract domain modules directly from functional requirements
    for fr in functional_requirements:
        clean_fr = clean_conversational_prefix(fr)
        short_title = clean_fr.split(".")[0].strip()
        clean_name = re.sub(
            r"^(?:The system shall|Must|Should|Can|Allow users to|Allow [a-zA-Z\s]+ to|Enable|Provide capability to|Manage|Track|Process|Handle|Support)\s+",
            "",
            short_title,
            flags=re.IGNORECASE,
        ).strip()
        tokens = [
            w for w in clean_name.split()
            if w.lower() not in ("user", "users", "the", "for", "with", "and", "via", "from", "into", "system", "real", "time", "all", "their")
        ]
        if tokens and len(tokens) >= 1:
            mod_candidate = " ".join(tokens[:3]).title()
            if not mod_candidate.lower().endswith(("management", "module", "service", "tracking", "processing", "engine", "control", "catalog", "operations")):
                mod_candidate = f"{mod_candidate} Management"
            if len(mod_candidate) >= 6 and mod_candidate not in modules:
                modules.append(mod_candidate)

    # 2. Check cross-cutting capability modules with strict keyword support
    joined_text = " ".join(functional_requirements).lower() + " " + system_type.lower()
    cross_cutting_patterns = [
        ("Authentication & Access Control", ["auth", "login", "register", "rbac", "password", "token", "session", "access control", "permission"]),
        ("Notification & Communication", ["notification", "sms alert", "email alert", "push notification", "in-app message", "reminder"]),
        ("Admin Dashboard & System Operations", ["admin dashboard", "system settings", "audit log", "system admin", "administrative"]),
        ("Reporting & Analytics", ["report", "analytics", "dashboard metrics", "kpi report", "statistics"]),
        ("Payment & Fee Processing", ["payment gateway", "fee payment", "tariff", "invoice", "refund", "receipt", "billing"]),
    ]
    for mod_title, keywords in cross_cutting_patterns:
        if any(re.search(rf"\b{re.escape(kw)}\b", joined_text) for kw in keywords):
            if mod_title not in modules:
                modules.append(mod_title)

    if not modules:
        modules = ["Core Operations Module", "User Identity & Access", "Reporting & Audit"]

    return list(dict.fromkeys(modules[:6]))


def sanitize_api_contracts(api_contracts: List[str], functional_requirements: List[str] = None) -> List[str]:
    """
    Remove placeholder endpoints like POST /resource or GET /resource/{id}.
    ARSRS must not invent dummy APIs.
    """
    if not api_contracts:
        return []

    sanitized: List[str] = []
    placeholder_tokens = ["/resource", "/endpoint", "/example", "dummy"]

    for api in api_contracts:
        if not api or not isinstance(api, str):
            continue
        api_clean = api.strip()
        lower = api_clean.lower()
        if any(token in lower for token in placeholder_tokens):
            continue
        if api_clean not in sanitized:
            sanitized.append(api_clean)

    return sanitized


def infer_workflows(functional_requirements: List[str], actors: List[str] = None) -> List[Dict[str, Any]]:
    """
    Generate business workflows dynamically from the CURRENT functional requirements and actors.
    Never injects hardcoded out-of-domain templates.
    """
    workflows: List[Dict[str, Any]] = []
    actors = actors or ["User"]
    primary_actor = actors[0] if actors else "User"

    # Derive workflows directly from the top functional requirements
    for idx, fr in enumerate(functional_requirements[:4], 1):
        clean_fr = clean_conversational_prefix(fr)
        short_title = clean_fr.split(".")[0].strip()
        if len(short_title) > 60:
            short_title = short_title[:57] + "..."

        # Determine best matching actor for this requirement
        req_actor = primary_actor
        fr_lower = clean_fr.lower()
        for act in actors:
            act_clean = clean_actor_role(act) if isinstance(act, str) else ""
            if act_clean and act_clean.lower() in fr_lower:
                req_actor = act_clean
                break
        if req_actor == primary_actor and len(actors) > 1 and idx % 2 == 0:
            req_actor = actors[1]

        # Extract core action keywords for workflow name
        clean_name = re.sub(
            r"^(?:The system shall|Must|Should|Can|Allow users to|Allow [a-zA-Z\s]+ to|Enable|Provide capability to)\s+",
            "",
            short_title,
            flags=re.IGNORECASE,
        ).strip()
        verbs = [w for w in re.findall(r"\b[A-Za-z]{3,}\b", clean_name) if w.lower() not in ("system", "user", "shall", "must", "allow", "provide", "enable", "support", "with", "from", "that", "the", "for")]
        action_name = " ".join(verbs[:3]).title() if verbs else f"Action {idx}"

        wf_title = f"{action_name} Workflow" if not action_name.lower().endswith("workflow") else action_name
        workflows.append({
            "id": f"WF-{idx:03d}",
            "name": wf_title,
            "actor": req_actor,
            "steps": [
                f"Initiate {clean_name.lower()}",
                f"Validate authorization and input parameters for {action_name.lower()}",
                f"Process and persist {action_name.lower()} state transition",
                f"Confirm execution and dispatch notification to {req_actor}",
            ],
        })

    if not workflows:
        workflows = [{
            "id": "WF-001",
            "name": "Core Domain Transaction Workflow",
            "actor": primary_actor,
            "steps": [
                "Initiate transaction request",
                "Validate business rules and input parameters",
                "Execute atomic state update",
                "Emit completion event and audit log",
            ],
        }]

    return workflows


def derive_business_rules(
    constraints: List[str],
    functional_requirements: List[str],
    interview_answers: List[str] = None,
) -> List[str]:
    """
    Automatically derive explicit business rules dynamically from constraints and requirements of CURRENT PS.
    """
    rules: List[str] = []

    # 1. Rules from explicit constraints
    for c in constraints:
        clean_c = clean_conversational_prefix(c)
        if clean_c and len(clean_c) > 10:
            rule_text = clean_c if clean_c.endswith(".") else f"{clean_c}."
            rules.append(rule_text)

    # 2. Dynamic rules derived from functional requirements keywords
    for fr in functional_requirements:
        clean_fr = clean_conversational_prefix(fr)
        fr_low = clean_fr.lower()
        if any(term in fr_low for term in ("payment", "pay", "fee", "cost", "charge", "price", "tariff")):
            rules.append("Payment and financial transactions must be verified and authorized prior to completing state transitions.")
        if any(term in fr_low for term in ("book", "reserve", "slot", "spot", "claim", "schedule", "allocate", "donation", "borrow")):
            rules.append("Resource reservations, allocations, and claims must enforce strict concurrency locking to prevent double-booking or duplicate allocation.")
        if any(term in fr_low for term in ("sensor", "iot", "telemetry", "tracking", "gps", "occupancy", "real-time")):
            rules.append("Real-time telemetry, sensor readings, and status updates must be validated and timestamped to maintain data freshness.")
        if any(term in fr_low for term in ("cancel", "delete", "remove", "refund", "revoke", "expire", "expiry")):
            rules.append("Cancellation, expiry handling, and revocation operations must validate eligibility against system policies.")
        if any(term in fr_low for term in ("stock", "inventory", "sku", "restock")):
            rules.append("Inventory stock balances and item quantities must remain non-negative with atomic ledger updates.")
        elif any(term in fr_low for term in ("capacity", "seat", "limit", "quota", "threshold", "slot count")):
            rules.append("System capacity limits and allocation thresholds must remain non-negative and enforce atomic boundary checks.")
        if any(term in fr_low for term in ("auth", "login", "register", "role", "access", "permission", "rbac")):
            rules.append("Only authenticated users with appropriate role permissions may access protected system operations.")

    if not rules:
        rules = [
            "Only authenticated users with valid permissions may access protected operations.",
            "All state-modifying transactions must maintain consistency and persist audit logs.",
        ]

    return list(dict.fromkeys(rules))


def refine_measurable_nfrs(nfr_list: List[str], interview_answers: List[str] = None) -> List[str]:
    """
    Replace vague NFR statements with measurable requirements.
    """
    refined: List[str] = []
    joined = (" ".join(nfr_list) + " " + " ".join(interview_answers or [])).lower()

    if any(k in joined for k in ["fast", "response time", "latency"]):
        refined.append("System response time shall be under 2.0 seconds for 95% of standard requests.")
    if any(k in joined for k in ["uptime", "availability", "sla"]):
        refined.append("System availability SLA shall meet or exceed 99.9% uptime.")
    if any(k in joined for k in ["concurrent", "user load", "capacity"]):
        refined.append("System shall support at least 1,000 active concurrent users without performance degradation.")
    if any(k in joined for k in ["heavy load", "graceful", "degradation"]):
        refined.append("System shall maintain graceful degradation and queueing under peak load spikes.")
    if any(k in joined for k in ["auth", "secure", "encryption", "storage"]):
        refined.append("All sensitive data at rest and in transit must be encrypted using AES-256 and TLS 1.3.")

    # Retain existing specific NFRs from input
    for nfr in nfr_list:
        clean = clean_conversational_prefix(nfr)
        if clean and not any(vague in clean.lower() for vague in ["fast performance", "good UI", "simple"]):
            refined.append(clean)

    return list(dict.fromkeys(refined))


def derive_success_criteria(
    interview_answers: List[str] = None,
    business_objectives: List[str] = None,
    goal: str = "",
) -> List[str]:
    """
    Derive success criteria dynamically matching the actual target problem statement.
    """
    criteria: List[str] = []
    authoritative = (goal + " " + " ".join(business_objectives or [])).lower()
    full_joined = (authoritative + " " + " ".join(interview_answers or [])).lower()

    # 1. Derive criteria from explicit business objectives
    if business_objectives:
        for obj in business_objectives[:3]:
            clean_obj = clean_conversational_prefix(obj)
            if clean_obj and len(clean_obj) > 10:
                criteria.append(f"End-to-end execution of {clean_obj.lower().rstrip('.')} with 100% data consistency.")

    # 2. General operational criteria
    if not criteria:
        clean_goal = clean_conversational_prefix(goal) if goal else "core domain operations"
        criteria.append(f"End-to-end execution of {clean_goal.lower().rstrip('.')} with 100% data consistency and zero unhandled errors.")

    if any(k in full_joined for k in ["latency", "speed", "response", "real-time", "tracking", "fast"]):
        criteria.append("Average API response latency remains under 500ms for core operational workflows.")
    if any(k in full_joined for k in ["manual", "effort", "efficiency", "automation", "automate"]):
        criteria.append("Manual operational effort and paper-based tracking are reduced by over 80%.")

    return list(dict.fromkeys(criteria))


def extract_integrations_from_text(raw_text: str, parameters: dict) -> List[str]:
    """
    Extract third-party integrations (Payment Gateway, SMS, Email, Insurance, etc.)
    from raw input and parameter dictionaries.
    """
    integrations: List[str] = []

    ext = parameters.get("external_services")
    if isinstance(ext, dict):
        ext = ext.get("value")
    if isinstance(ext, list):
        for e in ext:
            if isinstance(e, str) and e.strip():
                integrations.append(e.strip())

    joined = (raw_text + " " + " ".join(integrations)).lower()

    integration_signals = [
        (["payment", "stripe", "paypal", "razorpay", "billing gateway"], "Payment Gateway Integration"),
        (["sms", "twilio", "text notification"], "SMS Gateway Service"),
        (["email", "smtp", "sendgrid", "mailgun"], "Email Notification Service"),
        (["insurance", "claim", "verification"], "Insurance Verification API"),
        (["lab", "laboratory device", "hl7", "fhir"], "Laboratory Device Interface"),
        (["push notification", "firebase", "fcm"], "Push Notification Service"),
        (["auth0", "oauth", "sso", "identity"], "SSO / Identity Provider Integration"),
    ]

    for keywords, integration_name in integration_signals:
        if any(kw in joined for kw in keywords):
            if integration_name not in integrations:
                integrations.append(integration_name)

    return list(dict.fromkeys(integrations))


def classify_fr_nfr(items: List[str]) -> Tuple[List[str], List[str]]:
    """
    Classify requirement strings into (functional_requirements, non_functional_requirements).
    Ensures metrics, performance, SLAs, security specs land in NFR.
    System features, user capabilities, authentication land in FR.
    """
    fr_list: List[str] = []
    nfr_list: List[str] = []

    nfr_keywords = [
        "concurrent users", "requests under", "uptime", "availability",
        "response time", "ms", "seconds", "latency", "throughput",
        "encryption", "ssl", "tls", "256-bit", "secure data storage",
        "99.9%", "95%", "sla", "performance", "scalability", "reliability",
        "zero-downtime", "auto-scale"
    ]

    fr_keywords = [
        "search", "browse", "filter", "create", "update", "delete", "manage",
        "authentication", "login", "authenticate", "checkout", "register user",
        "schedule", "book", "cancel", "process transaction", "upload", "download"
    ]

    for item in items:
        if not item or not isinstance(item, str):
            continue
        cleaned = clean_conversational_prefix(item)
        if not cleaned:
            continue

        lower = cleaned.lower()
        if any(kw in lower for kw in nfr_keywords):
            nfr_list.append(cleaned)
        elif any(kw in lower for kw in fr_keywords):
            fr_list.append(cleaned)
        else:
            if re.search(r"\d+%\s*|\d+\s*(?:seconds|ms|users)|uptime|sla", lower):
                nfr_list.append(cleaned)
            else:
                fr_list.append(cleaned)

    return fr_list, nfr_list


def extract_fallback_goal(raw_input: str, parameters: dict) -> str:
    """
    Generate a complete project goal if goal is empty or trivial ('ok', 'yes', 'N/A').
    """
    goal_candidate = parameters.get("goal")
    if isinstance(goal_candidate, dict):
        goal_candidate = goal_candidate.get("value")

    if isinstance(goal_candidate, str) and len(goal_candidate.strip()) > 5:
        lower = goal_candidate.strip().lower()
        if lower not in ("ok", "yes", "n/a", "none", "true", "false"):
            return goal_candidate.strip()

    if raw_input and len(raw_input.strip()) > 10:
        lines = [l.strip() for l in raw_input.splitlines() if l.strip()]
        if lines:
            first_line = lines[0]
            first_line = clean_conversational_prefix(first_line)
            if not first_line.endswith("."):
                first_line += "."
            return first_line

    fr_list = parameters.get("functional_requirements")
    if isinstance(fr_list, dict):
        fr_list = fr_list.get("value", [])
    if isinstance(fr_list, list) and fr_list:
        actions = ", ".join(str(f) for f in fr_list[:4])
        return f"Build a system to support {actions}."

    return "Build a software application based on user requirements."


def extract_semantic_functional_requirements(raw_input: str) -> List[str]:
    """
    Extract discrete atomic functional requirements directly from raw project input text.
    Identifies capability verbs, user actions, and system features from sentence clauses.
    Used when REE extraction returns placeholders or insufficient requirements.
    """
    if not raw_input or not raw_input.strip():
        return []

    frs: List[str] = []
    text = raw_input.strip()

    # Match clauses that indicate user/staff/admin capabilities
    # E.g. "allows staff to manage products, record stock-in and stock-out transactions..."
    capability_patterns = [
        r"(?:allows?|enables?|lets?)\s+[\w\s]+\s+to\s+([^.]+)",
        r"(?:can|must|should|will)\s+([^.]+)",
        r"(?:provides?|features?|includes?)\s+([^.]+)",
    ]

    for pattern in capability_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            clause = match.group(1).strip()
            # Split by commas, 'and', 'as well as'
            parts = re.split(r",\s*|\s+and\s+|\s+as\s+well\s+as\s+", clause)
            for part in parts:
                clean = clean_conversational_prefix(part).strip()
                # Strip leading conjunctions, pronouns, and articles
                clean = re.sub(r"^(?:and\s+|as\s+well\s+as\s+|or\s+|also\s+|then\s+|plus\s+|to\s+|a\s+|an\s+|the\s+)+", "", clean, flags=re.IGNORECASE).strip()
                clean = re.sub(r"^(?:view\s+their\s+)", "View ", clean, flags=re.IGNORECASE).strip()
                clean = re.sub(r"^(?:their\s+)", "", clean, flags=re.IGNORECASE).strip()
                if len(clean) >= 6 and not any(clean.lower() == existing.lower() for existing in frs):
                    # Capitalize first letter
                    frs.append(clean[0].upper() + clean[1:] if clean else clean)

    # If clause matching produced nothing or too few, fallback to sentence splitting
    if len(frs) < 3:
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        for sentence in sentences:
            clean_s = clean_conversational_prefix(sentence).strip()
            if len(clean_s) >= 15 and not clean_s.lower().startswith(("the proposed system is", "this project is", "build a")):
                if not any(clean_s.lower() == existing.lower() for existing in frs):
                    frs.append(clean_s)

    return frs[:10]


def extract_actors_from_ps_text(text: str) -> List[str]:
    """
    Extract explicit domain persona roles directly from Problem Statement text.
    Identifies roles such as Student, Administrator, Organizer, Participant, Doctor, Patient, Recruiter, etc.
    """
    if not text or not text.strip():
        return []
    actors: List[str] = []
    lower_text = text.lower()

    # Explicit domain role mappings
    actor_patterns = [
        (r"\b(?:students?)\b", "Student"),
        (r"\b(?:administrators?|admins?)\b", "Administrator"),
        (r"\b(?:participants?|attendees?)\b", "Participant"),
        (r"\b(?:organizers?|coordinators?)\b", "Organizer"),
        (r"\b(?:instructors?|teachers?|professors?|faculty)\b", "Instructor"),
        (r"\b(?:donors?)\b", "Donor"),
        (r"\b(?:volunteers?)\b", "Volunteer"),
        (r"\b(?:doctors?|physicians?)\b", "Doctor"),
        (r"\b(?:patients?)\b", "Patient"),
        (r"\b(?:nurses?|staff)\b", "Staff"),
        (r"\b(?:sellers?|merchants?|vendors?)\b", "Merchant"),
        (r"\b(?:recruiters?|hiring\s+managers?)\b", "Recruiter"),
        (r"\b(?:candidates?|applicants?|job\s+seekers?)\b", "Candidate"),
        (r"\b(?:riders?|passengers?)\b", "Passenger"),
        (r"\b(?:borrowers?|members?)\b", "Member"),
        (r"\b(?:librarians?)\b", "Librarian"),
        (r"\b(?:managers?|supervisors?)\b", "Manager"),
    ]

    for pattern, canonical_role in actor_patterns:
        if re.search(pattern, lower_text):
            if canonical_role not in actors:
                actors.append(canonical_role)

    # Check grammar clauses: "allows <ACTOR> to", "<ACTOR> can"
    clause_matches = re.findall(r"(?:allows?|enables?|lets?)\s+([a-zA-Z\s]{3,20})\s+to", text, re.IGNORECASE)
    for m in clause_matches:
        cleaned = clean_actor_role(m)
        if cleaned and len(cleaned) >= 3 and cleaned.lower() not in ("system", "application", "platform", "user", "users"):
            if cleaned not in actors:
                actors.append(cleaned)

    can_matches = re.findall(r"\b([A-Z][a-zA-Z\s]{2,20})\s+can\s+(?:create|manage|view|track|access|update|delete|browse)", text)
    for m in can_matches:
        cleaned = clean_actor_role(m)
        if cleaned and len(cleaned) >= 3 and cleaned.lower() not in ("system", "application", "platform", "user", "users"):
            if cleaned not in actors:
                actors.append(cleaned)

    return actors



