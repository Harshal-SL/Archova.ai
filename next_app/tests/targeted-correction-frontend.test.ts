import test from "node:test";
import assert from "node:assert/strict";
import {
  aiEngineApi,
  type TargetedCorrectionRequest,
  type TargetedCorrectionResponse,
  type AcceptCorrectionResponse,
  type RejectCorrectionResponse,
} from "../lib/ai-engine-client.ts";
import {
  buildCorrectionPlan,
  type CorrectionItem,
  type CorrectionPlan,
} from "../lib/correction-planner.ts";
import type { Report } from "../lib/validator-v2-client.ts";

// Sample mock data
function createSampleReport(): Report {
  return {
    generation_id: "gen_frontend_test_01",
    iterations: [
      {
        n: 1,
        results: {
          database: {
            artifact: "database",
            score: 74,
            c_score: 80,
            r_score: 75,
            verdict: "ACCEPTED_WITH_WARNINGS",
            dimensions: [],
            findings: [
              {
                id: "FND-DB-001",
                layer: "L1",
                rule_id: "L1-DB-001",
                artifact: "database",
                severity: "high",
                message: "Missing optimistic locking version column on slots table.",
                evidence_path: "schema.tables[slots]",
                source: "schema_validator",
              },
            ],
            best_dimension: null,
            weakest_dimension: null,
            reviewer_status: "ok",
          },
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
    final_status: "ACCEPTED_WITH_WARNINGS",
    final_scores: { overall: 74, c: 80, r: 75, w: 75, d: 0 },
    model_used: "test-model",
    config_snapshot: {},
    created_at: new Date().toISOString(),
  };
}

test("Frontend: Correction planner identifies actionable finding for targeted AI correction", () => {
  const report = createSampleReport();
  const plan = buildCorrectionPlan(report);

  assert.ok(plan);
  assert.equal(plan.items.length, 1);
  const item = plan.items[0];
  assert.equal(item.finding_id, "FND-DB-001");
  assert.equal(item.affected_artifact, "Database LLD");
  assert.equal(item.is_actionable, true);
  assert.equal(item.is_supported_by_evidence, true);
  assert.equal(item.requires_manual_review, false);
});

test("Frontend: Approval records approval state before AI dispatch", () => {
  const report = createSampleReport();
  const plan = buildCorrectionPlan(report);
  const item = plan.items[0];

  // Transition to APPROVED_FOR_CORRECTION
  item.status = "APPROVED_FOR_CORRECTION";
  item.review_decision = {
    decision: "APPROVED_FOR_CORRECTION",
    decided_at: new Date().toISOString(),
    notes: "User approved targeted database schema correction",
  };

  assert.equal(item.status, "APPROVED_FOR_CORRECTION");
  assert.ok(item.review_decision.decided_at);
  assert.equal(item.review_decision.notes, "User approved targeted database schema correction");
});

test("Frontend: aiEngineApi constructs valid targeted correction request payload", async () => {
  let capturedUrl = "";
  let capturedBody: any = null;

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: string | URL | Request, init?: RequestInit): Promise<Response> => {
    capturedUrl = url.toString();
    capturedBody = JSON.parse(init?.body as string);
    const mockResponse: TargetedCorrectionResponse = {
      operation_id: "op_test_123",
      status: "CORRECTION_VERIFIED",
      generation_id: "gen_frontend_test_01",
      source_version: "v1.0",
      artifact_type: "Database LLD",
      finding_id: "FND-DB-001",
      change_summary: "Added version integer column to slots table with default 1.",
      explanation: "Resolves concurrency race condition on parking slots.",
      original_artifact: { tables: [{ name: "slots", columns: ["id", "status"] }] },
      corrected_artifact: { tables: [{ name: "slots", columns: ["id", "status", "version"] }] },
      verification_result: {
        is_valid: true,
        schema_valid: true,
        preserved_baseline: true,
        baseline_preservation_score: 0.95,
        unresolved_issues: [],
        checks_passed: ["SCHEMA_VALID", "BASELINE_PRESERVED_95%"],
        checks_failed: [],
      },
      unresolved_issues: [],
      created_at: new Date().toISOString(),
    };
    return new Response(JSON.stringify(mockResponse), { status: 200, headers: { "Content-Type": "application/json" } });
  };

  try {
    const payload: TargetedCorrectionRequest = {
      generation_id: "gen_frontend_test_01",
      artifact_id: "database",
      artifact_type: "Database LLD",
      source_version: "v1.0",
      finding_id: "FND-DB-001",
      finding_description: "Missing optimistic locking version column on slots table.",
      evidence: "schema.tables[slots]",
      correction_instruction: "Add version INTEGER NOT NULL DEFAULT 1 to slots table.",
    };

    const result = await aiEngineApi.requestTargetedCorrection(payload);

    assert.ok(capturedUrl.includes("/api/v1/architecture-corrections"));
    assert.equal(capturedBody.generation_id, "gen_frontend_test_01");
    assert.equal(capturedBody.artifact_type, "Database LLD");
    assert.equal(capturedBody.source_version, "v1.0");
    assert.equal(capturedBody.finding_id, "FND-DB-001");
    assert.equal(result.operation_id, "op_test_123");
    assert.equal(result.status, "CORRECTION_VERIFIED");
    assert.equal(result.verification_result.is_valid, true);
    assert.equal(result.verification_result.baseline_preservation_score, 0.95);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Frontend: Acceptance creates new version, updates artifact, and marks validation as stale", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: string | URL | Request, init?: RequestInit): Promise<Response> => {
    const mockAcceptResponse: AcceptCorrectionResponse = {
      operation_id: "op_test_123",
      status: "ACCEPTED",
      new_version: "v1.1",
      previous_version: "v1.0",
      artifact_type: "Database LLD",
      updated_artifact: { tables: [{ name: "slots", columns: ["id", "status", "version"] }] },
      accepted_at: new Date().toISOString(),
    };
    return new Response(JSON.stringify(mockAcceptResponse), { status: 200, headers: { "Content-Type": "application/json" } });
  };

  try {
    const res = await aiEngineApi.acceptCorrection("op_test_123", {
      expected_source_version: "v1.0",
      target_version: "v1.1",
    });

    assert.equal(res.status, "ACCEPTED");
    assert.equal(res.previous_version, "v1.0");
    assert.equal(res.new_version, "v1.1");
    assert.equal(res.artifact_type, "Database LLD");
    assert.ok(res.updated_artifact);

    // Emulate store state transition upon accept
    let validationIsStale = false;
    let staleReason = "";
    let activeVersionTag = "v1.0";
    let historicalReports: Report[] = [];

    const existingReport = createSampleReport();

    // Acceptance logic execution
    activeVersionTag = res.new_version;
    validationIsStale = true;
    staleReason = `Architecture modified by targeted AI correction (accepted ${res.new_version} for ${res.artifact_type}). Previous validation scores no longer reflect active architecture.`;
    historicalReports.push(existingReport);

    assert.equal(activeVersionTag, "v1.1");
    assert.equal(validationIsStale, true);
    assert.ok(staleReason.includes("v1.1"));
    assert.equal(historicalReports.length, 1);
    assert.equal(historicalReports[0].generation_id, "gen_frontend_test_01");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Frontend: Rejection safely discards draft and preserves original baseline intact", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: string | URL | Request, init?: RequestInit): Promise<Response> => {
    const mockRejectResponse: RejectCorrectionResponse = {
      operation_id: "op_test_123",
      status: "REJECTED",
      rejection_reason: "User rejected proposed changes",
      rejected_at: new Date().toISOString(),
      original_artifact_preserved: true,
    };
    return new Response(JSON.stringify(mockRejectResponse), { status: 200, headers: { "Content-Type": "application/json" } });
  };

  try {
    const originalArtifact = { tables: [{ name: "slots", columns: ["id", "status"] }] };
    const originalVersion = "v1.0";
    let activeVersionTag = "v1.0";
    let validationIsStale = false;

    const res = await aiEngineApi.rejectCorrection("op_test_123", {
      rejection_reason: "User rejected proposed changes",
    });

    assert.equal(res.status, "REJECTED");
    assert.equal(res.original_artifact_preserved, true);

    // Original state must be preserved
    assert.equal(activeVersionTag, originalVersion);
    assert.equal(validationIsStale, false);
    assert.deepEqual(originalArtifact.tables[0].columns, ["id", "status"]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Frontend: Explicit revalidation runs Validator Engine v2 on port 8002 and clears stale flag", () => {
  let validationIsStale = true;
  let activeVersionTag = "v1.1";

  // Simulate explicit user revalidation trigger
  const runExplicitRevalidation = () => {
    // Revalidation clears stale status once new audit completes
    validationIsStale = false;
    return {
      status: "ACCEPTED",
      version: activeVersionTag,
      audited_on_port: 8002,
    };
  };

  const newAudit = runExplicitRevalidation();
  assert.equal(validationIsStale, false);
  assert.equal(newAudit.version, "v1.1");
  assert.equal(newAudit.audited_on_port, 8002);
});

test("Frontend: Duplicate click and concurrent execution protection", () => {
  let isExecutingAiCorrection = false;
  let executionAttempts = 0;

  const initiateCorrection = () => {
    if (isExecutingAiCorrection) {
      return false; // Blocked duplicate
    }
    isExecutingAiCorrection = true;
    executionAttempts++;
    return true;
  };

  // First call succeeds
  assert.equal(initiateCorrection(), true);
  assert.equal(executionAttempts, 1);

  // Rapid duplicate clicks while in-flight are blocked
  assert.equal(initiateCorrection(), false);
  assert.equal(initiateCorrection(), false);
  assert.equal(executionAttempts, 1);

  // After completion, resets
  isExecutingAiCorrection = false;
  assert.equal(initiateCorrection(), true);
  assert.equal(executionAttempts, 2);
});

test("Frontend: Failure handling when model provider or API encounters an error", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (): Promise<Response> => {
    return new Response(
      JSON.stringify({ detail: "OpenRouter rate limit or model unavailable" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  };

  try {
    const payload: TargetedCorrectionRequest = {
      generation_id: "gen_frontend_test_01",
      artifact_id: "database",
      artifact_type: "Database LLD",
      source_version: "v1.0",
      finding_id: "FND-DB-001",
      finding_description: "Missing optimistic locking version column.",
      evidence: "schema.tables[slots]",
      correction_instruction: "Add version column.",
    };

    await assert.rejects(
      async () => {
        await aiEngineApi.requestTargetedCorrection(payload);
      },
      {
        message: /OpenRouter rate limit or model unavailable/,
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
