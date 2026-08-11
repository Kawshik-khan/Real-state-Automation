from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def now() -> datetime:
    return datetime.now(timezone.utc)


class Project(BaseModel):
    project_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2_000)
    created_at: datetime = Field(default_factory=now)
    version: int = 1


class InventoryUnit(BaseModel):
    unit_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    project_id: UUID
    bedrooms: int = Field(ge=0, le=20)
    price: Decimal = Field(gt=0)
    status: str = Field(default="AVAILABLE", pattern="^(AVAILABLE|RESERVED|SOLD)$")
    updated_at: datetime = Field(default_factory=now)
    version: int = 1


class Lead(BaseModel):
    lead_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    customer_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    contact: str = Field(min_length=1, max_length=200)
    source: str = Field(default="conversation", max_length=80)
    status: str = Field(default="NEW", pattern="^(NEW|QUALIFIED|CONVERTED|LOST)$")
    created_at: datetime = Field(default_factory=now)
    version: int = 1


class Booking(BaseModel):
    booking_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    customer_id: UUID
    project_id: UUID
    slot: datetime
    status: str = Field(default="CONFIRMED", pattern="^(CONFIRMED|CANCELLED)$")
    created_at: datetime = Field(default_factory=now)


class PaymentPlanRequest(BaseModel):
    price: Decimal = Field(gt=0)
    down_payment_percent: Decimal = Field(ge=0, le=100)
    installments: int = Field(ge=1, le=360)


class PaymentPlan(BaseModel):
    price: Decimal
    down_payment: Decimal
    financed_amount: Decimal
    installment_amount: Decimal
    installments: int


class MediaLink(BaseModel):
    media_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    project_id: UUID
    url: str = Field(min_length=1, max_length=2_000)
    media_type: str = Field(min_length=1, max_length=40)


class Handoff(BaseModel):
    handoff_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    conversation_id: UUID
    reason: str = Field(min_length=1, max_length=500)
    status: str = "REQUESTED"
    created_at: datetime = Field(default_factory=now)


@dataclass
class WorkflowStore:
    projects: dict[UUID, Project] = field(default_factory=dict)
    inventory: dict[UUID, InventoryUnit] = field(default_factory=dict)
    leads: dict[UUID, Lead] = field(default_factory=dict)
    bookings: dict[UUID, Booking] = field(default_factory=dict)
    media: dict[UUID, MediaLink] = field(default_factory=dict)
    handoffs: dict[UUID, Handoff] = field(default_factory=dict)
    idempotency: dict[tuple[UUID, str], object] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)


class TenantScopeError(Exception):
    pass


class ConflictError(Exception):
    pass


class WorkflowService:
    def __init__(self, store: WorkflowStore, events, automation=None) -> None:
        self.store = store
        self.events = events
        self.automation = automation

    def _check(self, tenant_id: UUID, value) -> None:
        if value.tenant_id != tenant_id:
            raise TenantScopeError

    def add_project(self, project: Project) -> Project:
        with self.store.lock:
            self.store.projects[project.project_id] = project
        self.events.publish("ProjectCreated", project.project_id, {"tenantId": str(project.tenant_id), "name": project.name})
        return project

    def search_projects(self, tenant_id: UUID, location: str | None = None) -> list[Project]:
        return [p for p in self.store.projects.values() if p.tenant_id == tenant_id and (not location or location.lower() in p.location.lower())]

    def add_inventory(self, unit: InventoryUnit) -> InventoryUnit:
        self._check(unit.tenant_id, self.store.projects.get(unit.project_id) or unit)
        self.store.inventory[unit.unit_id] = unit
        return unit

    def search_inventory(self, tenant_id: UUID, project_id: UUID | None, bedrooms: int | None, max_price: Decimal | None) -> list[InventoryUnit]:
        return [u for u in self.store.inventory.values() if u.tenant_id == tenant_id and u.status == "AVAILABLE" and (project_id is None or u.project_id == project_id) and (bedrooms is None or u.bedrooms == bedrooms) and (max_price is None or u.price <= max_price)]

    def create_lead(self, lead: Lead, idempotency_key: str | None) -> Lead:
        with self.store.lock:
            if idempotency_key:
                existing = self.store.idempotency.get((lead.tenant_id, idempotency_key))
                if existing:
                    if not isinstance(existing, Lead):
                        raise ConflictError
                    return existing
            self.store.leads[lead.lead_id] = lead
            if idempotency_key:
                self.store.idempotency[(lead.tenant_id, idempotency_key)] = lead
        self.events.publish("LeadCreated", lead.lead_id, {"tenantId": str(lead.tenant_id), "contact": lead.contact})
        
        # Publish to n8n automation
        if self.automation:
            import asyncio
            asyncio.create_task(self.automation.publish_lead_created(
                lead_id=lead.lead_id,
                customer_id=lead.customer_id or lead.lead_id,
                source=lead.source,
                initial_intent="property_inquiry",
                tenant_id=lead.tenant_id
            ))
        
        return lead

    def book(self, booking: Booking, idempotency_key: str | None) -> Booking:
        with self.store.lock:
            if idempotency_key:
                existing = self.store.idempotency.get((booking.tenant_id, idempotency_key))
                if isinstance(existing, Booking):
                    return existing
            if any(b.tenant_id == booking.tenant_id and b.slot == booking.slot and b.status == "CONFIRMED" for b in self.store.bookings.values()):
                raise ConflictError
            self.store.bookings[booking.booking_id] = booking
            if idempotency_key:
                self.store.idempotency[(booking.tenant_id, idempotency_key)] = booking
        self.events.publish("AppointmentBooked", booking.booking_id, {"tenantId": str(booking.tenant_id), "slot": booking.slot.isoformat()})
        
        # Publish to n8n automation
        if self.automation:
            import asyncio
            asyncio.create_task(self.automation.publish_booking_created(
                booking_id=booking.booking_id,
                customer_id=booking.customer_id,
                property_id=booking.property_id,
                date=booking.slot.date().isoformat(),
                time=booking.slot.time().isoformat(),
                tenant_id=booking.tenant_id
            ))
        
        return booking

    def calculate_plan(self, request: PaymentPlanRequest) -> PaymentPlan:
        down = (request.price * request.down_payment_percent / Decimal("100")).quantize(Decimal("0.01"))
        financed = request.price - down
        installment = (financed / request.installments).quantize(Decimal("0.01"))
        return PaymentPlan(price=request.price, down_payment=down, financed_amount=financed, installment_amount=installment, installments=request.installments)

    def request_handoff(self, handoff: Handoff) -> Handoff:
        self.store.handoffs[handoff.handoff_id] = handoff
        self.events.publish("HumanTransferRequested", handoff.handoff_id, {"tenantId": str(handoff.tenant_id), "conversationId": str(handoff.conversation_id)})
        return handoff