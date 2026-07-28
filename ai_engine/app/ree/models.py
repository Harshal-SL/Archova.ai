"""
REE Data Models

Defines:
  - NormalizedProjectContext  : Output of the Input Understanding Agent
  - SharedRequirementContext  : The live SRC passed between all agents
  - SRCStore                  : In-memory abstraction over the SRC
  - ArchitectureReadyStructuredRequirementSpec (ARSRS)
  - HTTP request/response shapes
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enumerations ──────────────────────────────────────────────────────────────


class REEStatus(str, Enum):
    """Lifecycle status of a REE workflow run."""
    PENDING = "pending"
    INPUT_UNDERSTANDING = "input_understanding"
    ENGINEERING = "engineering"
    REVIEWING = "reviewing"
    INTERVIEWING = "interviewing"
    FINALIZING = "finalizing"
    COMPLETE = "complete"
    FAILED = "failed"


class CompletenessLevel(str, Enum):
    """How complete the gathered requirements are."""
    INCOMPLETE = "incomplete"   # critical fields missing
    PARTIAL = "partial"         # most fields present; some gaps
    SUFFICIENT = "sufficient"   # enough for architecture generation
    COMPLETE = "complete"       # all fields confirmed by stakeholder


class InputSourceType(str, Enum):
    """Type of an input source."""
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


# ── Document section ──────────────────────────────────────────────────────────


@dataclass
class DocumentSection:
    """
    A named section extracted from a source document.

    Sections are preserved through normalization so downstream agents
    can reason about structure (e.g. 'Requirements' vs 'Background').
    """
    title: str
    """Section heading (or 'main' for unsectioned content)."""

    content: str
    """Cleaned section body text."""

    source: str
    """Source file/input label this section came from."""

    section_index: int = 0
    """Ordinal position within the source document."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "section_index": self.section_index,
        }


# ── Input source record ───────────────────────────────────────────────────────


@dataclass
class InputSourceRecord:
    """Metadata about one parsed input source."""
    label: str
    """Human-readable identifier (filename or 'text')."""

    source_type: InputSourceType
    """Detected file type."""

    char_count: int = 0
    """Character count of the parsed text."""

    parse_error: Optional[str] = None
    """Set if parsing produced an error (but still yielded partial content)."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "source_type": self.source_type.value,
            "char_count": self.char_count,
            "parse_error": self.parse_error,
        }


# ── Normalized Project Context ────────────────────────────────────────────────


@dataclass
class NormalizedProjectContext:
    """
    Output of the Input Understanding Agent.

    Contains the fully processed, deduplicated, and normalized text
    ready to be written into the Shared Requirement Context.

    This is the only object the Input Understanding Agent returns.
    It does NOT contain extracted requirement fields — that is the
    responsibility of the (future) AI Engineering agents.
    """

    # ── Primary content ───────────────────────────────────────────────────────
    full_text: str = ""
    """
    Single merged, normalized, deduplicated string of all inputs.
    This is the canonical input for downstream agents and LLM calls.
    """

    sections: List[DocumentSection] = field(default_factory=list)
    """
    Preserved document sections in order.
    Agents that need structure (e.g. to separate 'requirements' from
    'background') read from here instead of full_text.
    """

    # ── Token estimates ───────────────────────────────────────────────────────
    estimated_tokens: int = 0
    """Approximate token count of full_text (4 chars ≈ 1 token)."""

    requires_chunking: bool = False
    """True when estimated_tokens exceeds the single-pass LLM limit."""

    # ── Source traceability ───────────────────────────────────────────────────
    sources: List[InputSourceRecord] = field(default_factory=list)
    """One record per input source that was processed."""

    duplicate_blocks_removed: int = 0
    """Count of duplicate text blocks that were removed during normalization."""

    # ── Quality signals ───────────────────────────────────────────────────────
    warnings: List[str] = field(default_factory=list)
    """Non-fatal issues detected during input processing."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_text": self.full_text,
            "sections": [s.to_dict() for s in self.sections],
            "estimated_tokens": self.estimated_tokens,
            "requires_chunking": self.requires_chunking,
            "sources": [s.to_dict() for s in self.sources],
            "duplicate_blocks_removed": self.duplicate_blocks_removed,
            "warnings": self.warnings,
        }


# ── Review Result ─────────────────────────────────────────────────────────────


class ReviewVerdict(str, Enum):
    """Top-level verdict from the Requirement Review Agent."""
    READY = "ready"
    """Requirements are complete enough for architecture generation."""

    NEED_CLARIFICATION = "need_clarification"
    """Critical or important information is missing or unclear."""


