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

        # Strip bullet/numbering prefix
        line = re.sub(r"^(?:[\-\*\•\>]|\d+[\.\)])\s*", "", line).strip()
        if not line:
            continue

        # Split on semicolons if present
        if ";" in line:
            sub_parts = [p.strip() for p in line.split(";") if p.strip()]
            for p in sub_parts:
                p = re.sub(r"^(?:[\-\*\•\>]|\d+[\.\)])\s*", "", p).strip()
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
                        # Convert to title capability format if short, else format cleanly
                        feat_title = sf_clean.title()
                        atomic_items.append(f"System shall support {feat_title}")
            else:
                atomic_items.append(part.strip())

    # Deduplicate while preserving order
    result: List[str] = []
    for a in atomic_items:
        if a and a not in result:
            result.append(a)

    return result


def infer_modules(functional_requirements: List[str], system_type: str = "") -> List[str]:
    """
    Infer system modules by grouping functional requirements and domain context.
    """
    modules: List[str] = []
    joined_text = " ".join(functional_requirements).lower() + " " + system_type.lower()

    module_patterns = [
        ("Authentication & Access Control Module", ["auth", "login", "register", "rbac", "password", "token", "session", "user"]),
        ("Patient & User Management Module", ["patient", "profile", "medical history", "demographics", "registration"]),
        ("Appointment & Scheduling Module", ["appointment", "booking", "schedule", "slot", "doctor schedule", "calendar", "cancel"]),
        ("Prescription & Pharmacy Module", ["prescription", "pharmacy", "medicine", "drug", "dosage", "chemist"]),
        ("Laboratory & Diagnostics Module", ["lab", "laboratory", "test", "report", "diagnostic", "specimen"]),
        ("Billing & Payment Module", ["billing", "payment", "invoice", "fee", "receipt", "stripe", "transaction"]),
        ("Notification & Communication Module", ["notification", "sms", "email", "alert", "reminder", "message"]),
        ("System Administration & Audit Module", ["admin", "audit", "configuration", "logs", "dashboard", "report"]),
    ]

    for mod_title, keywords in module_patterns:
        if any(kw in joined_text for kw in keywords):
            modules.append(mod_title)

    if not modules:
        # Default fallback modules if none matched
        modules = [
            "Core Functional Module",
            "User Access Control Module",
            "Data Processing Module",
            "Integration & Notification Module",
        ]

    return list(dict.fromkeys(modules))


def infer_api_contracts(functional_requirements: List[str], modules: List[str]) -> List[str]:
    """
    Infer REST API endpoints from functional requirements and system modules.
    Example output:
      POST /api/v1/auth/login
      POST /api/v1/patients
      GET /api/v1/patients/{id}
      POST /api/v1/appointments
      DELETE /api/v1/appointments/{id}
    """
    endpoints: List[str] = []
    joined_text = " ".join(functional_requirements).lower()

    # Rule-based endpoint generator
    endpoint_rules = [
        (["login", "authenticate"], "POST /api/v1/auth/login"),
        (["register user", "patient registration", "signup"], "POST /api/v1/auth/register"),
        (["patient", "medical history"], "GET /api/v1/patients/{id}"),
        (["patient", "medical history"], "PUT /api/v1/patients/{id}"),
        (["appointment", "book appointment"], "POST /api/v1/appointments"),
        (["appointment", "cancel appointment"], "DELETE /api/v1/appointments/{id}"),
        (["appointment", "view appointment"], "GET /api/v1/appointments"),
        (["prescription"], "POST /api/v1/prescriptions"),
        (["prescription"], "GET /api/v1/prescriptions/{id}"),
        (["billing", "payment"], "POST /api/v1/payments/checkout"),
        (["billing", "invoice"], "GET /api/v1/invoices/{id}"),
        (["lab", "test report"], "GET /api/v1/lab-reports/{id}"),
        (["notification"], "POST /api/v1/notifications/send"),
    ]

    for keywords, endpoint in endpoint_rules:
        if any(kw in joined_text for kw in keywords):
            if endpoint not in endpoints:
                endpoints.append(endpoint)

    # General endpoint generation if empty or few
    if len(endpoints) < 3:
        for fr in functional_requirements[:5]:
            lower_fr = fr.lower()
            if "patient" in lower_fr:
                endpoints.append("GET /api/v1/patients")
                endpoints.append("POST /api/v1/patients")
            elif "appointment" in lower_fr:
                endpoints.append("POST /api/v1/appointments")
                endpoints.append("GET /api/v1/appointments/{id}")
            elif "user" in lower_fr:
                endpoints.append("POST /api/v1/users/login")
                endpoints.append("GET /api/v1/users/profile")

    if not endpoints:
        endpoints = [
            "POST /api/v1/resource",
            "GET /api/v1/resource/{id}",
            "PUT /api/v1/resource/{id}",
            "DELETE /api/v1/resource/{id}",
        ]

    return list(dict.fromkeys(endpoints))


def extract_integrations_from_text(raw_text: str, parameters: dict) -> List[str]:
    """
    Extract third-party integrations (Payment Gateway, SMS, Email, Insurance, etc.)
    from raw input and parameter dictionaries.
    """
    integrations: List[str] = []

    # Check external_services parameter
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
        "search books", "borrow books", "return books", "add books",
        "remove books", "authentication", "login", "authenticate",
        "checkout", "search catalog", "manage books", "register user"
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

