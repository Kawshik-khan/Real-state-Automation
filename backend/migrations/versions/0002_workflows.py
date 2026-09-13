"""Create authoritative property and customer workflow tables."""
from alembic import op
import sqlalchemy as sa


revision = "0002_workflows"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("projects", sa.Column("project_id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("location", sa.String(200), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])
    op.create_table("inventory_units", sa.Column("unit_id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("project_id", sa.String(36), nullable=False), sa.Column("bedrooms", sa.Integer(), nullable=False), sa.Column("price", sa.String(40), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_inventory_units_tenant_id", "inventory_units", ["tenant_id"])
    op.create_index("ix_inventory_units_project_id", "inventory_units", ["project_id"])
    op.create_table("leads", sa.Column("lead_id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("customer_id", sa.String(36)), sa.Column("name", sa.String(200), nullable=False), sa.Column("contact", sa.String(200), nullable=False), sa.Column("source", sa.String(80), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_leads_tenant_id", "leads", ["tenant_id"])
    op.create_table("bookings", sa.Column("booking_id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), nullable=False), sa.Column("customer_id", sa.String(36), nullable=False), sa.Column("project_id", sa.String(36), nullable=False), sa.Column("slot", sa.DateTime(timezone=True), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_bookings_tenant_id", "bookings", ["tenant_id"])


def downgrade() -> None:
    for table in ("bookings", "leads", "inventory_units", "projects"):
        op.drop_table(table)