@dataclass
class AmbiguityIssue:
    """A single ambiguity or clarity problem detected in the requirements."""
    field: str
    """Parameter key where the issue was found."""

    description: str
    """Human-readable description of the problem."""

    severity: str = "medium"
    """'low', 'medium', or 'high'."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class ContradictionIssue:
    """A pair of contradicting requirements."""
    field_a: str
    field_b: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_a": self.field_a,
            "field_b": self.field_b,
            "description": self.description,
        }


@dataclass
class DuplicateIssue:
    """A semantically duplicated requirement across fields or within a field."""
    field: str
    duplicate_items: List[str]
    canonical: str
    """The preferred form of the requirement."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "duplicate_items": self.duplicate_items,
            "canonical": self.canonical,
        }


@dataclass
class ConfidenceScore:
    """
    Per-dimension and overall confidence that the requirements are complete
    and ready for architecture generation.  All values are 0.0–1.0.
    """
    overall: float = 0.0

    completeness: float = 0.0
    """How many required fields are populated."""

    clarity: float = 0.0
    """How unambiguous the stated requirements are."""

    consistency: float = 0.0
    """Absence of contradictions."""

    specificity: float = 0.0
    """Level of detail (vague vs. concrete requirements)."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": round(self.overall, 3),
            "completeness": round(self.completeness, 3),
            "clarity": round(self.clarity, 3),
            "consistency": round(self.consistency, 3),
            "specificity": round(self.specificity, 3),
        }


@dataclass
class ReviewResult:
    """
    Complete output of the Requirement Review Agent.

    Attached to the SRC after the review stage.
    """

    # ── Verdict ───────────────────────────────────────────────────────────────
    verdict: ReviewVerdict = ReviewVerdict.NEED_CLARIFICATION
    """Top-level decision: ready or need_clarification."""

    # ── Scores ────────────────────────────────────────────────────────────────
    confidence: ConfidenceScore = field(default_factory=ConfidenceScore)

    # ── Issues found ─────────────────────────────────────────────────────────
    missing_items: List[str] = field(default_factory=list)
    """Names of missing critical or important fields."""

    ambiguities: List[AmbiguityIssue] = field(default_factory=list)
    """Vague or unclear requirements detected."""

    contradictions: List[ContradictionIssue] = field(default_factory=list)
    """Pairs of contradicting requirements."""

    duplicates: List[DuplicateIssue] = field(default_factory=list)
    """Semantically duplicated requirement items."""

    # ── Summary ───────────────────────────────────────────────────────────────
    review_summary: str = ""
    """Human-readable paragraph summarising the review findings."""

    reviewed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "confidence": self.confidence.to_dict(),
            "missing_items": self.missing_items,
            "ambiguities": [a.to_dict() for a in self.ambiguities],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "duplicates": [d.to_dict() for d in self.duplicates],
            "review_summary": self.review_summary,
            "reviewed_at": self.reviewed_at,
        }


# ── Quality Assessment ────────────────────────────────────────────────────────


@dataclass
class QualityAssessment:
    """
    Snapshot of how complete and consistent the current SRC is.
    Updated by the Requirement Review Agent after each pass.
    """
    completeness: CompletenessLevel = CompletenessLevel.INCOMPLETE
    missing_critical: List[str] = field(default_factory=list)
    missing_important: List[str] = field(default_factory=list)
    missing_optional: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    assessed_at: Optional[str] = None  # ISO datetime string

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completeness": self.completeness.value,
            "missing_critical": self.missing_critical,
            "missing_important": self.missing_important,
            "missing_optional": self.missing_optional,
            "notes": self.notes,
            "statistics": self.statistics,
            "assessed_at": self.assessed_at,
        }


# ── SRC Sections ─────────────────────────────────────────────────────────────
# These are the named sections of the Shared Requirement Context.
# Each section has a clear, bounded responsibility.


@dataclass
class ProjectContext:
    """
    Project Context section of the SRC.

    Holds the normalized raw input and document structure.
    Written exclusively by the Input Understanding Agent.
    """
    normalized_text: str = ""
    """The full normalized, deduplicated merged text from all inputs."""

    sections: List[DocumentSection] = field(default_factory=list)
    """Structured document sections preserved from source documents."""

    input_sources: List[InputSourceRecord] = field(default_factory=list)
    """Metadata about each parsed input source."""

    estimated_tokens: int = 0
    requires_chunking: bool = False
    duplicate_blocks_removed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "normalized_text": self.normalized_text,
            "sections": [s.to_dict() for s in self.sections],
            "input_sources": [s.to_dict() for s in self.input_sources],
            "estimated_tokens": self.estimated_tokens,
            "requires_chunking": self.requires_chunking,
            "duplicate_blocks_removed": self.duplicate_blocks_removed,
        }


@dataclass
class BusinessContext:
    """
    Business Context section of the SRC.

    Populated by AI Engineering agents. Holds inferred business domain
    information, stakeholder descriptions, and business objectives.
    """
    domain: Optional[str] = None
    """Detected business domain (e.g. 'food delivery', 'fintech')."""

    domain_keywords: List[str] = field(default_factory=list)
    """Keywords that drove domain detection."""

    business_objectives: List[str] = field(default_factory=list)
    """High-level business goals inferred or confirmed from input."""

    stakeholders: List[str] = field(default_factory=list)
    """Identified stakeholder roles (different from system actors)."""

    constraints: List[str] = field(default_factory=list)
    """Business and regulatory constraints (budget, compliance, timeline)."""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "domain": self.domain,
            "domain_keywords": self.domain_keywords,
            "business_objectives": self.business_objectives,
            "stakeholders": self.stakeholders,
            "constraints": self.constraints,
        }
        # Include dynamically-added fields from BusinessAnalystAgent
        for attr in ("kpis", "pain_points", "assumptions"):
            val = getattr(self, attr, None)
            if val is not None:
                d[attr] = val
        return d


@dataclass
class DomainContext:
    """
    Domain Context section of the SRC.

    Populated by AI Engineering agents and RAG retrieval.
    Holds domain-specific patterns, similar systems, and relevant
    architecture knowledge surfaced from the knowledge base.
    """
    system_type: Optional[str] = None
    """Classified system type (e.g. 'E-Commerce Platform')."""

    similar_systems: List[str] = field(default_factory=list)
    """Known real-world systems in the same domain (for RAG context)."""

    architecture_patterns: List[str] = field(default_factory=list)
    """Architecture patterns applicable to this domain."""

    technology_signals: List[str] = field(default_factory=list)
    """Technology keywords detected in the input."""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "system_type": self.system_type,
            "similar_systems": self.similar_systems,
            "architecture_patterns": self.architecture_patterns,
            "technology_signals": self.technology_signals,
        }
        # Include dynamically-added fields from DomainExpertAgent
        for attr in ("domain_constraints", "compliance", "scale", "risks"):
            val = getattr(self, attr, None)
            if val is not None:
                d[attr] = val
        return d


@dataclass
class RequirementsSection:
    """
    Requirements section of the SRC.

    Holds the structured parameter set extracted from the input.
    Uses the 11-field schema: each field is {"value": ..., "ai_suggestion": ...}.
    Written by the Input Understanding Agent (extraction) and enriched
    by AI Engineering agents.
    """
    parameters: Dict[str, Any] = field(default_factory=dict)
    """
    Structured requirement parameters.
    Keys: goal, core_objectives, system_type, actors,
          functional_requirements, inputs, outputs, external_services,
          system_behaviour, non_functional_requirements, free_constraint
    """

    def get_value(self, key: str) -> Any:
        node = self.parameters.get(key)
        if isinstance(node, dict):
            return node.get("value")
        return node

    def set_value(self, key: str, value: Any) -> None:
        if key in self.parameters and isinstance(self.parameters[key], dict):
            self.parameters[key]["value"] = value
        else:
            self.parameters[key] = {"value": value, "ai_suggestion": None}

    def is_missing(self, key: str) -> bool:
        node = self.parameters.get(key)
        if isinstance(node, dict):
            return node.get("value") is None
        return node is None

    def to_dict(self) -> Dict[str, Any]:
        return {"parameters": self.parameters}


@dataclass
class DiscussionNotes:
    """
    Discussion Notes section of the SRC.

    Accumulates free-form observations, agent notes, and clarification
    context gathered throughout the pipeline. Acts as an audit log
    of reasoning applied at each stage.
    """
    notes: List[Dict[str, Any]] = field(default_factory=list)
    """
    List of note entries.
    Each entry: {"stage": str, "agent": str, "note": str, "timestamp": str}
    """

    def add(self, stage: str, agent: str, note: str) -> None:
        self.notes.append({
            "stage": stage,
            "agent": agent,
            "note": note,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def to_dict(self) -> Dict[str, Any]:
        return {"notes": self.notes}


# ── Shared Requirement Context (SRC) ─────────────────────────────────────────


@dataclass
class SharedRequirementContext:
    """
    Shared Requirement Context (SRC).

    The canonical mutable container for all REE pipeline state.
    Every agent reads from and writes to the SRC. The Orchestrator
    passes this single object between stages.

    Structured into named sections:
      - project_context    : normalized input (from Input Understanding Agent)
      - business_context   : domain/business info (from AI Engineering agents)
      - domain_context     : technical domain info (from AI Engineering agents)
      - requirements       : structured parameter set (11-field schema)
      - discussion_notes   : pipeline audit log
      - quality_assessment : completeness snapshot (from Review Agent)
      - interview_history  : all interview rounds

    The flat fields (raw_input, parameters, etc.) are kept for backward
    compatibility with the Orchestrator and existing agents from Task 1.
    They are kept in sync with the section objects by the helper methods.
    """

    # ── Named sections (Task 2 requirement) ──────────────────────────────────
    project_context: ProjectContext = field(default_factory=ProjectContext)
    business_context: BusinessContext = field(default_factory=BusinessContext)
    domain_context: DomainContext = field(default_factory=DomainContext)
    requirements: RequirementsSection = field(default_factory=RequirementsSection)
    discussion_notes: DiscussionNotes = field(default_factory=DiscussionNotes)
    quality_assessment: QualityAssessment = field(default_factory=QualityAssessment)
    review_result: Optional[ReviewResult] = None
    """Populated by RequirementReviewAgent after each review pass."""

    interview_session: Optional[Any] = None
    """Populated by InterviewModerator. Holds full interview round history."""

    # ── Flat fields (backward-compat with Orchestrator / existing agents) ─────
    raw_input: str = ""
    """Combined plain-text input from all sources. Mirrors project_context.normalized_text."""

    input_sources: List[str] = field(default_factory=list)
    """Source labels. Mirrors project_context.input_sources[*].label."""

    parameters: Dict[str, Any] = field(default_factory=dict)
    """Structured parameters. Mirrors requirements.parameters."""

    # ── Interview tracking ────────────────────────────────────────────────────
    interview_history: List[Dict[str, Any]] = field(default_factory=list)
    missing_parameters: List[str] = field(default_factory=list)
    clarification_questions: List[Dict[str, Any]] = field(default_factory=list)
    interview_round: int = 0

    # ── Pipeline state ────────────────────────────────────────────────────────
    completeness: CompletenessLevel = CompletenessLevel.INCOMPLETE
    review_notes: List[str] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    status: REEStatus = REEStatus.PENDING
    errors: List[str] = field(default_factory=list)

    # ── Section metadata ──────────────────────────────────────────────────────
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ── Sync helpers (keep flat fields and section objects in sync) ───────────

    def apply_project_context(self, npc: NormalizedProjectContext) -> None:
        """
        Write a NormalizedProjectContext into the SRC.

        Updates both the ProjectContext section and the backward-compat
        flat fields so all consumers see consistent data.
        """
        # Update the ProjectContext section
        self.project_context.normalized_text = npc.full_text
        self.project_context.sections = list(npc.sections)
        self.project_context.input_sources = list(npc.sources)
        self.project_context.estimated_tokens = npc.estimated_tokens
        self.project_context.requires_chunking = npc.requires_chunking
        self.project_context.duplicate_blocks_removed = npc.duplicate_blocks_removed

        # Keep flat fields in sync
        self.raw_input = npc.full_text
        self.input_sources = [s.label for s in npc.sources]

        # Propagate warnings to errors list
        for w in npc.warnings:
            if w not in self.errors:
                self.errors.append(w)

    def sync_parameters(self) -> None:
        """
        Sync the flat parameters field <-> requirements.parameters and named sections.
        Ensures bidirectional data propagation across all SRC sections.
        """
        if self.parameters:
            self.requirements.parameters = self.parameters
        elif self.requirements.parameters:
            self.parameters = self.requirements.parameters

        # 1. System Type (DomainContext <-> parameters["system_type"])
        sys_type = self.get_parameter_value("system_type")
        if self.domain_context.system_type:
            self.parameters["system_type"] = {
                "value": self.domain_context.system_type,
                "ai_suggestion": None,
            }
        elif sys_type:
            self.domain_context.system_type = str(sys_type)

        # 2. Objectives / Goals (BusinessContext <-> parameters["core_objectives"] / ["goal"])
        biz_objs = (
            self.get_parameter_value("core_objectives")
            or self.get_parameter_value("business_objectives")
            or self.get_parameter_value("goal")
        )
        if biz_objs:
            val_list = biz_objs if isinstance(biz_objs, list) else [str(biz_objs)]
            for obj in val_list:
                if obj and obj not in self.business_context.business_objectives:
                    self.business_context.business_objectives.append(str(obj))
        elif self.business_context.business_objectives:
            objs = list(self.business_context.business_objectives)
            if "core_objectives" not in self.parameters or not self.get_parameter_value("core_objectives"):
                self.parameters["core_objectives"] = {"value": objs, "ai_suggestion": []}
            if "goal" not in self.parameters or not self.get_parameter_value("goal"):
                self.parameters["goal"] = {"value": objs[0], "ai_suggestion": None}

        # 3. Constraints (BusinessContext / DomainContext <-> parameters["constraints"])
        constraints = self.get_parameter_value("constraints")
        if isinstance(constraints, list):
            for c in constraints:
                if c and str(c) not in self.business_context.constraints:
                    self.business_context.constraints.append(str(c))
        elif self.business_context.constraints:
            if "constraints" not in self.parameters or not self.get_parameter_value("constraints"):
                self.parameters["constraints"] = {
                    "value": list(self.business_context.constraints),
                    "ai_suggestion": [],
                }

        # 4. Stakeholders / Actors (BusinessContext <-> parameters["stakeholders"] / ["actors"])
        stakeholders = self.get_parameter_value("stakeholders") or self.get_parameter_value("actors")
        if stakeholders:
            val_list = stakeholders if isinstance(stakeholders, list) else [str(stakeholders)]
            for s in val_list:
                if s and str(s) not in self.business_context.stakeholders:
                    self.business_context.stakeholders.append(str(s))
        elif self.business_context.stakeholders:
            if "actors" not in self.parameters or not self.get_parameter_value("actors"):
                self.parameters["actors"] = {
                    "value": list(self.business_context.stakeholders),
                    "ai_suggestion": [],
                }

        dom_val = self.get_parameter_value("domain")
        if dom_val:
            self.business_context.domain = str(dom_val)

        self.requirements.parameters = self.parameters

    def sync_requirements(self) -> None:
        """
        Sync requirements.parameters <-> flat parameters field.
        """
        self.sync_parameters()


    # ── Convenience parameter accessors (backward-compat) ────────────────────

    def get_parameter_value(self, key: str) -> Any:
        """Return the resolved value for a parameter key."""
        node = self.parameters.get(key)
        if isinstance(node, dict):
            return node.get("value")
        return node

    def set_parameter_value(self, key: str, value: Any) -> None:
        """Set only the value for a parameter key, preserving ai_suggestion."""
        if key in self.parameters and isinstance(self.parameters[key], dict):
            self.parameters[key]["value"] = value
        else:
            self.parameters[key] = {"value": value, "ai_suggestion": None}
        self.sync_parameters()

    def is_parameter_missing(self, key: str) -> bool:
        """Return True if the parameter value is None or absent."""
        node = self.parameters.get(key)
        if isinstance(node, dict):
            return node.get("value") is None
        return node is None

    def to_parameters_dict(self) -> Dict[str, Any]:
        """Return parameters in the standard {value, ai_suggestion} format."""
        return dict(self.parameters)

    def add_note(self, stage: str, agent: str, note: str) -> None:
        """Add a note to the DiscussionNotes section."""
        self.discussion_notes.add(stage, agent, note)

    def update_quality(self, assessment: QualityAssessment) -> None:
        """Replace the quality assessment and sync flat fields."""
        self.quality_assessment = assessment
        self.completeness = assessment.completeness
        self.review_notes = list(assessment.notes)
        self.missing_parameters = (
            assessment.missing_critical + assessment.missing_important
        )

    def set_review_result(self, result: ReviewResult) -> None:
        """Attach a ReviewResult from the Requirement Review Agent."""
        self.review_result = result

    def get_or_create_interview_session(self) -> Any:
        """Return existing InterviewSession or create a fresh one."""
        if self.interview_session is None:
            from app.ree.models import InterviewSession
            self.interview_session = InterviewSession()
        return self.interview_session

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Full serialisation of the SRC including all named sections."""
        return {
            # Named sections
            "project_context": self.project_context.to_dict(),
            "business_context": self.business_context.to_dict(),
            "domain_context": self.domain_context.to_dict(),
            "requirements": self.requirements.to_dict(),
            "discussion_notes": self.discussion_notes.to_dict(),
            "quality_assessment": self.quality_assessment.to_dict(),
            "review_result": self.review_result.to_dict() if self.review_result else None,
            "interview_session": self.interview_session.to_dict() if self.interview_session else None,
            # Flat / pipeline fields
            "raw_input": self.raw_input,
            "input_sources": self.input_sources,
            "parameters": self.parameters,
            "missing_parameters": self.missing_parameters,
            "clarification_questions": self.clarification_questions,
            "interview_history": self.interview_history,
            "interview_round": self.interview_round,
            "completeness": self.completeness.value,
            "review_notes": self.review_notes,
            "agent_outputs": self.agent_outputs,
            "status": self.status.value,
            "errors": self.errors,
            "session_id": self.session_id,
            "created_at": self.created_at,
        }


