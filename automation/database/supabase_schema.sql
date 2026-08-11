-- ============================================================
-- GLG ASSETS REAL ESTATE AI OS — SUPABASE & PINECONE DATABASE SCHEMA
-- Compatible with Supabase PostgreSQL, pgvector, RLS & Pinecone Dual Sync
-- ============================================================

-- 1. Enable Required PostgreSQL Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. System Users (Role-Based Access Control - RBAC)
CREATE TABLE IF NOT EXISTS system_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'manager', 'agent', 'viewer')),
    hashed_password TEXT NOT NULL,
    tenant_id VARCHAR(255) DEFAULT 'glg-default',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed Initial System Demo Accounts (Password: admin123, manager123, agent123, viewer123)
INSERT INTO system_users (id, email, full_name, role, hashed_password, tenant_id)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'admin@glgassets.com', 'Alex Mercer (Admin)', 'admin', '8b48a1262d1d07c08e50b181b5d153213c3b06316279f187a4d5e9b33a5957d1', 'glg-default'),
    ('00000000-0000-0000-0000-000000000002', 'manager@glgassets.com', 'Sarah Connor (Manager)', 'manager', '4b3226db9ebc0e0b3554d19d6ebfb937d5c9523f2f84260a95f9c47012354c41', 'glg-default'),
    ('00000000-0000-0000-0000-000000000003', 'agent@glgassets.com', 'Rahul Sharma (Agent)', 'agent', '5b927e1f486a4574972d5c07b76735515bf61b7f0e6b5278c66e2c38865e94b2', 'glg-default'),
    ('00000000-0000-0000-0000-000000000004', 'viewer@glgassets.com', 'Guest Stakeholder (Viewer)', 'viewer', '3c89d2d09e530b1b11b59cf9cf90538a08d2983584824361541484400e998782', 'glg-default')
ON CONFLICT (email) DO UPDATE SET 
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role;


-- 3. Customer Leads / End Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    platform VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Conversations Table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 5. Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    platform VARCHAR(50),
    message_type VARCHAR(50) DEFAULT 'text',
    intent VARCHAR(100),
    confidence DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 6. Property Projects Catalog Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    developer VARCHAR(255) DEFAULT 'GLG Assets',
    price VARCHAR(100),
    bedrooms INTEGER DEFAULT 2,
    amenities TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 7. Knowledge Documents Table (PDF OCR / RAG)
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    project VARCHAR(255),
    file_url TEXT NOT NULL,
    file_type VARCHAR(50),
    language VARCHAR(10) DEFAULT 'english',
    page_count INTEGER,
    word_count INTEGER,
    uploaded_by VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    indexed BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 8. Embeddings Table (pgvector 1536-dim for OpenAI text-embedding-3-small)
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Social Accounts Table
CREATE TABLE IF NOT EXISTS social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    account_name VARCHAR(255),
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(platform, account_id)
);

-- 10. Social Posts Table
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    account_id UUID REFERENCES social_accounts(id),
    content TEXT NOT NULL,
    media_urls TEXT[],
    hashtags TEXT[],
    status VARCHAR(50) DEFAULT 'scheduled',
    scheduled_for TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    engagement_likes INTEGER DEFAULT 0,
    engagement_comments INTEGER DEFAULT 0,
    engagement_shares INTEGER DEFAULT 0,
    engagement_impressions INTEGER DEFAULT 0,
    campaign_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 11. Comments & Social Interactions Table
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    comment_id VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(255),
    post_platform_id VARCHAR(255),
    commenter_id VARCHAR(255),
    commenter_name VARCHAR(255),
    comment_text TEXT NOT NULL,
    reply_text TEXT,
    intent VARCHAR(100),
    auto_replied BOOLEAN DEFAULT FALSE,
    replied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 12. Media Catalog Table
CREATE TABLE IF NOT EXISTS media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    media_id VARCHAR(255) UNIQUE NOT NULL,
    media_type VARCHAR(50) NOT NULL,
    file_url TEXT NOT NULL,
    file_size BIGINT,
    duration INTEGER,
    width INTEGER,
    height INTEGER,
    description TEXT,
    uploaded_by VARCHAR(255),
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    project VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 13. System Analytics Table
CREATE TABLE IF NOT EXISTS analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    platform VARCHAR(50),
    customer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    post_id UUID REFERENCES posts(id) ON DELETE SET NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. Marketing Ad Campaigns Table (Manager Dashboard KPIs)
CREATE TABLE IF NOT EXISTS ad_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id VARCHAR(255) UNIQUE NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    ad_budget_spent DECIMAL(12,2) DEFAULT 0.00,
    reach INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    qualified_leads INTEGER DEFAULT 0,
    cost_per_lead DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed Initial Ad Campaigns
