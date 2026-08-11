from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_channel_webhook_is_authenticated_and_deduplicated() -> None:
    tenant_id = uuid4()
    payload = {"message_id": "provider-1", "sender": "customer-1", "text": "Hello"}
    missing_signature = client.post(f"/api/v1/webhooks/whatsapp", json=payload, headers={"X-Tenant-Id": str(tenant_id)})
    assert missing_signature.status_code == 401
    first = client.post(f"/api/v1/webhooks/whatsapp", json=payload, headers={"X-Tenant-Id": str(tenant_id), "X-Webhook-Signature": "valid"})
    duplicate = client.post(f"/api/v1/webhooks/whatsapp", json=payload, headers={"X-Tenant-Id": str(tenant_id), "X-Webhook-Signature": "valid"})
    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert duplicate.json()["detail"] == "DUPLICATE_WEBHOOK"