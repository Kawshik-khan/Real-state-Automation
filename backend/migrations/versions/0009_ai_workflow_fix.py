"""AI workflow fix: buyer exclusions and deal breakers, per-channel assistant modes, shadow comparison pairs, and the
chat-history index.

Revision ID: 0009_ai_workflow_fix
Revises: 0008_sales_pipeline
Create Date: 2026-10-27

Idempotent: columns use ADD COLUMN IF NOT EXISTS and the new table is created with ``checkfirst``, so it is safe on
databases where the app's startup ``init_db`` already applied them.
"""
import sqlalchemy as sa
from alembic import op

revision = "0009_ai_workflow_fix"
down_revision = "0008_sales_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    import app.sales.models  # noqa: F401  (registers the tables)
    from app.models.models import Base
    from app.sales.schema_upgrades import upgrade_statements

    bind = op.get_bind()
    Base.metadata.tables["ai_shadow_pairs"].create(bind=bind, checkfirst=True)
    for statement in upgrade_statements():
        op.execute(sa.text(statement))


def downgrade() -> None:
    import app.sales.models  # noqa: F401
    from app.models.models import Base
    from app.sales.schema_upgrades import ADDED_COLUMNS, ADDED_INDEXES

    for name, _table, _columns in ADDED_INDEXES:
        op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
    for table, column, _type in ADDED_COLUMNS:
        op.execute(sa.text(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column}"))
    Base.metadata.tables["ai_shadow_pairs"].drop(bind=op.get_bind(), checkfirst=True)
