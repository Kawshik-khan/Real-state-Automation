"""Create active_refresh_tokens and revoked_tokens tables for distributed session security.

Revision ID: 0005_token_sessions
Revises: 0004_ai_control_plane
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_token_sessions"
down_revision = "0004_ai_control_plane"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. active_refresh_tokens
    op.create_table(
        "active_refresh_tokens",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), server_default="agent", nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_active_refresh_tokens_jti", "active_refresh_tokens", ["jti"])
    op.create_index("ix_active_refresh_tokens_user_id", "active_refresh_tokens", ["user_id"])
    op.create_index("ix_active_refresh_tokens_expires_at", "active_refresh_tokens", ["expires_at"])

    # 2. revoked_tokens
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("token_type", sa.String(32), server_default="refresh", nullable=False),
        sa.Column("reason", sa.String(128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_revoked_tokens_jti", "revoked_tokens", ["jti"])
    op.create_index("ix_revoked_tokens_user_id", "revoked_tokens", ["user_id"])
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_table("revoked_tokens")
    op.drop_table("active_refresh_tokens")
