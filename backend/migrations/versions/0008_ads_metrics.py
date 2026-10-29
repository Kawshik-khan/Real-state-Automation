"""Real ad-platform metrics tables, attribution columns and RLS lockdown.

Executes backend/migrations/sql/0008_ads_metrics.sql, the same idempotent script
that is applied to Supabase, so both environments share one schema definition.

Revision ID: 0008_ads_metrics
Revises: 0007_system_integrations
Create Date: 2026-09-27
"""
from pathlib import Path

from alembic import op

revision = "0008_ads_metrics"
down_revision = "0007_system_integrations"
branch_labels = None
depends_on = None

_SQL_PATH = Path(__file__).resolve().parent.parent / "sql" / "0008_ads_metrics.sql"


def upgrade() -> None:
    # Raw DB-API cursor with no parameters: the script contains format('%I') calls
    # that psycopg2 would otherwise try to interpolate as placeholders.
    cursor = op.get_bind().connection.cursor()
    try:
        cursor.execute(_SQL_PATH.read_text(encoding="utf-8"))
    finally:
        cursor.close()


def downgrade() -> None:
    # Drops only what this revision created. Columns added to pre-existing tables
    # and the RLS lockdown are intentionally kept: re-opening public write access
    # is never a safe rollback.
    op.execute("DROP TABLE IF EXISTS public.ad_sync_runs")
    op.execute("DROP TABLE IF EXISTS public.ad_campaign_period_reach")
    op.execute("DROP TABLE IF EXISTS public.ad_campaign_daily_metrics")
    op.execute("DROP TABLE IF EXISTS public.ad_accounts")
    op.execute("DROP TABLE IF EXISTS public.fx_rates")
