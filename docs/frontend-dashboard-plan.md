# GLG Assets — Frontend Dashboard Detailed Architecture & Implementation Plan

**Date:** 2026-07-29  
**Scope:** Modern React + Vite Glassmorphism Frontend Dashboard with Complete Analytics, Executive Dashboard Cards, Business Informatics, Content Engine & Advanced Knowledge Base Manager

---

## 1. Executive Summary

The **Frontend Dashboard** serves as the central command center for real estate administrators, sales leads, marketing executives, and C-suite leadership. It provides real-time visibility into customer communications across WhatsApp, Facebook Messenger, Instagram DM, and Website Chat, alongside full control over the AI Knowledge Base, Social Content Generation Engine, Property Inventory, and Business Informatics Analytics.

---

## 2. Technology Stack & Design System

### 2.1 Technology Stack
- **Core Framework**: React 18 + Vite (High-speed HMR, clean component structure).
- **Styling**: Custom Vanilla CSS with CSS Variables & Utility Tokens (Glassmorphism design system).
- **Typography**: Google Fonts **Outfit** (Headings) + **Inter** (Body text).
- **Icons**: Lucide Icons / Feather Icons (`lucide-react`).
- **Data Visualization**: Recharts / SVG Canvas Gauges for high-performance interactive charts.
- **HTTP & State**: Native `fetch` / `axios` API service layer connected to FastAPI (`http://localhost:8000`).

### 2.2 Aesthetic Design Tokens
- **Theme**: Premium Sleek Dark Mode with Glassmorphism.
- **Background**: `#0B0F19` with subtle deep radial glows (`radial-gradient(circle at 50% 0%, #1E1B4B 0%, #0B0F19 70%)`).
- **Glassmorphic Surface**: 
  ```css
  background: rgba(17, 24, 39, 0.7);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  border-radius: 16px;
  ```
- **Accent Gradients**:
  - Emerald Success: `linear-gradient(135deg, #10B981, #059669)`
  - Indigo/Violet Primary: `linear-gradient(135deg, #6366F1, #8B5CF6)`
  - Amber Warning / Escalation: `linear-gradient(135deg, #F59E0B, #D97706)`
  - Rose High Intent Alert: `linear-gradient(135deg, #F43F5E, #E11D48)`
  - Cyan Business Informatics: `linear-gradient(135deg, #06B6D4, #0891B2)`
  - Purple Content Engine: `linear-gradient(135deg, #A855F7, #9333EA)`
  - Blue Knowledge Hub: `linear-gradient(135deg, #3B82F6, #1D4ED8)`
- **Animations**: Micro-transitions (`transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1)`), glowing hover borders, real-time pulse indicators.

---

## 3. Directory & Folder Structure

```
frontend/
  ├── src/
  │   ├── assets/              (Logos, placeholder images, icons)
  │   ├── components/
  │   │   ├── layout/          (Sidebar, Header, StatusBadge, MetricCard)
  │   │   ├── conversations/   (ChatList, ChatWindow, MessageBubble, ChannelTag)
  │   │   ├── knowledge/       (PDFDropzone, DocumentList, ChunkEditorModal, ConflictDetectorAlert, SyntheticFaqModal, AccessControlSelector, RagSearchSimulator)
  │   │   ├── content/         (GeneratorForm, FBPreview, IGPreview, LinkedInPreview, ReelStoryboardModal, PersonaPresetPicker, ComplianceGuardBadge, ContentCalendarGrid)
  │   │   ├── properties/      (ProjectCard, UnitTable, MediaMapper)
  │   │   └── analytics/       (CoreMetricCards, DailyVolumeChart, IntentBreakdownChart, PipelineCard, HotLeadCard, SentimentRadarCard, CostSavingsCard, ExecutivePdfCard, BusinessInformaticsGrid)
  │   ├── pages/
  │   │   ├── DashboardHome.jsx
  │   │   ├── ConversationsPage.jsx
  │   │   ├── KnowledgePage.jsx
  │   │   ├── ContentGeneratorPage.jsx
  │   │   ├── PropertiesPage.jsx
  │   │   └── AnalyticsPage.jsx
  │   ├── services/
  │   │   ├── api.js           (FastAPI & n8n API client)
  │   │   └── websocket.js     (Live message streaming)
  │   ├── styles/
  │   │   ├── index.css        (Global resets, color tokens, typography)
  │   │   └── glassmorphism.css(Glass cards, animations, badges)
  │   ├── App.jsx              (Routing & tab state)
  │   └── main.jsx
  ├── index.html
  ├── package.json
  └── vite.config.js
```

