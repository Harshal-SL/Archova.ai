"""
Architecture-aware query builder.

Responsibilities:
  1. Detect query intent (architecture, security, scalability, …)
  2. Map intent → relevant Qdrant categories  (never search irrelevant buckets)
  3. Expand a single user query into multiple semantic sub-queries
  4. Build clean natural-language retrieval text from structured requirement JSON

None of the methods embed raw JSON.  They always produce human-readable
retrieval strings that are meaningful for cosine similarity search.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import ENABLE_QUERY_EXPANSION, MAX_EXPANSION_QUERIES


logger = logging.getLogger(__name__)


# ── Real category names as stored in Qdrant ──────────────────────────────────
# Discovered by inspecting the collection payload.

_ALL_CATEGORIES: List[str] = [
    "domain_architectures",
    "category_12_application_archetypes",
    "category_1_architecture_patterns",
    "category_2_architecture_decisions",
    "category_3_scaling_techniques",
    "category_4_caching_strategies",
    "category_5_database_design",
    "category_6_messaging_systems",
    "category_7_infrastructure_components",
    "category_8_deployment_strategies",
    "category_9_security_architecture",
    "category_10_real_world_systems",
    "category_11_failure_modes",
    "system_components",
    "technology_guides",
    "hld_templates",
    "lld_templates",
    "nfr_mapping",
    "production_readiness",
    "architecture_decision_matrix",
    "cloud_architecture",
    "ai_systems",
]

# ── Intent → category mapping ─────────────────────────────────────────────────

_INTENT_CATEGORIES: Dict[str, List[str]] = {
    "architecture_generation": [
        "domain_architectures",
        "category_12_application_archetypes",
        "category_1_architecture_patterns",
        "category_2_architecture_decisions",
        "hld_templates",
        "system_components",
        "architecture_decision_matrix",
        "category_10_real_world_systems",
        "category_3_scaling_techniques",
        "category_4_caching_strategies",
        "category_6_messaging_systems",
        "category_9_security_architecture",
        "category_8_deployment_strategies",
        "category_7_infrastructure_components",
        "technology_guides",
        "nfr_mapping",
        "production_readiness",
    ],
    "scalability": [
        "category_3_scaling_techniques",
        "category_4_caching_strategies",
        "nfr_mapping",
        "production_readiness",
        "category_7_infrastructure_components",
        "category_1_architecture_patterns",
    ],
    "security": [
        "category_9_security_architecture",
        "category_2_architecture_decisions",
        "production_readiness",
        "nfr_mapping",
        "system_components",
    ],
    "database": [
        "category_5_database_design",
        "technology_guides",
        "architecture_decision_matrix",
        "system_components",
    ],
    "messaging": [
        "category_6_messaging_systems",
        "technology_guides",
        "category_7_infrastructure_components",
        "architecture_decision_matrix",
    ],
    "deployment": [
        "category_8_deployment_strategies",
        "cloud_architecture",
        "production_readiness",
        "category_7_infrastructure_components",
    ],
    "cloud": [
        "cloud_architecture",
        "category_8_deployment_strategies",
        "production_readiness",
        "technology_guides",
    ],
    "technology_selection": [
        "technology_guides",
        "architecture_decision_matrix",
        "system_components",
        "category_4_caching_strategies",
        "category_5_database_design",
        "category_6_messaging_systems",
    ],
    "failure_resilience": [
        "category_11_failure_modes",
        "production_readiness",
        "category_1_architecture_patterns",
        "nfr_mapping",
    ],
    "ai_systems": [
        "ai_systems",
        "category_1_architecture_patterns",
        "technology_guides",
        "system_components",
    ],
}

# Keywords used to detect intent from free-text
_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "scalability": [
        "scale", "million users", "high load", "distributed", "horizontal",
        "vertical", "performance", "throughput", "latency", "load balancer",
        "auto scaling", "traffic",
    ],
    "security": [
        "security", "auth", "authentication", "authorization", "jwt", "oauth",
        "encryption", "https", "rbac", "zero trust", "firewall", "vulnerability",
        "compliance", "gdpr",
    ],
    "database": [
        "database", "sql", "nosql", "postgres", "mysql", "mongodb", "cassandra",
        "redis", "schema", "query", "index", "sharding", "replication",
    ],
    "messaging": [
        "kafka", "rabbitmq", "queue", "event", "pub/sub", "message", "stream",
        "notification", "async", "event-driven", "broker",
    ],
    "deployment": [
        "deploy", "kubernetes", "docker", "container", "ci/cd", "pipeline",
        "devops", "helm", "rollout", "blue-green", "canary",
    ],
    "cloud": [
        "aws", "azure", "gcp", "cloud", "lambda", "s3", "ec2", "serverless",
        "managed service", "iaas", "paas",
    ],
    "technology_selection": [
        "which", "compare", "vs", "versus", "choose", "best", "recommend",
        "trade-off", "pros and cons",
    ],
    "failure_resilience": [
        "fault tolerant", "resilience", "retry", "circuit breaker", "failover",
        "disaster recovery", "high availability", "99.9", "uptime", "redundancy",
    ],
    "ai_systems": [
        "ai", "machine learning", "ml", "llm", "rag", "vector", "embedding",
        "recommendation", "nlp", "model", "inference",
    ],
}

# Domain-specific query expansions (keyword → expansion templates)
_DOMAIN_EXPANSIONS: Dict[str, List[str]] = {
    "food delivery": [
        "Food Delivery Platform Architecture",
        "Real-Time Order Tracking System Design",
        "Restaurant and Courier Marketplace Architecture",
        "Geolocation and Dispatch Service Design",
        "Food Delivery Notification and Push System",
    ],
    "ride sharing": [
        "Ride Sharing Platform Architecture",
        "Real-Time Driver Matching and Dispatch",
        "Geolocation Tracking and Maps Integration",
        "Dynamic Pricing Engine Architecture",
    ],
    "e-commerce": [
        "E-Commerce Platform Architecture",
        "Product Catalog and Search Service Design",
        "Shopping Cart and Checkout Flow Architecture",
        "Order Management and Fulfillment System",
        "Payment Gateway Integration Architecture",
    ],
    "social media": [
        "Social Media Feed Architecture",
        "User Graph and Follow System Design",
        "Content Delivery and Media Storage Architecture",
        "Real-Time Notification Service",
    ],
    "streaming": [
        "Video Streaming Platform Architecture",
        "Content Delivery Network Design",
        "Adaptive Bitrate Streaming Architecture",
        "Content Recommendation Engine",
    ],
    "payment": [
        "Payment Processing Architecture",
        "Transaction Ledger and Double-Entry System",
        "Payment Gateway Integration Design",
        "Fraud Detection Architecture",
    ],
    "messaging": [
        "Real-Time Messaging Architecture",
        "WebSocket and Long-Polling Design",
        "Message Queue and Delivery Architecture",
        "Push Notification Service Design",
    ],
    "healthcare": [
        "Healthcare Platform Architecture",
        "Patient Data Management System",
        "HIPAA-Compliant Architecture Design",
        "Appointment Scheduling Service Architecture",
    ],
    "banking": [
        "Banking Platform Architecture",
        "Core Banking System Design",
        "Fraud Detection and Prevention Architecture",
        "Transaction Processing and Ledger Design",
    ],
    "search": [
        "Search Engine Architecture",
        "Inverted Index and Ranking Design",
        "Full-Text Search Service Architecture",
        "Autocomplete and Suggestion System",
    ],
}

# Generic expansion templates for any system with scale/NFR signals
_SCALE_EXPANSIONS: List[str] = [
    "Microservices Architecture Patterns",
    "API Gateway and Service Mesh Design",
    "Horizontal Scaling and Load Balancing Architecture",
    "Distributed Caching with Redis Architecture",
    "Message Queue Architecture for Async Processing",
    "High Availability and Fault Tolerance Patterns",
    "Database Sharding and Read Replica Architecture",
    "CDN and Static Asset Delivery Architecture",
]

_NFR_EXPANSIONS: Dict[str, str] = {
    "availability": "High Availability Architecture 99.9 percent uptime",
    "latency": "Low Latency Architecture Real-Time System Design",
    "throughput": "High Throughput Distributed System Architecture",
    "security": "Secure Architecture Authentication Authorization Encryption",
    "scalability": "Horizontal Scalability Auto Scaling Architecture",
    "observability": "Observability Monitoring Logging Distributed Tracing Architecture",
}


@dataclass
class QueryPlan:
    """
    The result of query planning: primary query, expansions, and target categories.
    """
    primary_query: str
    expanded_queries: List[str] = field(default_factory=list)
    target_categories: List[str] = field(default_factory=list)
    detected_intents: List[str] = field(default_factory=list)

    @property
    def all_queries(self) -> List[str]:
        """Primary query followed by unique expansions."""
        seen = {self.primary_query}
        result = [self.primary_query]
        for q in self.expanded_queries:
            if q not in seen:
                seen.add(q)
                result.append(q)
        return result


class QueryBuilder:
    """
    Converts a free-text query or structured requirement dict into a QueryPlan.

    Usage::

        plan = QueryBuilder.plan("food delivery for 20M users")
        plan = QueryBuilder.plan_from_requirements(parameters_dict)
    """

    # ── Public API ────────────────────────────────────────────────────────────

    @staticmethod
    def plan(query: str) -> QueryPlan:
        """
        Build a QueryPlan from a free-text query string.

        Args:
            query: Raw user query.

        Returns:
            QueryPlan with primary query, expansions, and categories.
        """
        query = query.strip()
        intents = QueryBuilder._detect_intents(query)
        categories = QueryBuilder._categories_for_intents(intents)
        expansions = QueryBuilder._expand_query(query, intents) if ENABLE_QUERY_EXPANSION else []

        logger.debug(
            f"QueryPlan: intents={intents}, categories={len(categories)}, "
            f"expansions={len(expansions)}"
        )
        return QueryPlan(
            primary_query=query,
            expanded_queries=expansions[:MAX_EXPANSION_QUERIES],
            target_categories=categories,
            detected_intents=intents,
        )

    @staticmethod
    def plan_from_requirements(requirements: Dict[str, Any]) -> QueryPlan:
        """
        Build a QueryPlan from a structured requirement dictionary.

        Extracts natural-language fields without embedding raw JSON.

        Args:
            requirements: Structured requirements as produced by the extractor.

        Returns:
            QueryPlan with primary query, expansions, and categories.
        """
        primary = QueryBuilder._requirements_to_text(requirements)
        intents = QueryBuilder._detect_intents(primary)

        # Add intents derived from explicit requirement fields
        intents = list(dict.fromkeys(
            intents + QueryBuilder._intents_from_requirements(requirements)
        ))

        categories = QueryBuilder._categories_for_intents(intents)
        expansions = (
            QueryBuilder._expand_from_requirements(requirements, primary, intents)
            if ENABLE_QUERY_EXPANSION
            else []
        )

        return QueryPlan(
            primary_query=primary,
            expanded_queries=expansions[:MAX_EXPANSION_QUERIES],
            target_categories=categories,
            detected_intents=intents,
        )

    # ── Legacy compatibility (design_service.py calls QueryBuilder.build_query) ──

    @staticmethod
    def build_query(requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy shim used by design_service.py.

        Returns the same shape as before: {query_text, target_categories}.
        """
        plan = QueryBuilder.plan_from_requirements(requirements)
        return {
            "query_text": plan.primary_query,
            "target_categories": plan.target_categories,
            "expanded_queries": plan.expanded_queries,
            "detected_intents": plan.detected_intents,
        }

    @staticmethod
    def build_hld_query(requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Build a query optimised for HLD generation."""
        base = QueryBuilder.build_query(requirements)
        hld_cats = [
            c for c in base["target_categories"]
            if "lld" not in c
        ]
        return {**base, "target_categories": hld_cats, "purpose": "hld"}

    @staticmethod
    def build_lld_query(requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Build a query optimised for LLD generation."""
        base = QueryBuilder.build_query(requirements)
        lld_cats = [
            c for c in base["target_categories"]
            if c in {
                "lld_templates", "system_components", "technology_guides",
                "architecture_decision_matrix", "category_5_database_design",
                "category_6_messaging_systems",
            }
        ] or ["lld_templates", "system_components", "technology_guides"]
        return {**base, "target_categories": lld_cats, "purpose": "lld"}

    # ── Intent detection ──────────────────────────────────────────────────────

    @staticmethod
    def _detect_intents(text: str) -> List[str]:
        """Return a ranked list of intents detected in *text*."""
        lower = text.lower()
        scores: Dict[str, int] = {}

        for intent, keywords in _INTENT_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in lower)
            if count:
                scores[intent] = count

        # architecture_generation is always included — it's the default intent
        scores.setdefault("architecture_generation", 1)

        return sorted(scores, key=lambda k: -scores[k])

    @staticmethod
    def _intents_from_requirements(req: Dict[str, Any]) -> List[str]:
        """Derive additional intents from structured requirement fields."""
        intents: List[str] = []
        nfr = req.get("non_functional_requirements", {})
        if isinstance(nfr, dict):
            if nfr.get("availability") or nfr.get("reliability"):
                intents.append("failure_resilience")
            if nfr.get("performance") or nfr.get("latency"):
                intents.append("scalability")
            if nfr.get("security"):
                intents.append("security")
            if nfr.get("scalability"):
                intents.append("scalability")
        if req.get("external_services"):
            intents.append("technology_selection")
        return intents

    # ── Category routing ──────────────────────────────────────────────────────

    @staticmethod
    def _categories_for_intents(intents: List[str]) -> List[str]:
        """Return the union of categories for all detected intents, ordered."""
        seen: Dict[str, int] = {}
        for intent in intents:
            for cat in _INTENT_CATEGORIES.get(intent, []):
                seen[cat] = seen.get(cat, 0) + 1

        # Sort by frequency so the most-relevant categories come first
        return sorted(seen, key=lambda c: -seen[c])

    # ── Query expansion ───────────────────────────────────────────────────────

    @staticmethod
    def _expand_query(text: str, intents: List[str]) -> List[str]:
        """Generate semantic sub-queries from a free-text input."""
        lower = text.lower()
        expansions: List[str] = []

        # 1. Domain-specific expansions
        for domain, templates in _DOMAIN_EXPANSIONS.items():
            if domain in lower:
                expansions.extend(templates)

        # 2. Scale signal → generic architectural expansions
        scale_signals = ["million", "billion", "users", "requests", "large scale"]
        if any(s in lower for s in scale_signals):
            expansions.extend(_SCALE_EXPANSIONS[:4])

        # 3. NFR-driven expansions
        for nfr_key, expansion in _NFR_EXPANSIONS.items():
            if nfr_key in lower or nfr_key in intents:
                expansions.append(expansion)

        # 4. Intent-driven fallback expansions
        if not expansions:
            for intent in intents[:3]:
                if intent == "architecture_generation":
                    expansions.append("Microservices Architecture Patterns")
                    expansions.append("System Design Components and Services")
                elif intent == "scalability":
                    expansions.append("Horizontal Scaling and Load Balancing")
                elif intent == "security":
                    expansions.append("Authentication and Authorization Architecture")
                elif intent == "database":
                    expansions.append("Database Selection SQL vs NoSQL Architecture")
                elif intent == "messaging":
                    expansions.append("Event-Driven Architecture with Message Queues")
                elif intent == "deployment":
                    expansions.append("Kubernetes Deployment and CI/CD Pipeline")

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for q in expansions:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        return unique

    @staticmethod
    def _expand_from_requirements(
        req: Dict[str, Any],
        primary: str,
        intents: List[str],
    ) -> List[str]:
        """Generate expansions from structured requirement fields."""
        expansions = QueryBuilder._expand_query(primary, intents)

        # Add NFR-specific expansions from structured fields
        nfr = req.get("non_functional_requirements", {})
        if isinstance(nfr, dict):
            for key in ("availability", "latency", "throughput", "security", "scalability"):
                if nfr.get(key) and key in _NFR_EXPANSIONS:
                    expansions.append(_NFR_EXPANSIONS[key])

        # Extract system_type as an expansion
        system_type = _extract_value(req, "system_type")
        if system_type:
            expansions.append(f"{system_type} Architecture Design Patterns")

        return expansions

    # ── Requirement → text ────────────────────────────────────────────────────

    @staticmethod
    def _requirements_to_text(req: Dict[str, Any]) -> str:
        """
        Convert a requirement dict to a clean natural-language retrieval query.

        Never embeds raw JSON.  Produces human-readable text for cosine search.
        """
        parts: List[str] = []

        field_order = [
            ("goal", "Goal"),
            ("system_type", "System Type"),
            ("core_objectives", "Objectives"),
            ("actors", "Actors"),
            ("functional_requirements", "Features"),
            ("non_functional_requirements", "Requirements"),
            ("external_services", "External Services"),
            ("system_behaviour", "Behaviour"),
            ("inputs", "Inputs"),
            ("outputs", "Outputs"),
            ("scale", "Scale"),
            ("constraints", "Constraints"),
        ]

        for key, label in field_order:
            value = _extract_value(req, key)
            if not value:
                continue
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value if v)
            elif isinstance(value, dict):
                # Flatten NFR dict to key: value pairs
                value_str = ", ".join(
                    f"{k}: {v}" for k, v in value.items() if v
                )
            else:
                value_str = str(value).strip()
            if value_str:
                parts.append(f"{label}: {value_str}")

        return "\n".join(parts) if parts else (
            "Design a scalable, secure software system architecture "
            "with clear HLD and LLD components."
        )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _extract_value(req: Dict[str, Any], key: str) -> Any:
    """
    Extract a value from a requirement dict that may use the
    ``{"value": ..., "ai_suggestion": ...}`` wrapper format.
    """
    node = req.get(key)
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


