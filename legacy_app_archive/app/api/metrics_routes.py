from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse


def build_metrics_router() -> APIRouter:
    router = APIRouter(tags=["observability"])

    @router.get("/metrics", response_class=PlainTextResponse)
    def metrics(request: Request) -> str:
        return request.app.state.metrics.prometheus()

    return router