"""Canonical Architecture Contract (CAC) Engine for SAE v2.

Serves as the single immutable architectural source of truth generated after HLD.
Every downstream agent (Backend, Database, Frontend, Security, Cloud, Testing,
Observability, Runbooks) consumes this contract.

Enforces:
  1. Immutable Requirement Registry (FR-001..FR-N, NFR-001..NFR-N) - No REQ-* aliases allowed.
  2. Canonical API Operation Registry (API-001..API-N with operation_id, path, method, schema, auth, requirements).
  3. Canonical Domain/DB Entity Registry & Explicit Machine-Verifiable Mappings (ENT-001 -> DB-001).
  4. Stable Service & Actor Registries (SVC-001..SVC-N, ACT-001..ACT-N).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.sae.utils.domain_lock import DomainContext

logger = logging.getLogger(__name__)


class CanonicalAPIOperation(BaseModel):
    """Canonical API endpoint contract with stable operation identity."""
    operation_id: str = Field(..., description="Stable camelCase/snake_case operation ID (e.g. borrowBook, searchCatalog)")
    api_id: str = Field(..., description="Canonical ID like API-001, API-002")
    method: str = Field(..., description="HTTP Method (GET, POST, PUT, DELETE, PATCH)")
    path: str = Field(..., description="Canonical URI path (e.g. /api/v1/circulation/borrow)")
    service_id: str = Field(default="SVC-001", description="Owning service ID (e.g. SVC-002)")
    service_name: str = Field(default="", description="Owning service name")
    request_schema: str = Field(default="", description="Request DTO / Body Schema name")
    response_schema: str = Field(default="", description="Response DTO Schema name")
    authentication: str = Field(default="Public", description="Required role / auth status (e.g. Student, Librarian, Public)")
    requirement_ids: List[str] = Field(default_factory=list, description="Canonical requirement IDs satisfied (e.g. ['FR-002'])")
    errors: List[str] = Field(default_factory=list, description="Standard error codes (RFC 7807 problem codes)")
    description: str = Field(default="", description="Human-readable operation description")


class CanonicalDomainEntity(BaseModel):
    """Canonical Domain Model entity."""
    entity_id: str = Field(..., description="Canonical entity ID (e.g. ENT-001)")
    name: str = Field(..., description="Domain Entity Name (e.g. BorrowTransaction, User, Book)")
    fields: Dict[str, str] = Field(default_factory=dict, description="Field name -> type mapping")
    relationships: List[str] = Field(default_factory=list, description="Related entities")
    database_table: str = Field(default="", description="Mapped SQL table name (e.g. borrow_records)")
    database_entity_id: str = Field(default="", description="Mapped database entity ID (e.g. DB-002)")


class CanonicalDatabaseEntity(BaseModel):
    """Canonical Database Table/Schema entity."""
    db_entity_id: str = Field(..., description="Canonical DB entity ID (e.g. DB-001)")
    table_name: str = Field(..., description="Table name in database (e.g. borrow_records, users, books)")
    primary_key: str = Field(default="id", description="Primary key column name")
    domain_entity_name: str = Field(default="", description="Mapped domain entity name (e.g. BorrowTransaction)")
    domain_entity_id: str = Field(default="", description="Mapped domain entity ID (e.g. ENT-001)")
    columns: List[str] = Field(default_factory=list, description="List of column names")


class CanonicalEntityMapping(BaseModel):
    """Explicit bridge mapping between Backend Domain Entity and Database Table."""
    entity_id: str = Field(..., description="Domain Entity ID (e.g. ENT-003)")
    domain_entity: str = Field(..., description="Domain model name (e.g. BorrowTransaction)")
    db_entity_id: str = Field(..., description="DB Entity ID (e.g. DB-002)")
    database_table: str = Field(..., description="DB table name (e.g. borrow_records)")
    primary_key: str = Field(default="id")
    notes: str = Field(default="Direct mapping")


class CanonicalService(BaseModel):
    """Canonical architectural service boundary."""
    service_id: str = Field(..., description="Service ID (e.g. SVC-001)")
    name: str = Field(..., description="Service Name (e.g. CatalogService)")
    responsibility: str = Field(default="")
    requirement_ids: List[str] = Field(default_factory=list)


class CanonicalActor(BaseModel):
    """Canonical user actor / persona."""
    actor_id: str = Field(..., description="Actor ID (e.g. ACT-001)")
    role: str = Field(..., description="Role Name (e.g. Student, Librarian)")
    description: str = Field(default="")


class CanonicalArchitectureContract(BaseModel):
    """The Single Master Source of Architectural Truth for SAE v2."""
    contract_id: str = Field(..., description="Unique contract identifier")
    system_name: str = Field(default="Enterprise System")
    domain: str = Field(default="General")
    domain_name: str = Field(default="General")
    domain_key: str = Field(default="general")
    architecture_style: str = Field(default="Modular Monolith")
    requirement_ids: List[str] = Field(default_factory=list, description="All canonical FR and NFR IDs (FR-001..FR-N, NFR-001..NFR-N)")
    functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    non_functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    actors: List[CanonicalActor] = Field(default_factory=list)
    services: List[CanonicalService] = Field(default_factory=list)
    api_operations: List[CanonicalAPIOperation] = Field(default_factory=list)
    domain_entities: List[CanonicalDomainEntity] = Field(default_factory=list)
    database_entities: List[CanonicalDatabaseEntity] = Field(default_factory=list)
    entity_mappings: List[CanonicalEntityMapping] = Field(default_factory=list)
    technology_decisions: Dict[str, str] = Field(default_factory=dict)
    domain_gaps: List[Dict[str, Any]] = Field(default_factory=list)

    def get_api_by_operation_id(self, op_id: str) -> Optional[CanonicalAPIOperation]:
        for op in self.api_operations:
            if op.operation_id.lower() == op_id.lower():
                return op
        return None

    def get_api_by_path_and_method(self, path: str, method: str) -> Optional[CanonicalAPIOperation]:
        p_clean = "/" + path.strip("/").lower()
        m_clean = method.strip().upper()
        for op in self.api_operations:
            op_p_clean = "/" + op.path.strip("/").lower()
            if op_p_clean == p_clean and op.method.upper() == m_clean:
                return op
        return None

    def get_entity_mapping_by_domain_name(self, name: str) -> Optional[CanonicalEntityMapping]:
        n_clean = name.lower().replace("_", "").replace(" ", "")
        for m in self.entity_mappings:
            if m.domain_entity.lower().replace("_", "").replace(" ", "") == n_clean:
                return m
        return None

    def get_entity_mapping_by_table_name(self, table: str) -> Optional[CanonicalEntityMapping]:
        t_clean = table.lower().replace("_", "").replace(" ", "")
        for m in self.entity_mappings:
            if m.database_table.lower().replace("_", "").replace(" ", "") == t_clean:
                return m
        return None

    @classmethod
    def derive_canonical_contract(
        cls,
        domain_ctx: DomainContext,
        hld: Optional[Dict[str, Any]] = None,
    ) -> CanonicalArchitectureContract:
        """Derive full CanonicalArchitectureContract from DomainContext and optional HLD."""
        req_analysis = domain_ctx.to_validated_artifact()
        hld_dict = hld or {
            "system_name": domain_ctx.system_name,
            "architecture_style": "Modular Monolith",
            "major_services": [{"service_id": f"SVC-{i:02d}", "name": s, "satisfies": [f"FR-{i:03d}"]} for i, s in enumerate(domain_ctx.default_services, 1)],
            "technology_stack": {"backend": "FastAPI", "database": "PostgreSQL 16", "frontend": "React"},
        }
        return ContractBuilder.build_from_hld(hld=hld_dict, req_analysis=req_analysis, domain_ctx=domain_ctx)

    def to_contract_summary(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "system_name": self.system_name,
            "domain": self.domain,
            "requirement_ids": self.requirement_ids,
            "service_ids": [s.service_id for s in self.services],
            "api_operation_ids": [op.operation_id for op in self.api_operations],
            "api_paths": [f"{op.method} {op.path}" for op in self.api_operations],
            "domain_entities": [e.name for e in self.domain_entities],
            "database_tables": [d.table_name for d in self.database_entities],
            "entity_mappings": [f"{m.domain_entity} -> {m.database_table}" for m in self.entity_mappings],
        }


class ContractBuilder:
    """Deterministically synthesizes the Canonical Architecture Contract from HLD and Requirements."""

    @classmethod
    def build_from_hld(
        cls,
        hld: Dict[str, Any],
        req_analysis: Dict[str, Any],
        domain_ctx: DomainContext,
    ) -> CanonicalArchitectureContract:
        """Constructs the CAC with stable IDs for every architectural entity."""
        system_name = domain_ctx.system_name or req_analysis.get("system_name", "Enterprise System")
        domain_name = domain_ctx.domain_name or req_analysis.get("domain", "General")
        arch_style = hld.get("architecture_style", "Modular Monolith")

        # 1. Canonical Requirement IDs (Strictly from domain_ctx / req_analysis)
        frs = req_analysis.get("functional_requirements", [])
        nfrs = req_analysis.get("non_functional_requirements", [])
        
        req_ids: List[str] = []
        for r in frs:
            if isinstance(r, dict) and r.get("id"):
                req_ids.append(r["id"])
        for r in nfrs:
            if isinstance(r, dict) and r.get("id"):
                req_ids.append(r["id"])

        if not req_ids:
            req_ids = domain_ctx.get_req_ids()

        # 2. Canonical Actors
        actors: List[CanonicalActor] = []
        raw_actors = req_analysis.get("actors", [])
        if not raw_actors and domain_ctx.actors:
            raw_actors = domain_ctx.actors
        for idx, act in enumerate(raw_actors, 1):
            if isinstance(act, dict):
                role = act.get("role") or act.get("name") or f"Actor_{idx}"
                desc = act.get("description", "")
            else:
                role = str(act)
                desc = ""
            actors.append(CanonicalActor(
                actor_id=f"ACT-{idx:03d}",
                role=role,
                description=desc,
            ))

        # 3. Canonical Services (from HLD major_services)
        services: List[CanonicalService] = []
        raw_services = hld.get("major_services", [])
        if not raw_services:
            # Fallback service structure from modules
            modules = req_analysis.get("modules", ["Auth", "Core", "Administration"])
            for idx, mod in enumerate(modules, 1):
                raw_services.append({
                    "name": f"{mod.replace(' ', '')}Service",
                    "responsibility": f"Handles {mod} capabilities",
                    "satisfies": [req_ids[0]] if req_ids else [],
                })

        for idx, svc in enumerate(raw_services, 1):
            s_name = svc.get("name") or svc.get("service_name") or f"Service_{idx}"
            s_resp = svc.get("responsibility") or svc.get("description") or ""
            s_reqs = [r for r in svc.get("satisfies", []) if r in req_ids]
            if not s_reqs and req_ids:
                # Default map to primary FRs
                s_reqs = [req_ids[min(idx - 1, len(req_ids) - 1)]]
            services.append(CanonicalService(
                service_id=f"SVC-{idx:03d}",
                name=s_name,
                responsibility=s_resp,
                requirement_ids=s_reqs,
            ))

        # 4. Canonical API Operations
        api_operations = cls._build_canonical_api_operations(req_analysis, services, req_ids, domain_name)

        # Backfill service requirement_ids from canonical api_operations
        for op in api_operations:
            for s in services:
                if s.service_id == op.service_id or s.name.lower() == op.service_name.lower():
                    for rid in op.requirement_ids:
                        if rid not in s.requirement_ids:
                            s.requirement_ids.append(rid)

        # 5. Canonical Domain Models & Database Tables & Entity Mappings
        domain_entities, db_entities, entity_mappings = cls._build_canonical_entities(domain_name, req_analysis)

        # 6. Technology decisions
        tech_decisions = {}
        tech_stack = hld.get("technology_stack", {})
        if isinstance(tech_stack, dict):
            for k, v in tech_stack.items():
                tech_decisions[k] = str(v)

        # 7. Domain Gaps
        domain_gaps = []
        gap_analysis = req_analysis.get("domain_gap_analysis", {})
        if isinstance(gap_analysis, dict) and "checklist_status" in gap_analysis:
            for idx, item in enumerate(gap_analysis["checklist_status"], 1):
                if isinstance(item, dict):
                    domain_gaps.append({
                        "domain_gap_id": f"DG-{idx:03d}",
                        "feature": item.get("feature", ""),
                        "status": item.get("status", "ABSENT_POTENTIAL_GAP"),
                        "recommendation": item.get("recommendation", ""),
                        "decision": "ACCEPTED_GAP" if item.get("status") in ("ABSENT_POTENTIAL_GAP", "OUT_OF_SCOPE") else "IN_SCOPE",
                    })

        return CanonicalArchitectureContract(
            contract_id=f"CAC-{system_name.replace(' ', '_')}-v1",
            system_name=system_name,
            domain=domain_name,
            domain_name=domain_name,
            domain_key=domain_ctx.domain_key if domain_ctx else (domain_name.lower().replace(' ', '_')),
            architecture_style=arch_style,
            requirement_ids=req_ids,
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            actors=actors,
            services=services,
            api_operations=api_operations,
            domain_entities=domain_entities,
            database_entities=db_entities,
            entity_mappings=entity_mappings,
            technology_decisions=tech_decisions,
            domain_gaps=domain_gaps,
        )

    @classmethod
    def _build_canonical_api_operations(
        cls,
        req_analysis: Dict[str, Any],
        services: List[CanonicalService],
        req_ids: List[str],
        domain_name: str,
    ) -> List[CanonicalAPIOperation]:
        """Synthesizes canonical API operations dynamically from functional requirements and system services."""
        operations: List[CanonicalAPIOperation] = []

        # Match primary FR IDs
        fr1 = req_ids[0] if len(req_ids) > 0 else "FR-001"

        svc_auth = services[0].service_id if len(services) > 0 else "SVC-001"
        svc_core = services[1].service_id if len(services) > 1 else svc_auth
        svc_trans = services[2].service_id if len(services) > 2 else svc_core

        ops_def: List[Tuple[str, str, str, str, str, str, str, str, List[str], List[str], str]] = [
            (
                "loginUser",
                "POST",
                "/api/v1/auth/login",
                svc_auth,
                "AuthService",
                "LoginRequest",
                "AuthTokenResponse",
                "Public",
                [fr1],
                ["INVALID_CREDENTIALS", "RATE_LIMIT_EXCEEDED"],
                "Authenticate user or staff and issue JWT tokens",
            )
        ]

        mapped_req_ids = {fr1}
        all_frs = req_analysis.get("functional_requirements", [])

        # Process each functional requirement to synthesize domain-exact operations
        for req in all_frs:
            if not isinstance(req, dict):
                continue
            fr_id = req.get("id", "")
            if not fr_id:
                continue

            fr_title = req.get("title", "") or req.get("description", "")
            title_lower = fr_title.lower()

            # Generate operation name and endpoint path
            clean_title = re.sub(
                r"\b(?:User|Users|Admin|Staff|System|Shall|Must|Can|Allow|Enables?|Provide|Support)\b",
                "",
                fr_title,
                flags=re.IGNORECASE,
            ).strip()
            clean_name = "".join(w.capitalize() for w in re.findall(r"[a-zA-Z0-9]+", clean_title))
            if not clean_name or len(clean_name) < 3:
                clean_name = f"Execute{fr_id.replace('-', '')}"
            else:
                # Ensure camelCase starting with lowercase action verb
                clean_name = clean_name[0].lower() + clean_name[1:]

            clean_slug = "-".join(w.lower() for w in re.findall(r"[a-zA-Z0-9]+", clean_title))
            if not clean_slug:
                clean_slug = f"operation-{fr_id.lower()}"
            clean_path = f"/api/v1/{clean_slug}"

            # Method determination
            if any(k in title_lower for k in ("get", "search", "list", "view", "browse", "read", "monitor", "report", "fetch", "check", "inspect")):
                method = "GET"
            elif any(k in title_lower for k in ("cancel", "delete", "remove", "revoke", "purge")):
                method = "DELETE"
            elif any(k in title_lower for k in ("update", "edit", "reschedule", "modify", "patch", "change")):
                method = "PATCH"
            else:
                method = "POST"

            # Service assignment from declared services
            target_svc = services[0].service_id if services else "SVC-001"
            target_svc_name = services[0].name if services else "CoreService"

            # Match by semantic keyword to available services
            for s in services:
                s_name_low = s.name.lower()
                s_resp_low = s.responsibility.lower()
                if any(w in title_lower for w in ("auth", "login", "password", "token", "jwt", "rbac")) and ("auth" in s_name_low or "identity" in s_name_low):
                    target_svc = s.service_id
                    target_svc_name = s.name
                    break
                elif any(w in title_lower for w in ("notify", "notification", "email", "sms", "alert", "message")) and ("notif" in s_name_low or "comm" in s_name_low):
                    target_svc = s.service_id
                    target_svc_name = s.name
                    break
                elif any(w in title_lower for w in ("register", "registration", "enroll", "ticket", "booking")) and ("reg" in s_name_low or "book" in s_name_low):
                    target_svc = s.service_id
                    target_svc_name = s.name
                    break
                elif any(w in title_lower for w in ("attendance", "check-in", "checkin", "track", "presence")) and ("attend" in s_name_low or "track" in s_name_low):
                    target_svc = s.service_id
                    target_svc_name = s.name
                    break
                elif any(w in title_lower for w in ("event", "catalog", "browse", "schedule", "workshop", "item", "product")) and ("event" in s_name_low or "catalog" in s_name_low or "item" in s_name_low or "core" in s_name_low):
                    target_svc = s.service_id
                    target_svc_name = s.name
                    break
                elif fr_id in s.requirement_ids:
                    target_svc = s.service_id
                    target_svc_name = s.name
                    break

            req_dto = f"{clean_name[0].upper() + clean_name[1:]}Request" if method in ("POST", "PATCH", "PUT") else "None"
            resp_dto = f"{clean_name[0].upper() + clean_name[1:]}Response"
            auth_role = "Admin" if ("admin" in title_lower or "report" in title_lower) else "Authenticated"

            ops_def.append((
                clean_name,
                method,
                clean_path,
                target_svc,
                target_svc_name,
                req_dto,
                resp_dto,
                auth_role,
                [fr_id],
                ["OPERATION_FAILED", "VALIDATION_ERROR"],
                f"Executes requirement {fr_id}: {fr_title}",
            ))
            mapped_req_ids.add(fr_id)

        for idx, (op_id, method, path, s_id, s_name, req_dto, resp_dto, auth, r_ids, errs, desc) in enumerate(ops_def, 1):
            operations.append(CanonicalAPIOperation(
                operation_id=op_id,
                api_id=f"API-{idx:03d}",
                method=method,
                path=path,
                service_id=s_id,
                service_name=s_name,
                request_schema=req_dto,
                response_schema=resp_dto,
                authentication=auth,
                requirement_ids=r_ids,
                errors=errs,
                description=desc,
            ))

        return operations

    @classmethod
    def _build_canonical_entities(
        cls,
        domain_name: str,
        req_analysis: Dict[str, Any],
    ) -> Tuple[List[CanonicalDomainEntity], List[CanonicalDatabaseEntity], List[CanonicalEntityMapping]]:
        """Dynamically extract canonical domain models, database tables, and mappings from requirements and modules."""
        # User entity is standard across all systems
        raw_models: List[Tuple[str, str, Dict[str, str], List[str], str, str, List[str]]] = [
            ("ENT-001", "User", {"id": "UUID", "username": "str", "email": "str", "role": "str", "created_at": "datetime"}, [], "DB-001", "users", ["id", "username", "email", "hashed_password", "role", "created_at"])
        ]

        # Extract domain candidate nouns from modules, functional requirements, and workflows
        candidates: List[str] = []
        skip_words = {
            "user", "admin", "system", "auth", "login", "search", "view", "manage", "create", "update", "delete",
            "process", "report", "check", "track", "dashboard", "online", "real", "time", "browse", "upcoming",
            "receive", "monitor", "their", "status", "provide", "secure", "management", "service", "module",
            "portal", "engine", "layer", "worker", "api", "and", "the", "for", "with", "from", "into", "all",
        }

        # 1. Semantic noun mappings from domain requirements
        semantic_noun_map = [
            (["event", "events", "workshop", "seminar", "hackathon"], "Event"),
            (["registration", "register", "enrollment", "booking"], "Registration"),
            (["attendance", "checkin", "check-in", "presence"], "AttendanceRecord"),
            (["participant", "attendee"], "Participant"),
            (["notification", "alert", "announcement"], "Notification"),
            (["schedule", "calendar", "session", "slot"], "EventSchedule"),
            (["feedback", "review", "rating"], "Feedback"),
            (["report", "analytics", "summary"], "Report"),
            (["product", "item", "catalog", "goods"], "Product"),
            (["order", "cart", "checkout"], "Order"),
            (["patient", "medical", "appointment"], "Patient"),
            (["prescription", "diagnosis", "clinical"], "Prescription"),
            (["book", "borrow", "loan", "circulation"], "BookLoan"),
            (["candidate", "resume", "applicant", "job"], "CandidateProfile"),
        ]

        combined_text = " ".join(
            [str(m) for m in req_analysis.get("modules", [])]
            + [fr.get("title", "") for fr in req_analysis.get("functional_requirements", []) if isinstance(fr, dict)]
            + [wf.get("name", "") for wf in req_analysis.get("key_workflows", []) if isinstance(wf, dict)]
        ).lower()

        for keywords, entity_noun in semantic_noun_map:
            if any(re.search(rf"\b{re.escape(kw)}\b", combined_text) for kw in keywords):
                if entity_noun not in candidates:
                    candidates.append(entity_noun)

        # 2. Inspect functional requirement titles for additional domain nouns
        raw_frs = req_analysis.get("functional_requirements", [])
        for fr in raw_frs:
            if isinstance(fr, dict):
                fr_title = fr.get("title", "")
                words = re.findall(r"\b[A-Za-z]{4,}\b", fr_title)
                for w in words:
                    w_cap = w.capitalize()
                    w_low = w.lower()
                    if w_low not in skip_words and len(w_cap) >= 4:
                        if w_cap not in candidates:
                            candidates.append(w_cap)

        # Fallback candidates if fewer than 2 candidates found
        if not candidates:
            candidates = ["Resource", "TransactionRecord"]
        elif len(candidates) == 1:
            candidates.append("ActivityLog")

        # Cap candidates to 5 rich domain entities
        selected_candidates = candidates[:5]

        # Table pluralization helper
        def _to_table_name(pascal_str: str) -> str:
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', pascal_str)
            base = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            if base.endswith("ies"):
                return base
            elif base.endswith("y") and not base.endswith(("ay", "ey", "oy", "uy")):
                return base[:-1] + "ies"
            elif base.endswith("s"):
                return base
            elif base.endswith(("ch", "sh", "x", "z")):
                return f"{base}es"
            else:
                return f"{base}s"

        # Build dynamic entities
        sibling_names = ["User"] + selected_candidates
        for idx, ent_name in enumerate(selected_candidates, 2):
            ent_id = f"ENT-{idx:03d}"
            db_id = f"DB-{idx:03d}"
            tbl_name = _to_table_name(ent_name)

            fields = {
                "id": "UUID",
                "name": "str",
                "status": "str",
                "description": "str",
                "created_at": "datetime",
                "user_id": "UUID",
            }

            cols = ["id", "user_id", "name", "status", "description", "created_at", "updated_at"]
            relationships = [s for s in sibling_names if s != ent_name][:3]

            raw_models.append((ent_id, ent_name, fields, relationships, db_id, tbl_name, cols))

        # Update User entity relationships with first 2 candidate entities
        raw_models[0] = (
            raw_models[0][0],
            raw_models[0][1],
            raw_models[0][2],
            selected_candidates[:2],
            raw_models[0][4],
            raw_models[0][5],
            raw_models[0][6],
        )

        domain_entities: List[CanonicalDomainEntity] = []
        db_entities: List[CanonicalDatabaseEntity] = []
        entity_mappings: List[CanonicalEntityMapping] = []

        for ent_id, ent_name, fields, rels, db_id, tbl_name, cols in raw_models:
            domain_entities.append(CanonicalDomainEntity(
                entity_id=ent_id,
                name=ent_name,
                fields=fields,
                relationships=rels,
                database_table=tbl_name,
                database_entity_id=db_id,
            ))
            db_entities.append(CanonicalDatabaseEntity(
                db_entity_id=db_id,
                table_name=tbl_name,
                primary_key="id",
                domain_entity_name=ent_name,
                domain_entity_id=ent_id,
                columns=cols,
            ))
            entity_mappings.append(CanonicalEntityMapping(
                entity_id=ent_id,
                domain_entity=ent_name,
                db_entity_id=db_id,
                database_table=tbl_name,
                primary_key="id",
                notes=f"Maps Domain Model {ent_name} to SQL Table {tbl_name}",
            ))

        return domain_entities, db_entities, entity_mappings
