"""Unit tests for n8n Workflow & Node Health Monitoring service & endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_n8n_health_telemetry_endpoint():
    """Test GET /api/v1/automation/n8n/health returns complete telemetry metrics."""
    response = client.get("/api/v1/automation/n8n/health")
    assert response.status_code == 200
    data = response.json()

    assert "overall_status" in data
    assert "metrics" in data
    assert "workflows" in data
    assert "node_issues" in data

    metrics = data["metrics"]
    assert metrics["total_workflows"] >= 6
    assert metrics["active_workflows"] >= 1
    assert metrics["total_nodes"] > 0
    assert metrics["avg_system_latency_ms"] >= 0

    # Verify workflow structures
    workflows = data["workflows"]
    tg_wf = next((wf for wf in workflows if wf["id"] == "wf-tg-001"), None)
    assert tg_wf is not None
    assert tg_wf["name"] == "Telegram AI Assistant & Lead Qualifier"
    assert len(tg_wf["nodes"]) == 4


def test_n8n_toggle_workflow():
    """Test POST /api/v1/automation/n8n/workflows/{id}/toggle toggles workflow status."""
    wf_id = "wf-tg-001"

    # Disable workflow
    resp = client.post(f"/api/v1/automation/n8n/workflows/{wf_id}/toggle", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False

    # Verify status updated in health query
    health_resp = client.get("/api/v1/automation/n8n/health")
    tg_wf = next(wf for wf in health_resp.json()["workflows"] if wf["id"] == wf_id)
    assert tg_wf["active"] is False

    # Re-enable workflow
    resp2 = client.post(f"/api/v1/automation/n8n/workflows/{wf_id}/toggle", json={"active": True})
    assert resp2.status_code == 200
    assert resp2.json()["active"] is True


def test_n8n_test_workflow_ping():
    """Test POST /api/v1/automation/n8n/workflows/{id}/test executes node latency ping."""
    wf_id = "wf-em-002"

    resp = client.post(f"/api/v1/automation/n8n/workflows/{wf_id}/test")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert data["workflow_id"] == wf_id
    assert data["execution_time_ms"] > 0
    assert data["nodes_tested"] == 4
    assert len(data["node_breakdown"]) == 4