# ── SRC Store (in-memory abstraction) ─────────────────────────────────────────


class SRCStore:
    """
    In-memory store for SharedRequirementContext instances.

    Provides a thin abstraction layer over SRC storage. Currently
    backed by a plain dict. Swap the backend (Redis, DB) without
    changing any agent code.

    All agents and the Orchestrator receive and return SRC objects
    directly. The store is used only for cross-request session
    persistence (e.g. multi-turn interview flows).
    """

    def __init__(self) -> None:
        self._store: Dict[str, SharedRequirementContext] = {}

    def save(self, src: SharedRequirementContext) -> str:
        """
        Persist an SRC instance and return its session_id.

        Args:
            src: The SRC to store.

        Returns:
            The session_id used as the storage key.
        """
        self._store[src.session_id] = src
        return src.session_id

    def load(self, session_id: str) -> Optional[SharedRequirementContext]:
        """
        Retrieve an SRC by session_id.

        Args:
            session_id: The session identifier.

        Returns:
            The SRC if found, otherwise None.
        """
        return self._store.get(session_id)

    def delete(self, session_id: str) -> None:
        """Remove an SRC from the store."""
        self._store.pop(session_id, None)

    def exists(self, session_id: str) -> bool:
        """Return True if an SRC with this session_id exists."""
        return session_id in self._store

    def __len__(self) -> int:
        return len(self._store)


