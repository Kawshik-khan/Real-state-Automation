"""Columns and indexes added after the sales tables first shipped, applied idempotently.

``create_all`` creates missing tables but never alters existing ones, so databases created before these columns
existed get them here: from ``init_db`` on start-up (PostgreSQL only) and from migration 0009 for Alembic users.
"""

ADDED_COLUMNS = [
    ("sales_leads", "excluded_areas", "JSON"),
    ("sales_leads", "must_have", "JSON"),
    ("sales_leads", "deal_breakers", "JSON"),
    ("sales_leads", "financing", "VARCHAR(32)"),
    ("sales_agent_settings", "channel_modes", "JSON"),
]

ADDED_INDEXES = [
    # Chat history reads the newest messages of one conversation on every AI turn.
    ("ix_messages_conversation_created", "messages", "conversation_id, created_at"),
]


# Marketing-post approvals belong to no lead.
RELAXED_COLUMNS = [("sales_approvals", "lead_id")]


def upgrade_statements() -> list[str]:
    statements = [f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {type_}" for table, column, type_ in ADDED_COLUMNS]
    statements += [f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL" for table, column in RELAXED_COLUMNS]
    statements += [f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})" for name, table, columns in ADDED_INDEXES]
    return statements
