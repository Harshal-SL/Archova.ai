import test from "node:test";
import assert from "node:assert/strict";
import {
  buildCorrectionPlan,
  mapValidatorArtifact,
  extractAffectedTarget,
  evaluateEvidenceSufficiency,
  identifyDependencies,
  generateCorrectionInstruction,
} from "../lib/correction-planner.ts";
import type { Finding, Report, ArtifactResult } from "../lib/validator-v2-client.ts";

// Helper to create a minimal valid ArtifactResult
function createArtifactResult(overrides: Partial<ArtifactResult> = {}): ArtifactResult {
  return {
    artifact: "hld",
    score: 80,
    c_score: 100,
    r_score: 80,
    verdict: "ACCEPTED",
    dimensions: [],
    findings: [],
    best_dimension: null,
    weakest_dimension: null,
    reviewer_status: "ok",
    ...overrides,
  };
}

// Helper to create a minimal valid report
function createBaseReport(overrides: Partial<Report> = {}): Report {
  return {
    generation_id: "gen_test_123",
    iterations: [
      {
        n: 1,
        results: {},
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
    final_status: "REJECTED",
    final_scores: { overall: 65, c: 70, r: 60, w: 65, d: 0 },
    model_used: "test-model",
    config_snapshot: {},
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST 1: Critical or high-severity finding with sufficient evidence
// ─────────────────────────────────────────────────────────────────────────────
test("Test 1: Critical or high-severity finding with sufficient evidence", () => {
  const finding: Finding = {
    id: "fnd_crit_01",
    layer: "L1",
    rule_id: "L1-DB-001",
    artifact: "database",
    severity: "critical",
    message: "Missing row-level locking (SELECT FOR UPDATE) on bookings table leading to race conditions.",
    evidence_path: "database.tables.bookings.locking",
    source: "ISO25010",
    suggested_fix: "Add SELECT FOR UPDATE in reservation query.",
  };

  const report = createBaseReport({
    final_status: "REJECTED",
    iterations: [
      {
        n: 1,
        results: {
          database: createArtifactResult({
            artifact: "database",
            score: 50,
            verdict: "REJECTED",
            findings: [finding],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  assert.equal(plan.status, "CORRECTION_NEEDED");
  assert.equal(plan.total_findings, 1);
  assert.equal(plan.actionable_count, 1);
  assert.equal(plan.items_by_severity.critical, 1);

  const item = plan.items[0];
  assert.equal(item.id, "corr_fnd_crit_01");
  assert.equal(item.finding_id, "fnd_crit_01");
  assert.equal(item.severity, "critical");
  assert.equal(item.affected_artifact, "Database LLD");
  assert.equal(item.affected_target, "Table: bookings");
  assert.equal(item.is_supported_by_evidence, true);
  assert.equal(item.is_actionable, true);
  assert.equal(item.requires_manual_review, false);
  assert.ok(item.correction_instruction.includes("L1-DB-001"));
  assert.ok(item.correction_instruction.includes("Add SELECT FOR UPDATE"));
  assert.ok(item.dependencies.some((d) => d.artifact === "Backend LLD" && d.impact_type === "schema"));
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 2: Finding affecting an LLD
// ─────────────────────────────────────────────────────────────────────────────
test("Test 2: Finding affecting an LLD (Backend API Idempotency)", () => {
  const finding: Finding = {
    id: "fnd_lld_02",
    layer: "REVIEW",
    rule_id: "REV-API-004",
    artifact: "backend",
    severity: "high",
    message: "Endpoint /api/v1/payments does not validate Idempotency-Key header for POST operations.",
    evidence_path: "backend.api.endpoints[/api/v1/payments]",
    source: "internal",
    suggested_fix: "Add idempotency middleware with Redis cache.",
  };

  const report = createBaseReport({
    final_status: "REJECTED",
    iterations: [
      {
        n: 1,
        results: {
          backend: createArtifactResult({
            artifact: "backend",
            score: 60,
            verdict: "REJECTED",
            findings: [finding],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  const item = plan.items[0];
  assert.equal(item.affected_artifact, "Backend LLD");
  assert.equal(item.affected_target, "Endpoint: /api/v1/payments");
  assert.ok(item.dependencies.some((d) => d.artifact === "Frontend LLD" && d.impact_type === "interface"));
  assert.equal(item.is_actionable, true);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 3: HLD finding with dependent LLDs
// ─────────────────────────────────────────────────────────────────────────────
test("Test 3: HLD finding with dependent LLDs", () => {
  const finding: Finding = {
    id: "fnd_hld_03",
    layer: "REVIEW",
    rule_id: "REV-HLD-002",
    artifact: "hld",
    severity: "high",
    message: "Service boundary violation: OrderService directly queries PaymentService private database.",
    evidence_path: "hld.major_services[OrderService].boundaries",
    source: "ISO42010",
    suggested_fix: "Decouple services using asynchronous event bus or gRPC API.",
  };

  const report = createBaseReport({
    final_status: "REJECTED",
    iterations: [
      {
        n: 1,
        results: {
          hld: createArtifactResult({
            artifact: "hld",
            score: 55,
            verdict: "REJECTED",
            findings: [finding],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  const item = plan.items[0];
  assert.equal(item.affected_artifact, "HLD");
  assert.equal(item.affected_target, "Service: OrderService");

  // Dependent LLDs must be explicitly identified with architectural reasons
  const backendDep = item.dependencies.find((d) => d.artifact === "Backend LLD");
  const dbDep = item.dependencies.find((d) => d.artifact === "Database LLD");
  assert.ok(backendDep, "Should identify Backend LLD dependency for service boundary change");
  assert.ok(dbDep, "Should identify Database LLD dependency because database isolation is violated");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 4: Finding with insufficient evidence
// ─────────────────────────────────────────────────────────────────────────────
test("Test 4: Finding with insufficient evidence requires clarification / manual review", () => {
  const finding: Finding = {
    id: "fnd_vague_04",
    layer: "REVIEW",
    rule_id: "REV-GEN-099",
    artifact: "hld",
    severity: "medium",
    message: "Architecture lacks general scalability and operational maturity.",
    evidence_path: null, // No path provided
    source: "general",
    suggested_fix: null,
  };

  const report = createBaseReport({
    final_status: "REJECTED",
    iterations: [
      {
        n: 1,
        results: {
          hld: createArtifactResult({
            artifact: "hld",
            score: 65,
            verdict: "REJECTED",
            findings: [finding],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  const item = plan.items[0];
  assert.equal(item.is_supported_by_evidence, false);
  assert.equal(item.requires_manual_review, true);
  assert.ok(item.clarification_needed, "Must explain what clarification is needed");
  assert.ok(item.correction_instruction.includes("MANUAL REVIEW REQUIRED"));
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 5: Report containing no actionable findings
// ─────────────────────────────────────────────────────────────────────────────
test("Test 5: Report containing no actionable findings yields empty state", () => {
  const report = createBaseReport({
    final_status: "ACCEPTED",
    final_scores: { overall: 92, c: 95, r: 90, w: 90, d: 0 },
    iterations: [
      {
        n: 1,
        results: {
          hld: createArtifactResult({
            artifact: "hld",
            score: 92,
            verdict: "ACCEPTED",
            findings: [],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  assert.equal(plan.status, "NO_ACTION_REQUIRED");
  assert.equal(plan.total_findings, 0);
  assert.equal(plan.actionable_count, 0);
  assert.equal(plan.items.length, 0);
  assert.ok(plan.summary.includes("ACCEPTED"));
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 6: ACCEPTED_WITH_WARNINGS report
// ─────────────────────────────────────────────────────────────────────────────
test("Test 6: ACCEPTED_WITH_WARNINGS report treats corrections as advisory without rejecting baseline", () => {
  const finding: Finding = {
    id: "fnd_warn_06",
    layer: "REVIEW",
    rule_id: "REV-OBS-001",
    artifact: "cloud",
    severity: "low",
    message: "Consider adding distributed tracing tags to cloud infrastructure outputs.",
    evidence_path: "cloud.infrastructure.observability",
    source: "best-practice",
    suggested_fix: "Add OpenTelemetry tags to Terraform manifests.",
  };

  const report = createBaseReport({
    final_status: "ACCEPTED_WITH_WARNINGS",
    iterations: [
      {
        n: 1,
        results: {
          cloud: createArtifactResult({
            artifact: "cloud",
            score: 82,
            verdict: "ACCEPTED_WITH_WARNINGS",
            findings: [finding],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  assert.equal(plan.validator_verdict, "ACCEPTED_WITH_WARNINGS");
  assert.ok(plan.summary.includes("ACCEPTED WITH WARNINGS"));
  assert.ok(plan.summary.includes("non-blocking advisory"));
  assert.equal(plan.items.length, 1);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 7: PROVISIONAL report caused by unavailable benchmarking
// ─────────────────────────────────────────────────────────────────────────────
test("Test 7: PROVISIONAL report caused by unavailable benchmarking is distinguished from defective architecture", () => {
  const report = createBaseReport({
    final_status: "PROVISIONAL",
    overall_w: null,
    corpus_status: "unavailable",
    iterations: [
      {
        n: 1,
        results: {
          hld: createArtifactResult({
            artifact: "hld",
            score: 75,
            verdict: "PROVISIONAL",
            findings: [], // No structural findings!
            reviewer_status: "unavailable",
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  assert.equal(plan.status, "PROVISIONAL_STAGE_UNAVAILABLE");
  assert.equal(plan.items.length, 0);
  assert.ok(plan.summary.includes("PROVISIONAL"));
  assert.ok(plan.summary.includes("unavailable"));
  assert.ok(!plan.summary.includes("defective"));
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 8: Failed validation request (null / undefined handling)
// ─────────────────────────────────────────────────────────────────────────────
test("Test 8: Failed validation request returns null without fabricating a plan", () => {
  assert.equal(buildCorrectionPlan(null), null);
  assert.equal(buildCorrectionPlan(undefined), null);
  assert.equal(buildCorrectionPlan({} as any), null);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 9: Duplicate findings do not create duplicate correction items
// ─────────────────────────────────────────────────────────────────────────────
test("Test 9: Duplicate findings do not create duplicate correction items", () => {
  const finding1: Finding = {
    id: "fnd_dup_09",
    layer: "L0",
    rule_id: "L0-DUP-01",
    artifact: "security",
    severity: "medium",
    message: "Missing TLS 1.3 enforcement on API ingress gateway.",
    evidence_path: "security.ingress.tls",
    source: "ASVS",
  };

  const finding2: Finding = {
    ...finding1, // Duplicate finding with exact same ID
  };

  const report = createBaseReport({
    final_status: "REJECTED",
    iterations: [
      {
        n: 1,
        results: {
          security: createArtifactResult({
            artifact: "security",
            score: 65,
            verdict: "REJECTED",
            findings: [finding1, finding2],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  assert.equal(plan.items.length, 1, "Duplicate findings must be deduplicated to exactly 1 item");
  assert.equal(plan.items[0].finding_id, "fnd_dup_09");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 10: Correct mapping of validator artifact identifiers
// ─────────────────────────────────────────────────────────────────────────────
test("Test 10: Correct mapping of all 7 supported artifact identifiers", () => {
  assert.equal(mapValidatorArtifact("arsrs"), "ARSRS");
  assert.equal(mapValidatorArtifact("hld"), "HLD");
  assert.equal(mapValidatorArtifact("backend"), "Backend LLD");
  assert.equal(mapValidatorArtifact("backend_lld"), "Backend LLD");
  assert.equal(mapValidatorArtifact("database"), "Database LLD");
  assert.equal(mapValidatorArtifact("database-lld"), "Database LLD");
  assert.equal(mapValidatorArtifact("frontend"), "Frontend LLD");
  assert.equal(mapValidatorArtifact("security"), "Security LLD");
  assert.equal(mapValidatorArtifact("cloud"), "Cloud LLD");
  assert.equal(mapValidatorArtifact("package", "database.tables.users"), "Database LLD");
  assert.equal(mapValidatorArtifact("system", "backend.endpoints[/health]"), "Backend LLD");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 11: Real-world benchmark findings from multiple reference systems are consolidated
// ─────────────────────────────────────────────────────────────────────────────
test("Test 11: Real-world benchmark findings from multiple reference systems are consolidated without repeating the same LLD", () => {
  const f1: Finding = {
    id: "fnd_rw_01",
    layer: "REAL_WORLD",
    rule_id: "RW-INSTAG-01",
    artifact: "backend",
    severity: "high",
    message: "Missing real-world capability 'Distributed Concurrency Lock' from reference system Instagram Photo Sharing: [Unverified evidence: 'None'] Downgraded to MISSING.",
    source: "Instagram Photo Sharing reference",
  };
  const f2: Finding = {
    id: "fnd_rw_02",
    layer: "REAL_WORLD",
    rule_id: "RW-LINKED-01",
    artifact: "backend",
    severity: "high",
    message: "Missing real-world capability 'Distributed Concurrency Lock' from reference system LinkedIn Social Graph: [Unverified evidence: 'None'] Downgraded to MISSING.",
    source: "LinkedIn Social Graph reference",
  };
  const f3: Finding = {
    id: "fnd_rw_03",
    layer: "REAL_WORLD",
    rule_id: "RW-REDDIT-01",
    artifact: "backend",
    severity: "high",
    message: "Missing real-world capability 'Distributed Concurrency Lock' from reference system Reddit Forum Platform: [Unverified evidence: 'None'] Downgraded to MISSING.",
    source: "Reddit Forum Platform reference",
  };

  const report = createBaseReport({
    final_status: "REJECTED",
    iterations: [
      {
        n: 1,
        results: {
          backend: createArtifactResult({
            artifact: "backend",
            score: 40,
            verdict: "REJECTED",
            findings: [f1, f2, f3],
          }),
        },
        corrections: [],
        started_at: new Date().toISOString(),
      },
    ],
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  assert.equal(plan.items.length, 1, "3 duplicate reference system findings must be consolidated into 1 item for Backend LLD");
  assert.equal(plan.items[0].affected_artifact, "Backend LLD");
  assert.equal(plan.items[0].consolidated_count, 3);
  assert.ok(plan.items[0].reference_systems?.includes("Instagram Photo Sharing"));
  assert.ok(plan.items[0].reference_systems?.includes("LinkedIn Social Graph"));
  assert.ok(plan.items[0].reference_systems?.includes("Reddit Forum Platform"));
  // Ensure no self-dependency: Backend LLD must not depend on Backend LLD
  assert.ok(!plan.items[0].dependencies.some((d) => d.artifact === "Backend LLD"));
});