# ── Module-level singleton store ──────────────────────────────────────────────
# All components import this singleton so they share the same in-memory store.

src_store = SRCStore()


# ── Interview Models ──────────────────────────────────────────────────────────


@dataclass
class InterviewQuestion:
    """
    A single question generated by the Interview Moderator for the stakeholder.

    Questions are reasoning-based — generated from gaps identified in the
    ReviewResult, not simply because a JSON field is null.
    """
    question_id: str
    """Unique identifier for this question within the session."""

    question: str
    """The natural-language question text."""

    rationale: str
    """Why this question is being asked — derived from ReviewResult findings."""

    target_section: str
    """Which SRC section this question aims to clarify
    (e.g. 'requirements', 'business_context', 'domain_context')."""

    target_field: Optional[str] = None
    """Specific parameter key being clarified, if applicable."""

    options: List[str] = field(default_factory=list)
    """Suggested answer options (empty = free-form answer expected)."""

    priority: str = "medium"
    """'high' | 'medium' | 'low' — drives ordering."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "rationale": self.rationale,
            "target_section": self.target_section,
            "target_field": self.target_field,
            "options": self.options,
            "priority": self.priority,
        }


@dataclass
class InterviewAnswer:
    """A stakeholder's answer to a single InterviewQuestion."""
    question_id: str
    answer: str
    answered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "answer": self.answer,
            "answered_at": self.answered_at,
        }