---

## 4. Detailed Module Specs & Features

### 4.1 Navigation & Global Header
- **Top Header**:
  - Real-time Connection Probes: `FastAPI Backend (8000)` | `n8n MCP (5678)` | `PostgreSQL DB`.
  - System Telemetry Gauge: RAG Latency (*45ms*), LLM Speed (*1.2s*).
- **Sidebar**:
  - Navigation links: `Dashboard Overview`, `Live Conversations`, `Knowledge Base`, `Content Generator`, `Property Inventory`, `Analytics & Executive Dashboard`.

---

### 4.2 Module 1: Live Conversations & Human Agent Takeover (`/conversations`)
- **Conversation Stream**: Real-time listing across WhatsApp 🟢, Facebook Messenger 🔵, Instagram 🟣, Website Chat 🌐.
- **Interactive Chat Window**:
  - Message bubble rendering with intent tags (`property_search`, `faq`, `booking`).
  - **Human Agent Takeover Button**: Instant toggle allowing human sales agents to take over conversations and pause AI auto-replies.
  - Quick action toolbar: `Send Brochure PDF`, `Send Project Images`, `Book Site Visit`.

---

### 4.3 Module 2: Knowledge Base & PDF OCR Manager (`/knowledge`) 📚

The **Knowledge Base & PDF OCR Manager** manages document indexing, chunk editing, conflict detection, and RAG testing:

- **Drag-and-Drop File Upload**: PDF, TXT, MD, JSON, CSV brochure uploader (`POST /api/knowledge/upload`).
- **Indexed Document Table**: Displays file size, chunk count, and OCR status badge (`Processing`, `Completed`, `Failed`).

#### ✏️ 1. Interactive Chunk Editor & Real-Estate Synonym Expansion
- Side drawer allowing knowledge managers to view split 500-word text chunks, edit boundaries, and add regional real-estate synonyms (*e.g., "3 BHK" = "3 Bedroom", "Katha" = "Measurement unit", "Handover" = "Possession date"*).

#### ⚠️ 2. Knowledge Conflict & Outdated Price Detection Engine
- Automatically scans newly uploaded documents against existing knowledge chunks to flag conflicting prices, superseded policies, or mismatched handover dates (*e.g., "Alert: Document A lists price as ৳90L, while Document B lists ৳95L for Gulshan Heights"*).

#### ❓ 3. 1-Click Synthetic FAQ Generator
- Analyzes uploaded PDF brochures and generates 25+ anticipated buyer FAQs with answers (*e.g., "Down payment schedule", "Utility connection fee"*), populating the `FAQAgent` bank automatically.

#### 🔒 4. Document Access Control & Privacy Sensitivity Tags
- Assigns access control tags (`Public Customer`, `Internal Sales Only`, `Legal Agreement`, `VIP Pricing`), ensuring internal notes are never exposed to public chat inquiries.

#### 🧪 5. Live RAG Search Simulator & Retrieval Tester
- Embedded workbench allowing admins to enter test queries (*"What documents are required for home loan approval?"*) and inspect top-3 retrieved vector chunks, similarity scores (0.00–1.00), and search latency in real-time.

---

### 4.4 Module 3: Social Content Generator & Approval Engine (`/content`) 🚀

The **Social Content Generator & Approval Engine** provides full AI post generation, multi-platform preview, compliance checking, and content calendar queueing:

- **AI Visual Post & Reel Storyboard Generator**: Visual carousel slide concepts & Instagram Reel script storyboards.
- **Dual-Language Localizer (English & Bengali / বাংলা)**: 1-click toggle for professional Bengali and English copy.
- **Property Catalog Auto-Sync (1-Click Property Post)**: Auto-populates property specs directly into post prompts.
- **AI Buyer Persona Switcher**: Toggle between *Ultra-Luxury VIP*, *First-Time Family Home*, *High-Yield Investor*, and *Pre-Launch Urgency*.
- **Real Estate Compliance & Legal Disclaimer Auto-Guard**: Scans posts for legal RERA compliance.
- **Multi-Channel Mockup Preview & Drag-and-Drop Content Calendar**: Native previews for FB, IG, LinkedIn, and WhatsApp Broadcast with calendar scheduling.

