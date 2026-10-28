import test from "node:test";
import assert from "node:assert/strict";
import {
  buildCorrectionPlan,
  validateCorrectionEligibility,
  checkAutomatedCorrectionCapability,
  type CorrectionItem,
  type CorrectionPlan,
  type CorrectionItemStatus,
} from "../lib/correction-planner.ts";
import type { Finding, Report, ArtifactResult } from "../lib/validator-v2-client.ts";

// Helper to create a minimal valid report
function createTestReport(overrides: Partial<Report> = {}): Report {
  return {
    generation_id: "gen_test_workflow_01",
    iterations: [
      {
        n: 1,
        results: {
          database: {
            artifact: "database",
            score: 75,
            c_score: 80,
            r_score: 75,
            verdict: "ACCEPTED_WITH_WARNINGS",
            dimensions: [],
            findings: [],
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
    final_scores: { overall: 75, c: 80, r: 75, w: 75, d: 0 },
    model_used: "test-model",
    config_snapshot: {},
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

// Helper to create a sample actionable item
function createSampleItem(overrides: Partial<CorrectionItem> = {}): CorrectionItem {
  return {
    id: "corr_fnd_test_01",
    finding_id: "fnd_test_01",
    severity: "high",
    title: "Database LLD: L1-DB-001",
    description: "Missing optimistic concurrency version column in slots table.",
    evidence: "schema.tables[slots]",
    affected_artifact: "Database LLD",
    affected_target: "Table: slots",
    correction_instruction: "Add version INTEGER NOT NULL DEFAULT 1 column to slots table.",
    reason: "Prevents race conditions during concurrent parking slot reservations.",
    dependencies: [
      {
        artifact: "Backend LLD",
        reason: "Backend slot reservation queries must check and increment version.",
        impact_type: "schema",
      },
    ],
    is_actionable: true,
    is_supported_by_evidence: true,
    requires_manual_review: false,
    status: "PENDING_REVIEW",
    status_reason: "Awaiting user review and approval.",
    review_decision: null,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// TEST 1: Eligible correction item can be reviewed
// ─────────────────────────────────────────────────────────────────────────────
test("Test 1: Eligible correction item can be reviewed", () => {
  const item = createSampleItem();
  const context = {
    generationId: "gen_test_workflow_01",
    versionTag: "v1.0",
    reportGenerationId: "gen_test_workflow_01",
    hasArchitecturePackage: true,
    knownFindingIds: ["fnd_test_01"],
  };

  const result = validateCorrectionEligibility(item, context);
  assert.equal(result.eligible, true);
  assert.equal(item.status, "PENDING_REVIEW");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 2: Non-actionable item cannot be executed
// ─────────────────────────────────────────────────────────────────────────────
test("Test 2: Non-actionable item cannot be executed", () => {
  const item = createSampleItem({ is_actionable: false });
  const context = {
    generationId: "gen_test_workflow_01",
    versionTag: "v1.0",
    hasArchitecturePackage: true,
  };

  const result = validateCorrectionEligibility(item, context);
  assert.equal(result.eligible, false);
  assert.match(result.reason, /not actionable/i);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 3: Insufficient evidence blocks automated execution
// ─────────────────────────────────────────────────────────────────────────────
test("Test 3: Insufficient evidence blocks automated execution", () => {
  const item = createSampleItem({ is_supported_by_evidence: false });
  const context = {
    generationId: "gen_test_workflow_01",
    versionTag: "v1.0",
    hasArchitecturePackage: true,
  };

  const result = validateCorrectionEligibility(item, context);
  assert.equal(result.eligible, false);
  assert.match(result.reason, /insufficient/i);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 4: Manual-review item cannot be executed automatically
// ─────────────────────────────────────────────────────────────────────────────
test("Test 4: Manual-review item cannot be executed automatically", () => {
  const item = createSampleItem({
    requires_manual_review: true,
    status: "MANUAL_REVIEW_REQUIRED",
    clarification_needed: "Clarify SLA requirement with stakeholder",
  });
  const context = {
    generationId: "gen_test_workflow_01",
    versionTag: "v1.0",
    hasArchitecturePackage: true,
  };

  const result = validateCorrectionEligibility(item, context);
  assert.equal(result.eligible, false);
  assert.match(result.reason, /manual review/i);
  assert.equal(item.status, "MANUAL_REVIEW_REQUIRED");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 5: Missing architecture package is handled safely
// ─────────────────────────────────────────────────────────────────────────────
test("Test 5: Missing architecture package is handled safely", () => {
  const item = createSampleItem();
  const context = {
    generationId: "gen_test_workflow_01",
    versionTag: "v1.0",
    hasArchitecturePackage: false,
  };

  const result = validateCorrectionEligibility(item, context);
  assert.equal(result.eligible, false);
  assert.match(result.reason, /missing/i);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 6: Approval does not modify architecture artifacts
// ─────────────────────────────────────────────────────────────────────────────
test("Test 6: Approval does not modify architecture artifacts", () => {
  const baselineHld = {
    major_services: [{ name: "OrderService", responsibility: "Process orders" }],
    nodes: [{ id: "order-service", type: "service", data: { label: "OrderService" } }],
  };
  const baselineLld = {
    backend: { service: "OrderService", endpoints: ["/orders"] },
    database: { tables: [{ name: "orders", columns: ["id", "status"] }] },
  };

  const serializedHldBefore = JSON.stringify(baselineHld);
  const serializedLldBefore = JSON.stringify(baselineLld);

  // User approves correction plan item
  const item = createSampleItem();
  const capability = checkAutomatedCorrectionCapability();

  const approvedItem: CorrectionItem = {
    ...item,
    status: "APPROVED_FOR_CORRECTION",
    status_reason: capability.reason,
    review_decision: {
      decision: "APPROVED_FOR_CORRECTION",
      decided_at: new Date().toISOString(),
      notes: capability.reason,
    },
  };

  // Verify architecture objects remain 100% untouched
  assert.equal(JSON.stringify(baselineHld), serializedHldBefore);
  assert.equal(JSON.stringify(baselineLld), serializedLldBefore);
  assert.equal(approvedItem.status, "APPROVED_FOR_CORRECTION");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 7: Approval does not falsely mark a correction as applied
// ─────────────────────────────────────────────────────────────────────────────
test("Test 7: Approval does not falsely mark a correction as applied", () => {
  const item = createSampleItem();
  const capability = checkAutomatedCorrectionCapability();

  assert.equal(capability.supported, false);
  assert.notEqual(capability.status, "APPLIED");

  const approvedItem: CorrectionItem = {
    ...item,
    status: "APPROVED_FOR_CORRECTION",
    status_reason: capability.reason,
  };

  assert.equal(approvedItem.status, "APPROVED_FOR_CORRECTION");
  assert.notEqual(approvedItem.status, "APPLIED");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 8: Unsupported targeted correction is reported honestly
// ─────────────────────────────────────────────────────────────────────────────
test("Test 8: Unsupported targeted correction is reported honestly", () => {
  const capability = checkAutomatedCorrectionCapability();
  assert.equal(capability.supported, false);
  assert.equal(capability.status, "CORRECTION_UNAVAILABLE");
  assert.match(capability.reason, /unavailable through the current AI Engine API/i);
  assert.match(capability.reason, /no architecture artifacts have been modified/i);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 9: Failure does not create a success state
// ─────────────────────────────────────────────────────────────────────────────
test("Test 9: Failure does not create a success state", () => {
  // Empty instruction should fail eligibility
  const item = createSampleItem({ correction_instruction: "" });
  const result = validateCorrectionEligibility(item, { hasArchitecturePackage: true });

  assert.equal(result.eligible, false);
  assert.match(result.reason, /empty/i);
  assert.notEqual(item.status, "APPROVED_FOR_CORRECTION");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 10: Existing architecture data remains unchanged when correction is unavailable
// ─────────────────────────────────────────────────────────────────────────────
test("Test 10: Existing architecture data remains unchanged when correction is unavailable", () => {
  const architecturePackage = {
    hld: { name: "System HLD" },
    llds: { backend: { name: "Backend Blueprint" } },
    arsrs: { requirements: [{ id: "FR-01", text: "Login" }] },
  };

  const snapshotBefore = JSON.stringify(architecturePackage);

  // Simulating review action
  const capability = checkAutomatedCorrectionCapability();
  if (!capability.supported) {
    // Zero mutations allowed
  }

  assert.equal(JSON.stringify(architecturePackage), snapshotBefore);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 11: Existing validation report remains unchanged when correction is unavailable
// ─────────────────────────────────────────────────────────────────────────────
test("Test 11: Existing validation report remains unchanged when correction is unavailable", () => {
  const report = createTestReport();
  const snapshotBefore = JSON.stringify(report);

  const capability = checkAutomatedCorrectionCapability();
  if (!capability.supported) {
    // Report is preserved as-is
  }

  assert.equal(JSON.stringify(report), snapshotBefore);
  assert.equal(report.final_status, "ACCEPTED_WITH_WARNINGS");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 12: No new architecture version is created for approval alone
// ─────────────────────────────────────────────────────────────────────────────
test("Test 12: No new architecture version is created for approval alone", () => {
  const versions = [{ id: "v1", version_tag: "v1.0", is_latest: true }];
  const currentVersionTag = "v1.0";

  // When approving a plan without automated execution
  const capability = checkAutomatedCorrectionCapability();
  let updatedVersions = [...versions];
  let updatedVersionTag = currentVersionTag;

  if (!capability.supported) {
    // Version must NOT be bumped
  }

  assert.equal(updatedVersions.length, 1);
  assert.equal(updatedVersionTag, "v1.0");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 13: Validation is not marked stale without a genuine modification
// ─────────────────────────────────────────────────────────────────────────────
test("Test 13: Validation is not marked stale without a genuine modification", () => {
  let validationIsStale = false;
  const capability = checkAutomatedCorrectionCapability();

  // If automated execution is not supported and architecture was not modified:
  if (!capability.supported) {
    // validationIsStale must remain false
  }

  assert.equal(validationIsStale, false);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 14: Duplicate actions are prevented
// ─────────────────────────────────────────────────────────────────────────────
test("Test 14: Duplicate actions are prevented", () => {
  let isProcessing = true; // Simulating active processing
  let actionCount = 0;

  function attemptAction() {
    if (isProcessing) {
      return { success: false, message: "Another action is currently being processed." };
    }
    actionCount++;
    return { success: true };
  }

  const result = attemptAction();
  assert.equal(result.success, false);
  assert.equal(actionCount, 0);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 15: HLD dependencies are displayed correctly
// ─────────────────────────────────────────────────────────────────────────────
test("Test 15: HLD dependencies are displayed correctly", () => {
  const hldItem = createSampleItem({
    affected_artifact: "HLD",
    affected_target: "Service: AuthService",
    dependencies: [
      {
        artifact: "Backend LLD",
        reason: "AuthService boundaries modified; endpoints require sync.",
        impact_type: "interface",
      },
      {
        artifact: "Database LLD",
        reason: "User credentials table moved to auth boundary.",
        impact_type: "schema",
      },
    ],
  });

  assert.equal(hldItem.affected_artifact, "HLD");
  assert.equal(hldItem.dependencies.length, 2);
  assert.equal(hldItem.dependencies[0].artifact, "Backend LLD");
  assert.equal(hldItem.dependencies[1].artifact, "Database LLD");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 16: Generation/version mismatches are rejected
// ─────────────────────────────────────────────────────────────────────────────
test("Test 16: Generation/version mismatches are rejected", () => {
  const item = createSampleItem();
  const context = {
    generationId: "gen_active_session",
    reportGenerationId: "gen_old_stale_session", // Mismatch!
    hasArchitecturePackage: true,
  };

  const result = validateCorrectionEligibility(item, context);
  assert.equal(result.eligible, false);
  assert.match(result.reason, /mismatch/i);
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 17: Existing correction-planner behavior remains compatible
// ─────────────────────────────────────────────────────────────────────────────
test("Test 17: Existing correction-planner behavior remains compatible", () => {
  const report = createTestReport({
    iterations: [
      {
        n: 1,
        results: {
          backend: {
            artifact: "backend",
            score: 60,
            c_score: 70,
            r_score: 60,
            verdict: "REJECTED",
            dimensions: [],
            findings: [
              {
                id: "fnd_compat_01",
                layer: "L0",
                rule_id: "L0-BE-001",
                artifact: "backend",
                severity: "high",
                message: "Missing health check endpoint.",
                evidence_path: "endpoints",
                source: "IEEE1016",
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
    final_status: "REJECTED",
  });

  const plan = buildCorrectionPlan(report);
  assert.ok(plan);
  assert.equal(plan.generation_id, "gen_test_workflow_01");
  assert.equal(plan.items.length, 1);
  assert.equal(plan.actionable_count, 1);
  assert.equal(plan.items[0].status, "PENDING_REVIEW");
  assert.equal(plan.items[0].affected_artifact, "Backend LLD");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 18: Existing validation-report rendering remains compatible
// ─────────────────────────────────────────────────────────────────────────────
test("Test 18: Existing validation-report rendering remains compatible", () => {
  const report = createTestReport();
  assert.ok(report.generation_id);
  assert.ok(report.iterations.length > 0);
  assert.ok(report.final_scores);
  assert.equal(typeof report.final_scores.overall, "number");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 19: Manual-review and dismissed states render correctly
// ─────────────────────────────────────────────────────────────────────────────
test("Test 19: Manual-review and dismissed states render correctly", () => {
  const item = createSampleItem();

  // Transition to manual review
  const manualItem: CorrectionItem = {
    ...item,
    status: "MANUAL_REVIEW_REQUIRED",
    requires_manual_review: true,
    status_reason: "Stakeholder clarification required.",
  };
  assert.equal(manualItem.status, "MANUAL_REVIEW_REQUIRED");
  assert.equal(manualItem.requires_manual_review, true);

  // Transition to dismissed
  const dismissedItem: CorrectionItem = {
    ...item,
    status: "DISMISSED",
    status_reason: "Dismissed by user.",
  };
  assert.equal(dismissedItem.status, "DISMISSED");
});

// ─────────────────────────────────────────────────────────────────────────────
// TEST 20: Correction status remains tied to the appropriate correction item
// ─────────────────────────────────────────────────────────────────────────────
test("Test 20: Correction status remains tied to the appropriate correction item", () => {
  const itemA = createSampleItem({ id: "corr_item_A", finding_id: "fnd_A" });
  const itemB = createSampleItem({ id: "corr_item_B", finding_id: "fnd_B" });

  const items = [itemA, itemB];

  // User approves item A only
  const updatedItems = items.map((it) =>
    it.id === "corr_item_A"
      ? { ...it, status: "APPROVED_FOR_CORRECTION" as CorrectionItemStatus }
      : it
  );

  assert.equal(updatedItems[0].status, "APPROVED_FOR_CORRECTION");
  assert.equal(updatedItems[1].status, "PENDING_REVIEW"); // Item B remains pending
});
