-- ============================================================================
-- 🌟 GLG ASSETS AGENTIC AI PLATFORM — LATEST SUPABASE DATABASE SCHEMA & SEED
-- ============================================================================
-- Target Database: Supabase Managed PostgreSQL + pgvector
-- Project Reference: fdjzbtkypedzlkwpzzzt
-- Instructions: Copy and run this entire script in Supabase Dashboard -> SQL Editor.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. EXTENSIONS SETUP
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify vector extension
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension could not be enabled. Please enable it in Database -> Extensions.';
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 2. CORE TABLES DDL
-- ----------------------------------------------------------------------------

-- Table 1: users (Omnichannel Customer Records)
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(256),
    phone VARCHAR(64),
    channel VARCHAR(32) DEFAULT 'website',
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 2: conversations (Chat Threads & Belief Memory States)
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(128) REFERENCES users(user_id) ON DELETE CASCADE,
    channel VARCHAR(32) DEFAULT 'website',
    status VARCHAR(32) DEFAULT 'active', -- 'active', 'escalated', 'closed'
    ai_paused BOOLEAN DEFAULT FALSE,
    beliefs JSONB DEFAULT '{}'::jsonb,
    last_message_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 3: messages (Complete Conversation Logs)
CREATE TABLE IF NOT EXISTS messages (
    message_id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    conversation_id VARCHAR(128) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    sender VARCHAR(32) NOT NULL, -- 'user', 'ai', 'human_agent'
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 4: projects (Real-Estate Developments Catalog)
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    location VARCHAR(256) NOT NULL,
    price VARCHAR(128) NOT NULL,
    price_val BIGINT, -- Numeric price in BDT for SQL range filtering
    bedrooms INT,
    description TEXT DEFAULT '',
    features JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 5: knowledge_documents (Registry of Processed PDFs & Docs)
CREATE TABLE IF NOT EXISTS knowledge_documents (
    doc_id VARCHAR(128) PRIMARY KEY,
    filename VARCHAR(256) NOT NULL,
    file_type VARCHAR(32) DEFAULT 'pdf',
    ocr_status VARCHAR(32) DEFAULT 'completed',
    chunk_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 6: knowledge_chunks (RAG pgvector Embeddings & Text Segments)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id VARCHAR(64) PRIMARY KEY,
    doc_id VARCHAR(128) REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
    chunk_index INT DEFAULT 0,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- 1536-dimensional vector for OpenAI / Groq embeddings
    content_tsv TSVECTOR,
    metadata JSONB DEFAULT '{}'::jsonb,
    filename VARCHAR(256),
    project VARCHAR(128),
    location VARCHAR(128),
    document_type VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 7: media (Brochures & Floor Plan Assets)
CREATE TABLE IF NOT EXISTS media (
    media_id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    project_id VARCHAR(128) REFERENCES projects(project_id) ON DELETE CASCADE,
    media_type VARCHAR(32) NOT NULL, -- 'brochure_pdf', 'floor_plan_image'
    url VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 8: analytics (Daily Operational KPIs & Aggregates)
CREATE TABLE IF NOT EXISTS analytics (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    date VARCHAR(10) NOT NULL, -- 'YYYY-MM-DD'
    total_messages INT DEFAULT 0,
    total_leads INT DEFAULT 0,
    ai_resolved INT DEFAULT 0,
    escalated INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 9: logs (Audit Trace & Diagnostic Logs)
CREATE TABLE IF NOT EXISTS logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    level VARCHAR(16) DEFAULT 'INFO',
    source VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ----------------------------------------------------------------------------
-- 3. PERFORMANCE & VECTOR SEARCH INDEXES
-- ----------------------------------------------------------------------------

-- HNSW Cosine Distance Index for sub-10ms pgvector similarity queries
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_hnsw 
ON knowledge_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Full-Text Keyword Search GIN Index
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_content_tsv 
ON knowledge_chunks 
USING gin (content_tsv);

-- JSONB GIN Indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_metadata_gin 
ON knowledge_chunks 
USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_projects_features_gin 
ON projects 
USING gin (features);

-- Standard Foreign Key & Filtering Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_channel ON conversations(channel);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_project ON knowledge_chunks(project);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_location ON knowledge_chunks(location);
CREATE INDEX IF NOT EXISTS idx_media_project_id ON media(project_id);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date);

-- Auto-update tsvector trigger for hybrid search
CREATE OR REPLACE FUNCTION update_chunk_content_tsv()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_chunk_tsv ON knowledge_chunks;
CREATE TRIGGER trg_update_chunk_tsv
BEFORE INSERT OR UPDATE OF content ON knowledge_chunks
FOR EACH ROW EXECUTE FUNCTION update_chunk_content_tsv();

-- ----------------------------------------------------------------------------
-- 4. SUPABASE PGVECTOR STORED PROCEDURE (RPC)
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION match_knowledge_chunks (
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.65,
    match_count INT DEFAULT 5,
    filter_project TEXT DEFAULT NULL,
    filter_location TEXT DEFAULT NULL
)
RETURNS TABLE (
    id VARCHAR(64),
    doc_id VARCHAR(128),
    chunk_index INT,
    content TEXT,
    filename VARCHAR(256),
    project VARCHAR(128),
    location VARCHAR(128),
    document_type VARCHAR(64),
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.doc_id,
        c.chunk_index,
        c.content,
        c.filename,
        c.project,
        c.location,
        c.document_type,
        c.metadata,
        (1 - (c.embedding <=> query_embedding))::FLOAT AS similarity
    FROM knowledge_chunks c
    WHERE c.embedding IS NOT NULL
      AND (1 - (c.embedding <=> query_embedding)) > match_threshold
      AND (filter_project IS NULL OR c.project ILIKE '%' || filter_project || '%')
      AND (filter_location IS NULL OR c.location ILIKE '%' || filter_location || '%')
    ORDER BY c.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;

-- ----------------------------------------------------------------------------
-- 5. SUPABASE STORAGE BUCKETS CONFIGURATION
-- ----------------------------------------------------------------------------

-- Insert storage buckets if not already present
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('brochures', 'brochures', true, 52428800, ARRAY['application/pdf']),
    ('floorplans', 'floorplans', true, 20971520, ARRAY['image/jpeg', 'image/png', 'image/webp', 'application/pdf']),
    ('ocr-documents', 'ocr-documents', false, 52428800, NULL)
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public;

-- Enable Public Access Policies for brochures and floorplans
DROP POLICY IF EXISTS "Public Brochure Access" ON storage.objects;
CREATE POLICY "Public Brochure Access" 
ON storage.objects FOR SELECT 
USING (bucket_id IN ('brochures', 'floorplans'));

DROP POLICY IF EXISTS "Service Role Full Access" ON storage.objects;
CREATE POLICY "Service Role Full Access" 
ON storage.objects FOR ALL 
USING (auth.role() = 'service_role');

-- ----------------------------------------------------------------------------
-- 6. CANONICAL SEED DATA (DHAKA LUXURY DEVELOPMENTS)
-- ----------------------------------------------------------------------------

INSERT INTO projects (project_id, name, location, price, price_val, bedrooms, description, features)
VALUES
(
    'proj_101',
    'GLG Gulshan Heights',
    'Road 79, Gulshan-2, Dhaka',
    'BDT 4.80 Cr - 7.50 Cr',
    48000000,
    4,
    'GLG Gulshan Heights is an ultra-luxury residential landmark situated in Dhaka diplomatic zone, featuring panoramic lake views, custom Italian marble interiors, and automated climate control.',
    '{
        "status": "Ready for Handover",
        "coordinates": [23.7925, 90.4078],
        "image": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        "brochure": "/GLG_Gulshan_Heights_Property_Details.pdf",
        "amenities": ["Rooftop Infinity Pool", "Private Elevators", "German Fitted Kitchens", "Double-Glazed Acoustic Glass", "24/7 Concierge & Security"],
        "proximity": [
            {"name": "Gulshan Lake Park", "dist": "0.3 km"},
            {"name": "Diplomatic Zone", "dist": "0.5 km"},
            {"name": "American Club", "dist": "0.8 km"}
        ],
        "floors": 18,
        "total_units": 32,
        "handover": "Q4 2026"
    }'::jsonb
),
(
    'proj_102',
    'Baridhara Luxury Suites',
    'Park Road, Baridhara Diplomatic Zone, Dhaka',
    'BDT 6.50 Cr - 12.00 Cr',
    65000000,
    5,
    'Exclusive boutique residences for HNIs, ambassadors, and corporate leaders. Features bespoke duplex units, temperature-controlled indoor pool, and private garden verandas.',
    '{
        "status": "Under Construction",
        "coordinates": [23.7998, 90.4221],
        "image": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        "brochure": "/GLG_Gulshan_Heights_Property_Details.pdf",
        "amenities": ["Temperature-Controlled Pool", "Private Garden Verandas", "Biometric Smart Access", "Basement Parking (3 cars/unit)", "EV Fast Chargers"],
        "proximity": [
            {"name": "Baridhara Park", "dist": "0.1 km"},
            {"name": "Embassy of Japan", "dist": "0.4 km"},
            {"name": "Gulshan 2 Circle", "dist": "1.2 km"}
        ],
        "floors": 14,
        "total_units": 18,
        "handover": "Q1 2027"
    }'::jsonb
),
(
    'proj_103',
    'GLG Sky Tower',
    'Gulshan Avenue, Gulshan 1, Dhaka',
    'BDT 3.50 Cr - 5.80 Cr',
    35000000,
    3,
    'Modern architectural high-rise offering 20:80 flexible subvention payment plans, floor-to-ceiling glass facades, and rooftop fitness club.',
    '{
        "status": "Under Construction",
        "coordinates": [23.7781, 90.4175],
        "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        "brochure": "/GLG_Gulshan_Heights_Property_Details.pdf",
        "amenities": ["Sky Gym & Spa", "20:80 Subvention Scheme", "Co-working Lounge", "Multi-tier Fire Safety", "Full Power Backup"],
        "proximity": [
            {"name": "Gulshan 1 DCC Market", "dist": "0.2 km"},
            {"name": "Hatirjheel Promenade", "dist": "0.6 km"},
            {"name": "Police Plaza Concord", "dist": "0.9 km"}
        ],
        "floors": 22,
        "total_units": 48,
        "handover": "Q3 2027"
    }'::jsonb
),
(
    'proj_104',
    'Banani Crest Towers',
    'Road 11, Block C, Banani, Dhaka',
    'BDT 3.20 Cr - 4.90 Cr',
    32000000,
    3,
    'Contemporary urban living on Banani vibrant Road 11 corridor. Proximity to top international schools, fine dining, and Kemal Ataturk Avenue expressway.',
    '{
        "status": "Ready for Handover",
        "coordinates": [23.7937, 90.4043],
        "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        "brochure": "/GLG_Gulshan_Heights_Property_Details.pdf",
        "amenities": ["Rooftop BBQ Pavilion", "High-Speed Elevators", "Children Play Zone", "CCTV Surveillance", "Solar Rooftop Grid"],
        "proximity": [
            {"name": "Banani Road 11 Dining Hub", "dist": "0.1 km"},
            {"name": "Kemal Ataturk Ave", "dist": "0.3 km"},
            {"name": "Banani Lake", "dist": "0.5 km"}
        ],
        "floors": 16,
        "total_units": 28,
        "handover": "Ready"
    }'::jsonb
),
(
    'proj_105',
    'Dhanmondi Lake Oasis',
    'Road 8/A, Dhanmondi, Dhaka',
    'BDT 2.80 Cr - 4.20 Cr',
    28000000,
    3,
    'Serene lake-facing residences in the cultural and educational heart of Dhanmondi. Designed for multi-generational family comfort with spacious verandas.',
    '{
        "status": "Under Construction",
        "coordinates": [23.7461, 90.3742],
        "image": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
        "brochure": "/GLG_Gulshan_Heights_Property_Details.pdf",
        "amenities": ["Lake Walking Trail", "Community Hall", "Rainwater Harvesting", "Emergency Doctor Room", "24/7 Security"],
        "proximity": [
            {"name": "Dhanmondi Lake", "dist": "0.1 km"},
            {"name": "Medinova Hospital", "dist": "0.4 km"},
            {"name": "Mastermind School", "dist": "0.7 km"}
        ],
        "floors": 12,
        "total_units": 24,
        "handover": "Q2 2026"
    }'::jsonb
)
ON CONFLICT (project_id) DO UPDATE SET
    name = EXCLUDED.name,
    location = EXCLUDED.location,
    price = EXCLUDED.price,
    price_val = EXCLUDED.price_val,
    bedrooms = EXCLUDED.bedrooms,
    description = EXCLUDED.description,
    features = EXCLUDED.features;

