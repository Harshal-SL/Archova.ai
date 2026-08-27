"""Unit tests for agent-owned live RAG retrieval integration."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.query_builder import (
    build_adversarial_review_query,
    build_backend_query,
    build_cloud_query,
    build_database_query,
    build_frontend_query,
    build_hld_query,
    build_observability_query,
    build_query_for_role,
    build_requirement_analysis_query,
    build_runbook_query,
    build_security_query,
    build_technology_advisor_query,
    build_testing_strategy_query,
)
from app.sae.agents.backend_lld_generation_agent import BackendLLDGenerationAgent
from app.sae.agents.cloud_lld_generation_agent import CloudLLDGenerationAgent
from app.sae.agents.database_lld_generation_agent import DatabaseLLDGenerationAgent
from app.sae.agents.security_lld_generation_agent import SecurityLLDGenerationAgent
from app.sae.services.architecture_knowledge_service import (
    ArchitectureKnowledgeService,
    RAGTimeoutError,
    RAGUnavailableError,
    RetrievedChunk,
)


class TestRAGAgentIntegration(unittest.TestCase):
    """Test suite for per-agent query construction, RAG retrieval, and resilient fallbacks."""

    def test_distinct_domain_queries_per_agent(self):
        sample_context = {
            "system_name": "College Library Management System",
            "domain": "Library Education",
            "architecture_style": "Modular Monolith",
            "technology_stack": {
                "backend": "FastAPI (Python)",
                "frontend": "React (Next.js)",
                "database": "PostgreSQL",
                "cloud": "AWS (ECS Fargate)",
            },
        }

        q_sec = build_security_query(sample_context)
        q_db = build_database_query(sample_context)
        q_cloud = build_cloud_query(sample_context)
        q_be = build_backend_query(sample_context)
        q_fe = build_frontend_query(sample_context)
        q_hld = build_hld_query(sample_context)
        q_tech = build_technology_advisor_query(sample_context)
        q_test = build_testing_strategy_query(sample_context)
        q_obs = build_observability_query(sample_context)
        q_run = build_runbook_query(sample_context)
        q_adv = build_adversarial_review_query(sample_context)

        # 1. Queries must not be empty
        queries = [q_sec, q_db, q_cloud, q_be, q_fe, q_hld, q_tech, q_test, q_obs, q_run, q_adv]
        for q in queries:
            self.assertTrue(len(q) > 20)

        # 2. Queries must be distinct and contain domain-specific keywords
        self.assertIn("OAuth2", q_sec)
        self.assertIn("PostgreSQL", q_db)
        self.assertIn("Fargate", q_cloud)
        self.assertIn("Clean Layered Architecture", q_be)
        self.assertIn("React", q_fe)
        self.assertIn("Modular Monolith", q_hld)
        self.assertIn("test automation", q_test.lower())
        self.assertIn("observability", q_obs.lower())
        self.assertIn("incident response", q_run.lower())
        self.assertIn("failure modes", q_adv.lower())

        # All queries must be unique
        self.assertEqual(len(set(queries)), len(queries))

    def test_query_router_dispatch(self):
        ctx = {"domain": "E-Commerce"}
        self.assertIn("OAuth2", build_query_for_role("security", ctx))
        self.assertIn("PostgreSQL", build_query_for_role("database", ctx))
        self.assertIn("Fargate", build_query_for_role("cloud", ctx))
        self.assertIn("Clean Layered", build_query_for_role("backend", ctx))
        self.assertIn("React", build_query_for_role("frontend", ctx))

    def test_knowledge_service_caching(self):
        service = ArchitectureKnowledgeService()
        dummy_chunks = [
            RetrievedChunk(text="Pattern A", score=0.85, source="doc1.md"),
            RetrievedChunk(text="Pattern B", score=0.78, source="doc2.md"),
        ]

        # Populate cache manually
        key = service._cache_key("test query", top_k=5, category_filter=None)
        service._cache[key] = dummy_chunks

        # Fetch context
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(service.get_context("test query", top_k=5))
            self.assertEqual(len(res), 2)
            self.assertEqual(res[0].text, "Pattern A")
            self.assertEqual(res[0].score, 0.85)
        finally:
            loop.close()

    def test_agent_fallback_on_rag_timeout(self):
        # Create a mock knowledge service that raises RAGTimeoutError
        mock_service = MagicMock()
        mock_service.get_context = AsyncMock(side_effect=RAGTimeoutError("Timeout"))

        agent = SecurityLLDGenerationAgent(knowledge_service=mock_service)
        context = {"domain": "Healthcare", "system_name": "Clinic Portal"}

        loop = asyncio.new_event_loop()
        try:
            rag_block, rag_meta = loop.run_until_complete(agent.retrieve_rag_context(context))
            self.assertEqual(rag_block, "")
            self.assertFalse(rag_meta["used_rag"])
            self.assertTrue(rag_meta["fallback"])
            self.assertEqual(rag_meta["chunk_count"], 0)
            self.assertIn("Timeout", rag_meta["reason"])
        finally:
            loop.close()

    def test_agent_fallback_on_rag_unavailable(self):
        # Create a mock knowledge service that raises RAGUnavailableError
        mock_service = MagicMock()
        mock_service.get_context = AsyncMock(side_effect=RAGUnavailableError("Qdrant connection refused"))

        agent = DatabaseLLDGenerationAgent(knowledge_service=mock_service)
        context = {"domain": "Banking", "system_name": "Core Banking"}

        loop = asyncio.new_event_loop()
        try:
            rag_block, rag_meta = loop.run_until_complete(agent.retrieve_rag_context(context))
            self.assertEqual(rag_block, "")
            self.assertFalse(rag_meta["used_rag"])
            self.assertTrue(rag_meta["fallback"])
            self.assertEqual(rag_meta["chunk_count"], 0)
            self.assertIn("Qdrant connection refused", rag_meta["reason"])
        finally:
            loop.close()

    def test_agent_successful_rag_injection(self):
        mock_service = MagicMock()
        mock_service.get_context = AsyncMock(
            return_value=[
                RetrievedChunk(text="PostgreSQL GIN indexing on JSONB", score=0.92, source="postgres_guide.md"),
                RetrievedChunk(text="Connection pooling with PgBouncer", score=0.88, source="scaling.md"),
            ]
        )

        agent = DatabaseLLDGenerationAgent(knowledge_service=mock_service)
        context = {"domain": "Library", "system_name": "Library DB"}

        loop = asyncio.new_event_loop()
        try:
            rag_block, rag_meta = loop.run_until_complete(agent.retrieve_rag_context(context))
            self.assertTrue(len(rag_block) > 50)
            self.assertTrue(rag_meta["used_rag"])
            self.assertFalse(rag_meta["fallback"])
            self.assertEqual(rag_meta["chunk_count"], 2)
            self.assertEqual(rag_meta["avg_similarity"], 0.90)

            # Test prompt injection
            base_prompt = "Generate database schema."
            injected_prompt = agent.inject_rag_context(base_prompt, rag_block)
            self.assertIn("RETRIEVED ARCHITECTURAL KNOWLEDGE PATTERNS", injected_prompt)
            self.assertIn("PostgreSQL GIN indexing on JSONB", injected_prompt)
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