# ── Per-Agent RAG Query Construction Functions ───────────────────────────────

def _flatten_context_snippet(ctx: Dict[str, Any], max_chars: int = 400) -> str:
    """Helper to extract a concise text representation from an agent context payload."""
    if not ctx:
        return ""
    parts = []
    for k in ["system_name", "domain", "architecture_style", "framework", "database"]:
        if k in ctx and ctx[k]:
            parts.append(f"{k}: {ctx[k]}")
    text = ", ".join(parts)
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    return text


def build_security_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for SecurityLLDGenerationAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    hld_sec = context.get("security_overview", {}) or {}
    sec_desc = hld_sec.get("authentication", "") if isinstance(hld_sec, dict) else ""
    return (
        f"Security architecture design patterns, OAuth2 PKCE authorization code flow, JWT RS256 token lifecycle, "
        f"Role-Based Access Control (RBAC), OWASP Top 10 API safeguards, AES-256 encryption at rest, TLS 1.3 in transit, "
        f"threat modeling mitigations, rate limiting, and regulatory compliance standards for {domain} {sec_desc}".strip()
    )


def build_database_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for DatabaseLLDGenerationAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    db_tech = context.get("technology_stack", {}).get("database", "") if isinstance(context.get("technology_stack"), dict) else ""
    data_strat = context.get("data_strategy", {}) or {}
    strat_desc = data_strat.get("primary_database", "") if isinstance(data_strat, dict) else ""
    return (
        f"Relational database schema design patterns, PostgreSQL {db_tech} {strat_desc}, table normalisation, "
        f"B-Tree and GIN indexing strategies, foreign key constraints, connection pool sizing (PgBouncer), "
        f"ACID transaction isolation, optimistic locking, and automated database migration schemas for {domain}".strip()
    )


