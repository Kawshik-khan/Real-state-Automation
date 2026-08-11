# 🏢 GLG Assets — AI-Powered Real Estate Customer Engagement Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://reactjs.org/)
[![n8n](https://img.shields.io/badge/n8n-Workflow-FF6D5A?style=flat&logo=n8n)](https://n8n.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker)](https://www.docker.com/)

An enterprise-grade, multi-channel AI customer engagement and lead automation platform built for real estate agencies. Combines FastAPI AI microservices, n8n workflow automation, vector search (RAG), multi-channel messaging (Telegram, WhatsApp, Meta), and a modern React dashboard.

---

## 🌟 Key Capabilities & Features

- **🤖 AI-Driven Lead Qualification & RAG**: Context-aware AI assistant powered by LLMs (OpenAI / Grok / LangGraph) for property FAQs, lead scoring, and inquiry routing.
- **⚡ n8n Workflow Automation**: Pre-built automated flows for lead capture, CRM syncing, social media engagement, and instant notifications.
- **💬 Multi-Channel Messaging**: Seamless integration across Telegram, WhatsApp Business, Facebook Messenger, and Instagram.
- **📊 Real-Time Analytics & Dashboard**: Modern React + Vite frontend for managing conversations, properties, leads, and analytics.
- **🐘 Vector Search & Database**: PostgreSQL + `pgvector` for semantic search on property details, FAQs, and governance guides.
- **🐳 Production Ready**: Multi-stage Docker containers, Nginx SPA static serving, Gunicorn multi-worker backend, and container healthchecks.

---

## 📁 Repository Structure

```text
├── backend/              # FastAPI AI Backend & Workstream Core (Port 8000)
│   ├── app/              # Domain logic, AI runtime, API endpoints, RAG
│   ├── tests/            # Pytest test suite
│   ├── Dockerfile        # Production multi-stage Docker image
│   └── .env.example      # Environment variables template
├── platform-api/         # Platform API Service (Port 8001)
│   ├── app/              # Analytics, conversation & tenant management
│   └── Dockerfile        # Production multi-stage Docker image
├── frontend/             # React + Vite Frontend Dashboard (Port 80)
│   ├── src/              # Dashboard UI components & API integration
│   ├── nginx.conf        # Production Nginx SPA & caching configuration
│   └── Dockerfile        # Production Nginx multi-stage build
├── automation/           # n8n Workflow Automation & Integration Scripts
│   ├── *.json            # Exported n8n workflow definitions
│   └── glg-assets/       # Property asset data & generator scripts
├── migrations/           # Alembic database migration scripts
├── docs/                 # Architecture, workflow guides, and audit documents
├── docker-compose.yml    # Full-stack production Docker Compose orchestration
└── render.yaml           # One-click Render cloud deployment blueprint
```

---

## 🚀 Quick Start (Docker Compose)

The easiest way to run the entire stack (Frontend, Backend, Platform API, n8n, and PostgreSQL) is with **Docker Compose**:

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd "Realstate Automation"

# 2. Copy environment variable templates
cp backend/.env.example backend/.env
cp automation/.env.example automation/.env
cp platform-api/.env.example platform-api/.env

# 3. Launch all services
docker compose up --build -d

# 4. Check service status
docker compose ps
```

### 🌐 Service Endpoints

| Service | Local URL | Description |
| :--- | :--- | :--- |
| **Frontend Dashboard** | `http://localhost:80` | React Web Dashboard |
| **FastAPI Backend** | `http://localhost:8000` | AI & Automation API (`/docs` for Swagger UI) |
| **Platform API** | `http://localhost:8001` | Platform Management API (`/docs`) |
| **n8n Automation** | `http://localhost:5678` | n8n Workflow Editor |
| **PostgreSQL Database** | `localhost:5432` | PostgreSQL + pgvector |

---

## 🛠️ Local Manual Setup (Development Mode)

If you prefer to run services individually without Docker:

### 1. Backend Service
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Application
```bash
cd frontend
npm install
npm run dev
```

### 3. Database Migrations
```bash
alembic upgrade head
```

---

## 🧪 Testing

Run backend unit and integration tests with `pytest`:

```bash
cd backend
pytest tests/ -v
```

---

## ☁️ Deployment

- **Docker Compose / VPS**: Pre-configured with container healthchecks, non-root system users, and security headers.
- **Render / Cloud**: Import `render.yaml` into Render for automated cloud deployment of the backend and frontend static site.

---

## 🛡️ License

This project is proprietary and confidential — reserved for **GLG Assets**.
