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

import asyncio
import logging
import time
import warnings
from contextlib import asynccontextmanager

# Suppress known LangGraph/LangChain internal serializer deprecation warnings before imports
warnings.filterwarnings("ignore", message=r".*allowed_objects.*")

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ai.endpoints import ai_chat
from app.api.v1.ai.endpoints import router as ai_router
from app.api.v1.ai_control_plane import router as ai_control_plane_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth.endpoints import router as auth_router
from app.api.v1.automation import router as automation_router
from app.api.v1.calendar.endpoints import router as calendar_router
from app.api.v1.content.endpoints import generate_content
from app.api.v1.content.endpoints import router as content_router
from app.api.v1.conversations.endpoints import router as conversations_router
from app.api.v1.developer.endpoints import router as developer_router
from app.api.v1.email.endpoints import router as email_router
from app.api.v1.escalations import router as escalations_router
from app.api.v1.knowledge.endpoints import knowledge_upload
from app.api.v1.knowledge.endpoints import router as knowledge_router
from app.api.v1.media import router as media_router
from app.api.v1.memory.endpoints import router as memory_router
from app.api.v1.moderation.endpoints import check_moderation
from app.api.v1.moderation.endpoints import router as moderation_router
from app.api.v1.notifications.endpoints import router as notifications_router
from app.api.v1.projects.endpoints import create_project, get_project, list_projects
from app.api.v1.projects.endpoints import router as projects_router
from app.api.v1.search.endpoints import router as search_router
from app.api.v1.search.endpoints import search_knowledge
from app.api.v1.social import router as social_router
from app.api.v1.ws import ws_router
from app.config import settings
from app.core.rate_limiter import custom_rate_limit_exceeded_handler, limiter
from app.database import get_session
from app.dependencies import require_automation_secret as _auth
from app.dependencies import require_roles
from app.models.user import UserRole
from app.services.log_streamer import log_streamer, setup_live_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"[startup] {settings.app_name} — Initializing database connection...")
    from app.database import check_connection, init_db
    from app.services.supabase_db import supabase_db
    try:
        is_connected = await check_connection()
        if is_connected:
            await init_db()
            logger.info("[startup] Supabase/PostgreSQL schema initialized successfully (pgvector & tables verified).")
        else:
            supa_health = supabase_db.check_health()
            if supa_health.get("configured"):
                logger.info(f"[startup] Supabase Cloud configured ({settings.supabase_url}) — REST Status: {supa_health.get('status')}")
            else:
                logger.warning("[startup] Database offline or unreachable; continuing with resilient fallback.")
    except Exception as db_err:
        logger.warning(f"[startup] Database initialization note: {db_err}")

    logger.info(f"[startup] {settings.app_name} — MVP routes registered at /api/")
    active_port = os.getenv("PORT", "8000")
    logger.info(f"[startup] Docs available at http://0.0.0.0:{active_port}/docs (or /docs behind reverse proxy)")

    # Only start email poller if Gmail credentials are configured
    poller_task = None
    from app.services.email_poller import email_poller_worker, stop_email_poller
    if settings.gmail_user_email and settings.gmail_app_password:
        poller_task = asyncio.create_task(email_poller_worker(interval_seconds=15))
        logger.info("[startup] Gmail IMAP poller started.")
    else:
        logger.info("[startup] Gmail credentials not configured — email poller disabled.")

    yield

    stop_email_poller()
    if poller_task and not poller_task.done():
        poller_task.cancel()
    logger.info(f"[shutdown] {settings.app_name} — Shutting down gracefully")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_live_logging()


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Enforce OWASP Security Headers and Dynamic Content Security Policy (CSP)."""
    response = await call_next(request)

    # 1. Anti-Clickjacking: Disallow embedding in external frames
    response.headers["X-Frame-Options"] = "DENY"

    # 2. Prevent MIME-type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # 3. Cross-Site Scripting Filter for legacy browsers
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # 4. Strict Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # 5. Restrict sensitive hardware/device permissions
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"

    # 6. HTTP Strict Transport Security (HSTS) on HTTPS connections
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    if is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # 7. Content Security Policy (CSP)
    path = request.url.path
    if path in ("/docs", "/redoc", "/openapi.json"):
        # Swagger UI and ReDoc require jsdelivr CDN assets and inline script/style
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "connect-src 'self' http: https: ws: wss:;"
        )
    else:
        # Standard API and Web application routes
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' ws: wss: http: https:; "
            "img-src 'self' data: https: blob:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline';"
        )

    return response


@app.middleware("http")
async def live_telemetry_logging_middleware(request: Request, call_next):
    """Real-time HTTP Request/Response telemetry logging middleware."""
    start_time = time.time()
    path = request.url.path
    method = request.method
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # Don't log spammy continuous SSE streams or favicon
        if not path.endswith("/stream") and not path.endswith("/favicon.ico"):
            level = "WARN" if response.status_code >= 400 else "INFO"
            module = "FastAPI"
            if "/developer" in path:
                module = "DeveloperAPI"
            elif "/auth" in path:
                module = "AuthEngine"
            elif "/chat" in path or "/conversations" in path:
                module = "SupervisorGraph"
            elif "/knowledge" in path:
                module = "RAGVectorDB"
            elif "/automation" in path or "/social" in path:
                module = "n8nWebhook"

            log_streamer.record_log(
                level=level,
                module=module,
                message=f"{method} {path} -> HTTP {response.status_code} [{latency_ms}ms]",
                path=path,
                method=method,
                status_code=response.status_code,
                latency_ms=latency_ms,
                client_ip=client_ip
            )

            # Dynamically update n8n workflow telemetry counter on live traffic
            try:
                from app.services.n8n_monitoring import N8nMonitoringService
                N8nMonitoringService.record_live_trigger(path, latency_ms)
            except Exception:
                pass
        return response
    except Exception as exc:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        log_streamer.record_log(
            level="ERROR",
            module="FastAPI",
            message=f"{method} {path} unhandled exception: {str(exc)}",
            path=path,
            method=method,
            status_code=500,
            latency_ms=latency_ms,
            client_ip=client_ip
        )
        raise exc


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


# ---------- Health Probes (Supports GET and HEAD for Cloud Health Checks) ----------

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"status": "ok", "service": settings.app_name, "docs": "/docs"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok", "service": settings.app_name}

@app.api_route("/health/ready", methods=["GET", "HEAD"])
async def health_ready():
    return {"status": "ok", "ready": True}

@app.api_route("/health/live", methods=["GET", "HEAD"])
async def health_live():
    return {"status": "ok", "live": True}




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
    return await ai_chat(request=request, body=chat_req, auth=auth)

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
    auth: dict = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
):
    """POST /api/knowledge/upload — Knowledge base OCR document indexer."""
    return await knowledge_upload(file, doc_id, project, location, document_type, auth)

@app.post("/api/moderation", tags=["MVP API"])
async def api_moderation_handler(body: dict, auth: dict = Depends(_auth)):
    """POST /api/moderation — AI content moderation safety check."""
    return await check_moderation(body, auth)

@app.get("/api/projects", tags=["MVP API"])
async def api_projects_handler(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_session),
    auth: dict = Depends(_auth),
):
    """GET /api/projects — List real-estate projects."""
    return await list_projects(request=request, response=response, db=db, auth=auth)

@app.post("/api/projects", tags=["MVP API"])
async def api_project_create_handler(body: dict, db: AsyncSession = Depends(get_session), auth: dict = Depends(_auth)):
    """POST /api/projects — Create a new property development."""
    return await create_project(body=body, db=db, auth=auth)

@app.get("/api/project/{project_id}", tags=["MVP API"])
async def api_project_detail_handler(project_id: str, db: AsyncSession = Depends(get_session), auth: dict = Depends(_auth)):
    """GET /api/project/{id} — Get project details by ID or name."""
    return await get_project(project_id=project_id, db=db, auth=auth)

@app.post("/api/search", tags=["MVP API"])
@limiter.limit("20/minute")
async def api_search_handler(request: Request, body: dict, auth: dict = Depends(_auth)):
    """POST /api/search — Hybrid RAG property & knowledge search."""
    return await search_knowledge(body, auth)


# ---------- Mount v1 Routers for Backward Compatibility ----------

app.include_router(auth_router,          prefix="/api/v1",              tags=["auth"])
app.include_router(developer_router,     prefix="/api/v1/developer",    tags=["developer"])
app.include_router(email_router,         prefix="/api/v1/email",        tags=["email"])
app.include_router(ai_router,           prefix="/api/v1/ai",           tags=["ai"])
app.include_router(ai_control_plane_router, prefix="/api/v1/ai-control", tags=["ai_control_plane"])
app.include_router(ai_control_plane_router, prefix="/api/ai", tags=["ai_control_plane_api"])
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
app.include_router(memory_router,       prefix="/api/v1/memory",       tags=["memory"])
app.include_router(projects_router,     prefix="/api/v1",              tags=["projects"])
app.include_router(search_router,       prefix="/api/v1",              tags=["search"])
app.include_router(calendar_router,     prefix="/api/v1/calendar",     tags=["calendar"])
app.include_router(calendar_router,     prefix="/api/calendar",        tags=["calendar"])
app.include_router(ws_router,           prefix="/api/v1",              tags=["websockets"])