def build_cloud_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for CloudLLDGenerationAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    dep_strat = context.get("deployment_strategy", {}) or {}
    target_cloud = dep_strat.get("target_cloud", "") if isinstance(dep_strat, dict) else ""
    return (
        f"Cloud infrastructure architecture, AWS ECS Fargate container orchestration, {target_cloud}, "
        f"custom VPC multi-AZ public private subnet topology, Application Load Balancer path routing, "
        f"target tracking auto-scaling policies, S3 static assets CDN, CloudWatch metrics alerting, and CI/CD pipeline for {domain}".strip()
    )


def build_backend_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for BackendLLDGenerationAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    tech_stack = context.get("technology_stack", {}) or {}
    backend_fw = tech_stack.get("backend", "FastAPI Python") if isinstance(tech_stack, dict) else "FastAPI"
    return (
        f"Backend low level design patterns, Clean Layered Architecture, {backend_fw}, "
        f"Repository pattern, RESTful API versioning strategy, RFC 7807 Problem Details error handling, "
        f"row-level locking (SELECT FOR UPDATE) concurrency, and client idempotency keys for {domain}".strip()
    )


def build_frontend_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for FrontendLLDGenerationAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    tech_stack = context.get("technology_stack", {}) or {}
    frontend_fw = tech_stack.get("frontend", "React Next.js") if isinstance(tech_stack, dict) else "React"
    return (
        f"Frontend single page application design patterns, {frontend_fw}, component hierarchy, "
        f"global state management (Zustand/Redux), client-side routing, API integration hooks, "
        f"secure token storage, responsive UI layouts, and accessibility standards for {domain}".strip()
    )


