"""
AI Engineering Team

Coordinates parallel execution of the three AI specialist agents:
  - RequirementEngineerAgent  : Technical requirements, actors, constraints
  - BusinessAnalystAgent      : Business goals, rules, stakeholders, KPIs
  - DomainExpertAgent         : Industry, compliance, patterns, risks

Execution model:
  - All three agents run in parallel (ThreadPoolExecutor, 3 workers)
  - Each agent receives a READ-ONLY snapshot of the SRC's project_context
    and its own section (to check existing state), preventing race conditions
  - Results are merged back into the SRC sequentially after all agents finish
  - Agents NEVER communicate directly — all collaboration goes through SRC
  - One agent failure does not block the others

The EngineeringTeamAgent itself contains no AI reasoning — it is a
deterministic parallel coordinator.
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from app.ree.models import SharedRequirementContext, REEStatus
from app.ree.agents.requirement_engineer import RequirementEngineerAgent
from app.ree.agents.business_analyst import BusinessAnalystAgent
from app.ree.agents.domain_expert import DomainExpertAgent

logger = logging.getLogger(__name__)


class EngineeringTeamAgent:
    """
    Parallel coordinator for the three AI Engineering Team specialists.

    Workflow:
      1. Create isolated SRC copies for each agent (prevents write conflicts)
      2. Submit all three agents to a thread pool concurrently
      3. Collect completed SRC copies as futures resolve
      4. Merge each agent's section output back into the master SRC
      5. Aggregate discussion notes from all agents

    The merge is deterministic:
      - RequirementEngineerAgent → SRC.requirements.parameters + SRC.parameters
      - BusinessAnalystAgent     → SRC.business_context
      - DomainExpertAgent        → SRC.domain_context
      - All agents               → SRC.discussion_notes (appended)
      - All agents               → SRC.agent_outputs (keyed by agent name)
    """

    _MAX_WORKERS = 3  # one per agent — they are independent

    def __init__(self) -> None:
        self._requirement_engineer = RequirementEngineerAgent()
        self._business_analyst = BusinessAnalystAgent()
        self._domain_expert = DomainExpertAgent()

    def run(self, src: SharedRequirementContext) -> SharedRequirementContext:
        """
        Execute all three specialist agents in parallel and merge results.

        Args:
            src: Current SRC with project_context populated.

        Returns:
            Updated SRC with all three agent sections populated.
        """
        # ── Dirty-State Check ──────────────────────────────────────────────────
        # Only rerun engineering if extraction inputs changed.
        # If only interview answers changed, skip Engineering Team.
        should_run = (
            not src.flags.engineering_completed
            or src.flags.project_context_changed
            or src.flags.raw_input_changed
        )
        if not should_run:
            logger.info(
                "EngineeringTeamAgent: inputs unchanged and engineering previously completed — skipping re-execution"
            )
            src.add_note(
                "engineering", "EngineeringTeamAgent",
                "Skipped re-execution: extraction inputs unchanged (interview answers updated active SRC)."
            )
            return src

        src.status = REEStatus.ENGINEERING
        logger.info("EngineeringTeamAgent: starting 3 parallel AI specialists")

        # Build isolated copies — each agent gets its own SRC so they
        # cannot stomp on each other's writes during parallel execution.
        src_re = _make_agent_copy(src)
        src_ba = _make_agent_copy(src)
        src_de = _make_agent_copy(src)

        # Map agent name → (agent instance, isolated_src_copy)
        agent_tasks: List[Tuple[str, object, SharedRequirementContext]] = [
            ("RequirementEngineer", self._requirement_engineer, src_re),
            ("BusinessAnalyst",     self._business_analyst,     src_ba),
            ("DomainExpert",        self._domain_expert,         src_de),
        ]

        completed: Dict[str, SharedRequirementContext] = {}

        futures = {}
        with ThreadPoolExecutor(max_workers=self._MAX_WORKERS) as executor:
            for name, agent, agent_src in agent_tasks:
                future = executor.submit(_run_agent_safe, name, agent, agent_src)
                futures[future] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                result_src = future.result()
                completed[name] = result_src
                logger.info("EngineeringTeamAgent: %s finished", name)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "EngineeringTeamAgent: %s raised an unhandled exception: %s",
                    name, exc, exc_info=True,
                )
                src.errors.append(f"{name} failed with unhandled exception: {exc}")

        # Merge outputs from each completed agent back into the master SRC
        if "RequirementEngineer" in completed:
            _merge_requirements(src, completed["RequirementEngineer"])

        if "BusinessAnalyst" in completed:
            _merge_business_context(src, completed["BusinessAnalyst"])

        if "DomainExpert" in completed:
            _merge_domain_context(src, completed["DomainExpert"])

        # Collect all discussion notes in completion order
        for name, _, _ in agent_tasks:
            if name not in completed:
                continue
            agent_src = completed[name]
            for note in agent_src.discussion_notes.notes:
                # Avoid duplicating notes that were already in the master SRC
                if note not in src.discussion_notes.notes:
                    src.discussion_notes.notes.append(note)

        # Collect agent_outputs
        for name in completed:
            agent_output = completed[name].agent_outputs.get(name)
            if agent_output is not None:
                src.agent_outputs[name] = agent_output

        # Sync flat parameters field after merge
        src.sync_requirements()

        # Update flags
        src.flags.engineering_completed = True
        src.flags.project_context_changed = False
        src.flags.raw_input_changed = False

        agent_count = len(completed)
        logger.info(
            "EngineeringTeamAgent: complete — %d/%d agents succeeded",
            agent_count, len(agent_tasks),
        )
        src.add_note(
            "engineering", "EngineeringTeamAgent",
            f"Parallel execution complete. {agent_count}/{len(agent_tasks)} agents succeeded."
        )

        return src


# ── Parallel execution helper ──────────────────────────────────────────────────


def _run_agent_safe(
    name: str,
    agent: object,
    agent_src: SharedRequirementContext,
) -> SharedRequirementContext:
    """
    Run a single agent against its isolated SRC copy.
    Catches all exceptions so one agent failure doesn't kill the thread pool.
    """
    try:
        return agent.run(agent_src)
    except Exception as exc:  # noqa: BLE001
        logger.error("Agent %s raised: %s", name, exc, exc_info=True)
        agent_src.errors.append(f"{name} failed: {exc}")
        return agent_src


# ── SRC copy helper ────────────────────────────────────────────────────────────


def _make_agent_copy(src: SharedRequirementContext) -> SharedRequirementContext:
    """
    Create a lightweight copy of the SRC for one agent to work on.

    Each copy shares the same project_context object (read-only by agents)
    but has its own mutable sections so agents don't clobber each other.
    """
    copy = SharedRequirementContext()

    # Share the project_context — all agents read it, none write to it
    copy.project_context = src.project_context   # shared reference (read-only)
    copy.raw_input = src.raw_input
    copy.input_sources = list(src.input_sources)

    # Each agent gets its own section to write into (deep-copy to be safe)
    copy.requirements = deepcopy(src.requirements)
    copy.business_context = deepcopy(src.business_context)
    copy.domain_context = deepcopy(src.domain_context)
    copy.discussion_notes = deepcopy(src.discussion_notes)

    # Copy flat parameters for agents that read them
    copy.parameters = deepcopy(src.parameters)
    copy.flags = deepcopy(src.flags)

    # Session metadata
    copy.session_id = src.session_id
    copy.status = src.status

    return copy


# ── Section merge helpers ──────────────────────────────────────────────────────


def _merge_requirements(
    master: SharedRequirementContext,
    agent_src: SharedRequirementContext,
) -> None:
    """
    Merge RequirementEngineer's output into master SRC.

    Copies new parameter keys and unions list values. Never overwrites
    a non-empty confirmed value[] that already existed in master.
    """
    for key, new_node in agent_src.requirements.parameters.items():
        if not isinstance(new_node, dict):
            continue

        if key not in master.requirements.parameters:
            master.requirements.parameters[key] = deepcopy(new_node)
            continue

        current = master.requirements.parameters[key]
        if not isinstance(current, dict):
            master.requirements.parameters[key] = deepcopy(new_node)
            continue

        # Union value[] or set scalar if missing
        new_value = new_node.get("value")
        if isinstance(new_value, list) and new_value:
            cur_value = current.get("value") or []
            if isinstance(cur_value, list):
                for item in new_value:
                    if item not in cur_value:
                        cur_value.append(item)
                current["value"] = cur_value
            elif cur_value is None:
                current["value"] = new_value
        elif isinstance(new_value, str) and new_value.strip():
            cur_value = current.get("value")
            if cur_value is None or cur_value == "" or cur_value == []:
                current["value"] = new_value.strip()

        # Union ai_suggestion[]
        new_sug = new_node.get("ai_suggestion")
        if isinstance(new_sug, list) and new_sug:
            cur_sug = current.get("ai_suggestion") or []
            if isinstance(cur_sug, list):
                for item in new_sug:
                    if item not in cur_sug and item not in (current.get("value") or []):
                        cur_sug.append(item)
                current["ai_suggestion"] = cur_sug
            elif cur_sug is None:
                current["ai_suggestion"] = new_sug

    master.parameters = master.requirements.parameters


def _merge_business_context(
    master: SharedRequirementContext,
    agent_src: SharedRequirementContext,
) -> None:
    """
    Merge BusinessAnalyst's output into master SRC.business_context.
    Uses union for all list fields; scalar (domain) only set if not present.
    """
    src_bc = agent_src.business_context
    dst_bc = master.business_context

    dst_bc.business_objectives = _union_lists(
        dst_bc.business_objectives, src_bc.business_objectives
    )
    dst_bc.stakeholders = _union_lists(dst_bc.stakeholders, src_bc.stakeholders)
    dst_bc.constraints = _union_lists(dst_bc.constraints, src_bc.constraints)
    dst_bc.domain_keywords = _union_lists(dst_bc.domain_keywords, src_bc.domain_keywords)

    if not dst_bc.domain and src_bc.domain:
        dst_bc.domain = src_bc.domain

    # Copy extended dynamic attributes
    for attr in ["kpis", "pain_points", "assumptions", "business_rules"]:
        src_val = getattr(src_bc, attr, [])
        dst_val = getattr(dst_bc, attr, [])
        setattr(dst_bc, attr, _union_lists(dst_val, src_val))


def _merge_domain_context(
    master: SharedRequirementContext,
    agent_src: SharedRequirementContext,
) -> None:
    """
    Merge DomainExpert's output into master SRC.domain_context.
    """
    src_dc = agent_src.domain_context
    dst_dc = master.domain_context

    if not dst_dc.system_type and src_dc.system_type:
        dst_dc.system_type = src_dc.system_type

    if not getattr(dst_dc, "industry", None) and getattr(src_dc, "industry", None):
        setattr(dst_dc, "industry", getattr(src_dc, "industry"))

    dst_dc.similar_systems = _union_lists(dst_dc.similar_systems, src_dc.similar_systems)
    dst_dc.architecture_patterns = _union_lists(
        dst_dc.architecture_patterns, src_dc.architecture_patterns
    )
    dst_dc.technology_signals = _union_lists(
        dst_dc.technology_signals, src_dc.technology_signals
    )

    # Copy extended dynamic attributes
    for attr in ["domain_constraints", "compliance", "scale", "risks", "domain_concepts"]:
        src_val = getattr(src_dc, attr, [])
        dst_val = getattr(dst_dc, attr, [])
        setattr(dst_dc, attr, _union_lists(dst_val, src_val))


def _union_lists(existing: List[str], new_items: List[str]) -> List[str]:
    """Return a new list with all items from existing + new_items, deduped."""
    result = list(existing)
    for item in (new_items or []):
        if item and item not in result:
            result.append(item)
    return result