-- Initial Knowledge Base Document Registration (Synced with existing 1,634 chunks)
INSERT INTO knowledge_documents (doc_id, filename, file_type, ocr_status, chunk_count)
VALUES
    ('doc_faq_2026', 'GLG_Assets_FAQ_2026.pdf', 'pdf', 'completed', 96),
    ('doc_governance', 'GLG_Company_Governance_and_Policies.pdf', 'pdf', 'completed', 33),
    ('doc_gulshan_heights', 'GLG_Gulshan_Heights_Property_Details.pdf', 'pdf', 'completed', 33),
    ('doc_legal', 'GLG_Legal_and_Compliance_Guide.pdf', 'pdf', 'completed', 33),
    ('doc_pricing_2026', 'GLG_Pricing_and_Payment_Plans_2026.pdf', 'pdf', 'completed', 33),
    ('doc_system_design', 'GLG_Assets_System_Design_and_Report.pdf', 'pdf', 'completed', 726),
    ('proj_proj_banani_crest', 'Projects_Catalog.json', 'json', 'completed', 12),
    ('proj_proj_gulshan_luxe', 'Projects_Catalog.json', 'json', 'completed', 11),
    ('proj_proj_gulshan_palace', 'Projects_Catalog.json', 'json', 'completed', 11),
    ('proj_proj_mumbai_luxe', 'Projects_Catalog.json', 'json', 'completed', 12)
