"""GLG Assets Social AI OS — FastAPI Backend (port 8000).

MVP Specification Endpoints exposed directly under /api/:
- POST /api/chat
- POST /api/content
- POST /api/knowledge/upload
- POST /api/moderation
- GET  /api/projects
- GET  /api/project/{id}
- POST /api/search
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.dependencies import require_automation_secret as _auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[startup] {settings.app_name} — MVP routes registered at /api/")
    print(f"[startup] Docs available at http://localhost:8000/docs")
    yield
    print(f"[shutdown] {settings.app_name} — Shutting down gracefully")


limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Global Auth Dependency ----------

async def verify_automation_secret(
    x_automation_secret: str = Header(None, alias="X-Automation-Secret"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
):
    if not x_automation_secret:
        raise HTTPException(status_code=401, detail="Missing X-Automation-Secret header")
    if x_automation_secret != settings.automation_shared_secret:
        raise HTTPException(status_code=403, detail="Invalid automation secret")
    return {"tenant_id": x_tenant_id or settings.default_tenant_id}


# ---------- Health Probes ----------

@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}

@app.get("/health/ready")
async def health_ready():
    return {"status": "ok", "ready": True}

@app.get("/health/live")
async def health_live():
    return {"status": "ok", "live": True}


# ---------- Import Sub-Routers ----------

from app.api.v1.ai.endpoints import ai_chat, router as ai_router
from app.api.v1.content.endpoints import generate_content, router as content_router
from app.api.v1.knowledge.endpoints import knowledge_upload, router as knowledge_router
from app.api.v1.moderation.endpoints import check_moderation, router as moderation_router
from app.api.v1.projects.endpoints import list_projects, get_project, router as projects_router
from app.api.v1.search.endpoints import search_knowledge, router as search_router
from app.api.v1.automation import router as automation_router
from app.api.v1.social import router as social_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.escalations import router as escalations_router
from app.api.v1.media import router as media_router
from app.api.v1.notifications.endpoints import router as notifications_router
from app.api.v1.conversations.endpoints import router as conversations_router

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Form, Request

# ---------- MVP Explicit API Routes (/api/...) ----------

@app.post("/api/chat", tags=["MVP API"])
@limiter.limit("20/minute")
async def api_chat_handler(request: Request, body: dict = None, auth: dict = Depends(_auth)):
    """POST /api/chat — Main AI conversation pipeline."""
    from app.schemas.chat import ChatRequest
    if isinstance(body, dict):
        chat_req = ChatRequest(**body)
    else:
        chat_req = body
    return await ai_chat(chat_req, auth=auth)

@app.post("/api/content", tags=["MVP API"])
async def api_content_handler(body: dict, auth: dict = Depends(_auth)):
    """POST /api/content — Social media content generator (FB, IG, LinkedIn)."""
    return await generate_content(body, auth)

@app.post("/api/knowledge/upload", tags=["MVP API"])
async def api_knowledge_upload_handler(
    file: UploadFile = File(...),
    doc_id: str = Form(None),
    project: str = Form(None),
    location: str = Form(None),
    document_type: str = Form(None),
    auth: dict = Depends(_auth),
):
    """POST /api/knowledge/upload — Knowledge base OCR document indexer."""
    return await knowledge_upload(file, doc_id, project, location, document_type, auth)

@app.post("/api/moderation", tags=["MVP API"])
async def api_moderation_handler(body: dict, auth: dict = Depends(_auth)):
    """POST /api/moderation — AI content moderation safety check."""
    return await check_moderation(body, auth)

@app.get("/api/projects", tags=["MVP API"])
async def api_projects_handler(auth: dict = Depends(_auth)):
    """GET /api/projects — List real-estate projects."""
    return await list_projects(auth)

@app.get("/api/project/{project_id}", tags=["MVP API"])
async def api_project_detail_handler(project_id: str, auth: dict = Depends(_auth)):
    """GET /api/project/{id} — Get project details by ID or name."""
    return await get_project(project_id, auth)

@app.post("/api/search", tags=["MVP API"])
@limiter.limit("20/minute")
async def api_search_handler(request: Request, body: dict, auth: dict = Depends(_auth)):
    """POST /api/search — Hybrid RAG property & knowledge search."""
    return await search_knowledge(body, auth)


# ---------- Mount v1 Routers for Backward Compatibility ----------

from app.api.v1.ws import ws_router

app.include_router(ai_router,           prefix="/api/v1/ai",           tags=["ai"])
app.include_router(notifications_router,prefix="/api/v1/notifications",tags=["notifications"])
app.include_router(conversations_router,prefix="/api/v1/conversations",  tags=["conversations"])
app.include_router(automation_router,   prefix="/api/v1/automation",   tags=["automation"])
app.include_router(content_router,      prefix="/api/v1/content",      tags=["content"])
app.include_router(social_router,       prefix="/api/v1/social",       tags=["social"])
app.include_router(moderation_router,   prefix="/api/v1/moderation",   tags=["moderation"])
app.include_router(knowledge_router,    prefix="/api/v1/knowledge",    tags=["knowledge"])
app.include_router(analytics_router,    prefix="/api/v1/analytics",    tags=["analytics"])
app.include_router(escalations_router,  prefix="/api/v1/escalations",  tags=["escalations"])
app.include_router(media_router,        prefix="/api/v1/media",        tags=["media"])
app.include_router(projects_router,     prefix="/api/v1",              tags=["projects"])
app.include_router(search_router,       prefix="/api/v1",              tags=["search"])
app.include_router(ws_router,           prefix="/api/v1",              tags=["websockets"])