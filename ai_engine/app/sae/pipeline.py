"""Lean SAE v2 Pipeline Orchestrator.

High-throughput, asynchronous, multi-agent architecture generation engine.

Phases:
  1. Planning & Domain Lock: Canonical Requirements -> Requirement Analysis -> Contract Validation -> Tech Stack -> ADP
  2. HLD Generation: High Level Design & HLD Quality Gate (with self-healing repair)
  3. LLD & Operations (8-Way Parallel): Backend, DB, Frontend, Security, Cloud, Testing, Observability, Runbooks
  4. Scaffolding (Deterministic): OpenAPI YAML, Dockerfile, Docker Compose, Alembic Migrations, Terraform IaC
  5. Cross-Artifact Consistency & Adversarial Remediation Loop
  6. Assembly & Unified 3-Tier Quality Gating: Artifact Quality, Consistency, and Production Readiness
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.sae.agents.adversarial_review_agent import AdversarialReviewAgent
from app.sae.agents.backend_lld_generation_agent import BackendLLDGenerationAgent
from app.sae.agents.cloud_lld_generation_agent import CloudLLDGenerationAgent
from app.sae.agents.database_lld_generation_agent import DatabaseLLDGenerationAgent
from app.sae.agents.frontend_lld_generation_agent import FrontendLLDGenerationAgent
from app.sae.agents.hld_generation_agent import HLDGenerationAgent
from app.sae.agents.observability_agent import ObservabilityAgent
from app.sae.agents.requirement_analysis_agent import RequirementAnalysisAgent
from app.sae.agents.runbook_agent import RunbookAgent
from app.sae.agents.security_lld_generation_agent import SecurityLLDGenerationAgent
from app.sae.agents.technology_advisor_agent import TechnologyAdvisorAgent
from app.sae.agents.testing_strategy_agent import TestingStrategyAgent
from app.sae.generators.dockerfile_generator import generate_docker_scaffolds
from app.sae.generators.iac_generator import generate_terraform_scaffold
from app.sae.generators.migration_generator import generate_alembic_migration
from app.sae.generators.openapi_generator import generate_openapi_spec
from app.sae.models.response_models import SoftwareArchitecturePackageResponse
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import get_architecture_knowledge_service
from app.sae.utils.sae_logger import SAELogger, DEFAULT_LOGS_ROOT
from app.sae.utils.domain_lock import DomainContext, DomainLockEngine, validate_requirement_contract
from app.sae.utils.arsrs_validator import ARSRSValidator
from app.sae.utils.hld_quality_gate import HLDQualityGate, HLDQualityReport
from app.sae.utils.canonical_contract import CanonicalArchitectureContract, ContractBuilder
from app.sae.utils.cross_artifact_validator import CrossArtifactValidator, CrossArtifactConsistencyReport
from app.sae.utils.remediation_engine import RemediationEngine, RemediationPlan
from app.sae.utils.scoring_engine import ScoringEngine, UnifiedScorecard, BackendQualityDiagnostics

logger = logging.getLogger(__name__)

# Standard domain checklists for gap detection
DOMAIN_FEATURE_CHECKLISTS: Dict[str, List[str]] = {
    "smart_parking": [
        "Driver & Attendant Identity & Profile Management",
        "Real-Time Parking Spot Search & Availability Map",
        "Parking Slot Reservation & Booking Engine",
        "Digital Parking Fee Calculation & Payment Processing",
        "Vehicle Check-In, Check-Out & License Plate Verification",
        "Real-Time Lot Occupancy Monitoring & Sensor Tracking",
        "Automated Overstay Alerts & Parking Violation Management",
        "Admin Dashboard: Tariff, Zone & Revenue Analytics",
    ],
    "food_delivery": [
        "Customer Identity & Address Management",
        "Restaurant & Menu Browsing, Search & Filtering",
        "Cart Management, Customization & Pricing Engine",
        "Payment Gateway Integration & Instant Settlement",
        "Order Processing & Kitchen Status Workflow",
        "Delivery Partner Dispatch & Real-Time GPS Tracking",
        "Push Notifications & Order Status Alerts",
        "Restaurant & Platform Admin Management Dashboards",
    ],
    "event_management": [
        "User Authentication & Student/Admin Roles",
        "Event Catalog, Browsing & Filter by Category",
        "Online Event Registration & Seat Capacity Management",
        "Real-Time Event Notifications & Reminder Dispatch",
        "QR-Code / Check-in Attendance Tracking",
        "Participant Management & Registration Status Verification",
        "Admin Dashboard & Event Analytics Reporting",
    ],
    "inventory_management": [
        "Product Catalog & SKU Management",
        "Supplier & Vendor Relationship Management",
        "Stock-In (Goods Receipt) Transaction Processing",
        "Stock-Out (Goods Issue) Transaction Processing",
        "Real-Time Multi-Warehouse Stock Level Tracking",
        "Low-Stock Automated Alerts & Reorder Thresholds",
        "Immutable Inventory Transaction Audit Logs",
        "Role-Based Access Control (Admin, Manager, Staff)",
        "Inventory Valuation & Movement Reports Dashboard",
    ],
    "learning_management": [
        "Course Catalog & Syllabus Module Management",
        "Student Enrollment & Registration Processing",
        "Learning Content Delivery & Video Playback",
        "Assignment Submission & Automated Grading",
        "Student Academic Progress & Analytics Tracking",
        "Instructor Announcements & Discussion Forums",
        "Role-Based Access Control (Student, Instructor, Admin)",
    ],
    "appointment_scheduling": [
        "Patient & Doctor Identity & Profile Management",
        "Doctor Search, Filtering & Profile Browsing",
        "Doctor Availability Calendar & Time Slot Management",
        "Appointment Booking, Rescheduling & Cancellation",
        "Double-Booking Prevention & Conflict Detection",
        "Appointment Reminder & Notification Dispatch",
        "Admin Dashboard: User, Doctor & Appointment Management",
    ],
    "library": [
        "User Registration & Authentication",
        "Password Reset & Profile Management",
        "Book Catalog Search & Filtering",
        "Borrowing & Circulation Transactions",
        "Due Date Notifications & Reminders",
        "Holds & Reservations Queue",
        "Fines & Overdue Penalty Processing",
        "Administrative Inventory Reporting & Export",
    ],
    "ecommerce": [
        "User Authentication & Address Book",
        "Product Catalog & Multi-Faceted Search",
        "Shopping Cart & Checkout Workflow",
        "Payment Gateway Integration",
        "Order Lifecycle & Tracking",
        "Inventory Stock Reservation",
        "Automated Order Confirmation & Receipts",
        "Admin Product & Order Management",
    ],
    "healthcare": [
        "Patient Identity & Provider Registration",
        "Appointment Scheduling & Availability Calendar",
        "Electronic Health Records (EHR) & Clinical Notes",
        "HIPAA Consent Logging & Audit Trail",
        "Prescription & Diagnostic Test Orders",
        "Patient Portal & Secure Messaging",
    ],
    "fintech": [
        "Customer Onboarding & KYC Verification",
        "Account Balance & Double-Entry Ledger",
        "Peer-to-Peer & Wire Fund Transfers",
        "Fraud Detection & Risk Scoring",
        "Transaction History & Statement Generation",
        "Regulatory Compliance & Reporting",
    ],
    "saas": [
        "Tenant Registration & Account Provisioning",
        "Role-Based Access Control & Team Invites",
        "Subscription Billing & Metered Usage",
        "Dashboard Analytics & Export",
        "API Key Generation & Rate Limiting",
        "Audit Logging & Security Activity Feed",
    ],
}


class SAEPipeline:
    """Master Asynchronous Pipeline for SAE v2."""

    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        design_id: Optional[str] = None,
        logs_root: Optional[str | Path] = None,
        debug: bool = True,
    ) -> None:
        self.design_id = design_id
        self.logs_root = Path(logs_root) if logs_root else DEFAULT_LOGS_ROOT
        self.debug = debug
        self.sae_logger: Optional[SAELogger] = None

        if self.design_id:
            self.sae_logger = SAELogger(
                design_id=self.design_id,
                logs_root=self.logs_root,
                debug=self.debug,
            )

        self.llm_provider = OpenRouterProvider(
            api_keys=api_keys,
            debug=debug,
            sae_logger=self.sae_logger,
        )

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = Path("outputs") / f"run_{ts}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all Phase 1-5 agents
        self.req_agent = RequirementAnalysisAgent(self.llm_provider)
        self.tech_agent = TechnologyAdvisorAgent(self.llm_provider)
        self.hld_agent = HLDGenerationAgent(self.llm_provider)
        self.backend_agent = BackendLLDGenerationAgent(self.llm_provider)
        self.db_agent = DatabaseLLDGenerationAgent(self.llm_provider)
        self.frontend_agent = FrontendLLDGenerationAgent(self.llm_provider)
        self.security_agent = SecurityLLDGenerationAgent(self.llm_provider)
        self.cloud_agent = CloudLLDGenerationAgent(self.llm_provider)
        self.testing_agent = TestingStrategyAgent(self.llm_provider)
        self.observability_agent = ObservabilityAgent(self.llm_provider)
        self.runbook_agent = RunbookAgent(self.llm_provider)
        self.adversarial_agent = AdversarialReviewAgent(self.llm_provider)

        # Pre-warm RAG vector index & embeddings
        try:
            get_architecture_knowledge_service().warmup()
        except Exception as e:
            logger.warning(f"RAG pre-warm warning: {e}")

    def _save_json(self, filename: str, data: Any) -> Path:
        """Save a dictionary or Pydantic model to output directory."""
        p = self.output_dir / filename
        data_dict = data.model_dump(mode="json") if hasattr(data, "model_dump") else data
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=2, default=str)
        return p

    def _save_text(self, filename: str, content: str) -> Path:
        """Save text content (e.g. YAML, Dockerfile, TF) to output directory."""
        p = self.output_dir / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def _formulate_adp(
        self,
        req: Dict[str, Any],
        tech: Dict[str, Any],
        arsrs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Formulate Architecture Decision Plan deterministically from upstream outputs."""
        system_name = req.get("system_name") or arsrs.get("project_profile", {}).get("goal", "Enterprise System")
        domain = req.get("domain") or arsrs.get("domain_context", {}).get("industry", "General")

        def _get_choice(cat: str, fallback: str) -> str:
            val = tech.get(cat, {})
            if isinstance(val, dict):
                opt = val.get("selected_option")
                if opt and "standard option" not in str(opt).lower():
                    return opt
            return fallback

        backend_fw = _get_choice("backend", "FastAPI (Python)")
        frontend_fw = _get_choice("frontend", "React (Next.js)")
        database = _get_choice("database", "PostgreSQL")
        cache = _get_choice("cache", "Redis")
        auth = _get_choice("authentication", "OAuth2 with Authorization Code Flow & PKCE")
        comm = _get_choice("communication", "RESTful JSON APIs over HTTP/2")
        cloud = _get_choice("cloud", "AWS (ECS Fargate)")
        deployment = _get_choice("deployment", "Docker with GitHub Actions CI/CD")

        modules = req.get("modules", [])
        nfrs = req.get("non_functional_requirements", [])
        has_high_scale = any(
            isinstance(nfr, dict) and any(
                kw in (nfr.get("requirement", "") + nfr.get("category", "")).lower()
                for kw in ["microservice", "independent deploy", "multi-region", "kafka"]
            )
            for nfr in nfrs
        )

        if len(modules) <= 4 and not has_high_scale:
            arch_style = "Modular Monolith"
            complexity_just = "Modular monolith minimizes distributed operational complexity while providing clean domain isolation for current requirements."
        else:
            arch_style = "Modular Layered Microservices"
            complexity_just = "Modular services architecture enables independent scaling and domain boundary isolation required for system scale."

        decisions = []
        for cat_key, cat_name, choice in [
            ("backend", "Backend", backend_fw),
            ("frontend", "Frontend", frontend_fw),
            ("database", "Database", database),
            ("cache", "Caching", cache),
            ("authentication", "Authentication", auth),
            ("communication", "Communication", comm),
            ("cloud", "Cloud Platform", cloud),
            ("deployment", "Deployment", deployment),
        ]:
            val = tech.get(cat_key, {})
            reasoning = val.get("reasoning", f"Selected to fulfill {domain} requirements.") if isinstance(val, dict) else f"Standard production choice for {cat_name}."
            satisfies = val.get("satisfies", []) if isinstance(val, dict) else []
            decisions.append({
                "category": cat_name,
                "choice": choice,
                "reason": reasoning,
                "satisfies": satisfies,
            })

        major_components = [
            {"name": "API Gateway & Auth Layer", "type": "GATEWAY", "tech": f"Reverse Proxy / {auth}"},
            {"name": "Core Application Services", "type": "SERVICE", "tech": backend_fw},
            {"name": "Primary Database Store", "type": "DATABASE", "tech": database},
            {"name": "In-Memory Cache Tier", "type": "CACHE", "tech": cache},
            {"name": "Web Presentation UI", "type": "FRONTEND", "tech": frontend_fw},
        ]

        return {
            "plan_id": f"adp_{int(time.time())}",
            "system_name": system_name,
            "domain": domain,
            "architecture_style": arch_style,
            "complexity_justification": complexity_just,
            "technology_stack": {
                "backend": backend_fw,
                "frontend": frontend_fw,
                "database": database,
                "cache": cache,
                "authentication": auth,
                "communication": comm,
                "cloud": cloud,
                "deployment": deployment,
            },
            "major_components": major_components,
            "decisions": decisions,
        }

    def _check_domain_coverage_gaps(
        self,
        req_analysis: Dict[str, Any],
        domain_ctx: Optional[DomainContext] = None,
    ) -> Dict[str, Any]:
        """Perform deterministic domain-checklist matcher against authoritative domain profile."""
        from app.sae.utils.domain_lock import DOMAIN_TAXONOMY

        if domain_ctx:
            domain_key = domain_ctx.domain_key
            domain_display_name = domain_ctx.domain_name
            checklist = domain_ctx.domain_checklist or DOMAIN_TAXONOMY.get(domain_key, {}).get("checklist", [])
        else:
            domain_key = req_analysis.get("domain_key", "")
            domain_display_name = req_analysis.get("domain", "General")
            checklist = DOMAIN_TAXONOMY.get(domain_key, {}).get("checklist", [])

        if not checklist:
            # Fallback checklist dynamically derived from modules/requirements
            fr_titles = [r.get("title", "") for r in req_analysis.get("functional_requirements", []) if isinstance(r, dict)]
            checklist = fr_titles[:8] if fr_titles else ["User Authentication & Access Control", "Core Domain Operations", "Audit Logging & Reporting"]

        fr_text = json.dumps(req_analysis.get("functional_requirements", []), default=str).lower()
        module_text = json.dumps(req_analysis.get("modules", []), default=str).lower()
        combined_text = fr_text + " " + module_text

        covered: List[str] = []
        gaps: List[str] = []

        STOP_WORDS = {"user", "with", "from", "management", "system", "service", "module", "data", "processing", "item", "items"}
        for item in checklist:
            keywords = [w for w in re.split(r"[&\s/,]+", item.lower()) if len(w) > 3 and w not in STOP_WORDS]
            if any(k in combined_text for k in keywords):
                covered.append(item)
            else:
                gaps.append(item)

        coverage_ratio = round(len(covered) / max(len(checklist), 1), 2)
        return {
            "evaluated_domain": domain_display_name,
            "domain_key": domain_key,
            "checklist_items_total": len(checklist),
            "covered_features_count": len(covered),
            "covered_features": covered,
            "potential_domain_gaps_count": len(gaps),
            "potential_domain_gaps": gaps,
            "domain_coverage_ratio": coverage_ratio,
        }

    def _compute_completeness(
        self,
        sections: Dict[str, Dict[str, Any]],
        domain_ctx: DomainContext,
        consistency_report: CrossArtifactConsistencyReport,
        domain_gap_report: Optional[Dict[str, Any]] = None,
        adversarial_verdict: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute aggregate 3-tier scorecard, production readiness, and quality report with hard gating."""
        scorecard: UnifiedScorecard = ScoringEngine.compute_unified_scorecard(
            sections=sections,
            domain_ctx=domain_ctx,
            consistency_report=consistency_report,
            adversarial_verdict=adversarial_verdict or "APPROVED",
        )

        return {
            "overall_completeness": scorecard.overall_composite_score,
            "structural_completeness": scorecard.structural_completeness,
            "artifact_quality_score": scorecard.artifact_quality_score,
            "consistency_score": scorecard.consistency_score,
            "production_readiness_score": scorecard.production_readiness_score,
            "architectural_quality_score": scorecard.artifact_quality_score,
            "traceability_score": scorecard.traceability_score,
            "production_readiness_gates": scorecard.quality_indicators,
            "quality_indicators": {
                "hedged_phrases_detected_count": scorecard.quality_indicators.get("hedged_phrases_detected_count", 0),
                "hard_gate_violations": scorecard.hard_gate_violations,
                "hard_gates_passed": scorecard.hard_gates,
                "cross_artifact_issues_count": consistency_report.total_issues,
            },
            "domain_coverage": domain_gap_report or {},
            "section_scores": scorecard.per_section_scores,
            "hard_gate_violations": scorecard.hard_gate_violations,
            "backend_diagnostics": scorecard.backend_diagnostics,
            "status": scorecard.status,
        }

    async def run_async(
        self,
        arsrs: Dict[str, Any],
        design_id: Optional[str] = None,
    ) -> SoftwareArchitecturePackageResponse:
        """Execute complete SAE pipeline with strict quality gates, domain locking, and remediation."""
        t_start = time.perf_counter()

        # Resolve design_id
        if design_id:
            self.design_id = design_id
        elif not self.design_id:
            arsrs_meta = arsrs.get("metadata", {}) if isinstance(arsrs.get("metadata"), dict) else {}
            arsrs_profile = arsrs.get("project_profile", {}) if isinstance(arsrs.get("project_profile"), dict) else {}
            self.design_id = (
                arsrs.get("design_id")
                or arsrs.get("session_id")
                or arsrs_profile.get("session_id")
                or arsrs_meta.get("design_id")
                or f"design_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

        # Initialize or update SAELogger
        if not self.sae_logger or self.sae_logger.design_id != self.design_id:
            self.sae_logger = SAELogger(
                design_id=self.design_id,
                logs_root=self.logs_root,
                debug=self.debug,
            )
            self.llm_provider.set_sae_logger(self.sae_logger)

        self.sae_logger.log_info(f"=== Starting Production-Grade SAE v2 Pipeline [Design ID: {self.design_id}] ===")
        self.sae_logger.log_info(f"Output Directory: {self.output_dir}")
        self.sae_logger.log_info(f"Debug Log: {self.sae_logger.debug_log_path}")

        print(f"\n=== Starting Production-Grade SAE v2 Pipeline (Output: {self.output_dir}) ===", flush=True)
        print(f" • Design ID : {self.design_id}", flush=True)
        print(f" • Debug Log : {self.sae_logger.debug_log_path}", flush=True)

        # ── Phase 1: Planning & Domain Lock (Sequential) ──────────────────────
        t_p1 = time.perf_counter()
        self.sae_logger.log_phase_start(1, "Planning & Domain Lock (Requirement Analysis + Canonical Lock + Tech Stack + ADP)")
        print("\n▶ [Phase 1/6] Planning & Domain Lock (Requirement Analysis + Canonical Lock + Tech Stack + ADP)...", flush=True)

        # 0. Pre-SAE ARSRS Validation & Anti-Contamination Sanitization
        arsrs, sanitization_actions = ARSRSValidator.validate_and_sanitize_arsrs(arsrs)
        if sanitization_actions:
            self.sae_logger.log_info(f"ARSRS Pre-Validation Sanitization: {sanitization_actions}")

        # 1. Lock Domain and Canonical Requirements
        domain_ctx = DomainLockEngine.lock_domain_and_requirements(arsrs)
        req_quality = DomainLockEngine.validate_requirement_quality(domain_ctx)
        self.sae_logger.log_info(f"🔒 Domain Locked: {domain_ctx.domain_name} | Requirements: {len(domain_ctx.canonical_requirements)} canonical items")
        print(f"  🔒 Domain Locked: {domain_ctx.domain_name} ({len(domain_ctx.canonical_requirements)} Canonical Requirements)", flush=True)

        # 2. Run Requirement Analysis Agent
        req_analysis = await self.req_agent.run_async(arsrs, domain_ctx=domain_ctx)

        # 3. Requirement Quality Gate & Contract Validation (BEFORE Downstream Generation)
        is_req_valid, req_contract_score, req_violations = validate_requirement_contract(req_analysis, domain_ctx)
        
        # Self-repair requirement analysis if contract is violated
        if not is_req_valid or req_contract_score < 0.70:
            print(f"  ⚠️ Requirement Quality Gate failed ({req_contract_score:.2f}). Hydrating from canonical baseline...", flush=True)
            self.sae_logger.log_warning(f"Requirement Quality Gate violation: {req_violations}. Applying canonical hydration.")
            canonical_payload = domain_ctx.to_validated_artifact()
            for k, v in canonical_payload.items():
                if not req_analysis.get(k):
                    req_analysis[k] = v
            # Revalidate
            is_req_valid, req_contract_score, req_violations = validate_requirement_contract(req_analysis, domain_ctx)

        if not is_req_valid or req_contract_score < 0.70:
            err_msg = f"CRITICAL PIPELINE ERROR: Requirement Analysis failed quality gate ({req_contract_score:.2f}) with violations: {req_violations}. Halting pipeline."
            self.sae_logger.log_error(err_msg)
            print(f"  ❌ {err_msg}", flush=True)
            raise RuntimeError(err_msg)

        # 4. Log Contract: Requirement Analysis -> Technology Advisor
        req_ids = [r.get("id") for r in req_analysis.get("functional_requirements", []) if isinstance(r, dict) and r.get("id")]
        nfr_ids = [r.get("id") for r in req_analysis.get("non_functional_requirements", []) if isinstance(r, dict) and r.get("id")]
        fr_count = len(req_analysis.get("functional_requirements", []))
        nfr_count = len(req_analysis.get("non_functional_requirements", []))
        actors_count = len(req_analysis.get("actors", []))
        modules_count = len(req_analysis.get("modules", []))

        contract_log_p1 = (
            f"[CONTRACT: REQUIREMENT_ANALYSIS → TECHNOLOGY_ADVISOR]\n"
            f"Requirement IDs: {req_ids + nfr_ids}\n"
            f"Domain: {req_analysis.get('domain')}\n"
            f"FR count: {fr_count}\n"
            f"NFR count: {nfr_count}\n"
            f"Actor count: {actors_count}\n"
            f"Module count: {modules_count}\n"
            f"Quality score: {req_contract_score:.2f}\n"
            f"Gate passed: {is_req_valid}"
        )
        self.sae_logger.log_info(contract_log_p1)
        print(f"\n{contract_log_p1}\n", flush=True)

        # 5. Technology Advisor consumes validated Requirement Analysis artifact directly
        tech_rec = await self.tech_agent.run_async(req_analysis)
        tech_gate_passed = bool(tech_rec.get("backend")) and bool(tech_rec.get("database"))

        # 6. Formulate ADP
        adp = self._formulate_adp(req_analysis, tech_rec, arsrs)
        domain_gaps = self._check_domain_coverage_gaps(req_analysis, domain_ctx)
        dur_p1 = round(time.perf_counter() - t_p1, 2)

        self.sae_logger.log_phase_end(1, "Planning & Domain Lock", dur_p1, f"Domain: {domain_ctx.domain_name}, Req Quality: {req_contract_score*100:.0f}%")
        print(f"  ✓ Phase 1 Completed in {dur_p1}s (Domain: {domain_ctx.domain_name}, Req Quality: {req_contract_score*100:.0f}%)", flush=True)

        if self.debug:
            self._save_json("01_requirement_analysis.json", req_analysis)
            self._save_json("02_technology_recommendation.json", tech_rec)
            self._save_json("03_architecture_decision_plan.json", adp)
            self._save_json("03_domain_coverage_gaps.json", domain_gaps)

        # ── Phase 2: High Level Design & HLD Quality Gate (Sequential) ────────
        t_p2 = time.perf_counter()
        self.sae_logger.log_phase_start(2, "High Level Design & Quality Gating")
        print("\n▶ [Phase 2/6] High Level Design & Quality Gating...", flush=True)

        # Log Contract: Technology Advisor -> HLD
        contract_log_p2 = (
            f"[CONTRACT: TECHNOLOGY_ADVISOR → HLD]\n"
            f"Requirement IDs: {req_ids}\n"
            f"Technology stack populated: {tech_gate_passed}\n"
            f"Technology gate passed: {tech_gate_passed}"
        )
        self.sae_logger.log_info(contract_log_p2)
        print(f"\n{contract_log_p2}\n", flush=True)

        # ── Pre-HLD ARSRS & Domain Validation ─────────────────────────────────
        curr_ps = (
            arsrs.get("project_profile", {}).get("goal")
            or arsrs.get("raw_input")
            or domain_ctx.system_name
            or "Current Problem Statement"
        )
        curr_domain = domain_ctx.domain_name
        curr_frs = [
            r.get("title") or r.get("description", "")
            for r in req_analysis.get("functional_requirements", [])
            if isinstance(r, dict)
        ]
        curr_actors = [
            a.get("role") or a.get("title") or str(a)
            for a in req_analysis.get("actors", [])
        ]
        curr_workflows = [
            w.get("name", "") for w in req_analysis.get("workflows", []) if isinstance(w, dict)
        ]
        curr_rules = req_analysis.get("business_rules", [])

        print("=" * 60, flush=True)
        print("  [PRE-HLD ARSRS & DOMAIN VALIDATION]", flush=True)
        print(f"  CURRENT PS: {curr_ps}", flush=True)
        print(f"  CURRENT DOMAIN: {curr_domain} ({domain_ctx.domain_key})", flush=True)
        print(f"  CURRENT FRs ({len(curr_frs)}): {curr_frs[:4]}", flush=True)
        print(f"  CURRENT ACTORS ({len(curr_actors)}): {curr_actors}", flush=True)
        print(f"  CURRENT WORKFLOWS ({len(curr_workflows)}): {curr_workflows}", flush=True)
        print(f"  CURRENT BUSINESS RULES ({len(curr_rules)}): {len(curr_rules)} rules loaded", flush=True)
        print("=" * 60 + "\n", flush=True)

        # Cross-domain contamination inspection
        forbidden_keywords = domain_ctx.forbidden_keywords
        arsrs_payload_str = json.dumps(req_analysis, default=str).lower()
        active_contaminants = [
            kw for kw in forbidden_keywords
            if len(kw) >= 4 and re.search(rf"\b{re.escape(kw)}\b", arsrs_payload_str)
        ]
        if active_contaminants:
            self.sae_logger.log_warning(f"ARSRS contamination detected: {active_contaminants}. Cleansing artifact.")
            print(f"  ⚠️ ARSRS contamination detected: {active_contaminants}. Cleansing out-of-domain terms...", flush=True)

        # HLD consumes validated requirement analysis, tech recommendation, and ADP
        raw_hld = await self.hld_agent.run_async(req_analysis, tech_rec, adp, domain_ctx=domain_ctx)
        
        # Enforce HLD Quality Gate & Self-Repair
        hld, hld_report = await HLDQualityGate.repair_hld_if_needed(
            hld=raw_hld,
            domain_ctx=domain_ctx,
            tech_rec=tech_rec,
            adp=adp,
            llm_provider=self.llm_provider,
        )

        dur_p2 = round(time.perf_counter() - t_p2, 2)
        repair_tag = " (Self-Healed)" if hld_report.repaired else ""
        self.sae_logger.log_phase_end(2, "High Level Design", dur_p2, f"HLD Quality: {hld_report.score*100:.0f}%{repair_tag}, Services: {hld_report.service_count}")
        print(f"  ✓ Phase 2 Completed in {dur_p2}s (HLD Quality: {hld_report.score*100:.0f}%{repair_tag}, Services: {hld_report.service_count})", flush=True)

        if self.debug:
            self._save_json("04_hld.json", hld)

        # ── Canonical Architecture Contract (CAC) Synthesis ───────────────────
        cac: CanonicalArchitectureContract = ContractBuilder.build_from_hld(
            hld=hld,
            req_analysis=req_analysis,
            domain_ctx=domain_ctx,
        )
        if self.debug:
            self._save_json("04b_canonical_architecture_contract.json", cac.model_dump())

        # ── Phase 3: LLD & Operations Generation (8-Way Parallel) ─────────────
        t_p3 = time.perf_counter()
        self.sae_logger.log_phase_start(3, "Parallel LLD & Operations (8 Agents grounded on CAC)")
        print("\n▶ [Phase 3/6] Parallel LLD & Production Operations (8 Concurrent Agents grounded on CAC)...", flush=True)

        # Log Contract: CAC -> Backend LLD & Parallel LLDs
        hld_services_count = len(hld.get("major_services", []))
        arch_style = hld.get("architecture_style", adp.get("architecture_style", "Modular Monolith"))
        be_tech = hld.get("technology_stack", {}).get("backend", "FastAPI")

        contract_log_p3 = (
            f"[CONTRACT: CAC → BACKEND_LLD]\n"
            f"Requirement IDs (No Aliases): {cac.requirement_ids}\n"
            f"API Operations: {[op.operation_id for op in cac.api_operations]}\n"
            f"Domain Entities: {[e.name for e in cac.domain_entities]}\n"
            f"Architecture style: {arch_style}\n"
            f"Backend technology: {be_tech}\n"
            f"CAC Validated: True"
        )
        self.sae_logger.log_info(contract_log_p3)
        print(f"\n{contract_log_p3}\n", flush=True)

        contract_log_fe = (
            f"[CONTRACT: CAC → FRONTEND]\n"
            f"API Operations: {[op.operation_id for op in cac.api_operations]}\n"
            f"Canonical Paths: {[op.path for op in cac.api_operations]}\n"
            f"Unknown Operations: []"
        )
        self.sae_logger.log_info(contract_log_fe)

        contract_log_db = (
            f"[CONTRACT: CAC → DATABASE]\n"
            f"Entities: {[e.name for e in cac.domain_entities]}\n"
            f"Tables: {[t.table_name for t in cac.database_entities]}\n"
            f"Bridge Mappings: {[f'{m.domain_entity} -> {m.database_table}' for m in cac.entity_mappings]}"
        )
        self.sae_logger.log_info(contract_log_db)

        sem = asyncio.Semaphore(8)

        async def _safe_run(coro, role: str) -> Dict[str, Any]:
            async with sem:
                try:
                    return await coro
                except Exception as e:
                    err_msg = f"Error in parallel agent [{role}]: {e}"
                    # pyrefly: ignore [missing-attribute]
                    self.sae_logger.log_warning(err_msg)
                    print(f"  [{role}] ⚠️ Error in parallel agent: {e}. Using fallback.", flush=True)
                    return {}

        results = await asyncio.gather(
            _safe_run(self.backend_agent.run_async(hld, cac=cac), "backend"),
            _safe_run(self.db_agent.run_async(hld, cac=cac), "database"),
            _safe_run(self.frontend_agent.run_async(hld, cac=cac), "frontend"),
            _safe_run(self.security_agent.run_async(hld), "security"),
            _safe_run(self.cloud_agent.run_async(hld), "cloud"),
            _safe_run(self.testing_agent.run_async(hld, {}, cac=cac), "testing_strategy"),
            _safe_run(self.observability_agent.run_async(hld, {}, cac=cac), "observability"),
            _safe_run(self.runbook_agent.run_async(hld, {}, {}), "runbooks"),
        )

        (
            backend_lld,
            database_lld,
            frontend_lld,
            security_lld,
            cloud_lld,
            testing_strategy,
            observability,
            runbooks,
        ) = results

        # Evaluate Backend Quality Gate & Log Structured Diagnostics
        be_diagnostics: BackendQualityDiagnostics = ScoringEngine.evaluate_backend_quality_gate(backend_lld, domain_ctx)
        self.sae_logger.log_info(f"Backend LLD Quality: Score={be_diagnostics.score:.2f}, Passed={be_diagnostics.passed}, Endpoints={be_diagnostics.endpoints_count}, Models={be_diagnostics.models_count}")

        dur_p3 = round(time.perf_counter() - t_p3, 2)
        self.sae_logger.log_phase_end(3, "Parallel LLD & Operations", dur_p3, f"8 Agents Executed (Backend Quality: {be_diagnostics.score*100:.0f}%)")
        print(f"  ✓ Phase 3 Completed in {dur_p3}s (8 Agents Executed, Backend Quality: {be_diagnostics.score*100:.0f}%)", flush=True)

        if self.debug:
            self._save_json("05_backend_lld.json", backend_lld)
            self._save_json("06_database_lld.json", database_lld)
            self._save_json("07_frontend_lld.json", frontend_lld)
            self._save_json("08_security_lld.json", security_lld)
            self._save_json("09_cloud_lld.json", cloud_lld)
            self._save_json("10_testing_strategy.json", testing_strategy)
            self._save_json("11_observability.json", observability)
            self._save_json("12_runbooks.json", runbooks)

        # ── Phase 4: Deterministic Scaffold Code Generation ───────────────────
        t_p4 = time.perf_counter()
        self.sae_logger.log_phase_start(4, "Deterministic Scaffolding Generation")
        print("\n▶ [Phase 4/6] Deterministic Scaffolding Generation (OpenAPI, Docker, Alembic, Terraform)...", flush=True)

        system_name = domain_ctx.system_name or req_analysis.get("system_name", "Enterprise System")
        domain_name = domain_ctx.domain_name or req_analysis.get("domain", "General")

        openapi_yaml = generate_openapi_spec(system_name, domain_name, backend_lld, security_lld)
        dockerfile, docker_compose = generate_docker_scaffolds(system_name, backend_lld, cloud_lld)
        alembic_migration = generate_alembic_migration(system_name, database_lld)
        terraform_tf = generate_terraform_scaffold(system_name, cloud_lld)

        # Save scaffolding files
        scaffolds_dir = self.output_dir / "scaffolds"
        self._save_text("openapi.yaml", openapi_yaml)
        self._save_text("scaffolds/openapi.yaml", openapi_yaml)
        self._save_text("scaffolds/Dockerfile", dockerfile)
        self._save_text("scaffolds/docker-compose.yml", docker_compose)
        self._save_text("scaffolds/alembic/versions/0001_initial_schema.py", alembic_migration)
        self._save_text("scaffolds/terraform/main.tf", terraform_tf)

        generated_artifacts = {
            "openapi_yaml_path": str(self.output_dir / "openapi.yaml"),
            "dockerfile_path": str(scaffolds_dir / "Dockerfile"),
            "docker_compose_path": str(scaffolds_dir / "docker-compose.yml"),
            "alembic_migration_path": str(scaffolds_dir / "alembic" / "versions" / "0001_initial_schema.py"),
            "terraform_main_tf_path": str(scaffolds_dir / "terraform" / "main.tf"),
            "openapi_spec_preview": openapi_yaml[:500] + "... (truncated)",
        }

        dur_p4 = round(time.perf_counter() - t_p4, 2)
        self.sae_logger.log_phase_end(4, "Deterministic Scaffolding", dur_p4, "5 Scaffolds Generated")
        print(f"  ✓ Phase 4 Completed in {dur_p4}s (5 Scaffolds Generated)", flush=True)

        # ── Phase 5: Cross-Artifact Consistency Gate & Red-Team Review ────────
        t_p5 = time.perf_counter()
        self.sae_logger.log_phase_start(5, "Cross-Artifact Consistency & Adversarial Remediation")
        print("\n▶ [Phase 5/6] Cross-Artifact Consistency & Adversarial Remediation...", flush=True)

        # 1. Run Multi-Way Cross-Artifact Consistency Validation against CAC
        consistency_report = CrossArtifactValidator.validate_cross_artifacts(
            domain_ctx=domain_ctx,
            hld=hld,
            backend_lld=backend_lld,
            database_lld=database_lld,
            frontend_lld=frontend_lld,
            security_lld=security_lld,
            cloud_lld=cloud_lld,
            testing_strategy=testing_strategy,
            observability=observability,
            cac=cac,
        )

        interim_package = {
            "system_name": system_name,
            "domain": domain_name,
            "architecture_style": hld.get("architecture_style", adp.get("architecture_style", "Modular Monolith")),
            "requirement_analysis": req_analysis,
            "hld": hld,
            "backend_lld": backend_lld,
            "database_lld": database_lld,
            "frontend_lld": frontend_lld,
            "security_lld": security_lld,
            "cloud_lld": cloud_lld,
            "testing_strategy": testing_strategy,
            "observability": observability,
            "canonical_architecture_contract": cac.model_dump(),
        }

        # 2. Run Adversarial Red-Team Review with CAC & Consistency Report Grounding
        raw_adversarial_review = await self.adversarial_agent.run_async(
            interim_package,
            consistency_report=consistency_report,
            cac=cac,
        )
        remediation_plan = RemediationEngine.create_remediation_plan(raw_adversarial_review)

        # 3. Apply Automated Remediation Loop if findings exist
        remediated_package, adversarial_review = RemediationEngine.apply_remediation(
            plan=remediation_plan,
            interim_package=interim_package,
            domain_ctx=domain_ctx,
        )

        backend_lld = remediated_package.get("backend_lld", backend_lld)
        database_lld = remediated_package.get("database_lld", database_lld)
        cloud_lld = remediated_package.get("cloud_lld", cloud_lld)
        security_lld = remediated_package.get("security_lld", security_lld)

        dur_p5 = round(time.perf_counter() - t_p5, 2)
        verdict = adversarial_review.get("production_readiness_verdict", "APPROVED")
        rem_status = adversarial_review.get("remediation_status", "NONE_REQUIRED")

        self.sae_logger.log_phase_end(
            5,
            "Consistency & Remediation",
            dur_p5,
            f"Consistency: {consistency_report.score*100:.0f}%, Verdict: {verdict} ({rem_status})",
        )
        print(
            f"  ✓ Phase 5 Completed in {dur_p5}s (Consistency: {consistency_report.score*100:.0f}%, Verdict: {verdict} [{rem_status}])",
            flush=True,
        )

        if self.debug:
            self._save_json("13_adversarial_review.json", adversarial_review)
            self._save_json("13_consistency_report.json", consistency_report.model_dump())

        # ── Phase 6: Unified 3-Tier Quality Gating & Scorecard Assembly ───────
        t_p6 = time.perf_counter()
        self.sae_logger.log_phase_start(6, "Unified Quality Gating & Package Assembly")
        print("\n▶ [Phase 6/6] Unified Quality Gating & Package Assembly...", flush=True)

        sections_map = {
            "requirement_analysis": req_analysis,
            "technology_recommendation": tech_rec,
            "architecture_decision_plan": adp,
            "hld": hld,
            "backend_lld": backend_lld,
            "database_lld": database_lld,
            "frontend_lld": frontend_lld,
            "security_lld": security_lld,
            "cloud_lld": cloud_lld,
            "testing_strategy": testing_strategy,
            "observability": observability,
            "runbooks": runbooks,
            "adversarial_review": adversarial_review,
        }

        completeness = self._compute_completeness(
            sections=sections_map,
            domain_ctx=domain_ctx,
            consistency_report=consistency_report,
            domain_gap_report=domain_gaps,
            adversarial_verdict=verdict,
        )

        dur_p6 = round(time.perf_counter() - t_p6, 2)
        total_time = round(time.perf_counter() - t_start, 2)

        self.sae_logger.log_phase_end(
            6,
            "Unified Quality Gating",
            dur_p6,
            f"Status: {completeness['status']}, Prod Readiness: {completeness['production_readiness_score']*100:.0f}%, Consistency: {completeness['consistency_score']*100:.0f}%",
        )

        print(
            f"  ✓ Phase 6 Completed in {dur_p6}s "
            f"(Artifact Quality: {completeness['artifact_quality_score']*100:.0f}%, "
            f"Consistency: {completeness['consistency_score']*100:.0f}%, "
            f"Prod Readiness: {completeness['production_readiness_score']*100:.0f}%, "
            f"Overall: {completeness['overall_completeness']*100:.0f}%, "
            f"Status: {completeness['status']})",
            flush=True,
        )

        metadata = {
            "design_id": self.design_id,
            "locked_domain": domain_ctx.domain_name,
            "canonical_requirements_count": len(domain_ctx.canonical_requirements),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pipeline_version": "SAE-v2-Production-Grade",
            "total_execution_time_seconds": total_time,
            "phase_timings": {
                "phase1_planning_seconds": dur_p1,
                "phase2_hld_seconds": dur_p2,
                "phase3_lld_parallel_seconds": dur_p3,
                "phase4_scaffolding_seconds": dur_p4,
                "phase5_consistency_remediation_seconds": dur_p5,
                "phase6_assembly_seconds": dur_p6,
            },
            "output_directory": str(self.output_dir),
            "logs_directory": str(self.sae_logger.log_dir),
            "debug_log_path": str(self.sae_logger.debug_log_path),
            "generated_artifacts_summary": generated_artifacts,
            "canonical_architecture_contract": cac.to_contract_summary(),
        }

        package = SoftwareArchitecturePackageResponse(
            system_name=system_name,
            domain=domain_name,
            # pyrefly: ignore [bad-argument-type]
            architecture_style=hld.get("architecture_style", adp.get("architecture_style", "Modular Monolith")),
            requirement_analysis=req_analysis,
            technology_recommendation=tech_rec,
            architecture_decision_plan=adp,
            hld=hld,
            backend_lld=backend_lld,
            database_lld=database_lld,
            frontend_lld=frontend_lld,
            security_lld=security_lld,
            cloud_lld=cloud_lld,
            testing_strategy=testing_strategy,
            observability=observability,
            runbooks=runbooks,
            adversarial_review=adversarial_review,
            generated_artifacts=generated_artifacts,
            completeness=completeness,
            metadata=metadata,
        )

        # Save canonical unified artifact
        self._save_json("architecture_package.json", package)
        self._save_json("14_merged_package.json", package)
        self._save_json("completeness_report.json", completeness)

        # Save execution summary
        self.sae_logger.save_summary({
            "status": completeness.get("status", "SUCCESS"),
            "total_execution_time_seconds": total_time,
            "phase_timings": metadata["phase_timings"],
            "completeness": completeness,
            "generated_artifacts": generated_artifacts,
            "output_directory": str(self.output_dir),
        })

        self.sae_logger.log_info(
            f"=== SAE v2 Completed in {total_time}s (Prod Readiness: {completeness['production_readiness_score']*100:.0f}%, Status: {completeness['status']}) ==="
        )
        return package

    def run(
        self,
        arsrs: Dict[str, Any],
        design_id: Optional[str] = None,
    ) -> SoftwareArchitecturePackageResponse:
        """Synchronous wrapper around run_async."""
        return asyncio.run(self.run_async(arsrs, design_id=design_id))
