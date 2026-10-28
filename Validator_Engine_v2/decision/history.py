"""Iteration History and Finding Diffing.

Diffs finding IDs and real-world pattern statuses between iterations to compute:
- resolved finding IDs
- unresolved finding IDs
- new finding IDs
- patterns_resolved vs patterns_still_missing
- score delta (score_before vs score_after)
"""

from __future__ import annotations

from typing import Dict, List, Optional
from Validator_Engine_v2.schemas import ArtifactResult, Correction, Iteration


def diff_iteration_corrections(
    prev_iteration: Optional[Iteration],
    curr_results: Dict[str, ArtifactResult],
    regenerated_artifacts: List[str],
    regenerated_with_feedback: bool = True,
) -> List[Correction]:
    """Compute correction records for artifacts regenerated between iterations."""
    corrections: List[Correction] = []

    if not prev_iteration:
        return corrections

    for art in regenerated_artifacts:
        prev_res = prev_iteration.results.get(art)
        curr_res = curr_results.get(art)

        if not prev_res or not curr_res:
            continue

        prev_finding_ids = {f.id for f in prev_res.findings}
        curr_finding_ids = {f.id for f in curr_res.findings}

        resolved = sorted(list(prev_finding_ids - curr_finding_ids))
        unresolved = sorted(list(prev_finding_ids & curr_finding_ids))
        new_findings = sorted(list(curr_finding_ids - prev_finding_ids))

        # Real-World pattern diffing
        patterns_resolved: List[str] = []
        patterns_still_missing: List[str] = []

        if prev_res.real_world and curr_res.real_world:
            prev_patterns = {a.pattern_id: a.status for a in prev_res.real_world.assessments}
            curr_patterns = {a.pattern_id: a.status for a in curr_res.real_world.assessments}

            for p_id, p_prev_st in prev_patterns.items():
                if p_prev_st in ("MISSING", "PARTIAL"):
                    p_curr_st = curr_patterns.get(p_id, "MISSING")
                    if p_curr_st in ("ALIGNED", "JUSTIFIED_DIVERGENCE"):
                        patterns_resolved.append(p_id)
                    elif p_curr_st in ("MISSING", "PARTIAL"):
                        patterns_still_missing.append(p_id)

        action_summary = (
            f"Regenerated '{art}' (attempt {prev_iteration.n + 1}): "
            f"resolved {len(resolved)} defect(s), {len(unresolved)} remaining, {len(new_findings)} new."
        )

        corrections.append(
            Correction(
                artifact=art,
                triggered_by=sorted(list(prev_finding_ids)),
                action_summary=action_summary,
                score_before=prev_res.score,
                score_after=curr_res.score,
                resolved=resolved,
                unresolved=unresolved,
                new_findings=new_findings,
                regenerated_with_feedback=regenerated_with_feedback,
                patterns_resolved=sorted(patterns_resolved),
                patterns_still_missing=sorted(patterns_still_missing),
            )
        )

    return corrections
