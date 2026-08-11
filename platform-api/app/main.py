"""GLG Assets — Platform API (port 8001).

Serves workstreams 34-45 of the Social AI OS.
Platform orchestration: conversations, events, social posting, campaigns, content distribution.
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="GLG Assets Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_platform_secret(
    x_automation_secret: str = Header(None, alias="X-Automation-Secret"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
):
    if not x_automation_secret:
        raise HTTPException(status_code=401, detail="Missing X-Automation-Secret header")
    if x_automation_secret != settings.automation_shared_secret:
        raise HTTPException(status_code=403, detail="Invalid automation secret")
    return {"tenant_id": x_tenant_id or settings.default_tenant_id}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "GLG Assets Platform API"}


# ----- Routers -----

from app.api.v1.conversations import router as conversations_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.platform import router as platform_router

app.include_router(conversations_router, prefix="/api/v1", tags=["conversations"])
app.include_router(analytics_router,     prefix="/api/v1", tags=["analytics"])
app.include_router(platform_router,      prefix="/api/v1", tags=["platform"])


@app.on_event("startup")
async def startup():
    print(f"[startup] Platform API — {len(app.routes)} routes registered")
    print(f"[startup] docs at http://localhost:8001/docs")
