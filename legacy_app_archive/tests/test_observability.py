from fastapi.testclient import TestClient

from app.main import app
from app.observability import Metrics, redact_pii


client = TestClient(app)


def test_metrics_and_redaction() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text
    assert redact_pii("email a@example.com phone 123456789") == "email [email] phone [number]"


def test_metrics_counter_is_thread_safe_api() -> None:
    metrics = Metrics()
    metrics.observe("requests", 0.1)
    assert metrics.prometheus() == "requests_total 1\nrequests_last_seconds 0.100000\n"