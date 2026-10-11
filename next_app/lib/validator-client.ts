/**
 * Standalone Validator Engine API Client
 * Connects the Next.js frontend directly to the independent Validator Engine (Port 8001).
 */

export const VALIDATOR_HOST = (process.env.NEXT_PUBLIC_VALIDATOR_ENGINE_URL || "http://localhost:8001").trim().replace(/\/+$/, "");
export const VALIDATE_URL = `${VALIDATOR_HOST}/api/v1/validator/validate`;
export const HEALTH_URL = `${VALIDATOR_HOST}/health`;
export const ARCHETYPES_URL = `${VALIDATOR_HOST}/api/v1/validator/archetypes`;

export interface Finding {
  id: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  requirement_id?: string | null;
  affected_component?: string;
  explanation: string;
  evidence?: string;
  recommendation?: string;
}

export interface HardQualityGates {
  structural_quality_gate: boolean;
  requirement_traceability_gate: boolean;
  cross_artifact_alignment_gate: boolean;
  nfr_feasibility_gate: boolean;
  red_team_adversarial_gate: boolean;
  zero_hard_gate_violations?: boolean;
}

export interface Scorecard {
  status: "HEALTHY" | "WARNING" | "CRITICAL_FAILURE" | string;
  overall_composite_score: number;
  structural_completeness: number;
  artifact_quality_score: number;
  consistency_score: number;
  requirement_alignment_score: number;
  production_readiness_score: number;
  traceability_score: number;
  evidence_support_score: number;
  hard_gates: HardQualityGates;
  hard_gates_passed: boolean;
  hard_gate_violations: string[];
  per_section_scores: Record<string, number>;
  quality_indicators: Record<string, any>;
}

export interface TraceabilityItem {
  requirement_id: string;
  title: string;
  category: string;
  satisfied_by_services: string[];
  satisfied_by_endpoints: string[];
  satisfied_by_tables: string[];
  satisfied_by_components: string[];
  status: "FULLY_SATISFIED" | "PARTIALLY_SATISFIED" | "UNSATISFIED" | string;
  notes?: string | null;
}

export interface MatchedArchetype {
  reference_system: string;
  domain: string;
  relevance_reason: string;
  structural_comparison: string;
  supporting_patterns: string[];
  cautionary_failure_modes: string[];
  recommended_guardrails: string[];
}

export interface TradeOffItem {
  reference_system: string;
  pros: string[];
  cons_and_complexities: string[];
}

export interface EvidenceSection {
  is_valid: boolean;
  has_evidence: boolean;
  score: number;
  evidence_quality_score: number;
  primary_archetype: string;
  matched_systems: any[];
  matched_archetypes: MatchedArchetype[];
  trade_off_analysis: TradeOffItem[];
  key_insights: string[];
  findings: Finding[];
}

export interface DecisionProvenance {
  decision_id: string;
  topic: string;
  decision_title: string;
  decision_type: string;
  chosen_option: string;
  selected_option?: string;
  rationale: string;
  why_chosen: string;
  traced_requirements: string[];
  driving_requirements?: string[];
  driving_constraints?: string[];
  trade_offs_considered: string[];
  rejected_alternatives: string[];
  real_world_precedent: string;
  supporting_real_world_evidence?: string;
  validation_status: "VALIDATED" | "WARNING" | "UNSUPPORTED" | string;
}

export interface RemediationAction {
  action_id: string;
  priority: "P0" | "P1" | "P2" | string;
  finding_id: string;
  category: string;
  severity: string;
  target_component: string;
  target_artifact?: string;
  issue_summary?: string;
  title?: string;
  description?: string;
  recommendation: string;
  revalidation_criteria?: string;
  recommended_patch?: Record<string, any>;
}

export interface RemediationSection {
  verdict: "APPROVED" | "NEEDS_REMEDIATION" | "REJECTED" | string;
  total_findings: number;
  total_findings_count: number;
  critical_findings_count: number;
  affected_components: string[];
  actions: RemediationAction[];
  remediation_actions?: RemediationAction[];
  suggested_patches?: Record<string, any>;
  remediation_summary?: string;
}