INSERT INTO ad_campaigns (campaign_id, campaign_name, platform, ad_budget_spent, reach, impressions, messages_received, qualified_leads, cost_per_lead, status)
VALUES
    ('cmp-001', 'GLG Sky Tower - Gulshan 3BHK', 'meta_whatsapp', 45000.00, 65000, 120000, 520, 58, 775.00, 'active'),
    ('cmp-002', 'Palm Beach Villa - Coastal Luxury', 'instagram_reels', 38000.00, 52000, 98000, 410, 42, 904.00, 'active'),
    ('cmp-003', 'Dhanmondi Heights - Residential', 'google_search', 24000.00, 38000, 72000, 310, 28, 857.00, 'active'),
    ('cmp-004', 'Bandra Skyline - Investment Units', 'meta_lead_form', 18000.00, 30000, 50000, 180, 14, 1285.00, 'paused')
ON CONFLICT (campaign_id) DO UPDATE SET 
    ad_budget_spent = EXCLUDED.ad_budget_spent,
    qualified_leads = EXCLUDED.qualified_leads;


-- 15. Executive KPIs Telemetry Table (Admin Dashboard KPIs)
CREATE TABLE IF NOT EXISTS executive_kpis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gdv_pipeline_value DECIMAL(15,2) DEFAULT 148000000.00,
    ai_attributed_deal_value DECIMAL(15,2) DEFAULT 82000000.00,
    autonomous_resolution_rate DECIMAL(5,2) DEFAULT 94.20,
    human_escalation_rate DECIMAL(5,2) DEFAULT 5.80,
    hot_leads_count INTEGER DEFAULT 12,
    avg_qualification_speed_seconds INTEGER DEFAULT 45,
    site_tour_booking_rate DECIMAL(5,2) DEFAULT 32.40,
    vector_rag_precision DECIMAL(5,2) DEFAULT 98.40,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed Initial Executive Telemetry Snapshot
INSERT INTO executive_kpis (gdv_pipeline_value, ai_attributed_deal_value, autonomous_resolution_rate, human_escalation_rate, hot_leads_count, avg_qualification_speed_seconds, site_tour_booking_rate, vector_rag_precision)
VALUES (148000000.00, 82000000.00, 94.20, 5.80, 12, 45, 32.40, 98.40);


-- 16. Logs Table
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_type VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL CHECK (level IN ('debug', 'info', 'warning', 'error', 'critical')),
    platform VARCHAR(50),
    customer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    workflow_id VARCHAR(255),
    message TEXT,
    error_details TEXT,
    stack_trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================
-- INDEXES & VECTOR OPTIMIZATION
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_system_users_email ON system_users(email);
CREATE INDEX IF NOT EXISTS idx_system_users_role ON system_users(role);
CREATE INDEX IF NOT EXISTS idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversations_platform ON conversations(platform);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_type ON knowledge_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_project ON knowledge_documents(project);
CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_ad_campaigns_status ON ad_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);

-- Cosine Distance Vector Similarity Index for pgvector
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_cosine ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- SUPABASE RPC VECTOR SEARCH FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION match_knowledge_documents (
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5,
    filter_project text DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_index INT,
    chunk_text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        embeddings.id,
        embeddings.document_id,
        embeddings.chunk_index,
        embeddings.chunk_text,
        1 - (embeddings.embedding <=> query_embedding) AS similarity
    FROM embeddings
    JOIN knowledge_documents ON knowledge_documents.id = embeddings.document_id
    WHERE 1 - (embeddings.embedding <=> query_embedding) >= match_threshold
      AND (filter_project IS NULL OR knowledge_documents.project = filter_project)
    ORDER BY embeddings.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- SUPABASE ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================

ALTER TABLE system_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE executive_kpis ENABLE ROW LEVEL SECURITY;

-- Allow full service_role access for backend & automated API calls
CREATE POLICY "Service Role Full Access system_users" ON system_users FOR ALL USING (true);
CREATE POLICY "Service Role Full Access users" ON users FOR ALL USING (true);
CREATE POLICY "Service Role Full Access conversations" ON conversations FOR ALL USING (true);
CREATE POLICY "Service Role Full Access messages" ON messages FOR ALL USING (true);
CREATE POLICY "Public Read Access projects" ON projects FOR SELECT USING (true);
CREATE POLICY "Service Role Full Access projects" ON projects FOR ALL USING (true);
CREATE POLICY "Public Read Access knowledge_documents" ON knowledge_documents FOR SELECT USING (true);
CREATE POLICY "Service Role Full Access knowledge_documents" ON knowledge_documents FOR ALL USING (true);
CREATE POLICY "Service Role Full Access embeddings" ON embeddings FOR ALL USING (true);
CREATE POLICY "Service Role Full Access ad_campaigns" ON ad_campaigns FOR ALL USING (true);
CREATE POLICY "Service Role Full Access executive_kpis" ON executive_kpis FOR ALL USING (true);

-- Updated_at Trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_system_users_updated_at BEFORE UPDATE ON system_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ad_campaigns_updated_at BEFORE UPDATE ON ad_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
