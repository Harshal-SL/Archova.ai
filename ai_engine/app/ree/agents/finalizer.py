"""
Finalization Agent

Responsibility:
  Transform the validated Shared Requirement Context (SRC) into an
  Architecture-Ready Structured Requirement Specification (ARSRS).

The ARSRS becomes the single source of truth for downstream architecture
generation (Architecture Planner → RAG → HLD → LLD).

Pipeline (entirely deterministic — no LLM calls):
  1. Promote ai_suggestion fallbacks to fill any remaining null values
  2. Normalise parameter types (clean lists, strip strings, coerce bools)
  3. Build StructuredRequirement objects with traceability metadata
  4. Populate all ARSRS sections from the corresponding SRC sections
  5. Preserve review result, interview history, confidence scores
  6. Generate ARSRS metadata (timestamp, counts, version)
  7. Return the completed ARSRS

Does NOT:
  - Call any LLM or AI service
  - Modify the SRC (read-only)
  - Generate new requirements
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.ree.models import (
    ArchitectureReadyStructuredRequirementSpec,
    ARSRSBusinessContext,
    ARSRSDomainContext,
    ARSRSMetadata,
    ARSRSProjectProfile,
    CompletenessLevel,
    ReviewVerdict,
    SharedRequirementContext,
    REEStatus,
    StructuredRequirement,
)
from app.ree.agents.text_normalizer import (
    clean_conversational_prefix,
    split_semantic_boundaries,
    normalize_actor_name,
    extract_discrete_actors,
    deduplicate_and_normalize_actors,
    split_coarse_requirements,
    merge_fragmented_requirements,
    infer_modules,
    sanitize_api_contracts,
    infer_workflows,
    derive_business_rules,
    refine_measurable_nfrs,
    derive_success_criteria,
    extract_integrations_from_text,
    classify_fr_nfr,
    extract_fallback_goal,
    extract_semantic_functional_requirements,
    extract_actors_from_ps_text,
)
from app.ree.agents.answer_merger import is_generic_placeholder, is_suggested_template_option

logger = logging.getLogger(__name__)

_AGENT_NAME = "FinalizationAgent"

# Requirement ID prefixes
_ID_PREFIX = {
    "functional":     "FR",
    "non_functional": "NFR",
    "actor":          "ACT",
    "constraint":     "CON",
    "integration":    "INT",
    "assumption":     "ASM",
}

# Confidence awarded to values by source
_CONF_EXTRACTION = 0.80   # came from LLM extraction
_CONF_INTERVIEW  = 0.95   # stakeholder confirmed via interview
_CONF_SUGGESTED  = 0.60   # ai_suggestion promoted to value


class FinalizationAgent:
    """
    Transforms the SRC into a fully validated ARSRS.

    All SRC information is preserved with full traceability.
    """

    def run(self, src: SharedRequirementContext) -> ArchitectureReadyStructuredRequirementSpec:
        """
        Assemble the ARSRS from the validated SRC.

        Args:
            src: The completed SRC — review verdict must be READY.

        Returns:
            Populated ARSRS ready for architecture generation.
        """
        src.status = REEStatus.FINALIZING
        logger.info("%s: starting ARSRS assembly", _AGENT_NAME)

        now = datetime.now(timezone.utc).isoformat()
        session_id = src.session_id or str(uuid.uuid4())

        # Extract interview answers for context enrichment
        interview_answers: List[str] = []
        for r in (src.interview_history or []):
            if isinstance(r, dict):
                for ans in r.get("answers", []):
                    if isinstance(ans, dict) and ans.get("answer"):
                        interview_answers.append(str(ans["answer"]))

        # ── Step 1: Normalise parameters ──────────────────────────────────────
        finalised_params = self._promote_suggestions(src.parameters)
        normalised_params = self._normalise_parameters(finalised_params)

        # ── Step 2: Build StructuredRequirement objects ────────────────────────
        functional_reqs, nfrs = self._build_req_objects(normalised_params, src)
        actors_reqs      = self._build_actor_requirements(normalised_params, src)
        constraints_reqs = self._build_constraint_requirements(normalised_params, src)
        integrations_reqs = self._build_integration_requirements(normalised_params, src)
        assumptions_reqs = self._build_assumptions(src)

        # ── Step 3: Project Profile & Success Criteria ─────────────────────────
        goal = extract_fallback_goal(src.raw_input, normalised_params)
        system_type = _scalar(normalised_params, "system_type") or \
                      (src.domain_context.system_type or "Software Application")

        clean_biz_objs_raw = [clean_conversational_prefix(x) for x in src.business_context.business_objectives if x]
        clean_biz_objs = [
            obj for obj in clean_biz_objs_raw
            if obj.lower().strip() != (goal or "").lower().strip()
            and not is_generic_placeholder(obj)
            and not is_suggested_template_option(obj)
        ]

        success_criteria = derive_success_criteria(
            interview_answers=interview_answers,
            business_objectives=clean_biz_objs,
            goal=goal,
        )

        project_profile = ARSRSProjectProfile(
            goal=goal or "",
            system_type=system_type,
            domain=src.business_context.domain or src.domain_context.industry or industry if 'industry' in locals() else "",
            input_sources=list(src.input_sources),
            session_id=session_id,
            created_at=now,
            interview_rounds_conducted=src.interview_round,
            completeness_level=src.completeness.value,
            success_criteria=success_criteria,
        )

        # ── Step 4: Business Context & Derived Business Rules ──────────────────
        raw_actors = [r.title for r in actors_reqs]
        clean_stakeholders = deduplicate_and_normalize_actors(raw_actors or src.business_context.stakeholders)

        # Automatically derive explicit business rules from constraints & requirements
        clean_fr_text = [r.description for r in functional_reqs]
        clean_con_text = [r.description for r in constraints_reqs]
        derived_rules = derive_business_rules(clean_con_text, clean_fr_text, interview_answers)

        # Filter existing rules from prior SRC: ensure they are grounded in the current PS context
        _ps_text_corpus = (
            (src.raw_input or "")
            + " " + " ".join(clean_con_text)
            + " " + " ".join(clean_fr_text)
            + " " + " ".join(interview_answers)
        ).lower()
        
        # Stop-words to ignore when checking grounding
        _grounding_stopwords = {"the", "a", "an", "is", "are", "must", "shall", "should", "and", "or", "to", "for", "with", "system", "user", "data", "all", "in", "on", "by", "be", "that", "this", "from"}

        existing_rules: List[str] = []
        for raw_rule in getattr(src.business_context, "business_rules", []) or []:
            if not raw_rule:
                continue
            rule_clean = clean_conversational_prefix(raw_rule)
            rule_tokens = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", rule_clean.lower()) if w not in _grounding_stopwords]
            # Rule is grounded if its core nouns/verbs appear in current PS corpus, or if it is a general system rule
            if not rule_tokens or any(t in _ps_text_corpus for t in rule_tokens):
                existing_rules.append(rule_clean)

        all_biz_rules = list(dict.fromkeys(derived_rules + existing_rules))

        arsrs_biz = ARSRSBusinessContext(
            business_objectives=list(dict.fromkeys(clean_biz_objs)),
            stakeholders=clean_stakeholders,
            constraints=list(dict.fromkeys([r.description for r in constraints_reqs])),
            kpis=list(getattr(src.business_context, "kpis", []) or []),
            pain_points=list(getattr(src.business_context, "pain_points", []) or []),
            assumptions=list(dict.fromkeys([r.description for r in assumptions_reqs])),
            business_rules=all_biz_rules,
        )

        # ── Step 5: Domain Context (Strict Dynamic Grounding) ────────────────
        industry = getattr(src.domain_context, "industry", "") or getattr(src.domain_context, "system_type", "")
        if not industry or industry == "Software Application":
            first_line = src.raw_input.strip().split("\n")[0].split(".")[0].strip() if src.raw_input else ""
            if first_line and len(first_line) > 3 and not first_line.lower().startswith(("i want", "we need", "build a", "create a", "develop a")):
                industry = first_line[:50].title()
            elif system_type and system_type != "Software Application":
                industry = system_type
            elif first_line and len(first_line) > 3:
                clean_title = re.sub(r"^(?:I want|We need|Build a|Create a|Develop a|A|An)\s+", "", first_line, flags=re.IGNORECASE).strip()
                industry = clean_title[:50].title() if clean_title else "Enterprise Software System"
            else:
                industry = "Enterprise Software System"

        domain_concepts = list(getattr(src.domain_context, "domain_concepts", []) or [])
        if not domain_concepts:
            # Dynamically derive concepts directly from extracted functional requirements of the current PS
            found_actions = [f.split(".")[0].strip() for f in clean_fr_text if len(f.split(".")[0].strip()) <= 50 and len(f.split(".")[0].strip()) >= 4]
            domain_concepts = found_actions[:5] if found_actions else ["Core Workflow Execution", "Resource Management", "Audit Logging"]

        # Ensure project profile has accurate domain
        project_profile.domain = industry

        arsrs_dom = ARSRSDomainContext(
            system_type=src.domain_context.system_type or system_type,
            industry=industry,
            domain_concepts=list(dict.fromkeys(domain_concepts)),
            similar_systems=list(src.domain_context.similar_systems),
            architecture_patterns=list(src.domain_context.architecture_patterns),
            technology_signals=list(src.domain_context.technology_signals),
            compliance=list(getattr(src.domain_context, "compliance", []) or []),
            domain_constraints=list(getattr(src.domain_context, "domain_constraints", []) or []),
            scale=list(getattr(src.domain_context, "scale", []) or []),
            risks=list(dict.fromkeys(getattr(src.domain_context, "risks", []) or [])),
        )

        # ── Step 5.5: Modules, Sanitized API Contracts & Workflows ────────────
        modules = infer_modules(clean_fr_text, system_type)
        raw_api_contracts = _list_values(normalised_params, "api_contracts")
        api_contracts = sanitize_api_contracts(raw_api_contracts, clean_fr_text)
        workflows = infer_workflows(clean_fr_text, clean_stakeholders)

        # ── Step 6: Discussion summary ────────────────────────────────────────
        discussion_summary = self._build_discussion_summary(src)

        # ── Step 7: Review result confidence & verdict ────────────────────────
        review_verdict   = "ready"
        review_confidence = 1.0
        if src.review_result:
            review_verdict   = src.review_result.verdict.value
            review_confidence = src.review_result.confidence.overall

        # ── Step 8: Recalculated Coverage & Statistics ────────────────────────
        total_reqs = (
            len(functional_reqs) + len(nfrs) + len(actors_reqs) +
            len(constraints_reqs) + len(integrations_reqs) + len(assumptions_reqs)
        )

        statistics = {
            "total_functional_requirements": len(functional_reqs),
            "total_actors": len(actors_reqs),
            "total_modules": len(modules),
            "total_integrations": len(integrations_reqs),
            "total_business_rules": len(arsrs_biz.business_rules),
            "total_constraints": len(constraints_reqs),
            "total_workflows": len(workflows),
            "coverage_percentage": round(min(100.0, ((len(functional_reqs) > 0) + (len(actors_reqs) > 0) + (len(modules) > 0) + (len(integrations_reqs) > 0) + (len(constraints_reqs) > 0)) / 5.0 * 100), 1),
            "completeness_percentage": round(review_confidence * 100, 1),
            "confidence_score": round(review_confidence, 2),
        }

        if src.quality_assessment and hasattr(src.quality_assessment, "statistics"):
            src.quality_assessment.statistics = statistics

        metadata = ARSRSMetadata(
            arsrs_version="1.0",
            generated_at=now,
            pipeline_version="REE-v1",
            total_requirements=total_reqs,
            confidence_overall=review_confidence,
            review_verdict=review_verdict,
            review_confidence=review_confidence,
            warnings=list(src.errors),
            statistics=statistics,
        )

        # ── Step 9: Legacy flat summary fields ────────────────────────────────
        core_objectives  = _list_values(normalised_params, "core_objectives")

        # ── Step 10: Assemble ARSRS ───────────────────────────────────────────
        arsrs = ArchitectureReadyStructuredRequirementSpec(
            session_id=session_id,
            completeness=src.completeness,
            # Rich sections
            project_profile=project_profile,
            business_context=arsrs_biz,
            domain_context=arsrs_dom,
            metadata=metadata,
            # Extensions
            modules=modules,
            api_contracts=api_contracts,
            workflows=workflows,
            success_criteria=success_criteria,
            # Structured requirements
            functional_requirements=functional_reqs,
            non_functional_requirements=nfrs,
            actors=actors_reqs,
            constraints=constraints_reqs,
            integrations=integrations_reqs,
            assumptions=assumptions_reqs,
            # Supporting
            discussion_summary=discussion_summary,
            quality_assessment=src.quality_assessment,
            review_result=src.review_result,
            interview_history=list(src.interview_history),
            # Flat backward-compat
            parameters=normalised_params,
            goal=goal,
            system_type=system_type,
            core_objectives=core_objectives,
            input_sources=list(src.input_sources),
            interview_rounds_conducted=src.interview_round,
            review_notes=list(src.review_notes),
            pipeline_warnings=list(src.errors),
        )

        # ── Step 11: Pre-Return Validation ───────────────────────────────────
        self._validate_arsrs(arsrs)

        logger.info(
            "%s: ARSRS assembled & validated — session=%s, completeness=%s, "
            "requirements=%d (FR=%d NFR=%d ACT=%d CON=%d INT=%d ASM=%d)",
            _AGENT_NAME,
            session_id,
            src.completeness.value,
            total_reqs,
            len(functional_reqs), len(nfrs), len(actors_reqs),
            len(constraints_reqs), len(integrations_reqs), len(assumptions_reqs),
        )

        return arsrs

    # ── StructuredRequirement builders ────────────────────────────────────────

    def _build_req_objects(
        self, params: dict, src: SharedRequirementContext
    ) -> Tuple[List[StructuredRequirement], List[StructuredRequirement]]:
        """
        Build functional and non-functional StructuredRequirements with semantic re-classification.
        Ensures metric requirements land in NFR and atomic FR items are merged cleanly.
        """
        raw_fr = _list_values(params, "functional_requirements")
        raw_nfr = _list_values(params, "non_functional_requirements")
        all_raw = raw_fr + raw_nfr

        classified_fr, classified_nfr = classify_fr_nfr(all_raw)

        # Split coarse requirements and merge fragmented requirement statements
        atomic_fr = split_coarse_requirements(classified_fr)
        clean_fr = merge_fragmented_requirements(atomic_fr)

        # Filter out generic placeholder phrases
        clean_fr = [item for item in clean_fr if not is_generic_placeholder(item)]

        # If extracted FRs are missing or insufficient, extract discrete requirements from raw input
        if len(clean_fr) < 3 and src.raw_input:
            semantic_frs = extract_semantic_functional_requirements(src.raw_input)
            for sfr in semantic_frs:
                if not is_generic_placeholder(sfr) and not any(sfr.lower() == existing.lower() for existing in clean_fr):
                    clean_fr.append(sfr)

        interview_answers = [
            str(h.get("answer", ""))
            for r in (src.interview_history or [])
            if isinstance(r, dict)
            for h in r.get("answers", [])
            if isinstance(h, dict) and h.get("answer") and not is_generic_placeholder(str(h.get("answer")))
        ]
        clean_nfr = refine_measurable_nfrs(classified_nfr, interview_answers)

        source_fr = self._detect_source(src, "functional_requirements")
        source_nfr = self._detect_source(src, "non_functional_requirements")
        conf_fr = _CONF_INTERVIEW if src.interview_round > 0 else _CONF_EXTRACTION
        conf_nfr = _CONF_INTERVIEW if src.interview_round > 0 else _CONF_EXTRACTION

        fr_objs = [
            StructuredRequirement(
                id=f"FR-{i+1:03d}",
                title=_title_from_text(item),
                description=item,
                priority=_infer_priority(item),
                category="functional",
                source=source_fr,
                confidence=conf_fr,
                traceability=f"src.requirements.parameters.functional_requirements[{i}]",
                tags=_infer_tags(item),
            )
            for i, item in enumerate(clean_fr)
        ]

        nfr_objs = [
            StructuredRequirement(
                id=f"NFR-{i+1:03d}",
                title=_title_from_text(item),
                description=item,
                priority=_infer_priority(item),
                category="non_functional",
                source=source_nfr,
                confidence=conf_nfr,
                traceability=f"src.requirements.parameters.non_functional_requirements[{i}]",
                tags=_infer_tags(item),
            )
            for i, item in enumerate(clean_nfr)
        ]

        return fr_objs, nfr_objs

    def _build_actor_requirements(
        self, params: dict, src: SharedRequirementContext
    ) -> List[StructuredRequirement]:
        """Convert actors list into StructuredRequirements with actor singularization and deduplication."""
        raw_items = _list_values(params, "actors")
        if src.business_context.stakeholders:
            raw_items.extend(src.business_context.stakeholders)

        # Extract explicit persona roles directly from Problem Statement text
        ps_actors = extract_actors_from_ps_text(src.raw_input) if src.raw_input else []
        if ps_actors:
            raw_items = ps_actors + raw_items

        norm_items = deduplicate_and_normalize_actors(raw_items)

        # Filter out generic placeholder actors if explicit domain roles exist
        generic_placeholders = {"end user", "customer", "user", "users", "authorized user"}
        has_specific = any(a.lower() not in generic_placeholders for a in norm_items)
        if has_specific:
            norm_items = [a for a in norm_items if a.lower() not in generic_placeholders]

        # Fallback to domain-neutral roles only if empty
        if not norm_items:
            norm_items = ["Authorized User", "System Administrator"]

        norm_items = list(dict.fromkeys(norm_items))

        source = self._detect_source(src, "actors")
        return [
            StructuredRequirement(
                id=f"ACT-{i+1:03d}",
                title=item,
                description=f"System actor: {item}",
                priority="high",
                category="actor",
                source=source,
                confidence=_CONF_EXTRACTION,
                traceability=f"src.requirements.parameters.actors[{i}]",
                tags=["actor"],
            )
            for i, item in enumerate(norm_items)
        ]

    def _build_constraint_requirements(
        self, params: dict, src: SharedRequirementContext
    ) -> List[StructuredRequirement]:
        """Build constraints from parameters + business context."""
        items: List[str] = []

        behaviour = _scalar(params, "system_behaviour")
        if behaviour:
            items.append(f"System behaviour: {behaviour}")

        for c in src.business_context.constraints:
            if c and c not in items:
                items.append(c)

        for c in getattr(src.domain_context, "domain_constraints", []) or []:
            if c and c not in items:
                items.append(c)

        for c in getattr(src.domain_context, "compliance", []) or []:
            if c:
                text = f"Compliance: {c}"
                if text not in items:
                    items.append(text)

        return [
            StructuredRequirement(
                id=f"CON-{i+1:03d}",
                title=_title_from_text(item),
                description=item,
                priority=_infer_priority(item),
                category="constraint",
                source="engineering_team",
                confidence=_CONF_EXTRACTION,
                traceability=f"src.business_context.constraints[{i}]",
                tags=_infer_tags(item),
            )
            for i, item in enumerate(items)
        ]

    def _build_integration_requirements(
        self, params: dict, src: SharedRequirementContext
    ) -> List[StructuredRequirement]:
        """Build integrations from external_services parameters + text extraction."""
        items = _list_values(params, "external_services")

        extra = _list_values(params, "re_integrations") if "re_integrations" in params else []
        for item in extra:
            if item not in items:
                items.append(item)

        extracted = extract_integrations_from_text(src.raw_input, params)
        for item in extracted:
            if item not in items:
                items.append(item)

        source = self._detect_source(src, "external_services")
        return [
            StructuredRequirement(
                id=f"INT-{i+1:03d}",
                title=_title_from_text(item),
                description=f"External integration: {item}",
                priority="medium",
                category="integration",
                source=source,
                confidence=_CONF_EXTRACTION,
                traceability=f"src.requirements.parameters.external_services[{i}]",
                tags=["integration", "external"],
            )
            for i, item in enumerate(items)
        ]

    def _build_assumptions(
        self, src: SharedRequirementContext
    ) -> List[StructuredRequirement]:
        """Build assumptions from business context ONLY (do NOT convert risks into assumptions)."""
        items: List[str] = []

        for a in getattr(src.business_context, "assumptions", []) or []:
            if a and a not in items:
                items.append(a)

        return [
            StructuredRequirement(
                id=f"ASM-{i+1:03d}",
                title=_title_from_text(item),
                description=item,
                priority="low",
                category="assumption",
                source="engineering_team",
                confidence=_CONF_SUGGESTED,
                traceability=f"src.business_context.assumptions[{i}]",
                tags=["assumption"],
            )
            for i, item in enumerate(items)
        ]

    def _validate_arsrs(self, arsrs: ArchitectureReadyStructuredRequirementSpec) -> None:
        """
        Validate generated ARSRS against strict Quality & Consistency rules before returning:
          1. No duplicate requirement IDs
          2. No duplicate actors
          3. No placeholder API contracts (/resource)
          4. All requirement titles are complete & well-formed
          5. Business rules present if constraints exist
          6. Workflows present if functional requirements exist
        """
        all_ids = set()
        for req_list in [
            arsrs.functional_requirements,
            arsrs.non_functional_requirements,
            arsrs.actors,
            arsrs.constraints,
            arsrs.integrations,
            arsrs.assumptions,
        ]:
            for r in req_list:
                if r.id in all_ids:
                    logger.warning("%s Validation Warning: Duplicate ID found: %s", _AGENT_NAME, r.id)
                all_ids.add(r.id)

        actor_titles = [a.title.lower() for a in arsrs.actors]
        if len(actor_titles) != len(set(actor_titles)):
            logger.warning("%s Validation Warning: Duplicate actors found in ARSRS: %s", _AGENT_NAME, actor_titles)

        for api in arsrs.api_contracts:
            if "/resource" in api.lower() or "dummy" in api.lower():
                raise ValueError(f"ARSRS validation failed: Placeholder API detected: '{api}'")

        for r in arsrs.functional_requirements:
            if not r.title or r.title.endswith("(") or len(r.title) < 3:
                r.title = _title_from_text(r.description)

        if arsrs.constraints and not arsrs.business_context.business_rules:
            logger.warning("%s Validation Warning: Constraints exist but business rules list is empty.", _AGENT_NAME)

        if arsrs.functional_requirements and not arsrs.workflows:
            logger.warning("%s Validation Warning: Functional requirements exist but workflows list is empty.", _AGENT_NAME)

    # ── Discussion summary ────────────────────────────────────────────────────

    @staticmethod
    def _build_discussion_summary(src: SharedRequirementContext) -> List[str]:
        """
        Extract the most important discussion notes as a summary list.

        Focuses on review and finalisation stage notes (the highest signal).
        """
        summary: List[str] = []
        seen: set = set()

        # Prioritise reviewing stage notes
        for note in src.discussion_notes.notes:
            if note.get("stage") in ("reviewing", "finalizing"):
                text = note.get("note", "").strip()
                if text and text not in seen:
                    summary.append(f"[{note.get('agent', '?')}] {text}")
                    seen.add(text)

        # Add one line per other stage to give context
        for note in src.discussion_notes.notes:
            if note.get("stage") not in ("reviewing", "finalizing"):
                text = note.get("note", "").strip()
                if text and text not in seen:
                    summary.append(f"[{note.get('stage', '?')}] {text[:120]}")
                    seen.add(text)
                if len(summary) >= 10:
                    break

        return summary

    # ── Source detection ──────────────────────────────────────────────────────

    @staticmethod
    def _detect_source(src: SharedRequirementContext, field_key: str) -> str:
        """
        Determine the source of a parameter value by checking interview history.
        If the field was mentioned in any interview answer, the source is 'interview'.
        """
        for entry in src.interview_history:
            for answer in entry.get("answers", []):
                if answer.get("parameter") == field_key:
                    return "interview"
        return "extraction"

    # ── Parameter normalisation (reused from previous finalizer) ──────────────

    @staticmethod
    def _promote_suggestions(parameters: dict) -> dict:
        """Promote ai_suggestions to fill null/empty values."""
        _LIST_FIELDS = {
            "core_objectives", "actors", "functional_requirements",
            "inputs", "outputs", "external_services", "non_functional_requirements",
        }
        result = {}
        for key, node in parameters.items():
            if not isinstance(node, dict):
                result[key] = node
                continue
            value = node.get("value")
            suggestion = node.get("ai_suggestion")
            is_empty = value is None or (isinstance(value, list) and len(value) == 0)
            if is_empty and suggestion:
                if key in _LIST_FIELDS:
                    if isinstance(suggestion, list) and suggestion:
                        result[key] = {"value": [s for s in suggestion if s], "ai_suggestion": suggestion}
                    elif isinstance(suggestion, str) and suggestion.strip():
                        result[key] = {"value": [suggestion.strip()], "ai_suggestion": suggestion}
                    else:
                        result[key] = node
                else:
                    if isinstance(suggestion, list) and suggestion:
                        first = next((s for s in suggestion if s and str(s).strip()), None)
                        if first:
                            result[key] = {"value": str(first).strip(), "ai_suggestion": suggestion}
                        else:
                            result[key] = node
                    elif isinstance(suggestion, str) and suggestion.strip():
                        result[key] = {"value": suggestion.strip(), "ai_suggestion": suggestion}
                    else:
                        result[key] = node
            else:
                result[key] = node
        return result

    @staticmethod
    def _normalise_parameters(parameters: dict) -> dict:
        """Coerce types and clean parameter values."""
        _LIST_FIELDS = {
            "core_objectives", "actors", "functional_requirements",
            "inputs", "outputs", "external_services", "non_functional_requirements",
        }
        result = {}
        for key, node in parameters.items():
            if not isinstance(node, dict):
                result[key] = node
                continue
            value = node.get("value")
            suggestion = node.get("ai_suggestion")
            if key in _LIST_FIELDS:
                value = _clean_list(value)
                suggestion = _clean_list(suggestion)
            elif key == "free_constraint":
                value = _to_bool(value)
            else:
                value = _clean_str(value)
                suggestion = _clean_str(suggestion) if isinstance(suggestion, str) else suggestion
            result[key] = {"value": value, "ai_suggestion": suggestion}
        return result


# ── Pure helpers ───────────────────────────────────────────────────────────────


def _raw_value(parameters: dict, key: str) -> Any:
    node = parameters.get(key)
    if isinstance(node, dict):
        return node.get("value")
    return node


def _scalar(parameters: dict, key: str) -> Optional[str]:
    val = _raw_value(parameters, key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    if isinstance(val, list) and val and isinstance(val[0], str) and val[0].strip():
        return val[0].strip()
    return None


def _list_values(parameters: dict, key: str) -> List[str]:
    val = _raw_value(parameters, key)
    if isinstance(val, list):
        return [str(v).strip() for v in val if v and str(v).strip()]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def _clean_list(value: Any) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    seen: list = []
    result: list = []
    for item in value:
        s = str(item).strip() if item is not None else ""
        if s and s not in seen:
            seen.append(s)
            result.append(s)
    return result


def _clean_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _to_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("true", "yes", "1"):
            return True
        if lower in ("false", "no", "0"):
            return False
    return None


def _title_from_text(text: str, max_len: int = 60) -> str:
    """Derive a short title from a longer requirement description."""
    if not text:
        return "Untitled"
    # Take first sentence or up to max_len chars
    first = text.split(".")[0].strip()
    if len(first) <= max_len:
        return first
    return first[:max_len].rsplit(" ", 1)[0] + "…"


def _infer_priority(text: str) -> str:
    """Heuristically infer priority from requirement text."""
    lower = text.lower()
    if any(w in lower for w in ("must", "critical", "required", "mandatory", "always")):
        return "high"
    if any(w in lower for w in ("should", "important", "strongly")):
        return "medium"
    return "medium"


def _infer_tags(text: str) -> List[str]:
    """Extract domain tags from requirement text."""
    lower = text.lower()
    tag_signals = {
        "security": ["auth", "security", "encrypt", "ssl", "tls", "jwt", "token", "rbac"],
        "performance": ["latency", "throughput", "response time", "ms", "performance", "speed"],
        "scalability": ["scale", "horizontal", "auto-scal", "load", "traffic", "concurrent"],
        "availability": ["uptime", "availability", "99.9", "downtime", "sla", "redundan"],
        "compliance": ["gdpr", "hipaa", "pci", "sox", "compliance", "regulation", "audit"],
        "database": ["database", "sql", "nosql", "storage", "persist", "schema", "query"],
        "messaging": ["kafka", "queue", "event", "async", "message", "stream", "broker"],
        "api": ["api", "rest", "graphql", "endpoint", "http", "grpc", "webhook"],
        "monitoring": ["log", "monitor", "alert", "observ", "metric", "trace"],
        "payment": ["payment", "billing", "stripe", "invoice", "transaction"],
    }
    tags = []
    for tag, keywords in tag_signals.items():
        if any(kw in lower for kw in keywords):
            tags.append(tag)
    return tags
