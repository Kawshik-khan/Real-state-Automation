"""Create tenant, conversation, audit, and event foundation tables."""
from alembic import op
import sqlalchemy as sa


revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("tenants", sa.Column("tenant_id", sa.String(36), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("customers", sa.Column("customer_id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("external_ref", sa.String(200)), sa.Column("profile", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_table("conversations", sa.Column("conversation_id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("customer_id", sa.String(36)), sa.Column("channel", sa.String(40), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"])
    op.create_table("messages", sa.Column("message_id", sa.String(36), primary_key=True), sa.Column("conversation_id", sa.String(36), nullable=False), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("direction", sa.String(20), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"])
    op.create_table("audit_logs", sa.Column("audit_id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("actor_id", sa.String(200)), sa.Column("action", sa.String(200), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_table("events", sa.Column("event_id", sa.String(36), primary_key=True), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("aggregate_id", sa.String(36), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_tenant_id", "events", ["tenant_id"])
    op.create_table("outbox", sa.Column("event_id", sa.String(36), primary_key=True), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)))
    op.create_index("ix_outbox_tenant_id", "outbox", ["tenant_id"])
    op.create_table("inbox", sa.Column("event_id", sa.String(36), primary_key=True), sa.Column("consumer", sa.String(200), primary_key=True), sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    for table in ("inbox", "outbox", "events", "audit_logs", "messages", "conversations", "customers", "tenants"):
        op.drop_table(table)