---

### 4.5 Module 4: Property Inventory & Media Catalog (`/properties`)
- **Project Cards Grid**: Catalog for developments (*GLG Gulshan Heights*, *GLG Grand Residency*, *GLG Banani Crest*).
- **Media Attachment Tool**: Map project brochure PDFs and floor plan image URLs to `media` database table for AI delivery.

---

### 4.6 Module 5: Analytics & Executive Dashboard (`/analytics`) ⭐

The **Analytics & Executive Dashboard** incorporates operational telemetry, executive intelligence, and strategic business informatics:

#### 📊 1. Core Operational Metric Cards & Charts:
- **AI Resolution % Metric Card**: Displays percentage of customer queries fully resolved by AI (`94.2% AI Handled`).
- **Escalation Rate % Metric Card**: Displays human handoff rate (`5.8% Escalated`), primary escalation reasons, and average resolution time.
- **Daily Message Volume by Channel Bar Chart**: Bar chart displaying message volume by channel (WhatsApp, Facebook, Instagram, Website).
- **Customer Intent Breakdown Pie Chart**: Donut/pie chart showing inquiry types (`property_search` 65%, `faq` 20%, `booking` 10%, `other` 5%).

#### 🃏 2. Executive Intelligence Cards:
- **Active Deal Pipeline & Conversion Velocity Card**: Real-time pipeline value (`৳14,80,00,000` / $1.24M USD) + AI Speed Advantage (`1.2s AI Response` vs `18m Human Response`).
- **Hot Lead Propensity Leaderboard Card**: Ranks active buyer conversations by AI Purchase Intent Score (0–100) with 1-click `Initiate Sales Call` / `Take Over Chat` buttons.
- **Customer Sentiment & Location Demand Radar Card**: Sentiment Heatmap (*High Buying Intent 48%*, *Price Sensitive 32%*) + neighborhood demand radar (*Gulshan 42%*, *Banani 28%*, *Dhanmondi 18%*).
- **Operational ROI & Labor Cost Savings Card**: Monthly labor cost saved counter (`৳5,20,000` / $4,400 USD saved) + 24/7 after-hours conversion rate (6 PM – 9 AM).
- **1-Click Executive PDF Briefing & Audio Digest Card**: `Download Executive PDF Briefing` button + `Play Daily Voice Briefing` text-to-speech audio player.

#### 💡 3. Strategic Business Informatics Features:
1. **Amenity & Feature Demand Matrix (Product Development Informatics)**: Ranks most requested property amenities (*Rooftop Garden 38%*, *Infinity Pool 29%*, *Lake View 24%*).
2. **Price Sensitivity & Budget Drop-Off Curve (Pricing Strategy Informatics)**: Visualizes conversion and drop-off rates across price brackets.
3. **Marketing Channel ROI & Lead Quality Attribution (Marketing Informatics)**: Correlates incoming lead channels with actual Buying Intent Scores.
4. **Sales Cycle Funnel Velocity & Bottleneck Diagnostic (Sales Informatics)**: Measures stage-by-stage conversion duration.
5. **Competitor Mentions & Buyer Objection Radar (Market Intelligence Informatics)**: Aggregates top buyer objections and competitor mentions extracted by AI.
6. **Inventory Turnover & Slow-Moving Unit Heatmap (Asset Management Informatics)**: Highlights unsold units at risk of stagnation.

---

## 5. Phased Implementation Timeline

| Phase | Milestone | Deliverables |
| :---: | :--- | :--- |
| **Phase 1** | Project Setup & Design System | Scaffolding Vite + React app, CSS resets, glassmorphic dark mode variables, typography setup. |
| **Phase 2** | Layout & Global Navigation | Responsive sidebar, top header, real-time status probes. |
| **Phase 3** | Core, Knowledge & Executive Build | Building Conversations, Advanced Knowledge Base, Content Generator, Properties, and Analytics & Executive Dashboard. |
| **Phase 4** | API Integration & Testing | Connecting frontend to FastAPI endpoints (`/api/chat`, `/api/content`, `/api/knowledge/upload`, `/api/projects`). |
| **Phase 5** | Polish & User Acceptance | Micro-animations, responsive layout checks, and live demo verification. |
