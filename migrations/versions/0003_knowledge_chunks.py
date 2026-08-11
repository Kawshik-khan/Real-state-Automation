"""Create knowledge_chunks table with pgvector + full-text search.

Revision ID: 0003_knowledge_chunks
Revises: 0002_workflows
Create Date: 2026-07-28
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0003_knowledge_chunks"
down_revision = "0002_workflows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        # Enable pgvector extension
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create knowledge_chunks table
    columns = [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("doc_id", sa.String(128), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer(), server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("filename", sa.String(256), nullable=True),
        sa.Column("project", sa.String(128), nullable=True),
        sa.Column("location", sa.String(128), nullable=True),
        sa.Column("document_type", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]

    if is_postgres:
        columns.extend([
            sa.Column("content_tsv", sa.TSVECTOR(), nullable=True),
            sa.Column("embedding", Vector(1536), nullable=True),
        ])
    else:
        columns.extend([
            sa.Column("content_tsv", sa.Text(), nullable=True),
            sa.Column("embedding", sa.JSON(), nullable=True),
        ])

    op.create_table("knowledge_chunks", *columns)

    # Create indexes
    op.create_index("idx_chunks_doc_id", "knowledge_chunks", ["doc_id"])
    op.create_index("idx_chunks_project", "knowledge_chunks", ["project"])

    if is_postgres:
        op.create_index(
            "idx_chunks_content_tsv", "knowledge_chunks", ["content_tsv"],
            postgresql_using="gin",
        )
        op.execute(
            "CREATE INDEX idx_chunks_embedding ON knowledge_chunks "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        )
        # Create tsvector auto-update trigger
        op.execute("""
            CREATE OR REPLACE FUNCTION knowledge_chunks_tsv_update()
            RETURNS trigger AS $$
            BEGIN
                NEW.content_tsv := to_tsvector('english', COALESCE(NEW.content, ''));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER trg_knowledge_chunks_tsv
                BEFORE INSERT OR UPDATE ON knowledge_chunks
                FOR EACH ROW EXECUTE FUNCTION knowledge_chunks_tsv_update()
        """)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("DROP TRIGGER IF EXISTS trg_knowledge_chunks_tsv ON knowledge_chunks")
        op.execute("DROP FUNCTION IF EXISTS knowledge_chunks_tsv_update()")

    op.drop_table("knowledge_chunks")

    if is_postgres:
        op.execute("DROP EXTENSION IF EXISTS vector")
        op.execute("DROP EXTENSION IF EXISTS pg_trgm")
