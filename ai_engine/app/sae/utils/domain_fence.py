"""Authoritative Domain Grounding & Scope Boundary for SAE v2.

Constructs clear, concise domain grounding blocks injected into LLM agent prompts
(HLD, Backend LLD, Database LLD, Frontend LLD, Security, Observability, Cloud, Testing, Runbooks).

Enforces:
1. Architectural knowledge determines HOW the system should be designed.
2. The CURRENT Problem Statement and CURRENT ARSRS determine WHAT the system is.
3. Zero tolerance for introducing unstated business capabilities from other domains or previous runs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.sae.utils.domain_lock import DomainContext
from app.sae.utils.canonical_contract import CanonicalArchitectureContract

logger = logging.getLogger(__name__)


def build_domain_fence(
    cac: Optional[CanonicalArchitectureContract] = None,
    domain_ctx: Optional[DomainContext] = None,
    raw_prompt: str = "",
    arsrs: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate an authoritative domain grounding prompt block.
    Injected into all LLM generation prompts to enforce strict adherence to the current Problem Statement.
    """
    domain_key = ""
    domain_name = "Enterprise Software System"
    system_name = "Enterprise Application"
    problem_statement = ""

    if domain_ctx:
        domain_key = domain_ctx.domain_key
        domain_name = domain_ctx.domain_name
        system_name = domain_ctx.system_name
        problem_statement = domain_ctx.system_goal
    elif cac:
        domain_name = getattr(cac, "domain_name", "") or getattr(cac, "domain", "Enterprise Software System")
        domain_key = getattr(cac, "domain_key", "") or domain_name.lower().replace(" ", "_")
        system_name = getattr(cac, "system_name", "Enterprise Application")
    elif arsrs:
        proj_prof = arsrs.get("project_profile", {}) if isinstance(arsrs.get("project_profile"), dict) else {}
        system_name = arsrs.get("system_name") or proj_prof.get("name") or "Enterprise Application"
        domain_name = proj_prof.get("domain") or arsrs.get("domain") or "Enterprise Software System"
        problem_statement = proj_prof.get("goal") or arsrs.get("raw_input") or ""

    if not problem_statement and raw_prompt:
        problem_statement = raw_prompt.strip()

    if not problem_statement and domain_ctx and domain_ctx.canonical_requirements:
        problem_statement = " | ".join([r.description for r in domain_ctx.canonical_requirements[:3]])

    # Canonical positive bindings
    canonical_details = []
    if cac:
        if cac.domain_entities:
            canonical_details.append(f" • Canonical Domain Entities : {', '.join([e.name for e in cac.domain_entities])}")
        if cac.api_operations:
            canonical_details.append(" • Canonical API Operations:")
            for op in cac.api_operations[:8]:
                canonical_details.append(f"     - {op.method} {op.path} ({op.operation_id}) -> satisfies {op.requirement_ids}")
    elif domain_ctx:
        if domain_ctx.canonical_requirements:
            canonical_details.append(" • Canonical Functional Requirements:")
            for r in domain_ctx.canonical_requirements[:6]:
                canonical_details.append(f"     - [{r.id}] {r.title}: {r.description}")

    canonical_block = "\n" + "\n".join(canonical_details) if canonical_details else ""

    fence = f"""
════════════════════════════════════════════════════════════════════════════════
 🛡️ ARCHITECTURAL DOMAIN GROUNDING & SCOPE BOUNDARY
════════════════════════════════════════════════════════════════════════════════
 CURRENT SYSTEM NAME       : {system_name}
 CURRENT DOMAIN CONTEXT    : {domain_name} ({domain_key or 'default'})
 CURRENT PROBLEM STATEMENT : {problem_statement or 'System requirements as specified in the ARSRS.'}

 ⚠️ CORE GENERATION PRINCIPLES (MANDATORY):
 1. Your architectural knowledge determines HOW the system should be designed.
    The CURRENT Problem Statement and CURRENT ARSRS determine WHAT the system is.
 2. Generate architecture ONLY for the business capabilities explicitly described in
    the CURRENT Problem Statement and CURRENT ARSRS.
 3. The ARSRS represents the requirements of THIS system only.
    Do not introduce requirements, entities, or APIs that are not represented in ARSRS.
 4. Do not introduce business capabilities from other domains.
 5. Do not use previous examples, previous runs, generic industry templates, or unstated
    assumptions to expand the business scope.
 6. If a capability is not described or reasonably implied by the current requirements,
    do not generate it.{canonical_block}
════════════════════════════════════════════════════════════════════════════════
"""
    return fence.strip()


def get_forbidden_domain_concepts(current_domain_key: str) -> Dict[str, Dict[str, Any]]:
    """Backward compatibility helper for cross-artifact validation."""
    from app.sae.utils.domain_lock import DOMAIN_TAXONOMY
    normalized_current = (current_domain_key or "").lower().replace("-", "_").strip()
    forbidden: Dict[str, Dict[str, Any]] = {}
    for dom_key, dom_data in DOMAIN_TAXONOMY.items():
        if dom_key.lower() == normalized_current or normalized_current in dom_key.lower():
            continue
        forbidden[dom_key] = {
            "display_name": dom_data.get("display_name", dom_key),
            "keywords": dom_data.get("keywords", [])[:6],
            "default_actors": [a.get("role") for a in dom_data.get("default_actors", []) if isinstance(a, dict)],
            "modules": dom_data.get("default_modules", [])[:4],
        }
    return forbidden