ON CONFLICT (doc_id) DO UPDATE SET
    filename = EXCLUDED.filename,
    file_type = EXCLUDED.file_type,
    ocr_status = EXCLUDED.ocr_status,
    chunk_count = EXCLUDED.chunk_count;

-- Initial Media Assets
INSERT INTO media (media_id, project_id, media_type, url)
VALUES
    ('med_101', 'proj_101', 'brochure_pdf', '/GLG_Gulshan_Heights_Property_Details.pdf'),
    ('med_102', 'proj_102', 'brochure_pdf', '/GLG_Gulshan_Heights_Property_Details.pdf'),
    ('med_103', 'proj_103', 'brochure_pdf', '/GLG_Gulshan_Heights_Property_Details.pdf')
ON CONFLICT (media_id) DO NOTHING;

-- Initial Daily Analytics Seed
INSERT INTO analytics (id, date, total_messages, total_leads, ai_resolved, escalated)
VALUES
    ('ana_today', TO_CHAR(NOW(), 'YYYY-MM-DD'), 156, 42, 38, 4)
ON CONFLICT (id) DO UPDATE SET
    total_messages = EXCLUDED.total_messages,
    total_leads = EXCLUDED.total_leads,
    ai_resolved = EXCLUDED.ai_resolved,
    escalated = EXCLUDED.escalated;

-- ----------------------------------------------------------------------------
-- 6. ENTERPRISE AUTOMATION & SOCIAL ENGINE EXTENSIONS
-- ----------------------------------------------------------------------------

-- Table 10: ad_campaigns (Multi-Channel ROI & Social Analytics)
CREATE TABLE IF NOT EXISTS public.ad_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_name VARCHAR(256) NOT NULL,
    platform VARCHAR(64) NOT NULL, -- 'facebook', 'instagram', 'youtube', 'linkedin', 'tiktok'
    campaign_type VARCHAR(64) DEFAULT 'lead_generation',
    project_id VARCHAR(128) REFERENCES public.projects(project_id) ON DELETE SET NULL,
    status VARCHAR(32) DEFAULT 'active',
    budget_bdt NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    ad_spend_bdt NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    impressions INT NOT NULL DEFAULT 0,
    reach INT NOT NULL DEFAULT 0,
    engagements INT NOT NULL DEFAULT 0,
    leads_generated INT NOT NULL DEFAULT 0,
    pipeline_value_bdt NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    cpl_bdt NUMERIC(10, 2) GENERATED ALWAYS AS (
        CASE WHEN leads_generated > 0 THEN ROUND(ad_spend_bdt / leads_generated, 2) ELSE 0.00 END
    ) STORED,
    roas NUMERIC(6, 2) GENERATED ALWAYS AS (
        CASE WHEN ad_spend_bdt > 0 THEN ROUND(pipeline_value_bdt / ad_spend_bdt, 2) ELSE 0.00 END
    ) STORED,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 11: social_posts (Content Generator, Approvals & Content Calendar)
