"""Unit tests for Layer 1 Executable Evidence checks.

Covers one passing fixture and one failing fixture per check (openapi, dockerfile, terraform, migration).
Verifies that missing external tools are skipped gracefully.
"""

import pytest

from Validator_Engine_v2.l1_evidence.dockerfile_check import check_dockerfile
from Validator_Engine_v2.l1_evidence.migration_check import check_migration
from Validator_Engine_v2.l1_evidence.openapi_check import check_openapi
from Validator_Engine_v2.l1_evidence.terraform_check import check_terraform
from Validator_Engine_v2.schemas import NormalizedEndpoint, NormalizedTable


# ── 1. OpenAPI Check Tests ──────────────────────────────────────────────────

VALID_OPENAPI = """openapi: 3.1.0
info:
  title: "Test API"
  version: "1.0.0"
paths:
  /api/v1/users:
    get:
      summary: "Get users"
      responses:
        '200':
          description: "OK"
    post:
      summary: "Create user"
      responses:
        '201':
          description: "Created"
"""

INVALID_OPENAPI_SYNTAX = """openapi: 3.1.0
info:
  title: "Broken API
paths:
  /bad: {
"""


def test_openapi_check_passing():
    endpoints = [
        NormalizedEndpoint(method="GET", path="/api/v1/users"),
        NormalizedEndpoint(method="POST", path="/api/v1/users"),
    ]
    findings, meta = check_openapi(VALID_OPENAPI, endpoints)
    assert meta["status"] == "ok"
    assert meta["matched_operations"] == 2
    assert meta["missing_in_spec"] == 0
    # No critical or high findings
    critical_high = [f for f in findings if f.severity in ("critical", "high")]
    assert len(critical_high) == 0


def test_openapi_check_failing():
    # 1. Missing endpoint in openapi
    endpoints = [
        NormalizedEndpoint(method="GET", path="/api/v1/users"),
        NormalizedEndpoint(method="DELETE", path="/api/v1/users/1"),  # missing in spec
    ]
    findings, meta = check_openapi(VALID_OPENAPI, endpoints)
    missing_findings = [f for f in findings if f.rule_id == "L1.OPENAPI_MISSING_ENDPOINT"]
    assert len(missing_findings) == 1
    assert "DELETE /api/v1/users/1" in missing_findings[0].message

    # 2. Syntax error
    findings_syntax, meta_syntax = check_openapi(INVALID_OPENAPI_SYNTAX, endpoints)
    assert meta_syntax["status"] == "syntax_error"
    assert any(f.rule_id == "L1.OPENAPI_SYNTAX_ERROR" for f in findings_syntax)


# ── 2. Dockerfile Check Tests ────────────────────────────────────────────────

PASSING_DOCKERFILE = """FROM python:3.11-slim AS runner
WORKDIR /app
RUN useradd -u 10001 appuser
USER appuser
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/live || exit 1
CMD ["python", "main.py"]
"""

FAILING_DOCKERFILE = """FROM python:latest
WORKDIR /app
USER root
CMD ["python", "main.py"]
"""


def test_dockerfile_check_passing():
    findings, meta = check_dockerfile(PASSING_DOCKERFILE)
    assert meta["status"] in ("ok", "skipped_tool_missing", "hadolint_executed")
    # No root user finding, no missing healthcheck, no unpinned base
    bad_findings = [f for f in findings if f.rule_id in (
        "L1.DOCKERFILE_ROOT_USER",
        "L1.DOCKERFILE_MISSING_HEALTHCHECK",
        "L1.DOCKERFILE_LATEST_TAG",
        "L1.DOCKERFILE_UNPINNED_BASE",
    )]
    assert len(bad_findings) == 0


def test_dockerfile_check_failing():
    findings, meta = check_dockerfile(FAILING_DOCKERFILE)
    rule_ids = {f.rule_id for f in findings}
    assert "L1.DOCKERFILE_LATEST_TAG" in rule_ids or "L1.DOCKERFILE_UNPINNED_BASE" in rule_ids
    assert "L1.DOCKERFILE_ROOT_USER" in rule_ids
    assert "L1.DOCKERFILE_MISSING_HEALTHCHECK" in rule_ids


# ── 3. Terraform Check Tests ─────────────────────────────────────────────────

PASSING_TERRAFORM = """terraform {
  required_version = ">= 1.5.0"
}
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
resource "aws_db_instance" "default" {
  allocated_storage = 20
  engine            = "postgres"
}
"""

FAILING_TERRAFORM = """terraform {
  required_version = ">= 1.5.0"
resource "aws_vpc" "main" {
"""  # Unbalanced brace and missing database


def test_terraform_check_passing():
    cloud_lld = {
        "networking": {"vpc": "10.0.0.0/16"},
        "database": {"engine": "PostgreSQL"},
    }
    findings, meta = check_terraform(PASSING_TERRAFORM, cloud_lld)
    assert meta["status"] in ("ok", "skipped_tool_missing", "terraform_executed")
    critical_high = [f for f in findings if f.severity in ("critical", "high")]
    assert len(critical_high) == 0


def test_terraform_check_failing():
    cloud_lld = {
        "networking": {"vpc": "10.0.0.0/16"},
        "database": {"engine": "PostgreSQL"},
    }
    findings, meta = check_terraform(FAILING_TERRAFORM, cloud_lld)
    rule_ids = {f.rule_id for f in findings}
    assert "L1.TERRAFORM_SYNTAX_UNBALANCED_BRACES" in rule_ids
    assert "L1.TERRAFORM_MISSING_DATABASE" in rule_ids


# ── 4. Migration Check Tests ─────────────────────────────────────────────────

PASSING_MIGRATION = '''"""Initial migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False)
    )
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'))
    )
'''

FAILING_MIGRATION = '''"""Incomplete migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True)
    )
'''


def test_migration_check_passing():
    db_tables = [
        NormalizedTable(name="users", columns=["id", "email"], pks=["id"]),
        NormalizedTable(name="orders", columns=["id", "user_id"], pks=["id"]),
    ]
    findings, meta = check_migration(PASSING_MIGRATION, db_tables)
    assert meta["status"] == "ok"
    assert meta["matched_tables"] == 2
    assert meta["missing_tables"] == 0
    assert len(findings) == 0


def test_migration_check_failing():
    db_tables = [
        NormalizedTable(name="users", columns=["id", "email"], pks=["id"]),
        NormalizedTable(name="orders", columns=["id", "user_id"], pks=["id"]),
    ]
    findings, meta = check_migration(FAILING_MIGRATION, db_tables)
    rule_ids = {f.rule_id for f in findings}
    # orders table missing
    assert "L1.MIGRATION_MISSING_TABLE" in rule_ids
    # email column in users missing
    assert "L1.MIGRATION_MISSING_COLUMN" in rule_ids
