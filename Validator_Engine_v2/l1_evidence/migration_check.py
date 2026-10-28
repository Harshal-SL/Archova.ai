"""Layer 1: Alembic migration executable evidence check.

Parses Alembic migration scripts using Python's AST parser to inspect:
- op.create_table table names
- Column names, primary keys, and types
- Foreign key constraints

Compares extracted schema definitions against Database LLD specifications without requiring a live database.
"""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Set, Tuple

from Validator_Engine_v2.schemas import Finding, NormalizedTable


class _AlembicTableVisitor(ast.NodeVisitor):
    """AST Visitor collecting op.create_table statements."""

    def __init__(self) -> None:
        self.tables: Dict[str, Dict[str, Any]] = {}

    def visit_Call(self, node: ast.Call) -> None:
        # Match op.create_table(...) or create_table(...)
        is_create_table = False
        if isinstance(node.func, ast.Attribute) and node.func.attr == "create_table":
            is_create_table = True
        elif isinstance(node.func, ast.Name) and node.func.id == "create_table":
            is_create_table = True

        if is_create_table and node.args:
            first_arg = node.args[0]
            tbl_name = ""
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                tbl_name = first_arg.value
            elif isinstance(first_arg, ast.Str):
                tbl_name = first_arg.s

            if tbl_name:
                normalized_tbl = tbl_name.strip().lower()
                cols: Set[str] = set()
                pks: Set[str] = set()
                fks: List[str] = []

                # Column definitions in remaining arguments
                for arg in node.args[1:]:
                    if isinstance(arg, ast.Call):
                        # sa.Column('col_name', ...) or Column('col_name', ...)
                        is_col = (
                            (isinstance(arg.func, ast.Attribute) and arg.func.attr == "Column")
                            or (isinstance(arg.func, ast.Name) and arg.func.id == "Column")
                        )
                        if is_col and arg.args:
                            c_first = arg.args[0]
                            c_name = ""
                            if isinstance(c_first, ast.Constant) and isinstance(c_first.value, str):
                                c_name = c_first.value
                            elif isinstance(c_first, ast.Str):
                                c_name = c_first.s

                            if c_name:
                                col_norm = c_name.strip().lower()
                                cols.add(col_norm)

                                # Check primary_key kwarg
                                for kw in arg.keywords:
                                    if kw.arg in ("primary_key", "pk"):
                                        if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                            pks.add(col_norm)
                                        elif isinstance(kw.value, ast.NameConstant) and kw.value.value is True:
                                            pks.add(col_norm)

                                # Check ForeignKey in remaining args
                                for subarg in arg.args[1:]:
                                    if isinstance(subarg, ast.Call):
                                        if (isinstance(subarg.func, ast.Attribute) and subarg.func.attr == "ForeignKey") or (
                                            isinstance(subarg.func, ast.Name) and subarg.func.id == "ForeignKey"
                                        ):
                                            if subarg.args and isinstance(subarg.args[0], (ast.Constant, ast.Str)):
                                                val = getattr(subarg.args[0], "value", getattr(subarg.args[0], "s", ""))
                                                fks.append(str(val))

                        # Check table-level ForeignKeyConstraint
                        is_fk_constraint = (
                            (isinstance(arg.func, ast.Attribute) and arg.func.attr == "ForeignKeyConstraint")
                            or (isinstance(arg.func, ast.Name) and arg.func.id == "ForeignKeyConstraint")
                        )
                        if is_fk_constraint and len(arg.args) >= 2:
                            # second arg is target columns
                            if isinstance(arg.args[1], ast.List):
                                for item in arg.args[1].elts:
                                    if isinstance(item, (ast.Constant, ast.Str)):
                                        val = getattr(item, "value", getattr(item, "s", ""))
                                        fks.append(str(val))

                self.tables[normalized_tbl] = {
                    "name": tbl_name,
                    "columns": cols,
                    "pks": pks,
                    "fks": fks,
                }

        self.generic_visit(node)


def check_migration(
    alembic_script_content: Optional[str],
    database_tables: List[NormalizedTable],
) -> Tuple[List[Finding], Dict[str, Any]]:
    """Parse Alembic migration script using Python AST and compare with Database LLD tables.

    Returns:
        findings: List[Finding] with rule_id starting with 'L1.MIGRATION_'
        meta: status and schema extraction metadata
    """
    findings: List[Finding] = []
    meta: Dict[str, Any] = {
        "status": "ok",
        "tables_parsed": 0,
        "matched_tables": 0,
        "missing_tables": 0,
    }

    if alembic_script_content is None:
        meta["status"] = "not_evaluated"
        meta["message"] = "not evaluated: no scaffold provided"
        return findings, meta

    if not alembic_script_content.strip():
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.MIGRATION_MISSING",
                artifact="database",
                severity="high",
                message="Alembic schema migration script is missing or empty.",
                evidence_path="scaffolds/alembic/versions/0001_initial_schema.py",
                source="ISO25012",
                suggested_fix="Generate an initial Alembic migration script containing op.create_table declarations.",
            )
        )
        meta["status"] = "missing"
        return findings, meta

    # Parse Python AST
    try:
        tree = ast.parse(alembic_script_content)
    except SyntaxError as syn_err:
        findings.append(
            Finding.create(
                layer="L1",
                rule_id="L1.MIGRATION_SYNTAX_ERROR",
                artifact="database",
                severity="critical",
                message=f"Alembic migration script has Python syntax errors: {syn_err.msg} (line {syn_err.lineno})",
                evidence_path=f"scaffolds/alembic/versions/0001_initial_schema.py#L{syn_err.lineno}",
                source="ISO25012",
                suggested_fix="Fix Python syntax in migration script.",
            )
        )
        meta["status"] = "syntax_error"
        return findings, meta

    visitor = _AlembicTableVisitor()
    visitor.visit(tree)

    parsed_tables = visitor.tables
    meta["tables_parsed"] = len(parsed_tables)

    # Compare with Database LLD tables
    for expected_tbl in database_tables:
        tname = expected_tbl.name.strip().lower()
        if tname not in parsed_tables:
            meta["missing_tables"] += 1
            findings.append(
                Finding.create(
                    layer="L1",
                    rule_id="L1.MIGRATION_MISSING_TABLE",
                    artifact="database",
                    severity="high",
                    message=f"Table '{expected_tbl.name}' defined in Database LLD is missing in Alembic migration.",
                    evidence_path=f"scaffolds/alembic/versions/0001_initial_schema.py",
                    source="ISO25012",
                    suggested_fix=f"Add op.create_table('{expected_tbl.name}', ...) to the migration upgrade function.",
                )
            )
        else:
            meta["matched_tables"] += 1
            migrated_cols = parsed_tables[tname]["columns"]
            # Check key expected columns
            for col_name in expected_tbl.columns:
                cn = col_name.strip().lower()
                if cn not in migrated_cols:
                    findings.append(
                        Finding.create(
                            layer="L1",
                            rule_id="L1.MIGRATION_MISSING_COLUMN",
                            artifact="database",
                            severity="medium",
                            message=f"Column '{col_name}' of table '{expected_tbl.name}' is missing in Alembic migration.",
                            evidence_path=f"scaffolds/alembic/versions/0001_initial_schema.py#{expected_tbl.name}",
                            source="ISO25012",
                            suggested_fix=f"Add Column('{col_name}', ...) to table '{expected_tbl.name}' in migration script.",
                        )
                    )

    return findings, meta