CREATE TABLE IF NOT EXISTS public.social_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(128) REFERENCES public.projects(project_id) ON DELETE SET NULL,
    platform VARCHAR(64) NOT NULL,
    topic VARCHAR(256) NOT NULL,
    post_content TEXT NOT NULL,
    hashtags TEXT[] DEFAULT '{}',
    media_url TEXT,
    tone VARCHAR(64) DEFAULT 'luxury',
    language VARCHAR(32) DEFAULT 'dual',
    status VARCHAR(32) DEFAULT 'draft',
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    shares_count INT DEFAULT 0,
    created_by VARCHAR(128) DEFAULT 'ai-content-engine',
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 12: bookings (Site Tour Appointments & Tour Calendar)
CREATE TABLE IF NOT EXISTS public.bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_reference VARCHAR(64) UNIQUE NOT NULL,
    project_id VARCHAR(128) REFERENCES public.projects(project_id) ON DELETE RESTRICT,
    customer_name VARCHAR(256) NOT NULL,
    customer_email VARCHAR(256),
    customer_phone VARCHAR(64) NOT NULL,
    tour_date DATE NOT NULL,
    tour_time_slot VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'pending',
    source VARCHAR(64) DEFAULT 'website',
    notes TEXT,
    assigned_agent_name VARCHAR(256),
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 13: calendar_milestones (Executive Critical Dates & Milestone Tracking)
CREATE TABLE IF NOT EXISTS public.calendar_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(256) NOT NULL,
    client_name VARCHAR(256) NOT NULL,
    project_id VARCHAR(128) REFERENCES public.projects(project_id) ON DELETE CASCADE,
    milestone_date DATE NOT NULL,
    time_range VARCHAR(64) DEFAULT 'All Day',
    milestone_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'upcoming',
    badge_variant VARCHAR(32) DEFAULT 'emerald',
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.ad_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.social_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calendar_milestones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow authenticated read ad_campaigns" ON public.ad_campaigns FOR SELECT USING (true);
CREATE POLICY "Allow service insert ad_campaigns" ON public.ad_campaigns FOR ALL USING (true);

CREATE POLICY "Allow authenticated read social_posts" ON public.social_posts FOR SELECT USING (true);
CREATE POLICY "Allow service insert social_posts" ON public.social_posts FOR ALL USING (true);

CREATE POLICY "Allow authenticated read bookings" ON public.bookings FOR SELECT USING (true);
CREATE POLICY "Allow service insert bookings" ON public.bookings FOR ALL USING (true);

CREATE POLICY "Allow authenticated read calendar_milestones" ON public.calendar_milestones FOR SELECT USING (true);
CREATE POLICY "Allow service insert calendar_milestones" ON public.calendar_milestones FOR ALL USING (true);

-- Seed Ad Campaigns
INSERT INTO public.ad_campaigns (campaign_name, platform, campaign_type, budget_bdt, ad_spend_bdt, impressions, reach, engagements, leads_generated, pipeline_value_bdt, start_date)
VALUES 
('GLG Gulshan Heights VIP Launch', 'facebook', 'lead_generation', 450000.00, 425000.00, 540000, 420000, 32400, 268, 24500000.00, CURRENT_DATE - INTERVAL '25 days'),
('Baridhara Diplomatic Luxe Showcase', 'instagram', 'lead_generation', 400000.00, 365000.00, 480000, 380000, 36800, 224, 38000000.00, CURRENT_DATE - INTERVAL '20 days'),
('Banani Crest Towers Commercial Suites', 'linkedin', 'lead_generation', 250000.00, 185000.00, 70000, 52000, 7800, 78, 14500000.00, CURRENT_DATE - INTERVAL '15 days'),
('GLG 4K Architectural Walkthrough', 'youtube', 'brand_awareness', 150000.00, 120000.00, 210000, 160000, 12400, 42, 6500000.00, CURRENT_DATE - INTERVAL '12 days'),
('Dhaka Luxury Living Lifestyle Shorts', 'tiktok', 'video_views', 80000.00, 45000.00, 120000, 95000, 18200, 30, 4200000.00, CURRENT_DATE - INTERVAL '10 days');

-- Seed Calendar Milestones
INSERT INTO public.calendar_milestones (title, client_name, milestone_date, time_range, milestone_type, status, badge_variant)
VALUES
('VIP Site Visit: GLG Gulshan Heights', 'Tanvir Ahmed (High Intent)', CURRENT_DATE + INTERVAL '1 day', '3:00 PM - 4:30 PM', 'tour', 'confirmed', 'emerald'),
('Contract Handover Review: Luxe Baridhara', 'Diplomatic Mission Corp', CURRENT_DATE + INTERVAL '3 days', '11:00 AM - 12:30 PM', 'handover', 'upcoming', 'coral'),
('Installment Milestone 2 Payment Review', 'Nusrat Jahan (Apt 8B)', CURRENT_DATE + INTERVAL '5 days', 'End of Day', 'payment', 'pending', 'amber'),
('HITL Booking Escalation Review', 'Rahim Chowdhury (Penthouse Inquirer)', CURRENT_DATE + INTERVAL '8 days', 'Needs Confirmation', 'escalation', 'action_required', 'rose');