def build_hld_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for HLDGenerationAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    style = context.get("architecture_style", "Modular Monolith")
    return (
        f"High Level System Design patterns, {style}, domain module boundary decomposition, "
        f"synchronous REST vs asynchronous message bus communication, API gateway topology, "
        f"distributed caching strategies (Redis), and high availability architecture for {domain}".strip()
    )


def build_technology_advisor_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for TechnologyAdvisorAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    sys_type = context.get("system_type", "Web Application")
    return (
        f"Enterprise technology stack selection matrix, {sys_type}, framework comparison (FastAPI, Spring Boot, Node.js), "
        f"database evaluation SQL vs NoSQL (PostgreSQL, MongoDB), caching layers (Redis), and cloud hosting trade-offs for {domain}".strip()
    )


def build_requirement_analysis_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for RequirementAnalysisAgent."""
    domain = context.get("domain", "") or context.get("industry", "Enterprise Software")
    return (
        f"Software requirement engineering principles, {domain} standard functional workflows, "
        f"actors and role permissions, non-functional requirement categorization (performance, security, availability), "
        f"and domain feature checklist gap analysis".strip()
    )


def build_testing_strategy_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for TestingStrategyAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    return (
        f"Software quality assurance and test automation strategy, unit test coverage targets, "
        f"pytest integration testing with ephemeral container databases (testcontainers), "
        f"OpenAPI contract testing (Schemathesis), Locust k6 load testing traffic modeling, and CI/CD test gates for {domain}".strip()
    )


def build_observability_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for ObservabilityAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    return (
        f"Site Reliability Engineering (SRE) observability architecture, Service Level Objectives (SLOs), "
        f"SLIs, error budget burn rate policies, Prometheus metric instrumentation (Golden Signals), "
        f"Grafana dashboard layouts, OpenTelemetry distributed tracing, and health check probes for {domain}".strip()
    )


def build_runbook_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for RunbookAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    return (
        f"DevOps incident response runbooks, on-call engineer escalation tiers, automated deployment rollback procedures, "
        f"database migration downgrade steps, monthly disaster recovery backup restore drills (RTO/RPO), and data retention purge flows for {domain}".strip()
    )


def build_adversarial_review_query(context: Dict[str, Any]) -> str:
    """Build domain-specific RAG query for AdversarialReviewAgent."""
    domain = context.get("domain", "") or context.get("system_name", "")
    style = context.get("architecture_style", "")
    return (
        f"Red-team architecture critique, common software failure modes, Single Points of Failure (SPOFs), "
        f"database connection pool exhaustion, cache thundering herd, unmitigated concurrency race conditions, "
        f"and horizontal scalability bottlenecks for {style} {domain}".strip()
    )


def build_query_for_role(role: str, context: Dict[str, Any]) -> str:
    """Route agent role to its dedicated query construction builder."""
    role_norm = (role or "").lower().replace("-", "_")

    if "security" in role_norm:
        return build_security_query(context)
    elif "database" in role_norm or "db" in role_norm:
        return build_database_query(context)
    elif "cloud" in role_norm or "infra" in role_norm:
        return build_cloud_query(context)
    elif "backend" in role_norm:
        return build_backend_query(context)
    elif "frontend" in role_norm:
        return build_frontend_query(context)
    elif role_norm == "hld":
        return build_hld_query(context)
    elif "tech" in role_norm or "advisor" in role_norm:
        return build_technology_advisor_query(context)
    elif "requirement" in role_norm:
        return build_requirement_analysis_query(context)
    elif "test" in role_norm or "qa" in role_norm:
        return build_testing_strategy_query(context)
    elif "observability" in role_norm or "sre" in role_norm:
        return build_observability_query(context)
    elif "runbook" in role_norm:
        return build_runbook_query(context)
    elif "adversarial" in role_norm or "review" in role_norm:
        return build_adversarial_review_query(context)
    else:
        domain = context.get("domain", "") or context.get("system_name", "Software System")
        return f"Software architecture design patterns, best practices, and components for {domain}".strip()

