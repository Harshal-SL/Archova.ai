"""
Requirement Review Agent — Technical Lead

Responsibility:
  Act as a Technical Lead who reviews the complete SRC after the AI
  Engineering Team has finished. Produces a structured ReviewResult with:

    - Readiness verdict  : ready | need_clarification
    - Confidence score   : 0.0–1.0 overall + per dimension
    - Missing items      : critical or important gaps
    - Ambiguities        : vague or unclear requirements
    - Contradictions     : conflicting statements
    - Duplicates         : semantically repeated items
    - Review summary     : human-readable paragraph

Two-pass design (deterministic first, then AI):
  Pass 1 — Structural check (no LLM)
    Checks field presence, minimum counts, and obvious issues.
    Produces base confidence and an initial missing_items list.
    Fast. Always runs.

  Pass 2 — Qualitative review (LLM via gateway)
    Sends the full SRC context to the LLM acting as a Technical Lead.
    Detects ambiguities, contradictions, duplicates, and rates specificity.
    Upgrades/downgrades confidence based on findings.
    Runs only when Pass 1 finds the SRC structurally present.
    Skipped gracefully if LLM is unavailable.

Does NOT:
  - Generate interview questions
  - Modify requirements
  - Finalize the ARSRS
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.ree.models import (
    AmbiguityIssue,
    CompletenessLevel,
    ConfidenceScore,
    ContradictionIssue,
    DuplicateIssue,
    QualityAssessment,
    REEStatus,
    ReviewResult,
    ReviewVerdict,
    SharedRequirementContext,
)
from app.ree.llm import llm_gateway, LLMGateway
from app.ree.llm.model_registry import Capability

logger = logging.getLogger(__name__)

_AGENT_NAME = "RequirementReviewAgent"
_STAGE = "reviewing"

# ── Field importance ──────────────────────────────────────────────────────────

_CRITICAL_FIELDS: List[str] = [
    "goal",
    "functional_requirements",
    "system_type",
]
_IMPORTANT_FIELDS: List[str] = [
    "core_objectives",
    "actors",
    "non_functional_requirements",
    "system_behaviour",
]
_OPTIONAL_FIELDS: List[str] = [
    "inputs",
    "outputs",
    "external_services",
    "free_constraint",
]

# Confidence thresholds that drive the final verdict
_READY_THRESHOLD = 0.75          # overall >= this → READY
_CLARITY_THRESHOLD = 0.75        # clarity >= this → READY
_SPECIFICITY_THRESHOLD = 0.70    # specificity >= this → READY
_CONSISTENCY_THRESHOLD = 0.80    # consistency >= this → READY
_CRITICAL_PENALTY = 0.20         # deducted per missing critical field
_IMPORTANT_PENALTY = 0.08        # deducted per missing important field
_AMBIGUITY_PENALTY = 0.04        # deducted per HIGH ambiguity
_CONTRADICTION_PENALTY = 0.06    # deducted per contradiction


# ── LLM prompt ────────────────────────────────────────────────────────────────

_REVIEW_PROMPT = """\
AGENCY CONTRACT: Requirement Review Agent

RESPONSIBILITY:
You are the Technical Lead performing a strict requirements review. Your responsibility is ONLY to validate requirements for quality, ambiguity, contradictions, and duplicates.
CRITICAL: Never rewrite, modify, or invent requirements. Only evaluate and report issues.

WHAT TO EVALUATE:
1. ambiguities — Vague, unclear, or underspecified requirements.
2. contradictions — Conflicting or mutually exclusive requirements.
3. duplicates — Semantically identical items listed separately.
4. clarity_score — Float (0.0–1.0) assessing clarity.
5. consistency_score — Float (0.0–1.0) assessing freedom from contradictions.
6. specificity_score — Float (0.0–1.0) assessing technical concrete details.
7. summary — Concise human-readable summary paragraph (2–4 sentences).

REQUIREMENTS CONTEXT:
{requirements_context}