-- ----------------------------------------------------------------------------
-- 10. AGENT CONFIGURATIONS & FINE-TUNING TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.agent_configurations (
    id VARCHAR(64) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    agent_key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    provider VARCHAR(64) DEFAULT 'groq',
    model VARCHAR(128) DEFAULT 'llama-3.3-70b-versatile',
    fallback_model VARCHAR(128) DEFAULT 'llama-3.1-8b-instant',
    temperature FLOAT DEFAULT 0.2,
    top_p FLOAT DEFAULT 0.9,
    max_tokens INT DEFAULT 1024,
    presence_penalty FLOAT DEFAULT 0.0,
    frequency_penalty FLOAT DEFAULT 0.0,
    system_prompt TEXT NOT NULL,
    rag_settings JSONB DEFAULT '{}'::jsonb,
    lora_adapter VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE,
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

CREATE TABLE IF NOT EXISTS public.fine_tuning_jobs (
    id VARCHAR(64) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    job_name VARCHAR(256) NOT NULL,
    base_model VARCHAR(128) NOT NULL,
    target_agent VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'running',
    dataset_samples INT DEFAULT 0,
    epochs INT DEFAULT 3,
    current_epoch INT DEFAULT 1,
    learning_rate FLOAT DEFAULT 0.0002,
    training_loss FLOAT DEFAULT 0.45,
    loss_history JSONB DEFAULT '[]'::jsonb,
    adapter_id VARCHAR(128),
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Enable RLS
ALTER TABLE public.agent_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fine_tuning_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_agent_configurations ON public.agent_configurations
FOR ALL USING (tenant_id = 'glg-assets-main') WITH CHECK (tenant_id = 'glg-assets-main');

CREATE POLICY tenant_isolation_fine_tuning_jobs ON public.fine_tuning_jobs
FOR ALL USING (tenant_id = 'glg-assets-main') WITH CHECK (tenant_id = 'glg-assets-main');

-- ----------------------------------------------------------------------------
-- 11. AI CONTROL PLANE, AGENT STUDIO & GOVERNANCE TABLES
-- ----------------------------------------------------------------------------

-- Table 14: ai_agents (Autonomous Agent Profiles)
CREATE TABLE IF NOT EXISTS public.ai_agents (
    id VARCHAR(64) PRIMARY KEY,
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    role VARCHAR(64) DEFAULT 'assistant',
    objective TEXT,
    owner VARCHAR(128) DEFAULT 'dev-team@glgassets.com',
    status VARCHAR(32) DEFAULT 'PRODUCTION',
    environment VARCHAR(32) DEFAULT 'production',
    primary_model VARCHAR(128) DEFAULT 'llama-3.3-70b-versatile',
    fallback_model VARCHAR(128) DEFAULT 'llama-3.1-8b-instant',
    current_prompt_version VARCHAR(32) DEFAULT 'v1.0',
    temperature FLOAT DEFAULT 0.2,
    top_p FLOAT DEFAULT 0.9,
    max_tokens INT DEFAULT 1024,
    presence_penalty FLOAT DEFAULT 0.0,
    frequency_penalty FLOAT DEFAULT 0.0,
    persona_preset VARCHAR(64) DEFAULT 'Consultative Luxury',
    enabled_tools JSONB DEFAULT '[]'::jsonb,
    rag_config JSONB DEFAULT '{}'::jsonb,
    memory_config JSONB DEFAULT '{}'::jsonb,
    guardrail_policy_ids JSONB DEFAULT '[]'::jsonb,
    output_schema JSONB,
    human_approval_policy VARCHAR(64) DEFAULT 'NONE',
    max_execution_steps INT DEFAULT 5,
    timeout_seconds INT DEFAULT 30,
    retry_policy JSONB DEFAULT '{}'::jsonb,
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 15: ai_agent_versions
CREATE TABLE IF NOT EXISTS public.ai_agent_versions (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) REFERENCES public.ai_agents(id) ON DELETE CASCADE,
    version_tag VARCHAR(32) NOT NULL,
    snapshot JSONB NOT NULL,
    changelog TEXT,
    created_by VARCHAR(128) DEFAULT 'developer@glgassets.com',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 16: ai_providers
CREATE TABLE IF NOT EXISTS public.ai_providers (
    id VARCHAR(64) PRIMARY KEY,
    provider_key VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    base_url VARCHAR(256),
    is_active BOOLEAN DEFAULT TRUE,
    health_status VARCHAR(32) DEFAULT 'HEALTHY',
    last_ping_ms FLOAT,
    last_checked_at TIMESTAMPTZ,
    capabilities JSONB DEFAULT '[]'::jsonb,
    rate_limit_rpm INT DEFAULT 60,
    rate_limit_tpm INT DEFAULT 100000,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 17: ai_models
CREATE TABLE IF NOT EXISTS public.ai_models (
    id VARCHAR(64) PRIMARY KEY,
    model_id VARCHAR(128) UNIQUE NOT NULL,
    provider_id VARCHAR(64) REFERENCES public.ai_providers(id) ON DELETE CASCADE,
    display_name VARCHAR(128) NOT NULL,
    model_type VARCHAR(32) DEFAULT 'BASE',
    context_window INT DEFAULT 131072,
    max_output_tokens INT DEFAULT 8192,
    input_cost_per_m FLOAT DEFAULT 0.59,
    output_cost_per_m FLOAT DEFAULT 0.79,
    cached_cost_per_m FLOAT DEFAULT 0.30,
    supports_structured_output BOOLEAN DEFAULT TRUE,
    supports_tools BOOLEAN DEFAULT TRUE,
    supports_streaming BOOLEAN DEFAULT TRUE,
    status VARCHAR(32) DEFAULT 'PRODUCTION',
    benchmark_scores JSONB DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 18: ai_prompt_templates
CREATE TABLE IF NOT EXISTS public.ai_prompt_templates (
    id VARCHAR(64) PRIMARY KEY,
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    target_agent_id VARCHAR(64) NOT NULL,
    system_prompt TEXT NOT NULL,
    developer_instructions TEXT,
    tool_instructions TEXT,
    output_constraints TEXT,
    active_version VARCHAR(32) DEFAULT 'v1.0',
    created_by VARCHAR(128) DEFAULT 'developer@glgassets.com',
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 19: ai_prompt_versions
CREATE TABLE IF NOT EXISTS public.ai_prompt_versions (
    id VARCHAR(64) PRIMARY KEY,
    template_id VARCHAR(64) REFERENCES public.ai_prompt_templates(id) ON DELETE CASCADE,
    version_tag VARCHAR(32) NOT NULL,
    system_prompt TEXT NOT NULL,
    developer_instructions TEXT,
    tool_instructions TEXT,
    output_constraints TEXT,
    declared_variables JSONB DEFAULT '[]'::jsonb,
    token_estimate INT DEFAULT 0,
    character_count INT DEFAULT 0,
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    created_by VARCHAR(128) DEFAULT 'developer@glgassets.com',
    changelog TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 20: ai_tools
CREATE TABLE IF NOT EXISTS public.ai_tools (
    id VARCHAR(64) PRIMARY KEY,
    tool_key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(64) DEFAULT 'data_retrieval',
    parameters_schema JSONB DEFAULT '{}'::jsonb,
    output_schema JSONB,
    requires_approval BOOLEAN DEFAULT FALSE,
    risk_level VARCHAR(32) DEFAULT 'LOW',
    timeout_ms INT DEFAULT 5000,
    is_enabled BOOLEAN DEFAULT TRUE,
    assigned_agents JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 21: ai_datasets
CREATE TABLE IF NOT EXISTS public.ai_datasets (
    id VARCHAR(64) PRIMARY KEY,
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    dataset_type VARCHAR(32) DEFAULT 'evaluation',
    target_agent VARCHAR(64) DEFAULT 'property_agent',
    version VARCHAR(32) DEFAULT 'v1.0',
    total_examples INT DEFAULT 0,
    quality_score FLOAT DEFAULT 96.5,
    train_count INT DEFAULT 0,
    val_count INT DEFAULT 0,
    test_count INT DEFAULT 0,
    is_locked BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(128) DEFAULT 'developer@glgassets.com',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 22: ai_evaluations
CREATE TABLE IF NOT EXISTS public.ai_evaluations (
    id VARCHAR(64) PRIMARY KEY,
    suite_name VARCHAR(128) NOT NULL,
    dataset_id VARCHAR(64) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    model_tested VARCHAR(128) NOT NULL,
    prompt_version VARCHAR(32) DEFAULT 'v1.0',
    total_cases INT DEFAULT 0,
    passed_cases INT DEFAULT 0,
    failed_cases INT DEFAULT 0,
    accuracy_pct FLOAT DEFAULT 0.0,
    groundedness_pct FLOAT DEFAULT 0.0,
    hallucination_pct FLOAT DEFAULT 0.0,
    tool_accuracy_pct FLOAT DEFAULT 0.0,
    schema_correctness_pct FLOAT DEFAULT 0.0,
    avg_latency_ms FLOAT DEFAULT 0.0,
    status VARCHAR(32) DEFAULT 'COMPLETED',
    gate_verdict VARCHAR(16) DEFAULT 'PASS',
    report_data JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(128) DEFAULT 'developer@glgassets.com',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 23: ai_guardrail_policies
CREATE TABLE IF NOT EXISTS public.ai_guardrail_policies (
    id VARCHAR(64) PRIMARY KEY,
    category VARCHAR(32) NOT NULL,
    rule_name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    action VARCHAR(32) DEFAULT 'BLOCK',
    severity VARCHAR(32) DEFAULT 'HIGH',
    rule_parameters JSONB DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN DEFAULT TRUE,
    total_triggers INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Table 24: ai_governance_logs
CREATE TABLE IF NOT EXISTS public.ai_governance_logs (
    id VARCHAR(64) PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    event_type VARCHAR(64) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    severity VARCHAR(32) DEFAULT 'INFO',
    actor VARCHAR(128) DEFAULT 'system',
    action_taken VARCHAR(64) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    tenant_id VARCHAR(128) DEFAULT 'glg-assets-main'
);

-- Enable RLS on AI tables
ALTER TABLE public.ai_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_agent_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_prompt_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_prompt_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_guardrail_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_governance_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow authenticated read ai_agents" ON public.ai_agents FOR SELECT USING (true);
CREATE POLICY "Allow service insert ai_agents" ON public.ai_agents FOR ALL USING (true);

CREATE POLICY "Allow authenticated read ai_models" ON public.ai_models FOR SELECT USING (true);
CREATE POLICY "Allow service insert ai_models" ON public.ai_models FOR ALL USING (true);

CREATE POLICY "Allow authenticated read ai_prompt_templates" ON public.ai_prompt_templates FOR SELECT USING (true);
CREATE POLICY "Allow service insert ai_prompt_templates" ON public.ai_prompt_templates FOR ALL USING (true);

CREATE POLICY "Allow authenticated read ai_tools" ON public.ai_tools FOR SELECT USING (true);
CREATE POLICY "Allow service insert ai_tools" ON public.ai_tools FOR ALL USING (true);

-- ----------------------------------------------------------------------------
-- 12. WORKFLOW TABLES (LEADS & INVENTORY UNITS)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.leads (
    lead_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL DEFAULT 'glg-assets-main',
    customer_id VARCHAR(36),
    name VARCHAR(200) NOT NULL,
    contact VARCHAR(200) NOT NULL,
    source VARCHAR(80) NOT NULL DEFAULT 'website',
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);
CREATE INDEX IF NOT EXISTS idx_leads_tenant_id ON public.leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON public.leads(status);

CREATE TABLE IF NOT EXISTS public.inventory_units (
    unit_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL DEFAULT 'glg-assets-main',
    project_id VARCHAR(128) REFERENCES public.projects(project_id) ON DELETE CASCADE,
    bedrooms INT NOT NULL,
    price VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    version INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);
CREATE INDEX IF NOT EXISTS idx_inventory_units_project_id ON public.inventory_units(project_id);

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_units ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow authenticated read leads" ON public.leads FOR SELECT USING (true);
CREATE POLICY "Allow service insert leads" ON public.leads FOR ALL USING (true);
CREATE POLICY "Allow authenticated read inventory_units" ON public.inventory_units FOR SELECT USING (true);
CREATE POLICY "Allow service insert inventory_units" ON public.inventory_units FOR ALL USING (true);

-- ----------------------------------------------------------------------------
-- 13. CANONICAL SEED DATA (AI CONTROL PLANE & AGENTS)
-- ----------------------------------------------------------------------------

-- Seed AI Providers
INSERT INTO public.ai_providers (id, provider_key, display_name, base_url, is_active, health_status, last_ping_ms, capabilities, rate_limit_rpm, rate_limit_tpm)
VALUES
('prov-groq', 'groq', 'Groq LPU Inference Engine', 'https://api.groq.com/openai/v1', true, 'HEALTHY', 142.5, '["chat", "streaming", "tools", "structured_output"]'::jsonb, 60, 120000),
('prov-openai', 'openai', 'OpenAI Enterprise Gateway', 'https://api.openai.com/v1', true, 'HEALTHY', 210.0, '["chat", "streaming", "tools", "embeddings", "structured_output"]'::jsonb, 120, 250000)
ON CONFLICT (id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    base_url = EXCLUDED.base_url,
    is_active = EXCLUDED.is_active;

-- Seed AI Models
INSERT INTO public.ai_models (id, model_id, provider_id, display_name, model_type, context_window, max_output_tokens, input_cost_per_m, output_cost_per_m, supports_structured_output, supports_tools, supports_streaming, status, is_enabled)
VALUES
('model-llama-33-70b', 'llama-3.3-70b-versatile', 'prov-groq', 'Llama 3.3 70B Versatile (Groq)', 'BASE', 131072, 8192, 0.59, 0.79, true, true, true, 'PRODUCTION', true),
('model-llama-31-8b', 'llama-3.1-8b-instant', 'prov-groq', 'Llama 3.1 8B Instant (Groq Fast Fallback)', 'BASE', 131072, 8192, 0.05, 0.08, true, true, true, 'PRODUCTION', true),
('model-gpt-4o', 'gpt-4o', 'prov-openai', 'GPT-4o Omnichannel Flagship (OpenAI)', 'BASE', 128000, 4096, 2.50, 10.00, true, true, true, 'PRODUCTION', true),
('model-emb-3-large', 'text-embedding-3-large', 'prov-openai', 'OpenAI Text Embedding 3 Large (1024/1536d)', 'EMBEDDING', 8191, 0, 0.13, 0.0, false, false, false, 'PRODUCTION', true)
ON CONFLICT (id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    is_enabled = EXCLUDED.is_enabled;

-- Seed Autonomous AI Agents
INSERT INTO public.ai_agents (id, slug, name, description, role, objective, owner, status, environment, primary_model, fallback_model, current_prompt_version, temperature, top_p, max_tokens, persona_preset, enabled_tools, rag_config, memory_config, guardrail_policy_ids, human_approval_policy, max_execution_steps, timeout_seconds)
VALUES
('agent-prop-001', 'property_agent', 'Property Consultant Agent', 'Consultative real estate advisor specialized in Gulshan, Banani, and Baridhara luxury residences, verified unit layouts, and BDT pricing.', 'Property Advisor', 'Guide high-net-worth investors through luxury floor plans, verified prices, and private site visits.', 'sales-tech@glgassets.com', 'PRODUCTION', 'production', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'v2.1', 0.2, 0.9, 1024, 'Consultative Luxury', '["property_search", "availability_check", "crm_lead_sync", "schedule_tour"]'::jsonb, '{"top_k": 5, "chunk_size": 512, "hybrid_alpha": 0.65, "enabled_sources": ["property_db", "brochures", "pricing_matrix"], "grounding_enforced": true, "similarity_threshold": 0.68}'::jsonb, '{"scope": "CONVERSATION", "max_entries": 20, "retention_ttl_hours": 168, "relevance_threshold": 0.65}'::jsonb, '["gr-fact-001", "gr-pii-001", "gr-inj-001"]'::jsonb, 'HIGH_RISK_ONLY', 6, 30),
('agent-faq-002', 'faq_agent', 'FAQ & Customer Advisory Agent', 'Official policy advisor addressing NID/TIN verification, installment schedules, legal disclosures, and developer credentials.', 'Policy Specialist', 'Answer customer questions factually using approved company policies and financing partnerships.', 'legal-compliance@glgassets.com', 'PRODUCTION', 'production', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'v1.4', 0.15, 0.85, 1024, 'Analytical Advisor', '["knowledge_search", "policy_lookup"]'::jsonb, '{"top_k": 4, "chunk_size": 512, "hybrid_alpha": 0.7, "enabled_sources": ["faq_policies", "legal_disclosures"], "grounding_enforced": true, "similarity_threshold": 0.7}'::jsonb, '{"scope": "CONVERSATION", "max_entries": 10, "retention_ttl_hours": 72, "relevance_threshold": 0.7}'::jsonb, '["gr-pii-001", "gr-inj-001"]'::jsonb, 'NONE', 4, 25),
('agent-sup-003', 'supervisor', 'Supervisor Intent Orchestrator', 'Deterministic classifier routing incoming multi-lingual inquiries (Bangla, Banglish, English) to the optimal domain agent with confidence telemetry.', 'Router & Orchestrator', 'Detect user intent, extract location/budget entities, and dispatch to appropriate sub-agents.', 'core-ai@glgassets.com', 'PRODUCTION', 'production', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'v2.0', 0.1, 0.85, 512, 'Deterministic Router', '["crm_lead_sync"]'::jsonb, '{"top_k": 3, "chunk_size": 256, "hybrid_alpha": 0.5, "enabled_sources": ["faq_policies"], "grounding_enforced": false, "similarity_threshold": 0.6}'::jsonb, '{"scope": "SHORT_TERM", "max_entries": 6, "retention_ttl_hours": 24, "relevance_threshold": 0.6}'::jsonb, '["gr-inj-001"]'::jsonb, 'NONE', 3, 15),
('agent-email-004', 'email_agent', 'Lead & Email Concierge Agent', 'Executive correspondent drafting formal proposals, VIP site visit itineraries, and structured payment plan breakdowns for investors.', 'Executive Concierge', 'Compose polished investor communications and confirm scheduled appointments.', 'investor-relations@glgassets.com', 'PRODUCTION', 'production', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'v1.2', 0.3, 0.9, 1200, 'High-Urgency Closer', '["email_dispatch", "schedule_tour", "crm_lead_sync"]'::jsonb, '{"top_k": 4, "chunk_size": 512, "hybrid_alpha": 0.6, "enabled_sources": ["property_db", "pricing_matrix"], "grounding_enforced": true, "similarity_threshold": 0.65}'::jsonb, '{"scope": "CUSTOMER", "max_entries": 15, "retention_ttl_hours": 336, "relevance_threshold": 0.65}'::jsonb, '["gr-fact-001", "gr-pii-001"]'::jsonb, 'HIGH_RISK_ONLY', 5, 35),
('agent-social-005', 'social_bridge', 'Social Media Omnichannel Bridge', 'Engaging conversational bridge managing WhatsApp, Facebook Messenger, and Instagram Direct conversations with warm hospitality.', 'Social Concierge', 'Convert social engagements into qualified buyer leads via welcoming Bangla/Banglish/English interaction.', 'growth-marketing@glgassets.com', 'PRODUCTION', 'production', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'v1.5', 0.35, 0.95, 850, 'Warm Conversational', '["whatsapp_send", "property_search", "crm_lead_sync"]'::jsonb, '{"top_k": 3, "chunk_size": 384, "hybrid_alpha": 0.55, "enabled_sources": ["property_db", "brochures"], "grounding_enforced": true, "similarity_threshold": 0.6}'::jsonb, '{"scope": "CONVERSATION", "max_entries": 8, "retention_ttl_hours": 48, "relevance_threshold": 0.6}'::jsonb, '["gr-fact-001", "gr-pii-001", "gr-inj-001"]'::jsonb, 'NONE', 4, 20)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    primary_model = EXCLUDED.primary_model,
    fallback_model = EXCLUDED.fallback_model,
    rag_config = EXCLUDED.rag_config;

-- Seed Guardrail Policies
INSERT INTO public.ai_guardrail_policies (id, category, rule_name, description, action, severity, is_enabled)
VALUES
('gr-fact-001', 'FACTUAL_GROUNDING', 'Anti-Hallucination Factual Grounding', 'Requires all unit specifications, prices, and amenities to match verified knowledge base chunks with >= 0.70 grounding confidence score.', 'REWRITE', 'CRITICAL', true),
('gr-pii-001', 'PRIVACY', 'PII Masking & Privacy Shield', 'Redacts Bangladeshi National ID (NID), Tax Identification Numbers (TIN), personal bank account numbers, and credit card numbers prior to model inference.', 'REDACT', 'HIGH', true),
('gr-inj-001', 'SECURITY', 'Prompt Injection & Jailbreak Defense', 'Detects and blocks adversarial jailbreak attempts, system prompt exfiltration, and unauthorized role overrides.', 'BLOCK', 'CRITICAL', true)
ON CONFLICT (id) DO UPDATE SET
    rule_name = EXCLUDED.rule_name,
    is_enabled = EXCLUDED.is_enabled;

-- Seed Agent Configurations (Studio UI Sync)
INSERT INTO public.agent_configurations (id, agent_key, name, description, provider, model, fallback_model, temperature, top_p, max_tokens, system_prompt)
VALUES
('cfg-prop-001', 'property_agent', 'Property Consultant Agent', 'Luxury real-estate specialist for Gulshan, Banani, and Baridhara developments.', 'groq', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 0.2, 0.9, 1024, 'You are the Elite Real Estate Consultant for GLG Assets LTD, Dhaka premiere luxury developer. Always answer professionally, cite specific developments (GLG Gulshan Heights, Baridhara Luxury Suites, GLG Sky Tower, Banani Crest Towers, Dhanmondi Lake Oasis), provide exact BDT pricing when available, and invite clients to book VIP site tours.'),
('cfg-faq-002', 'faq_agent', 'FAQ & Policy Advisor', 'Official policy advisor on booking procedures, payment plans, and handover timelines.', 'groq', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 0.15, 0.85, 1024, 'You are the Compliance & Customer Advisory Specialist for GLG Assets LTD. Answer inquiries regarding payment schedules, legal documentation, RAJUK approvals, and warranty coverage accurately based on official policy documentation.'),
('cfg-sup-003', 'supervisor', 'Supervisor Intent Orchestrator', 'Routes user queries to the appropriate specialized agent.', 'groq', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 0.1, 0.85, 512, 'You are the Master Orchestration Supervisor for GLG Assets Social AI OS. Analyze customer language (English, Bangla, Banglish), identify intent (property inquiry, price negotiation, site visit booking, complaints, general greeting), and route accordingly.')
ON CONFLICT (agent_key) DO UPDATE SET
    name = EXCLUDED.name,
    model = EXCLUDED.model,
    system_prompt = EXCLUDED.system_prompt;

-- ----------------------------------------------------------------------------
-- SUCCESS VERIFICATION QUERY
-- ----------------------------------------------------------------------------
SELECT 
    'Supabase Database Initialized Successfully!' AS status,
    (SELECT COUNT(*) FROM projects) AS total_projects,
    (SELECT COUNT(*) FROM ad_campaigns) AS total_campaigns,
    (SELECT COUNT(*) FROM calendar_milestones) AS total_milestones,
    (SELECT COUNT(*) FROM knowledge_documents) AS total_documents,
    (SELECT COUNT(*) FROM ai_agents) AS total_ai_agents,
    (SELECT COUNT(*) FROM ai_models) AS total_ai_models;

