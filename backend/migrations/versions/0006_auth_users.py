"""Create auth_users table for persistent staff credentials and RBAC.

Revision ID: 0006_auth_users
Revises: 0005_token_sessions
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa


revision = "0006_auth_users"
down_revision = "0005_token_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("full_name", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), server_default="agent", nullable=False),
        sa.Column("tenant_id", sa.String(128), server_default="glg-default", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_users_email", "auth_users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_table("auth_users")
