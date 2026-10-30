/**
 * Evidence-Based Architecture Correction Planner (Part 2.1).
 *
 * Transforms Validator Engine v2 reports into a structured, typed,
 * evidence-grounded correction plan without executing artifact regeneration.
 */

import type { Finding, Report, ArtifactResult } from "./validator-v2-client";

export type SupportedArtifact =
  | "ARSRS"
  | "HLD"
  | "Backend LLD"
  | "Database LLD"
  | "Frontend LLD"
  | "Security LLD"
  | "Cloud LLD";

export type ImpactType =
  | "interface"
  | "schema"
  | "protocol"
  | "security_boundary"
  | "infrastructure"
  | "reference";

export type CorrectionItemStatus =
  | "PENDING_REVIEW"
  | "APPROVED_FOR_CORRECTION"
  | "MANUAL_REVIEW_REQUIRED"
  | "DISMISSED"
  | "CORRECTION_UNAVAILABLE"
  | "CORRECTION_FAILED"
  | "APPLIED";

export interface CorrectionDependency {
  artifact: SupportedArtifact;
  reason: string;
  impact_type: ImpactType;
}

export interface CorrectionItem {
  id: string; // Unique correction item ID, e.g. "corr_fnd_xxx"
  finding_id: string; // Original validator finding ID
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  description: string;
  evidence: string | null; // Evidence supporting finding (evidence_path or snippet)
  affected_artifact: SupportedArtifact;
  affected_target: string | null; // Specific component, service, interface, db table, etc.
  correction_instruction: string; // Specific, localized instruction for AI Engine
  reason: string; // Rationale explaining why correction is necessary
  dependencies: CorrectionDependency[]; // Specific affected dependent artifacts
  is_actionable: boolean; // True if finding has clear actionable defect
  is_supported_by_evidence: boolean; // True if evidence is sufficient to formulate safe correction
  requires_manual_review: boolean; // True if evidence is insufficient or ambiguous
  clarification_needed?: string | null; // Details on what clarification is required
  status: CorrectionItemStatus; // Current review or execution status
  status_reason?: string | null; // Explanation of the current status
  reference_systems?: string[]; // Optional benchmark reference systems consolidated for this item
  consolidated_count?: number; // Number of redundant/benchmark findings consolidated into this item
  review_decision?: {
    decided_at: string;
    decision: CorrectionItemStatus;
    notes?: string;
    generation_id?: string;
    version_tag?: string;
  } | null;
}

export type CorrectionPlanStatus =
  | "NO_ACTION_REQUIRED"
  | "CORRECTION_NEEDED"
  | "MANUAL_REVIEW_REQUIRED"
  | "PROVISIONAL_STAGE_UNAVAILABLE";

export interface CorrectionPlan {
  id: string; // Unique plan ID
  generation_id: string;
  created_at: string;
  validator_verdict: "ACCEPTED" | "ACCEPTED_WITH_WARNINGS" | "REJECTED" | "PROVISIONAL" | "UNRESOLVED";
  total_findings: number;
  actionable_count: number;
  requires_review_count: number;
  items_by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  items: CorrectionItem[];
  summary: string;
  status: CorrectionPlanStatus;
}

/**
 * Explicit, tested mapping of validator artifact identifiers to SupportedArtifact.
 */
export const VALIDATOR_ARTIFACT_MAP: Record<string, SupportedArtifact> = {
  // Lowercase standard
  hld: "HLD",
  backend: "Backend LLD",
  database: "Database LLD",
  frontend: "Frontend LLD",
  security: "Security LLD",
  cloud: "Cloud LLD",
  arsrs: "ARSRS",

  // Hyphenated and underscored variants
  "backend-lld": "Backend LLD",
  backend_lld: "Backend LLD",
  "database-lld": "Database LLD",
  database_lld: "Database LLD",
  "frontend-lld": "Frontend LLD",
  frontend_lld: "Frontend LLD",
  "security-lld": "Security LLD",
  security_lld: "Security LLD",
  "cloud-lld": "Cloud LLD",
  cloud_lld: "Cloud LLD",

  // Capitalized variants
  HLD: "HLD",
  BACKEND: "Backend LLD",
  DATABASE: "Database LLD",
  FRONTEND: "Frontend LLD",
  SECURITY: "Security LLD",
  CLOUD: "Cloud LLD",
  ARSRS: "ARSRS",
  "Backend LLD": "Backend LLD",
  "Database LLD": "Database LLD",
  "Frontend LLD": "Frontend LLD",
  "Security LLD": "Security LLD",
  "Cloud LLD": "Cloud LLD",
};