@dataclass
class InterviewRound:
    """
    One complete round of the stakeholder interview.

    A round is: questions generated → stakeholder answers → SRC updated.
    Multiple rounds repeat until the ReviewResult verdict is READY.
    """
    round_number: int
    """1-based round counter."""

    questions: List[InterviewQuestion] = field(default_factory=list)
    answers: List[InterviewAnswer] = field(default_factory=list)

    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None

    updated_sections: List[str] = field(default_factory=list)
    """Which SRC sections were updated after this round's answers were applied."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "questions": [q.to_dict() for q in self.questions],
            "answers": [a.to_dict() for a in self.answers],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "updated_sections": self.updated_sections,
        }


@dataclass
class InterviewSession:
    """
    Tracks the complete history of all interview rounds for one REE session.

    Stored on the SRC and included in serialisation so the full
    interview audit trail is preserved across multi-turn API calls.
    """
    rounds: List[InterviewRound] = field(default_factory=list)
    """All completed and in-progress rounds."""

    total_rounds: int = 0
    """Count of rounds completed."""

    def add_round(self, round_: InterviewRound) -> None:
        self.rounds.append(round_)
        self.total_rounds = len(self.rounds)

    def current_round(self) -> Optional[InterviewRound]:
        """Return the most recent round, or None if no rounds yet."""
        return self.rounds[-1] if self.rounds else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rounds": [r.to_dict() for r in self.rounds],
            "total_rounds": self.total_rounds,
        }


# ── Interview Result (legacy thin wrapper kept for orchestrator compat) ────────


# ── Interview Result ──────────────────────────────────────────────────────────


@dataclass
class InterviewResult:
    """A single interview round — questions and answers."""
    round_number: int
    missing_parameters: List[str]
    questions: List[Dict[str, Any]]
    answers: List[Dict[str, Any]] = field(default_factory=list)
    is_complete: bool = False


# ── ARSRS Supporting Models ───────────────────────────────────────────────────


@dataclass
class StructuredRequirement:
    """
    A single structured requirement with full traceability metadata.

    Every functional requirement, NFR, constraint, integration, and
    assumption in the ARSRS is represented as a StructuredRequirement
    so downstream tools can filter, sort, and trace back to the SRC.
    """
    id: str
    """Unique identifier within the ARSRS (e.g. 'FR-001', 'NFR-003')."""

    title: str
    """Short one-line title."""

    description: str
    """Full requirement statement."""

    priority: str = "medium"
    """'high' | 'medium' | 'low'."""

    category: str = "functional"
    """
    'functional' | 'non_functional' | 'constraint' | 'integration' |
    'assumption' | 'actor'
    """

    source: str = "extraction"
    """
    Where this requirement came from:
    'extraction' | 'engineering_team' | 'interview' | 'review' | 'manual'
    """

    confidence: float = 1.0
    """0.0–1.0 confidence that this requirement is correct and complete."""

    traceability: str = ""
    """
    Reference back to the SRC field/interview round that produced this.
    E.g. 'requirements.functional_requirements[2]' or 'interview.round_1.q-abc'
    """

    tags: List[str] = field(default_factory=list)
    """Optional categorisation tags (e.g. 'security', 'performance')."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "source": self.source,
            "confidence": round(self.confidence, 3),
            "traceability": self.traceability,
            "tags": self.tags,
        }