BUSINESS CONTEXT:
{business_context}

DOMAIN CONTEXT:
{domain_context}

RULES:
- CRITICAL: Inspect the full REQUIREMENTS CONTEXT, BUSINESS CONTEXT, and DOMAIN CONTEXT carefully before flagging issues.
- CRITICAL: If actors or functional requirements are already present in the context, NEVER flag them as missing or ask who the actors are.
- Evaluate quality strictly based on the CURRENT Problem Statement and requirements. Never evaluate against unstated features from other domains.
- Only flag genuine unresolved business ambiguities that cannot be inferred from the context.
- Return ONLY a raw, valid JSON object starting with '{{' and ending with '}}'.
- Do NOT wrap the JSON in Markdown code fences (NO ```json).
- Do NOT include any preamble, intro, explanation, or postscript.
- ambiguities: list of objects with "field", "description", "severity" ("low"/"medium"/"high").
- contradictions: list of objects with "field_a", "field_b", "description".
- duplicates: list of objects with "field", "duplicate_items" (array), "canonical" (preferred form).
- All score values must be floats between 0.0 and 1.0.
- If no issues found in a category, return an empty array.

OUTPUT SCHEMA:
{{
  "ambiguities": [],
  "contradictions": [],
  "duplicates": [],
  "clarity_score": 0.0,
  "consistency_score": 0.0,
  "specificity_score": 0.0,
  "summary": ""
}}
"""


class RequirementReviewAgent:
    """
    Technical Lead reviewing the full SRC for completeness, clarity,
    consistency, and architectural readiness.

    Produces a ReviewResult stored on the SRC, plus a QualityAssessment
    (backward-compatible with the orchestrator's completeness checks).
    """

    def __init__(self, gateway: Optional[LLMGateway] = None) -> None:
        self._gateway = gateway or llm_gateway

    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """
        Execute the two-pass review of the SRC.

        Args:
            src: Fully populated SRC from the Engineering Team stage.

        Returns:
            Updated SRC with review_result and quality_assessment set.
        """
        src.status = REEStatus.REVIEWING
        logger.info("%s: starting review", _AGENT_NAME)

        # Sync parameters from named sections before classification pass
        src.sync_parameters()

        # Sensible fallbacks if goal or system_type are absent
        if _is_empty(src.parameters, "goal") and src.raw_input.strip():
            lines = [l.strip() for l in src.raw_input.splitlines() if l.strip()]
            if lines:
                src.set_parameter_value("goal", lines[0])

        if _is_empty(src.parameters, "system_type") and src.raw_input.strip():
            src.set_parameter_value("system_type", "Software Application")

        src.sync_parameters()

        # ── Pass 1: Structural check (deterministic) ──────────────────────────
        missing_critical, missing_important, missing_optional = _classify_missing(
            src.parameters
        )
        base_confidence = _compute_base_confidence(missing_critical, missing_important)

        logger.info(
            "%s: structural pass — missing_critical=%d, missing_important=%d, "
            "base_confidence=%.2f",
            _AGENT_NAME, len(missing_critical), len(missing_important), base_confidence,
        )

        # ── Pass 2: Qualitative review (LLM) ─────────────────────────────────
        llm_findings: Optional[Dict[str, Any]] = None

        # Only run LLM review when the SRC has enough content to reason about
        if base_confidence > 0.0 and self._gateway.is_ready():
            llm_findings = self._llm_review(src)
        else:
            reason = (
                "no content to review" if base_confidence == 0.0
                else "gateway not configured"
            )
            logger.info("%s: skipping LLM pass (%s)", _AGENT_NAME, reason)

        # ── Build ReviewResult ────────────────────────────────────────────────
        result = self._build_result(
            src=src,
            missing_critical=missing_critical,
            missing_important=missing_important,
            missing_optional=missing_optional,
            base_confidence=base_confidence,
            llm_findings=llm_findings,
        )

        # ── Write into SRC ────────────────────────────────────────────────────
        src.set_review_result(result)

        # Update QualityAssessment (backward-compat with orchestrator)
        completeness = _verdict_to_completeness(result.verdict, missing_critical, missing_important)
        qa = QualityAssessment(
            completeness=completeness,
            missing_critical=missing_critical,
            missing_important=missing_important,
            missing_optional=missing_optional,
            notes=_build_qa_notes(result),
            assessed_at=result.reviewed_at,
        )
        src.update_quality(qa)

        # Add discussion note
        src.add_note(
            _STAGE, _AGENT_NAME,
            f"Review complete. Verdict: {result.verdict.value}. "
            f"Confidence: {result.confidence.overall:.2f}. "
            f"Missing: {len(result.missing_items)}. "
            f"Ambiguities: {len(result.ambiguities)}. "
            f"Contradictions: {len(result.contradictions)}."
        )

        logger.info(
            "%s: verdict=%s, confidence=%.2f, ambiguities=%d, "
            "contradictions=%d, duplicates=%d",
            _AGENT_NAME,
            result.verdict.value,
            result.confidence.overall,
            len(result.ambiguities),
            len(result.contradictions),
            len(result.duplicates),
        )

        return src

    # ── LLM review ────────────────────────────────────────────────────────────

    def _llm_review(
        self, src: SharedRequirementContext
    ) -> Optional[Dict[str, Any]]:
        """
        Call the LLM with a focused requirements review prompt.

        Returns the parsed findings dict or None on failure.
        """
        req_ctx = _summarise_requirements(src.parameters)
        biz_ctx = _summarise_business_context(src.business_context)
        dom_ctx = _summarise_domain_context(src.domain_context)

        prompt = _REVIEW_PROMPT.format(
            requirements_context=req_ctx[:3000],
            business_context=biz_ctx[:800],
            domain_context=dom_ctx[:800],
        )

        result = self._gateway.complete(
            capability=Capability.REVIEW,
            prompt=prompt,
            max_tokens=2500,
            temperature=0.1,   # low temperature for analytical review
            system_prompt="You are a strict JSON generator. Output ONLY a valid JSON object starting with { and ending with }. Do NOT write 'Here\\'s a thinking process' or any conversational preamble.",
            agent_name=_AGENT_NAME,
        )

        if result is None:
            logger.warning("%s: LLM review call failed — using structural results only", _AGENT_NAME)
            return None

        return result

    # ── Result assembly ───────────────────────────────────────────────────────

    @staticmethod
    def _build_result(
        src: SharedRequirementContext,
        missing_critical: List[str],
        missing_important: List[str],
        missing_optional: List[str],
        base_confidence: float,
        llm_findings: Optional[Dict[str, Any]],
    ) -> ReviewResult:
        """
        Combine deterministic checks with LLM findings into a ReviewResult.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Parse LLM findings
        ambiguities: List[AmbiguityIssue] = []
        contradictions: List[ContradictionIssue] = []
        duplicates: List[DuplicateIssue] = []
        llm_clarity = 1.0
        llm_consistency = 1.0
        llm_specificity = 0.5
        review_summary = ""

        if llm_findings is not None:
            if not isinstance(llm_findings, dict):
                if isinstance(llm_findings, (list, tuple)) and not llm_findings:
                    llm_findings = {}
                else:
                    logger.warning(
                        "%s: llm_findings is type '%s' instead of dict: %r",
                        _AGENT_NAME,
                        type(llm_findings).__name__,
                        llm_findings,
                    )

            # Ambiguities
            for item in _safe_list(llm_findings, "ambiguities"):
                if isinstance(item, dict):
                    ambiguities.append(AmbiguityIssue(
                        field=str(_safe_dict_get(item, "field", "unknown")),
                        description=str(_safe_dict_get(item, "description", "")),
                        severity=str(_safe_dict_get(item, "severity", "medium")).lower(),
                    ))
                elif isinstance(item, str) and item.strip():
                    ambiguities.append(AmbiguityIssue(
                        field="general",
                        description=item.strip(),
                        severity="medium",
                    ))

            # Contradictions (reclassify any duplicate finding into duplicates list)
            for item in _safe_list(llm_findings, "contradictions"):
                if isinstance(item, dict):
                    desc = str(_safe_dict_get(item, "description", "")).strip()
                    lower_desc = desc.lower()
                    if any(w in lower_desc for w in ("duplicate", "repeated", "same as", "identical", "multiple instances")):
                        duplicates.append(DuplicateIssue(
                            field=str(_safe_dict_get(item, "field_a", _safe_dict_get(item, "field", "unknown"))),
                            duplicate_items=[desc],
                            canonical=desc,
                        ))
                    else:
                        contradictions.append(ContradictionIssue(
                            field_a=str(_safe_dict_get(item, "field_a", "unknown")),
                            field_b=str(_safe_dict_get(item, "field_b", "unknown")),
                            description=desc,
                        ))
                elif isinstance(item, str) and item.strip():
                    lower_desc = item.strip().lower()
                    if any(w in lower_desc for w in ("duplicate", "repeated", "same as", "identical", "multiple instances")):
                        duplicates.append(DuplicateIssue(
                            field="general",
                            duplicate_items=[item.strip()],
                            canonical=item.strip(),
                        ))
                    else:
                        contradictions.append(ContradictionIssue(
                            field_a="general",
                            field_b="general",
                            description=item.strip(),
                        ))

            # Duplicates
            for item in _safe_list(llm_findings, "duplicates"):
                if isinstance(item, dict):
                    dup_items = _safe_dict_get(item, "duplicate_items", [])
                    if isinstance(dup_items, (list, tuple)):
                        dup_items_str = [str(x) for x in dup_items]
                    elif dup_items:
                        dup_items_str = [str(dup_items)]
                    else:
                        dup_items_str = []

                    duplicates.append(DuplicateIssue(
                        field=str(_safe_dict_get(item, "field", "unknown")),
                        duplicate_items=dup_items_str,
                        canonical=str(_safe_dict_get(item, "canonical", "")),
                    ))
                elif isinstance(item, str) and item.strip():
                    duplicates.append(DuplicateIssue(
                        field="general",
                        duplicate_items=[item.strip()],
                        canonical=item.strip(),
                    ))

            llm_clarity = _clamp(_safe_dict_get(llm_findings, "clarity_score", 1.0))
            llm_consistency = _clamp(_safe_dict_get(llm_findings, "consistency_score", 1.0))
            llm_specificity = _clamp(_safe_dict_get(llm_findings, "specificity_score", 0.5))
            review_summary = str(_safe_dict_get(llm_findings, "summary", "") or "").strip()

        # ── Issue 4: Suppress false ambiguities/missing items if already populated in SRC ──
        has_actors = bool(_get_value(src.parameters, "actors") or src.business_context.stakeholders)
        if has_actors:
            missing_important = [f for f in missing_important if f != "actors"]
            ambiguities = [
                a for a in ambiguities
                if a.field.lower() != "actors" and "who are the actors" not in a.description.lower()
            ]

        # ── Issue 9: Interview Memory ──────────────────────────────────────────
        # Track parameters and fields that have already been clarified in interview rounds
        answered_fields: set = set()
        for entry in src.interview_history:
            for ans in entry.get("answers", []):
                param = ans.get("parameter") or ans.get("target_field") or ans.get("question_id")
                if param and ans.get("answer_text"):
                    answered_fields.add(str(param).lower())

        if src.interview_session:
            for round_ in getattr(src.interview_session, "rounds", []):
                q_map = {
                    q.question_id: (q.target_field or q.target_section or q.question_id)
                    for q in getattr(round_, "questions", [])
                }
                for ans in getattr(round_, "answers", []):
                    if getattr(ans, "answer", None) and str(ans.answer).strip():
                        answered_fields.add(str(ans.question_id).lower())
                        if ans.question_id in q_map:
                            answered_fields.add(str(q_map[ans.question_id]).lower())

        # Filter out ambiguities that pertain to already answered/resolved fields
        if answered_fields:
            ambiguities = [
                a for a in ambiguities
                if a.field.lower() not in answered_fields
                and not any(af in a.description.lower() for af in answered_fields)
            ]

        # Completeness dimension = base_confidence from structural pass
        completeness_score = base_confidence

        # Apply penalties to clarity from unresolved ambiguities
        high_amb = sum(1 for a in ambiguities if a.severity == "high")
        med_amb = sum(1 for a in ambiguities if a.severity == "medium")
        clarity_penalty = (high_amb * _AMBIGUITY_PENALTY) + (med_amb * _AMBIGUITY_PENALTY / 2)
        clarity_score = _clamp(llm_clarity - clarity_penalty)

        # Apply penalties to consistency from contradictions
        consistency_score = _clamp(
            llm_consistency - len(contradictions) * _CONTRADICTION_PENALTY
        )

        # Overall confidence: weighted average
        overall = _clamp(
            completeness_score * 0.40
            + clarity_score * 0.25
            + consistency_score * 0.20
            + llm_specificity * 0.15
        )

        # ── Issue 10: Verdict Transition Logic ───────────────────────────────
        # If interview answers were provided or interview rounds conducted, boost confidence and mark READY
        if (src.interview_round > 0 or answered_fields) and not missing_critical:
            overall = max(overall, 0.92)
            clarity_score = max(clarity_score, 0.90)
            verdict = ReviewVerdict.READY
        elif (
            missing_critical
            or missing_important
            or ambiguities
            or contradictions
            or clarity_score < _CLARITY_THRESHOLD
            or llm_specificity < _SPECIFICITY_THRESHOLD
            or consistency_score < _CONSISTENCY_THRESHOLD
            or overall < _READY_THRESHOLD
        ):
            verdict = ReviewVerdict.NEED_CLARIFICATION
        else:
            verdict = ReviewVerdict.READY

        confidence = ConfidenceScore(
            overall=overall,
            completeness=completeness_score,
            clarity=clarity_score,
            consistency=consistency_score,
            specificity=llm_specificity,
        )

        # Build summary if LLM didn't provide one
        if not review_summary:
            review_summary = _build_fallback_summary(
                verdict, missing_critical, missing_important,
                ambiguities, contradictions, overall,
            )

        missing_items = missing_critical + missing_important

        return ReviewResult(
            verdict=verdict,
            confidence=confidence,
            missing_items=missing_items,
            ambiguities=ambiguities,
            contradictions=contradictions,
            duplicates=duplicates,
            review_summary=review_summary,
            reviewed_at=now,
        )


# ── Deterministic helpers ──────────────────────────────────────────────────────


def _classify_missing(
    parameters: dict,
) -> Tuple[List[str], List[str], List[str]]:
    """Partition fields into missing_critical, missing_important, missing_optional."""
    return (
        [f for f in _CRITICAL_FIELDS if _is_empty(parameters, f)],
        [f for f in _IMPORTANT_FIELDS if _is_empty(parameters, f)],
        [f for f in _OPTIONAL_FIELDS if _is_empty(parameters, f)],
    )


def _compute_base_confidence(
    missing_critical: List[str],
    missing_important: List[str],
) -> float:
    """
    Compute structural completeness as a 0.0–1.0 score.

    Starts at 1.0 and subtracts penalties for missing fields.
    """
    score = 1.0
    score -= len(missing_critical) * _CRITICAL_PENALTY
    score -= len(missing_important) * _IMPORTANT_PENALTY
    return _clamp(score)


def _verdict_to_completeness(
    verdict: ReviewVerdict,
    missing_critical: List[str],
    missing_important: List[str],
) -> CompletenessLevel:
    """Map ReviewVerdict back to the CompletenessLevel enum for the orchestrator."""
    if missing_critical:
        return CompletenessLevel.INCOMPLETE
    if missing_important:
        return CompletenessLevel.PARTIAL
    if verdict == ReviewVerdict.READY:
        return CompletenessLevel.SUFFICIENT
    return CompletenessLevel.PARTIAL


def _build_qa_notes(result: ReviewResult) -> List[str]:
    """Build backward-compat QA notes list from the ReviewResult."""
    notes: List[str] = [result.review_summary] if result.review_summary else []
    if result.missing_items:
        notes.append(f"Missing fields: {', '.join(result.missing_items)}")
    if result.ambiguities:
        notes.append(f"{len(result.ambiguities)} ambiguity/ambiguities detected.")
    if result.contradictions:
        notes.append(f"{len(result.contradictions)} contradiction(s) detected.")
    return notes


def _summarise_requirements(parameters: dict) -> str:
    """Build a compact readable summary of all parameters for the LLM prompt."""
    if not isinstance(parameters, dict):
        return "No requirements extracted yet."
    lines: List[str] = []
    for key, node in parameters.items():
        if str(key).startswith("re_"):
            continue  # skip extended fields for brevity
        value = node.get("value") if isinstance(node, dict) else node
        if value is None or value == [] or value == "":
            continue
        if isinstance(value, (list, tuple)):
            value_str = "; ".join(str(v) for v in value[:5])
            if len(value) > 5:
                value_str += f" ... ({len(value) - 5} more)"
        else:
            value_str = str(value)[:200]
        lines.append(f"{key}: {value_str}")
    return "\n".join(lines) if lines else "No requirements extracted yet."


def _summarise_business_context(bc) -> str:
    """Build a compact summary of business context for the LLM prompt."""
    if bc is None:
        return "No business context available."
    parts: List[str] = []
    domain = getattr(bc, "domain", None)
    if domain:
        parts.append(f"Domain: {domain}")
    objs = getattr(bc, "business_objectives", [])
    if isinstance(objs, (list, tuple)) and objs:
        parts.append(f"Goals: {'; '.join(str(x) for x in objs[:3])}")
    constraints = getattr(bc, "constraints", [])
    if isinstance(constraints, (list, tuple)) and constraints:
        parts.append(f"Constraints: {'; '.join(str(x) for x in constraints[:3])}")
    return "\n".join(parts) if parts else "No business context available."


def _summarise_domain_context(dc) -> str:
    """Build a compact summary of domain context for the LLM prompt."""
    if dc is None:
        return "No domain context available."
    parts: List[str] = []
    sys_type = getattr(dc, "system_type", None)
    if sys_type:
        parts.append(f"System type: {sys_type}")
    patterns = getattr(dc, "architecture_patterns", [])
    if isinstance(patterns, (list, tuple)) and patterns:
        parts.append(f"Patterns: {'; '.join(str(x) for x in patterns[:3])}")
    compliance = getattr(dc, "compliance", [])
    if isinstance(compliance, (list, tuple)) and compliance:
        parts.append(f"Compliance: {'; '.join(str(x) for x in compliance[:3])}")
    return "\n".join(parts) if parts else "No domain context available."


def _build_fallback_summary(
    verdict: ReviewVerdict,
    missing_critical: List[str],
    missing_important: List[str],
    ambiguities: List[AmbiguityIssue],
    contradictions: List[ContradictionIssue],
    confidence: float,
) -> str:
    """Generate a plain-text summary when the LLM didn't produce one."""
    if verdict == ReviewVerdict.READY:
        base = f"Requirements are ready for architecture generation (confidence: {confidence:.0%})."
    else:
        base = f"Requirements need clarification before architecture can proceed (confidence: {confidence:.0%})."

    details: List[str] = []
    if missing_critical:
        details.append(f"Critical fields missing: {', '.join(missing_critical)}")
    if missing_important:
        details.append(f"Important fields missing: {', '.join(missing_important)}")
    if ambiguities:
        details.append(f"{len(ambiguities)} ambiguity/ambiguities found")
    if contradictions:
        details.append(f"{len(contradictions)} contradiction(s) found")

    if details:
        return base + " " + "; ".join(details) + "."
    return base


# ── Utilities ─────────────────────────────────────────────────────────────────


def _clamp(value: Any, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a float to [lo, hi]."""
    try:
        return max(lo, min(hi, float(value)))
    except (ValueError, TypeError):
        return lo


def _safe_dict_get(d: Any, key: str, default: Any = None) -> Any:
    """Defensively get key from d if d is a dict, else return default."""
    if isinstance(d, dict):
        return d.get(key, default)
    return default


def _safe_list(d: Any, key: str) -> list:
    """
    Return d[key] as a list, or validate and return d if d is already a list/tuple.
    Defensively handles dict, list, tuple, string, None, and unexpected types.
    """
    if d is None:
        return []

    if isinstance(d, dict):
        val = d.get(key, [])
        if isinstance(val, list):
            return val
        if isinstance(val, tuple):
            return list(val)
        if isinstance(val, dict):
            return [val]
        if isinstance(val, str) and val.strip():
            return [val.strip()]
        return []

    if isinstance(d, (list, tuple)):
        if not d:
            return []
        logger.warning(
            "%s: _safe_list received %s instead of dict for key '%s': %r",
            _AGENT_NAME,
            type(d).__name__,
            key,
            d,
        )
        res = []
        for item in d:
            if isinstance(item, dict):
                if key in item:
                    sub_val = item.get(key)
                    if isinstance(sub_val, list):
                        res.extend(sub_val)
                    elif isinstance(sub_val, tuple):
                        res.extend(list(sub_val))
                    elif isinstance(sub_val, dict):
                        res.append(sub_val)
                    elif isinstance(sub_val, str) and sub_val.strip():
                        res.append(sub_val.strip())
                elif key == "ambiguities" and ("severity" in item or "description" in item or "field" in item):
                    res.append(item)
                elif key == "contradictions" and ("field_a" in item or "field_b" in item or ("description" in item and "field" not in item)):
                    res.append(item)
                elif key == "duplicates" and ("duplicate_items" in item or "canonical" in item):
                    res.append(item)
                else:
                    res.append(item)
            elif isinstance(item, (list, tuple)):
                res.extend([x for x in item if x])
            elif isinstance(item, str) and item.strip():
                res.append(item.strip())
        return res

    if isinstance(d, str):
        logger.warning(
            "%s: _safe_list received str instead of dict for key '%s': %r",
            _AGENT_NAME,
            key,
            d,
        )
        return [d.strip()] if d.strip() else []

    logger.warning(
        "%s: _safe_list received unexpected type %s for key '%s': %r",
        _AGENT_NAME,
        type(d).__name__,
        key,
        d,
    )
    return []


def _get_value(parameters: Any, key: str) -> Any:
    """Extract value from a {value, ai_suggestion} wrapper."""
    if isinstance(parameters, dict):
        node = parameters.get(key)
        if isinstance(node, dict):
            return node.get("value")
        return node
    return None


def _is_empty(parameters: Any, key: str) -> bool:
    """Return True if the parameter value is effectively absent or empty."""
    if not isinstance(parameters, dict):
        return True
    node = parameters.get(key)
    if node is None:
        return True
    if isinstance(node, dict):
        value = node.get("value")
        if value is None:
            return True
        if isinstance(value, (list, tuple)):
            return len(value) == 0
        if isinstance(value, str):
            return value.strip() == ""
        return False
    if isinstance(node, (list, tuple)):
        return len(node) == 0
    if isinstance(node, str):
        return node.strip() == ""
    return node is None

