"""Deterministic Alembic Initial Migration Generator for SAE v2."""

from __future__ import annotations

import datetime
from typing import Any, Dict, List


def _map_sql_type_to_sa(col_type: str) -> str:
    """Map SQL column type string to SQLAlchemy / Alembic type expression."""
    t = col_type.upper()
    if "UUID" in t:
        return "sa.UUID(as_uuid=True)"
    elif "VARCHAR" in t or "CHAR" in t:
        import re
        m = re.search(r"\d+", t)
        length = m.group(0) if m else "255"
        return f"sa.String(length={length})"
    elif "TEXT" in t:
        return "sa.Text()"
    elif "INT" in t or "SERIAL" in t:
        return "sa.Integer()"
    elif "BIGINT" in t:
        return "sa.BigInteger()"
    elif "NUMERIC" in t or "DECIMAL" in t:
        return "sa.Numeric(10, 2)"
    elif "FLOAT" in t or "DOUBLE" in t:
        return "sa.Float()"
    elif "BOOL" in t:
        return "sa.Boolean()"
    elif "TIMESTAMPTZ" in t or "TIMESTAMP WITH TIME ZONE" in t:
        return "sa.DateTime(timezone=True)"
    elif "TIMESTAMP" in t or "DATETIME" in t:
        return "sa.DateTime()"
    elif "DATE" in t:
        return "sa.Date()"
    elif "JSONB" in t:
        return "postgresql.JSONB(astext_type=sa.Text())"
    elif "JSON" in t:
        return "sa.JSON()"
    return "sa.String(length=255)"


def generate_alembic_migration(
    system_name: str,
    database_lld: Dict[str, Any],
) -> str:
    """Generate clean, executable Alembic revision script from database LLD table definitions."""
    tables: List[Dict[str, Any]] = database_lld.get("tables", [])
    relationships: List[Dict[str, Any]] = database_lld.get("relationships", [])
    indexes: List[Dict[str, Any]] = database_lld.get("indexes", [])

    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        '"""Initial database schema migration.',
        "",
        f"Revision ID: 0001_initial_{system_name.lower().replace(' ', '_')}",
        "Revises: None",
        f"Create Date: {date_str}",
        '"""',
        "",
        "from typing import Sequence, Union",
        "",
        "from alembic import op",
        "import sqlalchemy as sa",
        "from sqlalchemy.dialects import postgresql",
        "",
        "# revision identifiers, used by Alembic.",
        f"revision: str = '0001_initial_{system_name.lower().replace(' ', '_')}'",
        "down_revision: Union[str, None] = None",
        "branch_labels: Union[str, Sequence[str], None] = None",
        "depends_on: Union[str, Sequence[str], None] = None",
        "",
        "",
        "def upgrade() -> None:",
        "    # ── Enable UUID-OSSP Extension if PostgreSQL ──────────────────────────",
        "    op.execute('CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";')",
        "    op.execute('CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";')",
        "",
    ]

    # Create tables
    for table in tables:
        tname = table.get("table_name", "unnamed_table")
        desc = table.get("description", "")
        cols = table.get("columns", [])

        lines.append(f"    # ### Create table: {tname} ({desc}) ###")
        lines.append(f"    op.create_table(")
        lines.append(f"        '{tname}',")

        for col in cols:
            cname = col.get("name", "id")
            ctype = col.get("type", "VARCHAR(255)")
            constraints = str(col.get("constraints", "")).upper()

            sa_type = _map_sql_type_to_sa(ctype)
            is_pk = "PRIMARY KEY" in constraints
            is_nullable = "NOT NULL" not in constraints and not is_pk
            is_unique = "UNIQUE" in constraints and not is_pk

            col_args = [f"sa.Column('{cname}', {sa_type}"]
            if is_pk:
                col_args.append("primary_key=True")
            if not is_nullable:
                col_args.append("nullable=False")
            if is_unique:
                col_args.append("unique=True")
            if "NOW()" in constraints or "DEFAULT NOW()" in constraints:
                col_args.append("server_default=sa.text('now()')")
            elif "GEN_RANDOM_UUID()" in constraints:
                col_args.append("server_default=sa.text('gen_random_uuid()')")

            lines.append(f"        {', '.join(col_args)}),")

        lines.append("    )")
        lines.append("")

    # Create Indexes
    if indexes:
        lines.append("    # ### Create Indexes ###")
        for idx in indexes:
            itbl = idx.get("table", "")
            icols = idx.get("columns", [])
            itype = idx.get("type", "BTREE").upper()
            is_uniq = "UNIQUE" in itype
            iname = f"ix_{itbl}_{'_'.join(icols)}"

            col_repr = ", ".join([f"'{c}'" for c in icols])
            lines.append(f"    op.create_index('{iname}', '{itbl}', [{col_repr}], unique={is_uniq})")
        lines.append("")

    lines.extend([
        "",
        "def downgrade() -> None:",
        "    # ### Downgrade Schema ###",
    ])

    # Drop indexes and tables in reverse
    if indexes:
        for idx in reversed(indexes):
            itbl = idx.get("table", "")
            icols = idx.get("columns", [])
            iname = f"ix_{itbl}_{'_'.join(icols)}"
            lines.append(f"    op.drop_index('{iname}', table_name='{itbl}')")

    for table in reversed(tables):
        tname = table.get("table_name", "unnamed_table")
        lines.append(f"    op.drop_table('{tname}')")

    return "\n".join(lines) + "\n"
