from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.adapters.in_memory import InMemoryConversationRepository, InMemoryEventPublisher
from app.adapters.runtime import InMemoryIdempotencyStore, InMemoryRateLimiter
from app.adapters.sqlalchemy import SqlAlchemyConversationRepository, SqlAlchemyEventPublisher
from app.api.context import RequestContext, current_request_context
from app.api.errors import validation_error_handler
from app.api.routes import build_router
from app.api.workflow_routes import build_workflow_router
from app.application.ai import AIOrchestrator
from app.application.services import ConversationService
from app.config import settings
from app.contexts.real_estate import WorkflowService, WorkflowStore
from app.application.knowledge import KnowledgeStore
from app.application.memory import MemoryStore
from app.application.tools import ToolGateway
from app.channels import ChannelAdapter
from app.api.channel_routes import build_channel_router
from app.api.admin_routes import build_admin_router
from app.api.metrics_routes import build_metrics_router
from app.api.n8n_routes import build_n8n_router
from app.observability import Metrics
from app.adapters.n8n import N8nConfig
from app.application.automation import automation_service
from app.persistence.database import build_engine, build_session_factory
from app.persistence.models import Base


def create_app() -> FastAPI:
    if settings.enable_persistence:
        engine = build_engine()
        Base.metadata.create_all(engine)
        sessions = build_session_factory()
        repository = SqlAlchemyConversationRepository(sessions)
        events = SqlAlchemyEventPublisher(sessions)
    else:
        repository = InMemoryConversationRepository()
        events = InMemoryEventPublisher()
    conversation_service = ConversationService(repository, events)
    orchestrator = AIOrchestrator(events)
    idempotency = InMemoryIdempotencyStore()
    limiter = InMemoryRateLimiter(settings.rate_limit_per_minute)
    workflow_service = WorkflowService(WorkflowStore(), events, automation_service)
    knowledge = KnowledgeStore()
    memory = MemoryStore()
    tools = ToolGateway()
    channels = ChannelAdapter()
    metrics = Metrics()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend foundation aligned with the SAS, AAD, and shared architecture contracts.",
    )
    application.state.repository = repository
    application.state.events = events
    application.state.settings = settings
    application.state.workflow_service = workflow_service
    application.state.knowledge = knowledge
    application.state.memory = memory
    application.state.tools = tools
    application.state.channels = channels
    application.state.metrics = metrics
    application.include_router(build_router(conversation_service, orchestrator, idempotency))
    application.include_router(build_workflow_router(workflow_service))
    application.include_router(build_channel_router(channels))
    application.include_router(build_admin_router())
    application.include_router(build_metrics_router())
    
    # Add n8n integration router if enabled
    if settings.enable_n8n:
        n8n_config = N8nConfig(
            webhook_url=settings.n8n_webhook_url,
            api_url=settings.n8n_api_url,
            api_key=settings.n8n_api_key,
            webhook_secret=settings.n8n_webhook_secret,
            timeout=settings.n8n_timeout
        )
        application.include_router(build_n8n_router(n8n_config))

    @application.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid4())
        trace_id = request.headers.get("trace_id") or str(uuid4())
        tenant_id = request.headers.get("X-Tenant-Id")
        identity = request.client.host if request.client else "unknown"
        if not request.url.path.startswith("/health/") and not limiter.allow(identity):
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMITED", "message": "Too many requests"}},
            )
        token = current_request_context.set(RequestContext(correlation_id, trace_id, tenant_id))
        try:
            started = __import__("time").perf_counter()
            response = await call_next(request)
            metrics.observe("http_requests", __import__("time").perf_counter() - started)
            response.headers["X-Correlation-Id"] = correlation_id
            response.headers["trace_id"] = trace_id
            return response
        finally:
            current_request_context.reset(token)

    @application.get("/health/live", tags=["health"])
    def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready", tags=["health"])
    def readiness() -> dict[str, str]:
        repository_name = "sqlalchemy" if settings.enable_persistence else "in-memory"
        return {"status": "ready", "repository": repository_name, "environment": settings.environment}

    application.add_exception_handler(RequestValidationError, validation_error_handler)

    @application.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
        )

    return application


app = create_app()
