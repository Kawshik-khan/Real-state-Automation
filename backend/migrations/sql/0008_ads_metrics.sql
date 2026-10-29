-- ============================================================================
-- 0008 — Real ad-platform metrics (Meta, Google Ads, TikTok) + RLS lockdown
-- ============================================================================
-- Idempotent: safe to run more than once, on Supabase (SQL editor / MCP) and on
-- a plain local PostgreSQL (Alembic revision 0008 executes this same file).
--
-- 1. RLS lockdown: drops the "USING (true) FOR ALL TO public" policies that let
--    anyone holding the public anon key read, change or delete rows. The backend
--    uses the service_role key, which bypasses RLS, so it is unaffected.
-- 2. New tables: ad_accounts, ad_campaign_daily_metrics, ad_campaign_period_reach,
--    ad_sync_runs, fx_rates (+ system_integrations if it was never created).
-- 3. New columns on ad_campaigns, social_posts and leads for platform identity,
--    attribution and demo flagging.
-- 4. Marks the pre-existing seed rows as demo data (is_demo = true) so the
--    dashboards stop presenting them as live metrics.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. RLS lockdown of permissive public policies
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'ad_campaigns', 'social_posts', 'leads', 'bookings', 'calendar_milestones',
        'inventory_units', 'ai_agents', 'ai_models', 'ai_prompt_templates', 'ai_tools', 'auth_users'
    ]
    LOOP
        IF to_regclass('public.' || t) IS NOT NULL THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
            EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', 'Allow authenticated read ' || t, t);
            EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', 'Allow service insert ' || t, t);
        END IF;
    END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- 2. New tables
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ad_accounts (
    id VARCHAR(160) PRIMARY KEY,                      -- '<platform>:<external_account_id>'
    platform VARCHAR(32) NOT NULL,                    -- meta | google_ads | tiktok
    external_account_id VARCHAR(128) NOT NULL,
    name VARCHAR(256),
    currency VARCHAR(8),
    timezone VARCHAR(64),
    status VARCHAR(32) DEFAULT 'active',
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_ad_accounts_platform_external UNIQUE (platform, external_account_id)
);

-- One row per campaign per day per delivery channel (Meta splits a campaign into
-- facebook / instagram / messenger / audience_network via publisher_platform).
-- Additive metrics only; reach is stored per day but must NOT be summed across
-- days (see ad_campaign_period_reach).
CREATE TABLE IF NOT EXISTS public.ad_campaign_daily_metrics (
    platform VARCHAR(32) NOT NULL,
    external_campaign_id VARCHAR(128) NOT NULL,
    metric_date DATE NOT NULL,
    channel VARCHAR(32) NOT NULL DEFAULT 'all',
    ad_account_id VARCHAR(160),
    currency VARCHAR(8),
    impressions BIGINT NOT NULL DEFAULT 0,
    reach BIGINT,
    clicks BIGINT NOT NULL DEFAULT 0,
    link_clicks BIGINT NOT NULL DEFAULT 0,
    engagements BIGINT NOT NULL DEFAULT 0,
    spend NUMERIC(14, 2) NOT NULL DEFAULT 0,
    leads INTEGER NOT NULL DEFAULT 0,
    messaging_conversations INTEGER NOT NULL DEFAULT 0,
    conversions NUMERIC(14, 2) NOT NULL DEFAULT 0,
    video_views BIGINT NOT NULL DEFAULT 0,
    video_completions BIGINT NOT NULL DEFAULT 0,
    raw JSONB,
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (platform, external_campaign_id, metric_date, channel)
);
CREATE INDEX IF NOT EXISTS idx_ad_daily_metrics_date ON public.ad_campaign_daily_metrics (metric_date);

-- De-duplicated reach for rolling windows ending on until_date, fetched from the
-- platform already aggregated (reach is not additive across days). The row with
-- external_campaign_id = '__account__' holds account-level (cross-campaign) reach.
CREATE TABLE IF NOT EXISTS public.ad_campaign_period_reach (
    platform VARCHAR(32) NOT NULL,
    external_campaign_id VARCHAR(128) NOT NULL,
    window_days INTEGER NOT NULL,
    since_date DATE NOT NULL,
    until_date DATE NOT NULL,
    reach BIGINT,
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (platform, external_campaign_id, window_days)
);

