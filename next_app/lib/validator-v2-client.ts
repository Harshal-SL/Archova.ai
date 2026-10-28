/**
 * Validator Engine v2 Client.
 * Communicates with Validator Engine v2 (FastAPI port 8002).
 */

export interface Finding {
  id: string;
  layer: "L0" | "L1" | "REVIEW" | "REAL_WORLD";
  rule_id: string;
  artifact: string;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
  evidence_path: string | null;
  source: string;
  suggested_fix?: string | null;
}

export interface DimensionScore {
  id: string;
  label: string;
  weight: number;
  score: number; // 0-5
  evidence_path?: string | null;
  missing: string[];
  rationale: string;
}

export interface ReferenceSystemUsed {
  id: string;
  system_name: string;
  match_reasons: string[];
  scale_note?: string | null;
  sources: string[];
}

export interface PatternAssessment {
  pattern_id: string;
  system_name: string;
  pattern_name: string;
  category: string;
  priority: number; // 1-3
  status: "ALIGNED" | "PARTIAL" | "MISSING" | "JUSTIFIED_DIVERGENCE" | "NOT_APPLICABLE";
  evidence_path?: string | null;
  justification: string;
  requirement_refs: string[];
}

export interface RealWorldResult {
  artifact: string;
  score: number | null;
  confidence: "normal" | "low" | "unavailable";
  counts: {
    aligned: number;
    partial: number;
    missing: number;
    justified_divergence: number;
    not_applicable: number;
    downgraded_unverified: number;
  };
  assessments: PatternAssessment[];
  references_used: ReferenceSystemUsed[];
}

export interface ArtifactResult {
  artifact: string;
  score: number; // 0-100 (composite score S)
  final_score?: number;
  c_score?: number; // Phase 1 & 2: Structural and Technical Correctness (0-100)
  r_score?: number; // Phase 3: Architecture Quality Review (0-100)
  w_score?: number | null; // Phase 4: Real-World Architecture Suitability (0-100)
  penalty_d?: number; // Additional verified defect penalties
  rubric_score?: number;
  real_world?: RealWorldResult | null;
  verdict: "ACCEPTED" | "ACCEPTED_WITH_WARNINGS" | "REJECTED" | "PROVISIONAL";
  dimensions: DimensionScore[];
  findings: Finding[];
  best_dimension: string | null;
  weakest_dimension: string | null;
  reviewer_status: "ok" | "unavailable" | "partial";
  dropped_unverified?: number;
  truncated?: boolean;
}

export interface Correction {
  artifact: string;
  triggered_by: string[];
  action_summary: string;
  score_before: number;
  score_after: number;
  resolved: string[];
  unresolved: string[];
  new_findings: string[];
  patterns_resolved?: string[];
  patterns_still_missing?: string[];
  regenerated_with_feedback: boolean;
}

export interface Iteration {
  n: number;
  results: Record<string, ArtifactResult>;
  corrections: Correction[];
  started_at: string;
  finished_at?: string | null;
}

export interface Report {
  generation_id: string;
  iterations: Iteration[];
  final_status: "ACCEPTED" | "ACCEPTED_WITH_WARNINGS" | "REJECTED" | "PROVISIONAL" | "UNRESOLVED";
  final_scores: Record<string, any>;
  overall_c?: number;
  overall_r?: number;
  overall_w?: number | null;
  overall_d?: number;
  model_used: string;
  reviewer_mode?: "live" | "mock";
  corpus_status?: string;
  references_used?: ReferenceSystemUsed[];
  config_snapshot: Record<string, any>;
  created_at: string;
}

export interface PipelineStatus {
  generation_id: string;
  state: "idle" | "running" | "completed" | "failed";
  current_step: string;
  iteration: number;
  error?: string | null;
}

export interface ReportWithPackage {
  report: Report;
  final_package: Record<string, any>;
}

const VALIDATOR_V2_BASE_URL =
  process.env.NEXT_PUBLIC_VALIDATOR_V2_URL || "http://localhost:8002";

export const validatorV2Client = {
  baseUrl: VALIDATOR_V2_BASE_URL,

  async runPipeline(
    generationId: string,
    packagePayload?: Record<string, any>
  ): Promise<{ generation_id: string; status: string }> {
    const res = await fetch(`${this.baseUrl}/v1/pipeline/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        generation_id: generationId,
        package: packagePayload,
      }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to start pipeline: ${res.status} ${errText}`);
    }
    return res.json();
  },

  async getStatus(generationId: string): Promise<PipelineStatus> {
    const res = await fetch(`${this.baseUrl}/v1/pipeline/${generationId}/status`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to get pipeline status: ${res.status} ${errText}`);
    }
    return res.json();
  },

  async getReport(generationId: string): Promise<ReportWithPackage> {
    const res = await fetch(`${this.baseUrl}/v1/reports/${generationId}`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to fetch validation report: ${res.status} ${errText}`);
    }
    const data = await res.json();
    return {
      report: data.report || data,
      final_package: data.final_package || data,
    };
  },

  async pollPipeline(
    generationId: string,
    onProgress?: (status: PipelineStatus) => void,
    intervalMs = 2000,
    maxWaitMs = 600000
  ): Promise<ReportWithPackage> {
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitMs) {
      const st = await this.getStatus(generationId);
      if (onProgress) {
        onProgress(st);
      }
      if (st.state === "completed") {
        return await this.getReport(generationId);
      }
      if (st.state === "failed") {
        throw new Error(st.error || "Validation pipeline failed");
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
    throw new Error(`Pipeline polling timed out after ${maxWaitMs / 1000}s`);
  },

  async directValidate(packagePayload: Record<string, any>): Promise<Report> {
    const res = await fetch(`${this.baseUrl}/v1/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(packagePayload),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Direct validation failed: ${res.status} ${errText}`);
    }
    return res.json();
  },

  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/health`);
      return res.ok;
    } catch {
      return false;
    }
  },
};