@dataclass
class ARSRSProjectProfile:
    """Human-readable profile of the project being designed."""
    goal: str = ""
    system_type: str = ""
    domain: str = ""
    input_sources: List[str] = field(default_factory=list)
    session_id: str = ""
    created_at: str = ""
    interview_rounds_conducted: int = 0
    completeness_level: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "system_type": self.system_type,
            "domain": self.domain,
            "input_sources": self.input_sources,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "interview_rounds_conducted": self.interview_rounds_conducted,
            "completeness_level": self.completeness_level,
        }


@dataclass
class ARSRSBusinessContext:
    """Business context extracted from the SRC.business_context section."""
    business_objectives: List[str] = field(default_factory=list)
    stakeholders: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "business_objectives": self.business_objectives,
            "stakeholders": self.stakeholders,
            "constraints": self.constraints,
            "kpis": self.kpis,
            "pain_points": self.pain_points,
            "assumptions": self.assumptions,
            "business_rules": self.business_rules,
        }


@dataclass
class ARSRSDomainContext:
    """Domain and technical context extracted from the SRC.domain_context section."""
    system_type: str = ""
    industry: str = ""
    domain_concepts: List[str] = field(default_factory=list)
    similar_systems: List[str] = field(default_factory=list)
    architecture_patterns: List[str] = field(default_factory=list)
    technology_signals: List[str] = field(default_factory=list)
    compliance: List[str] = field(default_factory=list)
    domain_constraints: List[str] = field(default_factory=list)
    scale: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_type": self.system_type,
            "industry": self.industry,
            "domain_concepts": self.domain_concepts,
            "similar_systems": self.similar_systems,
            "architecture_patterns": self.architecture_patterns,
            "technology_signals": self.technology_signals,
            "compliance": self.compliance,
            "domain_constraints": self.domain_constraints,
            "scale": self.scale,
            "risks": self.risks,
        }


