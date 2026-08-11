from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_inventory_search_is_tenant_scoped_and_filtered() -> None:
    tenant_id = uuid4()
    other_tenant = uuid4()
    project = client.post("/api/v1/projects", json={"tenant_id": str(tenant_id), "name": "Downtown", "location": "Downtown"})
    assert project.status_code == 201
    project_id = project.json()["project_id"]
    created = client.post(
        "/api/v1/inventory",
        json={"tenant_id": str(tenant_id), "project_id": project_id, "bedrooms": 2, "price": "250000"},
    )
    assert created.status_code == 201
    hidden = client.get(f"/api/v1/inventory?tenant_id={other_tenant}")
    assert hidden.status_code == 200
    assert hidden.json() == []
    filtered = client.get(f"/api/v1/inventory?tenant_id={tenant_id}&bedrooms=2&max_price=300000")
    assert len(filtered.json()) == 1


def test_lead_retry_returns_same_resource_and_requires_key() -> None:
    tenant_id = uuid4()
    payload = {"tenant_id": str(tenant_id), "name": "Customer", "contact": "customer@example.com"}
    missing = client.post("/api/v1/leads", json=payload)
    assert missing.status_code == 400
    first = client.post("/api/v1/leads", json=payload, headers={"Idempotency-Key": "lead-1"})
    second = client.post("/api/v1/leads", json=payload, headers={"Idempotency-Key": "lead-1"})
    assert first.status_code == second.status_code == 201
    assert first.json()["lead_id"] == second.json()["lead_id"]


def test_booking_conflict_is_not_confirmed_twice() -> None:
    tenant_id = uuid4()
    booking = {
        "tenant_id": str(tenant_id),
        "customer_id": str(uuid4()),
        "project_id": str(uuid4()),
        "slot": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    }
    first = client.post("/api/v1/bookings", json=booking, headers={"Idempotency-Key": "booking-1"})
    assert first.status_code == 201
    conflict = client.post("/api/v1/bookings", json=booking, headers={"Idempotency-Key": "booking-2"})
    assert conflict.status_code == 409
    retry = client.post("/api/v1/bookings", json=booking, headers={"Idempotency-Key": "booking-1"})
    assert retry.status_code == 201
    assert retry.json()["booking_id"] == first.json()["booking_id"]


def test_payment_plan_is_deterministic() -> None:
    response = client.post("/api/v1/payments/plans", json={"price": "100000", "down_payment_percent": "20", "installments": 4})
    assert response.status_code == 200
    assert response.json()["down_payment"] == "20000.00"
    assert response.json()["installment_amount"] == "20000.00"