/**
 * Maps a raw validator artifact string to a canonical SupportedArtifact.
 * Falls back to inspecting evidence_path or message context if generic.
 */
export function mapValidatorArtifact(
  rawArtifact: string,
  evidencePath?: string | null,
  message?: string
): SupportedArtifact {
  const normalized = (rawArtifact || "").trim().toLowerCase();
  if (VALIDATOR_ARTIFACT_MAP[normalized]) {
    return VALIDATOR_ARTIFACT_MAP[normalized];
  }

  // Check evidence path hints
  const ev = (evidencePath || "").toLowerCase();
  const msg = (message || "").toLowerCase();

  if (ev.includes("database") || ev.includes("table") || ev.includes("schema") || msg.includes("table") || msg.includes("migration")) {
    return "Database LLD";
  }
  if (ev.includes("backend") || ev.includes("endpoint") || ev.includes("service") || msg.includes("api endpoint") || msg.includes("service boundary")) {
    return "Backend LLD";
  }
  if (ev.includes("frontend") || ev.includes("route") || ev.includes("ui") || msg.includes("frontend") || msg.includes("component hierarchy")) {
    return "Frontend LLD";
  }
  if (ev.includes("security") || ev.includes("auth") || ev.includes("jwt") || msg.includes("security") || msg.includes("zero-trust")) {
    return "Security LLD";
  }
  if (ev.includes("cloud") || ev.includes("terraform") || ev.includes("docker") || msg.includes("cloud") || msg.includes("infrastructure")) {
    return "Cloud LLD";
  }
  if (ev.includes("arsrs") || ev.includes("requirement") || msg.includes("arsrs") || msg.includes("fr-") || msg.includes("nfr-")) {
    return "ARSRS";
  }

  // Default fallback for system/package level architectural coordination
  return "HLD";
}

/**
 * Identifies the specific component, service, table, or endpoint affected.
 */
