from fastapi import APIRouter, Request


def build_admin_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

    @router.get("/summary")
    def summary(request: Request) -> dict[str, int]:
        workflow = request.app.state.workflow_service.store
        return {"projects": len(workflow.projects), "inventory": len(workflow.inventory), "leads": len(workflow.leads), "bookings": len(workflow.bookings), "handoffs": len(workflow.handoffs)}

    return router