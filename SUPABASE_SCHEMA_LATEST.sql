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

-- Initial Knowledge Base Document Registration
INSERT INTO knowledge_documents (doc_id, filename, file_type, ocr_status, chunk_count)
VALUES
    ('doc_101', 'GLG_Gulshan_Heights_Property_Details.pdf', 'pdf', 'completed', 14),
    ('doc_102', 'GLG_Pricing_and_Payment_Plans_2026.pdf', 'pdf', 'completed', 10),
    ('doc_103', 'GLG_Legal_and_Compliance_Guide.pdf', 'pdf', 'completed', 8)
ON CONFLICT (doc_id) DO NOTHING;

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
-- SUCCESS VERIFICATION QUERY
-- ----------------------------------------------------------------------------
SELECT 
    'Supabase Database Initialized Successfully!' AS status,
    (SELECT COUNT(*) FROM projects) AS total_projects,
    (SELECT COUNT(*) FROM ad_campaigns) AS total_campaigns,
    (SELECT COUNT(*) FROM calendar_milestones) AS total_milestones,
    (SELECT COUNT(*) FROM knowledge_documents) AS total_documents;
