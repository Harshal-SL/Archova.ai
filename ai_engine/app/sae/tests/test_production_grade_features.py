import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.sae.generators.dockerfile_generator import generate_docker_scaffolds
from app.sae.generators.iac_generator import generate_terraform_scaffold
from app.sae.generators.migration_generator import generate_alembic_migration
from app.sae.generators.openapi_generator import generate_openapi_spec
from app.sae.models.response_models import (
    AdversarialReviewResponse,
    ObservabilityResponse,
    RunbookResponse,
    SoftwareArchitecturePackageResponse,
    TestingStrategyResponse,
)
from app.sae.pipeline import SAEPipeline


class TestProductionGradeFeatures(unittest.TestCase):
    def setUp(self):
        self.pipeline = SAEPipeline.__new__(SAEPipeline)

    def test_domain_gap_detector_library(self):
        req_analysis = {
            "system_name": "College Library Management System",
            "domain": "Library Management",
            "functional_requirements": [
                {"title": "Book Catalog Search & Filtering"},
                {"title": "Borrowing & Circulation Transactions"},
            ],
            "modules": ["Catalog Management", "Circulation"],
        }
        gaps = self.pipeline._check_domain_coverage_gaps(req_analysis)
        self.assertEqual(gaps["evaluated_domain"], "Library")
        self.assertEqual(gaps["covered_features_count"], 2)
        self.assertIn("Password Reset & Profile Management", gaps["potential_domain_gaps"])
        self.assertIn("Fines & Overdue Penalty Processing", gaps["potential_domain_gaps"])

    def test_openapi_generator(self):
        backend_lld = {
            "api_endpoints": [
                {
                    "route": "/api/v1/books",
                    "method": "GET",
                    "description": "List books",
                    "request": {"query_params": ["page", "limit"]},
                    "response": {"status": 200, "body": "BookSummary list"},
                    "error_responses": [{"status": 400, "code": "BAD_REQUEST", "description": "Invalid page"}],
                    "auth_required": False,
                },
                {
                    "route": "/api/v1/borrowings",
                    "method": "POST",
                    "description": "Borrow book",
                    "request": {"body": {"book_id": "UUID", "due_days": "int"}},
                    "response": {"status": 201, "body": "BorrowRecord"},
                    "error_responses": [{"status": 409, "code": "OUT_OF_STOCK", "description": "No copies available"}],
                    "auth_required": True,
                },
            ]
        }
        openapi_yaml = generate_openapi_spec("Library System", "Education", backend_lld)
        self.assertIn("openapi: 3.1.0", openapi_yaml)
        self.assertIn("/api/v1/books:", openapi_yaml)
        self.assertIn("/api/v1/borrowings:", openapi_yaml)
        self.assertIn("BearerAuth:", openapi_yaml)
        self.assertIn("ProblemDetails:", openapi_yaml)

    def test_dockerfile_and_compose_generator(self):
        backend_lld = {"framework_config": {"framework": "FastAPI", "language": "Python 3.11+"}}
        cloud_lld = {"cloud_provider": "AWS"}
        dockerfile, docker_compose = generate_docker_scaffolds("Library System", backend_lld, cloud_lld)
        self.assertIn("FROM python:3.11-slim AS builder", dockerfile)
        self.assertIn("USER appuser", dockerfile)
        self.assertIn("version: '3.8'", docker_compose)
        self.assertIn("postgres:", docker_compose)
        self.assertIn("redis:", docker_compose)

    def test_alembic_migration_generator(self):
        database_lld = {
            "tables": [
                {
                    "table_name": "books",
                    "description": "Catalog books inventory",
                    "columns": [
                        {"name": "id", "type": "UUID", "constraints": "PRIMARY KEY"},
                        {"name": "title", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                        {"name": "available_copies", "type": "INTEGER", "constraints": "NOT NULL"},
                    ],
                }
            ],
            "indexes": [
                {"table": "books", "columns": ["title"], "type": "BTREE"}
            ],
        }
        migration_py = generate_alembic_migration("Library System", database_lld)
        self.assertIn("def upgrade() -> None:", migration_py)
        self.assertIn("op.create_table(", migration_py)
        self.assertIn("'books'", migration_py)
        self.assertIn("op.create_index(", migration_py)
        self.assertIn("def downgrade() -> None:", migration_py)

    def test_terraform_generator(self):
        cloud_lld = {"cloud_provider": "AWS"}
        tf = generate_terraform_scaffold("Library System", cloud_lld)
        self.assertIn("resource \"aws_vpc\" \"main\"", tf)
        self.assertIn("resource \"aws_ecs_cluster\" \"app_cluster\"", tf)
        self.assertIn("resource \"aws_db_instance\" \"postgres\"", tf)

    def test_production_readiness_scoring_gating(self):
        # Full production-ready sections
        ready_sections = {
            "requirement_analysis": {"functional_requirements": [{"id": "FR-001"}], "non_functional_requirements": [{"id": "NFR-001"}]},
            "backend_lld": {"api_endpoints": [{"route": "/api/v1/books", "satisfies": ["FR-001"], "error_responses": [{"status": 400}]}]},
            "cloud_lld": {"cost_estimation": {"monthly_cost_breakdown_usd": {"total_estimated_monthly_usd": 115.0}}},
            "security_lld": {"compliance": {"determinations": [{"standard": "OWASP", "status": "IN_SCOPE"}]}},
            "testing_strategy": {"load_testing": {"traffic_model": {"concurrent_virtual_users": 500}}},
            "observability": {"service_level_objectives": [{"name": "SLO 1"}, {"name": "SLO 2"}]},
        }
        report = self.pipeline._compute_completeness(ready_sections, adversarial_verdict="APPROVED")
        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["production_readiness_score"], 1.0)
        self.assertEqual(report["quality_indicators"]["hedged_phrases_detected_count"], 0)


if __name__ == "__main__":
    unittest.main()
