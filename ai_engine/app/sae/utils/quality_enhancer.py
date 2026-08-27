"""Backward compatibility module re-exporting quality package constructs from app.sae.quality."""

from app.sae.quality import (
    ArchitectureReviewGenerator,
    DecisionTraceabilityBuilder,
    FieldCompletenessAnalyzer,
    ModelDataEnricher,
    QualityReportGenerator,
    ReferenceArchitectureMatcher,
)

__all__ = [
    "FieldCompletenessAnalyzer",
    "ReferenceArchitectureMatcher",
    "DecisionTraceabilityBuilder",
    "QualityReportGenerator",
    "ArchitectureReviewGenerator",
    "ModelDataEnricher",
]
