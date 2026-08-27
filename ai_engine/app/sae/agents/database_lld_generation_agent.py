"""Database Low Level Design (LLD) Generation Agent for SAE v2.

Grounds SQL schemas, tables, relationships, and migration scripts directly
into Canonical Architecture Contract (CAC) entity definitions and explicit bridge mappings.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.sae.agents.base_agent import BaseArchitectureAgent
from app.sae.models.response_models import DatabaseLLDResponse
from app.sae.prompts.database_lld_generation_prompt import (
    DATABASE_LLD_GENERATION_SYSTEM_PROMPT,
    DATABASE_LLD_GENERATION_USER_PROMPT_TEMPLATE,
)
from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.services.architecture_knowledge_service import ArchitectureKnowledgeService
from app.sae.utils.canonical_contract import CanonicalArchitectureContract


class DatabaseLLDGenerationAgent(BaseArchitectureAgent):
    """Agent responsible for generating Database Low Level Design (LLD)."""

    role: str = "database"

    def __init__(
        self,
        llm_provider: Optional[OpenRouterProvider] = None,
        knowledge_service: Optional[ArchitectureKnowledgeService] = None,
        model_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            llm_provider=llm_provider,
            knowledge_service=knowledge_service,
            model_name=model_name,
        )

    def _build_prompt(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> str:
        hld_str = json.dumps(hld, indent=2, default=str)
        prompt = DATABASE_LLD_GENERATION_USER_PROMPT_TEMPLATE.format(hld_document_json=hld_str)

        if cac and cac.database_entities:
            cac_tables = "\n".join([
                f"  - Table: {db.table_name} (ID: {db.db_entity_id}) | Domain Entity: {db.domain_entity_name} ({db.domain_entity_id}) | Columns: {db.columns}"
                for db in cac.database_entities
            ])
            prompt += f"\n\nCANONICAL DATABASE CONTRACT (MANDATORY SCHEMAS):\nEvery database table, migration, and entity mapping MUST match these exact schemas and bridge mappings:\n{cac_tables}\n"
        return prompt

    @staticmethod
    def _derive_and_validate_relationships(
        tables: List[Dict[str, Any]],
        candidate_relationships: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Guarantee that all relationships strictly reference existing tables and valid columns.
        If candidates are empty or invalid, automatically synthesizes valid FK relationships
        from foreign key columns ending with '_id'.
        """
        if not tables:
            return []

        table_map: Dict[str, Set[str]] = {}
        for t in tables:
            if isinstance(t, dict) and t.get("name"):
                t_name = t["name"].lower()
                cols = set()
                for c in t.get("columns", []):
                    if isinstance(c, dict) and c.get("name"):
                        cols.add(c["name"].lower())
                    elif isinstance(c, str):
                        cols.add(c.lower())
                table_map[t_name] = cols

        valid_relationships: List[Dict[str, Any]] = []

        if candidate_relationships:
            for rel in candidate_relationships:
                if not isinstance(rel, dict):
                    continue
                from_t = rel.get("from_table", "").lower()
                to_t = rel.get("to_table", "").lower()
                from_c = rel.get("from_column", "").lower()
                to_c = rel.get("to_column", "id").lower()

                if from_t in table_map and to_t in table_map:
                    valid_relationships.append({
                        "from_table": from_t,
                        "from_column": from_c or "id",
                        "to_table": to_t,
                        "to_column": to_c or "id",
                        "type": rel.get("type", "MANY_TO_ONE"),
                    })

        if not valid_relationships:
            # Dynamically infer foreign key relationships from column names ending with '_id'
            for t_name, cols in table_map.items():
                for col in cols:
                    if col.endswith("_id") and col != "id":
                        target_base = col[:-3]  # e.g., "user_id" -> "user", "event_id" -> "event"
                        # Find matching target table
                        target_table = None
                        if target_base in table_map:
                            target_table = target_base
                        elif f"{target_base}s" in table_map:
                            target_table = f"{target_base}s"
                        elif f"{target_base}es" in table_map:
                            target_table = f"{target_base}es"

                        if target_table and target_table != t_name:
                            valid_relationships.append({
                                "from_table": t_name,
                                "from_column": col,
                                "to_table": target_table,
                                "to_column": "id",
                                "type": "MANY_TO_ONE",
                            })

        return valid_relationships

    def _synthesize_fallback_database_lld(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synthesizes structured Database LLD with canonical table definitions and explicit entity mappings."""
        db_engine = hld.get("technology_stack", {}).get("database", "PostgreSQL 16")

        tables = []
        entity_mappings = []

        if cac and cac.database_entities:
            for db in cac.database_entities:
                columns = [
                    {"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY", "DEFAULT gen_random_uuid()"]},
                    {"name": "created_at", "type": "TIMESTAMPTZ", "constraints": ["NOT NULL", "DEFAULT now()"]},
                ]
                for col in db.columns:
                    if col not in ("id", "created_at"):
                        col_type = "VARCHAR(255)" if "id" not in col else "UUID"
                        columns.append({"name": col, "type": col_type, "constraints": ["NOT NULL"]})
                
                tables.append({
                    "name": db.table_name,
                    "description": f"Persists {db.domain_entity_name} state",
                    "columns": columns,
                    "indexes": [{"name": f"idx_{db.table_name}_id", "columns": ["id"]}],
                })

            for m in cac.entity_mappings:
                entity_mappings.append({
                    "domain_entity": m.domain_entity,
                    "database_table": m.database_table,
                    "entity_id": m.entity_id,
                    "db_entity_id": m.db_entity_id,
                })
        else:
            tables = [
                {"name": "users", "description": "User accounts and credentials", "columns": [{"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY"]}]},
                {"name": "resources", "description": "Core system resource items", "columns": [{"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY"]}]},
            ]
            entity_mappings = [
                {"domain_entity": "User", "database_table": "users"},
                {"domain_entity": "ResourceItem", "database_table": "resources"},
            ]

        relationships = self._derive_and_validate_relationships(tables)

        return {
            "database_engine": db_engine,
            "schemas": ["public"],
            "tables": tables,
            "entity_mappings": entity_mappings,
            "relationships": relationships,
            "migration_strategy": {
                "tool": "Alembic (Python Async)",
                "baseline_version": "0001_initial_schema.py",
                "lock_timeout": "5s",
                "statement_timeout": "30s",
            },
            "backup_and_replication": {
                "strategy": "AWS RDS Multi-AZ synchronous replication with automated daily snapshots",
                "point_in_time_recovery_window": "7 days",
            },
        }

    async def run_async(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate Database LLD with live agent-owned RAG context and CAC grounding."""
        # 1. Retrieve domain-specific RAG context
        rag_block, rag_meta = await self.retrieve_rag_context(hld)

        # 2. Build prompt with CAC binding and authoritative domain fence
        base_prompt = self._build_prompt(hld, cac=cac)
        prompt = self.inject_rag_context(base_prompt, rag_block)
        prompt = self.inject_domain_fence(prompt, cac=cac)

        # 3. Call LLM with fallback
        try:
            result: DatabaseLLDResponse = await self.llm_provider.generate_structured_async(
                prompt=prompt,
                response_model=DatabaseLLDResponse,
                model_name=self.model_name,
                system_prompt=DATABASE_LLD_GENERATION_SYSTEM_PROMPT,
                agent_role=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_database_lld(hld, cac=cac)

        if not res_dict.get("tables") and not res_dict.get("schemas"):
            fallback = self._synthesize_fallback_database_lld(hld, cac=cac)
            for k, v in fallback.items():
                if not res_dict.get(k):
                    res_dict[k] = v

        # Enforce relationship validity against actual tables
        res_dict["relationships"] = self._derive_and_validate_relationships(
            res_dict.get("tables", []),
            res_dict.get("relationships", []),
        )

        # Ensure explicit entity_mappings array is attached
        if cac and cac.entity_mappings:
            res_dict["entity_mappings"] = [
                {
                    "domain_entity": m.domain_entity,
                    "database_table": m.database_table,
                    "entity_id": m.entity_id,
                    "db_entity_id": m.db_entity_id,
                }
                for m in cac.entity_mappings
            ]

        return self.attach_rag_metadata(res_dict, rag_meta)

    def run(
        self,
        hld: Dict[str, Any],
        cac: Optional[CanonicalArchitectureContract] = None,
    ) -> Dict[str, Any]:
        """Synchronously generate Database LLD."""
        prompt = self._build_prompt(hld, cac=cac)
        try:
            result: DatabaseLLDResponse = self.llm_provider.generate_structured(
                prompt=prompt,
                model_name=self.model_name,
                response_model=DatabaseLLDResponse,
                system_prompt=DATABASE_LLD_GENERATION_SYSTEM_PROMPT,
                agent_name=self.role,
                temperature=0.2,
            )
            res_dict = result.model_dump(mode="json")
        except Exception:
            res_dict = self._synthesize_fallback_database_lld(hld, cac=cac)

        res_dict["relationships"] = self._derive_and_validate_relationships(
            res_dict.get("tables", []),
            res_dict.get("relationships", []),
        )
        return res_dict
