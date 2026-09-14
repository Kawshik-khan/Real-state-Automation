"""Tests for Phase 1 Security: Identity-aware rate limiting & OWASP security headers."""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.core.rate_limiter import get_rate_limit_identity
from app.core.security import create_access_token
from app.config import settings
from app.main import app

client = TestClient(app)


def test_security_headers_present():
    """Verify that OWASP security headers are present on API responses."""
    response = client.get("/api/v1/projects")
    # Even if 200 or 401, security headers must be applied by middleware
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers
    assert "Content-Security-Policy" in response.headers


def test_docs_csp_allows_cdn_jsdelivr():
    """Verify that Swagger UI endpoint /docs receives CSP permitting jsdelivr."""
    response = client.get("/docs")
    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy", "")
    assert "cdn.jsdelivr.net" in csp


def test_get_rate_limit_identity_bearer_token():
    """Verify identity extraction from Bearer JWT."""
    token = create_access_token({"sub": "usr-test-123", "role": "agent"})
    
    # Mock Request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [(b"authorization", f"Bearer {token}".encode())],
        "client": ("192.168.1.50", 12345),
    }
    req = Request(scope)
    identity = get_rate_limit_identity(req)
    assert identity == "user:usr-test-123:agent"


def test_get_rate_limit_identity_automation_secret():
    """Verify identity extraction from X-Automation-Secret."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": [(b"x-automation-secret", settings.automation_shared_secret.encode())],
        "client": ("192.168.1.50", 12345),
    }
    req = Request(scope)
    identity = get_rate_limit_identity(req)
    assert identity == "system:automation"


def test_get_rate_limit_identity_client_ip_and_forwarded():
    """Verify identity extraction from client IP and X-Forwarded-For."""
    # Direct IP
    scope1 = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "client": ("203.0.113.195", 12345),
    }
    req1 = Request(scope1)
    assert get_rate_limit_identity(req1) == "ip:203.0.113.195"

    # Forwarded IP behind proxy
    scope2 = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [(b"x-forwarded-for", b"198.51.100.42, 10.0.0.1")],
        "client": ("10.0.0.1", 12345),
    }
    req2 = Request(scope2)
    assert get_rate_limit_identity(req2) == "ip:198.51.100.42"
