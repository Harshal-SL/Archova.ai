"""Scoring entrypoint and re-export module for Validator Engine v2.

Authoritative Specification:
Formula:
  Normal:         S = 0.20*C + 0.45*R + 0.35*W - D
  Low Confidence: S = 0.20*C + 0.65*R + 0.15*W - D

Where:
  C = Structural and Technical Correctness (0-100), calculated from Phase 1 & 2 checks.
  R = Architecture Quality Review (0-100), calculated from weighted 0-5 rubric dimensions.
  W = Real-World Architecture Suitability (0-100), calculated from applicable benchmark patterns.
  D = Additional verified defect penalties (0-100), avoiding double-counting.
"""

from Validator_Engine_v2.decision.scoring import (
    compute_artifact_score,
)

__all__ = [
    "compute_artifact_score",
]
