"""Unit tests for authentication and Role-Based Access Control (RBAC)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_success_admin():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@glgassets.com", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@glgassets.com"
    assert data["user"]["role"] == "admin"


def test_login_success_manager():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@glgassets.com", "password": "manager123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "manager"


def test_login_success_agent():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@glgassets.com", "password": "agent123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "agent"


def test_login_success_developer():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "developer@glgassets.com", "password": "dev123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "developer"
    assert data["user"]["email"] == "developer@glgassets.com"


def test_login_invalid_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@glgassets.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_me_with_jwt():
    # Login first
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@glgassets.com", "password": "admin123"},
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@glgassets.com"
    assert me_res.json()["role"] == "admin"


def test_list_users_rbac_restriction():
    # Agent token
    agent_login = client.post(
        "/api/v1/auth/login",
        json={"email": "agent@glgassets.com", "password": "agent123"},
    )
    agent_token = agent_login.json()["access_token"]

    # Agent should be forbidden from calling list_users (Admin & Manager only)
    headers = {"Authorization": f"Bearer {agent_token}"}
    res = client.get("/api/v1/auth/users", headers=headers)
    assert res.status_code == 403
    assert "Access forbidden" in res.json()["detail"]

    # Admin should be allowed
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@glgassets.com", "password": "admin123"},
    )
    admin_token = admin_login.json()["access_token"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    res_admin = client.get("/api/v1/auth/users", headers=headers_admin)
    assert res_admin.status_code == 200
    assert len(res_admin.json()) >= 4
