from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.contexts.real_estate import (
    Booking,
    ConflictError,
    Handoff,
    InventoryUnit,
    Lead,
    MediaLink,
    PaymentPlanRequest,
    Project,
    TenantScopeError,
    WorkflowService,
)


def _tenant(header: UUID | None, body: UUID) -> UUID:
    if header is not None and header != body:
        raise HTTPException(status_code=403, detail="TENANT_SCOPE_VIOLATION")
    return body


def build_workflow_router(service: WorkflowService) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["real-estate"])

    @router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
    def create_project(project: Project, tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id")) -> Project:
        _tenant(tenant_header, project.tenant_id)
        return service.add_project(project)

    @router.get("/projects", response_model=list[Project])
    def search_projects(tenant_id: UUID = Query(...), location: str | None = None, tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id")) -> list[Project]:
        return service.search_projects(_tenant(tenant_header, tenant_id), location)

    @router.post("/inventory", response_model=InventoryUnit, status_code=status.HTTP_201_CREATED)
    def create_inventory(unit: InventoryUnit, tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id")) -> InventoryUnit:
        _tenant(tenant_header, unit.tenant_id)
        try:
            return service.add_inventory(unit)
        except TenantScopeError as exc:
            raise HTTPException(status_code=403, detail="TENANT_SCOPE_VIOLATION") from exc

    @router.get("/inventory", response_model=list[InventoryUnit])
    def search_inventory(
        tenant_id: UUID = Query(...),
        project_id: UUID | None = None,
        bedrooms: int | None = Query(default=None, ge=0, le=20),
        max_price: Decimal | None = Query(default=None, gt=0),
        tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id"),
    ) -> list[InventoryUnit]:
        return service.search_inventory(_tenant(tenant_header, tenant_id), project_id, bedrooms, max_price)

    @router.post("/leads", response_model=Lead, status_code=status.HTTP_201_CREATED)
    def create_lead(
        lead: Lead,
        tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> Lead:
        _tenant(tenant_header, lead.tenant_id)
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="IDEMPOTENCY_KEY_REQUIRED")
        return service.create_lead(lead, idempotency_key)

    @router.post("/bookings", response_model=Booking, status_code=status.HTTP_201_CREATED)
    def create_booking(
        booking: Booking,
        tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> Booking:
        _tenant(tenant_header, booking.tenant_id)
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="IDEMPOTENCY_KEY_REQUIRED")
        try:
            return service.book(booking, idempotency_key)
        except ConflictError as exc:
            raise HTTPException(status_code=409, detail="BOOKING_SLOT_UNAVAILABLE") from exc

    @router.post("/payments/plans", response_model=object)
    def calculate_payment_plan(request: PaymentPlanRequest):
        return service.calculate_plan(request)

    @router.post("/media", response_model=MediaLink, status_code=status.HTTP_201_CREATED)
    def register_media(media: MediaLink, tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id")) -> MediaLink:
        _tenant(tenant_header, media.tenant_id)
        service.store.media[media.media_id] = media
        return media

    @router.post("/handoffs", response_model=Handoff, status_code=status.HTTP_201_CREATED)
    def request_handoff(handoff: Handoff, tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id")) -> Handoff:
        _tenant(tenant_header, handoff.tenant_id)
        return service.request_handoff(handoff)

    return router