@dataclass
class ARSRSMetadata:
    """Generation metadata for the ARSRS document."""
    arsrs_version: str = "1.0"
    generated_at: str = ""
    pipeline_version: str = "REE-v1"
    total_requirements: int = 0
    confidence_overall: float = 0.0
    review_verdict: str = ""
    review_confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arsrs_version": self.arsrs_version,
            "generated_at": self.generated_at,
            "pipeline_version": self.pipeline_version,
            "total_requirements": self.total_requirements,
            "confidence_overall": round(self.confidence_overall, 3),
            "review_verdict": self.review_verdict,
            "review_confidence": round(self.review_confidence, 3),
            "warnings": self.warnings,
            "statistics": self.statistics,
        }


# ── ARSRS ─────────────────────────────────────────────────────────────────────


@dataclass
class ArchitectureReadyStructuredRequirementSpec:
    """
    Architecture-Ready Structured Requirement Specification (ARSRS).

    The single source of truth for downstream architecture generation.
    Produced by the FinalizationAgent when the Review verdict is READY.

    Contains everything the Architecture Planner, RAG, HLD and LLD
    generators need — all SRC information fully preserved with traceability.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    session_id: str = ""
    completeness: CompletenessLevel = CompletenessLevel.SUFFICIENT

    # ── Rich structured sections ──────────────────────────────────────────────
    project_profile: ARSRSProjectProfile = field(default_factory=ARSRSProjectProfile)
    business_context: ARSRSBusinessContext = field(default_factory=ARSRSBusinessContext)
    domain_context: ARSRSDomainContext = field(default_factory=ARSRSDomainContext)
    metadata: ARSRSMetadata = field(default_factory=ARSRSMetadata)

    # ── Architecture & Modular Extensions ─────────────────────────────────────
    modules: List[str] = field(default_factory=list)
    api_contracts: List[str] = field(default_factory=list)

    # ── Structured requirements (with traceability) ───────────────────────────
    functional_requirements: List[StructuredRequirement] = field(default_factory=list)
    non_functional_requirements: List[StructuredRequirement] = field(default_factory=list)
    actors: List[StructuredRequirement] = field(default_factory=list)
    constraints: List[StructuredRequirement] = field(default_factory=list)
    integrations: List[StructuredRequirement] = field(default_factory=list)
    assumptions: List[StructuredRequirement] = field(default_factory=list)

    # ── Discussion summary ────────────────────────────────────────────────────
    discussion_summary: List[str] = field(default_factory=list)
    """Key observations from DiscussionNotes across all pipeline stages."""

    # ── Quality assessment ────────────────────────────────────────────────────
    quality_assessment: Optional[Any] = None
    """The QualityAssessment object from the SRC (serialised as dict)."""

    review_result: Optional[Any] = None
    """The ReviewResult from the ReviewAgent (serialised as dict)."""

    # ── Interview history ─────────────────────────────────────────────────────
    interview_history: List[Dict[str, Any]] = field(default_factory=list)
    """Complete interview round history from SRC.interview_history."""

    # ── Flat parameters (backward-compat for downstream consumers) ────────────
    parameters: Dict[str, Any] = field(default_factory=dict)

    # ── Legacy flat summary fields (backward-compat) ─────────────────────────
    goal: Optional[str] = None
    system_type: Optional[str] = None
    core_objectives: List[str] = field(default_factory=list)
    input_sources: List[str] = field(default_factory=list)
    interview_rounds_conducted: int = 0
    review_notes: List[str] = field(default_factory=list)
    pipeline_warnings: List[str] = field(default_factory=list)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Full serialisation of the ARSRS."""
        return {
            # Identity
            "session_id": self.session_id,
            "completeness": self.completeness.value,
            # Rich sections
            "project_profile": self.project_profile.to_dict(),
            "business_context": self.business_context.to_dict(),
            "domain_context": self.domain_context.to_dict(),
            "metadata": self.metadata.to_dict(),
            # Architecture extensions
            "modules": self.modules,
            "api_contracts": self.api_contracts,
            # Structured requirements
            "functional_requirements": [r.to_dict() for r in self.functional_requirements],
            "non_functional_requirements": [r.to_dict() for r in self.non_functional_requirements],
            "actors": [r.to_dict() for r in self.actors],
            "constraints": [r.to_dict() for r in self.constraints],
            "integrations": [r.to_dict() for r in self.integrations],
            "assumptions": [r.to_dict() for r in self.assumptions],
            # Supporting
            "discussion_summary": self.discussion_summary,
            "quality_assessment": (
                self.quality_assessment.to_dict()
                if hasattr(self.quality_assessment, "to_dict")
                else self.quality_assessment
            ),
            "review_result": (
                self.review_result.to_dict()
                if hasattr(self.review_result, "to_dict")
                else self.review_result
            ),
            "interview_history": self.interview_history,
            # Backward-compat flat fields
            "parameters": self.parameters,
            "goal": self.goal,
            "system_type": self.system_type,
            "core_objectives": self.core_objectives,
            "input_sources": self.input_sources,
            "interview_rounds_conducted": self.interview_rounds_conducted,
            "review_notes": self.review_notes,
            "pipeline_warnings": self.pipeline_warnings,
        }

    def to_parameters_for_design(self) -> Dict[str, Any]:
        """
        Extract a flat parameters dict suitable for run_design_pipeline().

        The downstream design pipeline accepts the legacy {key: {value, ai_suggestion}}
        format. This method builds that from the structured ARSRS fields so
        the existing design_service.py works without modification.
        """
        params = dict(self.parameters)  # start from the normalised parameters

        # Ensure the most important fields are present as plain values
        # (design_service uses QueryBuilder which reads these directly)
        def _ensure(key: str, value: Any) -> None:
            if value and key not in params or not params.get(key, {}).get("value"):
                params[key] = {"value": value, "ai_suggestion": None}

        _ensure("goal", self.goal)
        _ensure("system_type", self.system_type or self.domain_context.system_type)
        _ensure(
            "functional_requirements",
            [r.description for r in self.functional_requirements] or self.core_objectives,
        )
        _ensure(
            "non_functional_requirements",
            [r.description for r in self.non_functional_requirements],
        )
        _ensure("actors", [r.title for r in self.actors])
        _ensure(
            "external_services",
            [r.title for r in self.integrations],
        )
        _ensure(
            "constraints",
            [r.description for r in self.constraints],
        )

        return params


# ── HTTP request / response shapes ────────────────────────────────────────────


@dataclass
class REERequest:
    """Input to the REE Orchestrator."""
    combined_prompt: str
    input_sources: List[str] = field(default_factory=list)
    prior_parameters: Optional[Dict[str, Any]] = None
    prior_src: Optional[Dict[str, Any]] = None
    """
    Full serialised SRC from a previous REEResponse.src.
    When provided, the Orchestrator restores the complete pipeline state
    (including interview session history) instead of starting fresh.
    Takes precedence over prior_parameters when both are given.
    """
    interview_answers: Optional[List[Dict[str, Any]]] = None
    max_interview_rounds: int = 3


@dataclass
class REEResponse:
    """Output from the REE Orchestrator for one workflow execution."""
    status: REEStatus
    src: Dict[str, Any]
    arsrs: Optional[Dict[str, Any]] = None
    interview_result: Optional[Dict[str, Any]] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "src": self.src,
            "arsrs": self.arsrs,
            "interview_result": self.interview_result,
        }