CREATE TABLE IF NOT EXISTS public.ad_sync_runs (
    id VARCHAR(64) PRIMARY KEY,
    platform VARCHAR(32) NOT NULL,
    ad_account_id VARCHAR(160),
    trigger VARCHAR(32) NOT NULL DEFAULT 'schedule',  -- schedule | nightly | backfill | manual
    status VARCHAR(16) NOT NULL DEFAULT 'running',    -- running | success | partial | failed | skipped
    since_date DATE,
    until_date DATE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    campaigns_upserted INTEGER DEFAULT 0,
    metric_rows_upserted INTEGER DEFAULT 0,
    posts_upserted INTEGER DEFAULT 0,
    error TEXT,
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main'
);
CREATE INDEX IF NOT EXISTS idx_ad_sync_runs_platform_started ON public.ad_sync_runs (platform, started_at DESC);

-- Conversion rates into the reporting currency (BDT). Maintained by an admin;
-- a currency without a rate is excluded from money totals and flagged in the UI.
CREATE TABLE IF NOT EXISTS public.fx_rates (
    currency VARCHAR(8) PRIMARY KEY,
    rate_to_bdt NUMERIC(14, 6) NOT NULL,
    source VARCHAR(64) DEFAULT 'manual',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO public.fx_rates (currency, rate_to_bdt, source)
VALUES ('BDT', 1, 'identity')
ON CONFLICT (currency) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.system_integrations (
    service_key VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'ai',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    encrypted_credentials TEXT NOT NULL,
    masked_preview JSON NOT NULL DEFAULT '{}',
    last_tested_at TIMESTAMPTZ,
    last_status VARCHAR(32) NOT NULL DEFAULT 'not_tested',
    last_error TEXT,
    updated_by VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ad_campaign_daily_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ad_campaign_period_reach ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ad_sync_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fx_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_integrations ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 3. New columns on existing tables
-- ---------------------------------------------------------------------------
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS external_id VARCHAR(128);
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS ad_account_id VARCHAR(160);
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS objective VARCHAR(64);
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS currency VARCHAR(8);
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS budget_amount NUMERIC(14, 2);
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS budget_type VARCHAR(16);
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS source VARCHAR(32) DEFAULT 'manual';
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE IF EXISTS public.ad_campaigns ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;

ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS external_post_id VARCHAR(128);
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS permalink TEXT;
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS media_type VARCHAR(32);
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS views BIGINT;
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS reach BIGINT;
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS saves INTEGER;
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS metrics_synced_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS source VARCHAR(32) DEFAULT 'content_engine';
ALTER TABLE IF EXISTS public.social_posts ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE IF EXISTS public.leads ADD COLUMN IF NOT EXISTS platform VARCHAR(32);
ALTER TABLE IF EXISTS public.leads ADD COLUMN IF NOT EXISTS external_lead_id VARCHAR(128);
ALTER TABLE IF EXISTS public.leads ADD COLUMN IF NOT EXISTS external_campaign_id VARCHAR(128);
ALTER TABLE IF EXISTS public.leads ADD COLUMN IF NOT EXISTS external_ad_id VARCHAR(128);
ALTER TABLE IF EXISTS public.leads ADD COLUMN IF NOT EXISTS form_id VARCHAR(128);
ALTER TABLE IF EXISTS public.leads ADD COLUMN IF NOT EXISTS raw JSONB;

-- Upsert targets (full unique indexes: NULLs never collide, so legacy rows are fine)
DO $$
BEGIN
    IF to_regclass('public.ad_campaigns') IS NOT NULL THEN
        CREATE UNIQUE INDEX IF NOT EXISTS ux_ad_campaigns_platform_external
            ON public.ad_campaigns (platform, external_id);
    END IF;
    IF to_regclass('public.social_posts') IS NOT NULL THEN
        CREATE UNIQUE INDEX IF NOT EXISTS ux_social_posts_platform_external
            ON public.social_posts (platform, external_post_id);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 4. Flag pre-existing seed rows as demo data
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.ad_campaigns') IS NOT NULL THEN
        -- No ad platform sync existed before this migration: every row without a
        -- platform ID was inserted by a seed script.
        UPDATE public.ad_campaigns SET is_demo = TRUE WHERE external_id IS NULL AND is_demo = FALSE;
    END IF;
    IF to_regclass('public.social_posts') IS NOT NULL THEN
        -- Exact topics inserted by backend/scripts/seed_social_analytics_db.py.
        UPDATE public.social_posts SET is_demo = TRUE
        WHERE external_post_id IS NULL AND is_demo = FALSE AND topic IN (
            'Baridhara Luxury Suites — Infinity Pool Aerial Reel',
            'GLG Sky Tower — Penthouse Sunset Walkthrough',
            'Full 4K Architectural Tour: Banani Crest Smart Homes',
            'Commercial Real Estate ROI: Dhanmondi & Gulshan Corporate Suites',
            'Uttara Sector 3 Family Residences — 20:80 Payment Scheme',
            'Architectural Spotlight: Master Bedroom Suite Design',
            'Dhaka Luxury Penthouse Rooftop Drone View'
        );
    END IF;
END $$;