export function extractAffectedTarget(
  evidencePath?: string | null,
  message?: string
): string | null {
  const ev = (evidencePath || "").trim();
  const msg = (message || "").trim();

  // 1. Direct path parsing
  if (ev) {
    // e.g. "database.tables.bookings.locking" or "tables[bookings]" -> "Table: bookings"
    const tableMatch = ev.match(/tables?(?:\[|[\._])['"]?([a-zA-Z0-9_\-]+)['"]?\]?/i);
    if (tableMatch) return `Table: ${tableMatch[1]}`;

    // e.g. "backend.services.payment_service" or "major_services[OrderService]" -> "Service: OrderService"
    const serviceMatch = ev.match(/(?:major_)?services?(?:\[|[\._])['"]?([a-zA-Z0-9_\-]+)['"]?\]?/i);
    if (serviceMatch) return `Service: ${serviceMatch[1]}`;

    // e.g. "backend.api.endpoints[/reservations]" -> "Endpoint: /reservations"
    const endpointMatch = ev.match(/endpoints?(?:\[|[\._])['"]?([/a-zA-Z0-9_\-{}:]+)['"]?\]?/i);
    if (endpointMatch) return `Endpoint: ${endpointMatch[1]}`;

    // e.g. "security.auth.jwt" -> "Auth: jwt"
    const authMatch = ev.match(/auth(?:entication)?\.([a-zA-Z0-9_\-]+)/i);
    if (authMatch) return `Auth: ${authMatch[1]}`;

    // e.g. "cloud.infrastructure.rds" -> "Infra: rds"
    const infraMatch = ev.match(/(?:infra|infrastructure|resources?)\.([a-zA-Z0-9_\-]+)/i);
    if (infraMatch) return `Resource: ${infraMatch[1]}`;

    return ev;
  }

  // 2. Message extraction fallback
  const msgTable = msg.match(/(?:table|entity)\s+[`"']?([a-zA-Z0-9_\-]+)[`"']?/i);
  if (msgTable) return `Table: ${msgTable[1]}`;

  const msgService = msg.match(/(?:service|module)\s+[`"']?([a-zA-Z0-9_\-]+)[`"']?/i);
  if (msgService) return `Service: ${msgService[1]}`;

  const msgEndpoint = msg.match(/(?:endpoint|route|path)\s+[`"']?([/a-zA-Z0-9_\-{}:]+)[`"']?/i);
  if (msgEndpoint) return `Endpoint: ${msgEndpoint[1]}`;

  return null;
}

/**
 * Evaluates whether a finding has sufficient evidence to formulate a safe, targeted correction.
 */
export function evaluateEvidenceSufficiency(
  finding: Finding
): { isSupported: boolean; reason?: string } {
  const ev = (finding.evidence_path || "").trim();
  const msg = (finding.message || "").trim();

  // If evidence_path is provided and non-trivial
  if (ev.length > 2 && !ev.includes("unknown") && !ev.includes("none")) {
    return { isSupported: true };
  }

  // If evidence_path is missing, check if the message specifies concrete, localized technical anchors
  const hasSpecificAnchor =
    /table|service|endpoint|column|primary key|foreign key|idempotency|jwt|mtls|terraform|dockerfile|docker|alembic|openapi|http\s+\d+|status code/i.test(
      msg
    );

  const hasSpecificIdentifier = /[`"'][a-zA-Z0-9_\-/]+[`"']|FR-\d+|NFR-\d+|\/[a-zA-Z0-9_\-/]+/.test(
    msg
  );

  if (hasSpecificAnchor && hasSpecificIdentifier) {
    return { isSupported: true };
  }

  return {
    isSupported: false,
    reason:
      "Finding lacks a verified evidence path or concrete architectural identifier. Scope is ambiguous; automated correction could risk unintended structural changes.",
  };
}

/**
 * Identifies explicit architectural dependencies for an affected artifact.
 * Does NOT blindly list all artifacts; only includes verifiable dependents.
 */
export function identifyDependencies(
  artifact: SupportedArtifact,
  finding: Finding,
  affectedTarget: string | null
): CorrectionDependency[] {
  const deps: CorrectionDependency[] = [];
  const msg = (finding.message || "").toLowerCase();
  const ev = (finding.evidence_path || "").toLowerCase();
  const rule = (finding.rule_id || "").toLowerCase();

  switch (artifact) {
    case "HLD": {
      // 1. Service boundary or inter-service interface change
      if (
        msg.includes("service") ||
        msg.includes("boundary") ||
        msg.includes("interface") ||
        rule.includes("boundary") ||
        ev.includes("services")
      ) {
        deps.push({
          artifact: "Backend LLD",
          reason: "Backend service controllers, interfaces, and inter-service client calls must align with HLD topology.",
          impact_type: "interface",
        });
      }

      // 2. Client-facing API Gateway or external protocol change
      if (msg.includes("gateway") || msg.includes("api") || msg.includes("client") || msg.includes("frontend")) {
        deps.push({
          artifact: "Frontend LLD",
          reason: "Client API routing, BFF endpoints, and transport adapters must reflect gateway modifications.",
          impact_type: "protocol",
        });
      }

      // 3. Security boundary or trust zone change
      if (msg.includes("trust") || msg.includes("auth") || msg.includes("zone") || msg.includes("network")) {
        deps.push({
          artifact: "Security LLD",
          reason: "Security trust boundaries, mTLS enforcement, and ingress policies must align with HLD network topology.",
          impact_type: "security_boundary",
        });
      }

      // 4. Data store ownership change in HLD
      if (msg.includes("database") || msg.includes("persistence") || msg.includes("storage") || msg.includes("datastore")) {
        deps.push({
          artifact: "Database LLD",
          reason: "Database engine allocation and schema ownership must match HLD component data responsibilities.",
          impact_type: "schema",
        });
      }

      // 5. Cloud deployment topology change
      if (msg.includes("cluster") || msg.includes("region") || msg.includes("vpc") || msg.includes("availability zone")) {
        deps.push({
          artifact: "Cloud LLD",
          reason: "Cloud multi-region topology and VPC subnet allocations must mirror HLD deployment specifications.",
          impact_type: "infrastructure",
        });
      }
      break;
    }

    case "Database LLD": {
      // Database schema, tables, keys, or locking changes
      deps.push({
        artifact: "Backend LLD",
        reason: "Backend ORM entity mappings, repository queries, and transaction locking semantics must match table definitions.",
        impact_type: "schema",
      });

      // Clustering, storage sizing, or migration infrastructure
      if (msg.includes("cluster") || msg.includes("sharding") || msg.includes("migration") || msg.includes("backup") || msg.includes("rds")) {
        deps.push({
          artifact: "Cloud LLD",
          reason: "Database cloud instance sizing, read-replica provisioning, and storage IOPS must support persistence requirements.",
          impact_type: "infrastructure",
        });
      }
      break;
    }

    case "Backend LLD": {
      // API contract or endpoint changes
      if (msg.includes("endpoint") || msg.includes("contract") || msg.includes("route") || msg.includes("request") || msg.includes("response")) {
        deps.push({
          artifact: "Frontend LLD",
          reason: "Frontend API client types, request payloads, and response models depend on backend endpoint schemas.",
          impact_type: "interface",
        });
      }

      // Auth middleware, authorization, or cryptographic operations
      if (msg.includes("auth") || msg.includes("jwt") || msg.includes("token") || msg.includes("permission") || msg.includes("encryption")) {
        deps.push({
          artifact: "Security LLD",
          reason: "Security authorization rules, token signing algorithms, and RBAC policies must validate backend middleware.",
          impact_type: "security_boundary",
        });
      }

      // Worker, container, or execution port configuration
      if (msg.includes("docker") || msg.includes("port") || msg.includes("queue") || msg.includes("worker") || msg.includes("concurrency")) {
        deps.push({
          artifact: "Cloud LLD",
          reason: "Container runtime definitions, task scaling, and load balancer target groups depend on backend service ports.",
          impact_type: "infrastructure",
        });
      }
      break;
    }

    case "Frontend LLD": {
      // Client authentication or CSRF handling
      if (msg.includes("auth") || msg.includes("token") || msg.includes("cookie") || msg.includes("storage") || msg.includes("cors")) {
        deps.push({
          artifact: "Security LLD",
          reason: "Client-side token storage (e.g. HttpOnly cookies vs localStorage) must comply with Security LLD standards.",
          impact_type: "security_boundary",
        });
      }
      break;
    }

    case "Security LLD": {
      // Authentication, headers, or cipher changes
      deps.push({
        artifact: "Backend LLD",
        reason: "Backend service middleware must implement security controls (e.g., JWT validation, CORS headers, rate limiting).",
        impact_type: "security_boundary",
      });
      deps.push({
        artifact: "Frontend LLD",
        reason: "Frontend client authentication headers, login state handling, and CSRF tokens must comply with security policies.",
        impact_type: "protocol",
      });
      if (msg.includes("waf") || msg.includes("tls") || msg.includes("certificate") || msg.includes("kms") || msg.includes("firewall")) {
        deps.push({
          artifact: "Cloud LLD",
          reason: "Cloud WAF, ingress TLS certificates, and KMS encryption key policies must enforce declared security rules.",
          impact_type: "infrastructure",
        });
      }
      break;
    }

    case "Cloud LLD": {
      // Security groups, network ACLs, or KMS integration
      if (msg.includes("security group") || msg.includes("firewall") || msg.includes("kms") || msg.includes("iam")) {
        deps.push({
          artifact: "Security LLD",
          reason: "Cloud IAM roles, security groups, and encryption at rest must mirror Zero-Trust Security controls.",
          impact_type: "infrastructure",
        });
      }
      break;
    }

    case "ARSRS": {
      deps.push({
        artifact: "HLD",
        reason: "High-level architecture must allocate and trace all functional and non-functional requirements.",
        impact_type: "reference",
      });
      break;
    }
  }

  // Deduplicate dependencies and eliminate self-dependencies
  const uniqueDeps: CorrectionDependency[] = [];
  const seenArtifacts = new Set<SupportedArtifact>();

  for (const dep of deps) {
    if (dep.artifact !== artifact && !seenArtifacts.has(dep.artifact)) {
      seenArtifacts.add(dep.artifact);
      uniqueDeps.push(dep);
    }
  }

  return uniqueDeps;
}

export interface ConsolidatedFindingContext {
  finding: Finding;
  affectedArtifact: SupportedArtifact;
  affectedTarget: string | null;
  referenceSystems: string[];
  consolidatedCount: number;
}

/**
 * Canonicalizes, deduplicates, and consolidates raw validator findings.
 * 
 * Prevents repeating identical architectural defects across:
 * 1. Multiple benchmark reference systems (e.g. Instagram, LinkedIn, Reddit reporting the exact same pattern defect).
 * 2. Multiple identical rule violations on the same target component/path.
 * 3. Identical finding IDs or identical rule_id + evidence_path combinations.
 */
export function deduplicateAndConsolidateFindings(
  findings: Finding[]
): ConsolidatedFindingContext[] {
  const consolidatedMap = new Map<string, {
    finding: Finding;
    affectedArtifact: SupportedArtifact;
    affectedTarget: string | null;
    referenceSystems: Set<string>;
    count: number;
  }>();

  const SEVERITY_WEIGHTS: Record<string, number> = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  };

  for (const f of findings) {
    if (!f) continue;

    const affectedArtifact = mapValidatorArtifact(f.artifact, f.evidence_path, f.message);
    const affectedTarget = extractAffectedTarget(f.evidence_path, f.message);

    // Check if this is a real-world benchmark capability finding
    const isRealWorld =
      f.layer === "REAL_WORLD" ||
      (f.rule_id && f.rule_id.startsWith("RW-")) ||
      (f.message && f.message.toLowerCase().includes("missing real-world capability"));

    let dedupKey: string;
    let extractedPatternName = "";
    let extractedRefSystem = "";

    if (isRealWorld) {
      const patternMatch = f.message ? f.message.match(/missing real-world capability ['"]([^'"]+)['"]/i) : null;
      extractedPatternName = patternMatch ? patternMatch[1].trim() : (f.rule_id || "general_pattern");

      const refMatch = f.message ? f.message.match(/from reference system ([^:]+):/i) : null;
      if (refMatch) {
        extractedRefSystem = refMatch[1].trim();
      } else if (f.source) {
        extractedRefSystem = f.source.replace(/ reference$/i, "").trim();
      }

      // Group by canonical artifact + pattern name
      dedupKey = `rw::${affectedArtifact.toLowerCase()}::${extractedPatternName.toLowerCase()}`;
    } else {
      const normalizedRule = (f.rule_id || "").trim().toLowerCase();
      const normalizedPath = (f.evidence_path || "").trim().toLowerCase();
      const normalizedTarget = (affectedTarget || "").trim().toLowerCase();
      
      // If finding has a concrete evidence path or target, deduplicate by rule + path/target
      if (normalizedPath || normalizedTarget) {
        dedupKey = `std::${affectedArtifact.toLowerCase()}::${normalizedRule}::${normalizedPath}::${normalizedTarget}`;
      } else {
        // Fall back to finding ID or rule + message snippet
        const msgSnippet = (f.message || "").slice(0, 60).trim().toLowerCase();
        dedupKey = `std::${affectedArtifact.toLowerCase()}::${normalizedRule || f.id}::${msgSnippet}`;
      }
    }

    const existing = consolidatedMap.get(dedupKey);
    if (existing) {
      existing.count++;
      if (extractedRefSystem) {
        existing.referenceSystems.add(extractedRefSystem);
      }

      // Upgrade severity if duplicate has higher severity
      const existingWeight = SEVERITY_WEIGHTS[existing.finding.severity.toLowerCase()] || 0;
      const incomingWeight = SEVERITY_WEIGHTS[(f.severity || "").toLowerCase()] || 0;
      if (incomingWeight > existingWeight) {
        existing.finding.severity = f.severity;
      }

      // Prefer non-null evidence path
      if (!existing.finding.evidence_path && f.evidence_path) {
        existing.finding.evidence_path = f.evidence_path;
      }
      // Prefer non-null suggested fix
      if (!existing.finding.suggested_fix && f.suggested_fix) {
        existing.finding.suggested_fix = f.suggested_fix;
      }
    } else {
      const refSet = new Set<string>();
      if (extractedRefSystem) {
        refSet.add(extractedRefSystem);
      }
      consolidatedMap.set(dedupKey, {
        finding: { ...f },
        affectedArtifact,
        affectedTarget,
        referenceSystems: refSet,
        count: 1,
      });
    }
  }

  // Format consolidated findings
  return Array.from(consolidatedMap.values()).map((entry) => {
    const refList = Array.from(entry.referenceSystems);
    if (refList.length > 1) {
      const patternMatch = entry.finding.message ? entry.finding.message.match(/missing real-world capability ['"]([^'"]+)['"]/i) : null;
      const patternName = patternMatch ? patternMatch[1].trim() : entry.finding.rule_id;
      entry.finding.source = `Benchmark systems: ${refList.join(", ")}`;
      entry.finding.message = `Missing real-world capability '${patternName}' across benchmark reference systems (${refList.join(", ")}). Ground with explicit requirement references.`;
    }
    return {
      finding: entry.finding,
      affectedArtifact: entry.affectedArtifact,
      affectedTarget: entry.affectedTarget,
      referenceSystems: refList,
      consolidatedCount: entry.count,
    };
  });
}

/**
 * Synthesizes a concise, specific, localized correction instruction for the AI Engine.
 */
export function generateCorrectionInstruction(
  finding: Finding,
  artifact: SupportedArtifact,
  affectedTarget: string | null,
  isSupportedByEvidence: boolean
): { instruction: string; reason: string; requiresReview: boolean; clarification?: string } {
  const targetLabel = affectedTarget ? ` for [${affectedTarget}]` : "";
  const ev = finding.evidence_path ? ` (at ${finding.evidence_path})` : "";
  const fix = finding.suggested_fix ? ` Specifically: ${finding.suggested_fix}` : "";

  if (!isSupportedByEvidence) {
    return {
      instruction: `MANUAL REVIEW REQUIRED: Inspect ${artifact}${targetLabel} to clarify finding ${finding.rule_id} ("${finding.message}"). Do not perform automated code or schema modifications until the specific defect location is verified.`,
      reason: `Finding lacks verifiable evidence path or specific component identifier. Automated modification risks corrupting unrelated, valid architecture decisions.`,
      requiresReview: true,
      clarification: `Clarify exact component, table, or endpoint affected by "${finding.message}" prior to re-prompting.`,
    };
  }

  const instruction = [
    `In ${artifact}${targetLabel}${ev}, resolve rule violation [${finding.rule_id}]: "${finding.message}".`,
    fix,
    `Preserve all existing, valid architectural choices outside this scope. Do not add unrequested components or rewrite unrelated sections.`,
  ]
    .filter(Boolean)
    .join(" ");

  const reason = `Corrects ${finding.severity.toUpperCase()} severity defect identified by Validator Engine v2 rule [${finding.rule_id}] based on verified evidence in ${artifact}.`;

  return {
    instruction,
    reason,
    requiresReview: false,
  };
}

/**
 * Builds a structured, evidence-based CorrectionPlan from a Validator Engine v2 Report.
 */
export function buildCorrectionPlan(report: Report | null | undefined): CorrectionPlan | null {
  if (!report) {
    return null;
  }

  const genId = report.generation_id || "gen-live";
  const verdict = report.final_status || "PROVISIONAL";
  const now = new Date().toISOString();
  const planId = `cplan_${genId}_${Date.now()}`;

  // 1. Collect all findings from latest iteration results
  const rawFindings: Finding[] = [];

  const rawIterations = Array.isArray(report.iterations) ? report.iterations : [];
  const latestIter = rawIterations.length > 0
    ? rawIterations[rawIterations.length - 1]
    : null;

  if (latestIter && latestIter.results) {
    Object.values(latestIter.results).forEach((artRes: ArtifactResult) => {
      if (artRes && Array.isArray(artRes.findings)) {
        artRes.findings.forEach((f: Finding) => {
          if (f) {
            rawFindings.push(f);
          }
        });
      }
    });
  } else if ((report as any).validation?.findings && Array.isArray((report as any).validation.findings)) {
    (report as any).validation.findings.forEach((f: Finding) => {
      if (f) rawFindings.push(f);
    });
  } else if (Array.isArray((report as any).findings)) {
    (report as any).findings.forEach((f: Finding) => {
      if (f) rawFindings.push(f);
    });
  }

  // Deduplicate and consolidate findings across reference systems and redundant targets
  const consolidatedContexts = deduplicateAndConsolidateFindings(rawFindings);

  // 2. Verdict-specific handling
  if (verdict === "ACCEPTED" && consolidatedContexts.length === 0) {
    return {
      id: planId,
      generation_id: report.generation_id,
      created_at: now,
      validator_verdict: "ACCEPTED",
      total_findings: 0,
      actionable_count: 0,
      requires_review_count: 0,
      items_by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
      items: [],
      summary: "Architecture is ACCEPTED by Validator Engine v2. All architectural standards and rubrics satisfied. No corrections required.",
      status: "NO_ACTION_REQUIRED",
    };
  }

  // 3. Process findings into typed CorrectionItems
  const items: CorrectionItem[] = [];
  const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
  let actionableCount = 0;
  let requiresReviewCount = 0;

  for (const ctx of consolidatedContexts) {
    const f = ctx.finding;
    const sev = (f.severity || "medium").toLowerCase() as "critical" | "high" | "medium" | "low";
    if (sev in severityCounts) {
      severityCounts[sev]++;
    }

    const affectedArtifact = ctx.affectedArtifact;
    const affectedTarget = ctx.affectedTarget;
    const evidenceEval = evaluateEvidenceSufficiency(f);
    const dependencies = identifyDependencies(affectedArtifact, f, affectedTarget);

    const { instruction, reason, requiresReview, clarification } = generateCorrectionInstruction(
      f,
      affectedArtifact,
      affectedTarget,
      evidenceEval.isSupported
    );

    const isActionable = verdict !== "UNRESOLVED" && (evidenceEval.isSupported || f.severity === "critical" || f.severity === "high");

    if (isActionable) {
      actionableCount++;
    }
    if (requiresReview) {
      requiresReviewCount++;
    }

    const initialStatus: CorrectionItemStatus = requiresReview || !evidenceEval.isSupported
      ? "MANUAL_REVIEW_REQUIRED"
      : isActionable
      ? "PENDING_REVIEW"
      : "PENDING_REVIEW";

    const initialStatusReason = requiresReview
      ? (clarification || "Manual review required due to ambiguous or insufficient evidence.")
      : isActionable
      ? "Awaiting user review and approval."
      : "Advisory finding; awaiting user review.";

    items.push({
      id: `corr_${f.id}`,
      finding_id: f.id,
      severity: sev,
      title: `${affectedArtifact}: ${f.rule_id}`,
      description: f.message,
      evidence: f.evidence_path || (evidenceEval.isSupported ? "Extracted from verified architectural context" : null),
      affected_artifact: affectedArtifact,
      affected_target: affectedTarget,
      correction_instruction: instruction,
      reason,
      dependencies,
      is_actionable: isActionable,
      is_supported_by_evidence: evidenceEval.isSupported,
      requires_manual_review: requiresReview,
      clarification_needed: clarification || null,
      status: initialStatus,
      status_reason: initialStatusReason,
      reference_systems: ctx.referenceSystems.length > 0 ? ctx.referenceSystems : undefined,
      consolidated_count: ctx.consolidatedCount > 1 ? ctx.consolidatedCount : undefined,
      review_decision: null,
    });
  }

  // 4. Determine overall plan status and summary
  let planStatus: CorrectionPlanStatus = "CORRECTION_NEEDED";
  let summary = "";

  if (verdict === "UNRESOLVED") {
    planStatus = "MANUAL_REVIEW_REQUIRED";
    summary = `Architecture is UNRESOLVED after maximum validation rounds. ${actionableCount} unmitigated defect(s) remain. Automated regeneration stopped to prevent infinite loops. Manual review required.`;
  } else if (verdict === "PROVISIONAL" && items.length === 0) {
    planStatus = "PROVISIONAL_STAGE_UNAVAILABLE";
    summary = `Architecture received a PROVISIONAL verdict because external reviewer models or real-world benchmark data were unavailable. No structural defects were detected in deterministic Layer 0/1 checks.`;
  } else if (verdict === "ACCEPTED_WITH_WARNINGS") {
    planStatus = "CORRECTION_NEEDED";
    summary = `Architecture is ACCEPTED WITH WARNINGS. ${items.length} non-blocking advisory correction(s) identified. Baseline architecture remains approved.`;
  } else if (verdict === "ACCEPTED") {
    planStatus = "NO_ACTION_REQUIRED";
    summary = `Architecture is ACCEPTED. ${items.length} informational notice(s) noted. No mandatory corrections required.`;
  } else {
    // REJECTED or PROVISIONAL with findings
    planStatus = requiresReviewCount > 0 && actionableCount === 0 ? "MANUAL_REVIEW_REQUIRED" : "CORRECTION_NEEDED";
    summary = `Validator Engine v2 issued ${verdict}. Identified ${actionableCount} actionable correction item(s) across ${new Set(items.map((i) => i.affected_artifact)).size} artifact(s).`;
  }

  return {
    id: planId,
    generation_id: report.generation_id,
    created_at: now,
    validator_verdict: verdict,
    total_findings: items.length,
    actionable_count: actionableCount,
    requires_review_count: requiresReviewCount,
    items_by_severity: severityCounts,
    items,
    summary,
    status: planStatus,
  };
}

/**
 * Validates whether a correction item is eligible for user review and approval.
 * Prevents approving items with missing architecture packages, generation mismatches,
 * non-actionable findings, or insufficient evidence.
 */
export function validateCorrectionEligibility(
  item: CorrectionItem,
  context: {
    generationId?: string | null;
    versionTag?: string | null;
    reportGenerationId?: string | null;
    hasArchitecturePackage?: boolean;
    knownFindingIds?: string[];
  }
): { eligible: boolean; reason: string } {
  if (!item) {
    return { eligible: false, reason: "Correction item does not exist." };
  }

  if (context.hasArchitecturePackage === false) {
    return { eligible: false, reason: "Architecture package is missing." };
  }

  if (context.generationId && context.reportGenerationId && context.generationId !== context.reportGenerationId) {
    return { eligible: false, reason: "Generation ID mismatch: item does not belong to active generation." };
  }

  if (context.knownFindingIds && context.knownFindingIds.length > 0 && !context.knownFindingIds.includes(item.finding_id)) {
    return { eligible: false, reason: "Finding ID does not belong to the active validation report." };
  }

  if (!item.is_actionable) {
    return { eligible: false, reason: "Finding is not actionable and cannot be approved for automated correction." };
  }

  if (item.requires_manual_review) {
    return { eligible: false, reason: "Correction item requires manual review before it can proceed." };
  }

  if (!item.is_supported_by_evidence) {
    return { eligible: false, reason: "Evidence is insufficient to safely formulate an automated correction." };
  }

  if (!item.correction_instruction || item.correction_instruction.trim().length === 0) {
    return { eligible: false, reason: "Correction instruction is empty." };
  }

  return { eligible: true, reason: "Correction item is eligible for review and approval." };
}

/**
 * Checks whether automated targeted correction execution is supported by the AI Engine.
 * Per project specification and AI Engine inspection, automated targeted single-finding
 * correction is currently unsupported by unchanged AI Engine APIs.
 */
export function checkAutomatedCorrectionCapability(): { supported: boolean; reason: string; status: "CORRECTION_UNAVAILABLE" } {
  return {
    supported: false,
    reason: "Your correction plan has been approved for review. Automated targeted correction is unavailable through the current AI Engine API. No architecture artifacts have been modified.",
    status: "CORRECTION_UNAVAILABLE",
  };
}

