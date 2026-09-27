"""Create system_integrations table for encrypted third-party service credentials.

Revision ID: 0007_system_integrations
Revises: 0006_auth_users
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa


revision = "0007_system_integrations"
down_revision = "0006_auth_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_integrations",
        sa.Column("service_key", sa.String(64), primary_key=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), server_default="ai", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("encrypted_credentials", sa.Text(), nullable=False),
        sa.Column("masked_preview", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(32), server_default="not_tested", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_integrations")
