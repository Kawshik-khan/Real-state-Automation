"""Sales pipeline: units, payment plans, leads, visits, follow-ups, conversations, approvals, assistant settings.

Revision ID: 0008_sales_pipeline
Revises: 0007_system_integrations
Create Date: 2026-10-27

Tables are created from ``app.sales.models`` with ``checkfirst`` so this is safe on databases where the app's
startup ``init_db`` already created them. The job queue (Procrastinate) and conversation checkpoints (LangGraph)
create their own tables: run ``python -m app.worker --setup``.
"""
from alembic import op

revision = "0008_sales_pipeline"
down_revision = "0007_system_integrations"
branch_labels = None
depends_on = None

# Dependency order: referenced tables first.
TABLES = [
    "property_units",
    "payment_plans",
    "sales_leads",
    "lead_events",
    "visit_slots",
    "site_visits",
    "followup_sequences",
    "followup_steps",
    "followup_enrollments",
    "sales_conversations",
    "sales_messages",
    "sales_approvals",
    "sales_agent_settings",
    "sales_agent_turns",
]


def _tables():
    import app.sales.models  # noqa: F401  (registers the tables)
    from app.models.models import Base

    return [Base.metadata.tables[name] for name in TABLES]


def upgrade() -> None:
    from app.models.models import Base

    Base.metadata.create_all(bind=op.get_bind(), tables=_tables(), checkfirst=True)


def downgrade() -> None:
    for table in reversed(_tables()):
        table.drop(bind=op.get_bind(), checkfirst=True)
