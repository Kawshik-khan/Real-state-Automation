# GLG Assets — Supabase & Supabase pgvector Integration Guide

**Date:** 2026-07-29  
**Scope:** Connecting Managed Supabase PostgreSQL, Supabase pgvector, and Supabase Storage

---

## 1. Executive Summary

This guide outlines how to connect **Supabase Managed PostgreSQL**, **Supabase pgvector**, and **Supabase Storage** to the GLG Assets Real Estate Automation platform. 

Because Supabase is native PostgreSQL with `pgvector` pre-installed, **zero backend code changes or database schema refactoring** are required. You only need to update your `DATABASE_URL` in `backend/.env` to point to your Supabase project URL.

---

## 2. Supabase Environment Setup

### 2.1 Get Supabase Connection Credentials
From your Supabase Project Dashboard (`https://supabase.com/dashboard/project/[your-project-ref]/settings/database`):

1. **Database Host**: `aws-0-[region].pooler.supabase.com`
2. **Database Port**: `6543` (Transaction Pooler) or `5432` (Direct Connection)
3. **Database Name**: `postgres`
4. **User / Password**: `postgres.[your-project-ref]` / `[your-password]`

### 2.2 Add Credentials to `backend/.env`
```env
# --- SUPABASE DATABASE & PGVECTOR ---
DATABASE_URL=postgresql+asyncpg://postgres.[your-project-ref]:[your-password]@aws-0-[region].pooler.supabase.com:6543/postgres

# --- SUPABASE STORAGE & CLIENT SDK (OPTIONAL) ---
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
```

---

## 3. Supabase SQL Initializer Script

Run this SQL snippet in your **Supabase SQL Editor**:

```sql
-- 1. Enable pgvector for 1536-dim OpenAI Embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Enable UUID generator
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 3. Verify pgvector extension is active
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## 4. Supabase Storage Buckets Setup

Create 3 storage buckets in **Supabase Dashboard $\rightarrow$ Storage $\rightarrow$ Create Bucket**:

1. **`brochures`** (Public Access): For property PDF brochures sent to customers via WhatsApp/FB (`send_brochure`).
2. **`floorplans`** (Public Access): For unit layout images sent to customers (`send_images`).
3. **`ocr-documents`** (Private Access): For raw uploaded files before text chunking.

---

## 5. RAG pgvector Cosine Search in Supabase

Our `backend/app/rag/vector_store.py` performs vector similarity queries on Supabase `knowledge_chunks`:

```sql
SELECT 
    id, 
    content, 
    metadata, 
    project,
    1 - (embedding <=> CAST(:emb AS vector)) AS similarity
FROM knowledge_chunks
WHERE 1 - (embedding <=> CAST(:emb AS vector)) > 0.70
ORDER BY embedding <=> CAST(:emb AS vector)
LIMIT 5;
```

---

## 6. Migration Steps

1. Update `DATABASE_URL` in `backend/.env` with your Supabase Connection Pooler URL.
2. Initialize tables on Supabase:
   ```bash
   python -c "import asyncio; from backend.app.persistence.database import init_db; asyncio.run(init_db())"
   ```
3. Run test suite to verify 100% endpoint pass rate:
   ```bash
   pytest backend/tests/test_mvp_endpoints.py
   ```