export interface ValidatedArchitectureResponse {
  architecture: Record<string, any>;
  validation: {
    status: string;
    summary: {
      overall_score: number;
      verdict: "APPROVED" | "NEEDS_REMEDIATION" | "REJECTED" | string;
      total_findings_count: number;
      critical_findings_count: number;
      high_findings_count: number;
      medium_findings_count: number;
      low_findings_count: number;
      is_valid: boolean;
    };
    scorecard: Scorecard;
    structural_validation: {
      is_valid: boolean;
      score: number;
      missing_sections: string[];
      malformed_elements: string[];
      placeholder_items: string[];
      orphan_components: string[];
      findings: Finding[];
      details?: Record<string, any>;
    };
    requirement_alignment: {
      is_valid: boolean;
      is_aligned: boolean;
      score: number;
      alignment_score: number;
      total_requirements: number;
      covered_requirements_count: number;
      uncovered_requirements_count: number;
      traceability_ratio: number;
      traceability_matrix: TraceabilityItem[];
      findings: Finding[];
    };
    cross_artifact_consistency: {
      is_valid: boolean;
      is_consistent: boolean;
      score: number;
      consistency_score: number;
      hld_to_backend_alignment: number;
      backend_to_database_alignment: number;
      frontend_to_backend_alignment: number;
      security_to_backend_alignment: number;
      cloud_to_architecture_alignment: number;
      inconsistencies: string[];
      findings: Finding[];
    };
    nfr_validation: {
      is_valid: boolean;
      score: number;
      feasibility_score: number;
      total_nfrs: number;
      supported_nfrs_count: number;
      nfr_assessments: Array<{
        nfr_id: string;
        category: string;
        description: string;
        status: "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED" | string;
        primary_artifact: string;
        detected_mechanisms: string[];
        gap_reason?: string;
        recommendation?: string;
      }>;
      findings: Finding[];
    };
    red_team_review: {
      is_valid: boolean;
      score: number;
      verdict: string;
      review_status: string;
      single_points_of_failure: string[];
      scalability_bottlenecks: string[];
      untested_assumptions: string[];
      unresolved_risks: string[];
      security_vulnerabilities: string[];
      production_readiness_verdict: string;
      findings: Finding[];
    };
    findings: Finding[];
  };
  evidence: EvidenceSection;
  explainability: {
    decisions_provenance: DecisionProvenance[];
    architecture_overview_rationale?: string;
  };
  remediation: RemediationSection;
  metadata: {
    validator_version: string;
    package_id: string;
    system_name: string;
    domain: string;
    validated_at: string;
    input_fingerprint?: string;
    execution_duration_ms: number;
  };
  is_fully_validated?: boolean;
  attempt?: number;
  max_retries?: number;
  correction_history?: CorrectionAttempt[];
}

export interface CorrectionAttempt {
  attempt: number;
  timestamp: string;
  findings_count_before: number;
  findings_count_after: number;
  resolved_issue_ids: string[];
  unresolved_issue_ids: string[];
  regenerated_artifacts: string[];
  summary: string;
  issues_detected_count?: number;
  affected_artifacts?: string[];
  changes_applied?: Record<string, any>;
  subsequent_validation_passed?: boolean;
}

export const validatorApi = {
  // 1. Health check
  async checkHealth(): Promise<{ ok: boolean; version?: string }> {
    try {
      const res = await fetch(HEALTH_URL, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        return { ok: true, version: data?.version || "1.0.0" };
      }
      return { ok: false };
    } catch {
      return { ok: false };
    }
  },

  // 2. Validate Architecture Package
  async validate(
    packagePayload: Record<string, any>,
    attempt = 1,
    maxRetries = 2
  ): Promise<ValidatedArchitectureResponse> {
    const res = await fetch(`${VALIDATE_URL}?attempt=${attempt}&max_retries=${maxRetries}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(packagePayload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Validator error (${res.status})`);
    }
    return data as ValidatedArchitectureResponse;
  },

  // 3. Get Structured Correction Feedback
  async getFeedback(packagePayload: Record<string, any>, attempt = 1): Promise<any> {
    const res = await fetch(`${VALIDATOR_HOST}/api/v1/validator/feedback?attempt=${attempt}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(packagePayload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Feedback error (${res.status})`);
    }
    return data;
  },

  // 4. List Knowledge Archetypes
  async listArchetypes(): Promise<any[]> {
    try {
      const res = await fetch(ARCHETYPES_URL, { cache: "no-store" });
      if (res.ok) {
        return await res.json();
      }
      return [];
    } catch {
      return [];
    }
  },
};

