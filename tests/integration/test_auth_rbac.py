"""[INTEGRATION TEST] User authentication, JWT tokens, and RBAC authorization permissions.
"""

import pytest
from fastapi.testclient import TestClient
from app.core.constants import UserRole


def test_user_registration_and_duplicate_handling(client: TestClient):
    """Verify successful user registration and rejection of duplicate emails."""
    reg_payload = {
        "email": "newresearcher@smartgrid.com",
        "password": "SecurePassword123!",
        "role": UserRole.RESEARCHER.value,
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    assert res.json()["email"] == "newresearcher@smartgrid.com"
    assert res.json()["role"] == UserRole.RESEARCHER.value

    # Attempt duplicate
    res_dup = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"]


def test_user_login_success_and_invalid_credentials(client: TestClient):
    """Verify login with correct vs incorrect credentials."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"email": "loginuser@smartgrid.com", "password": "Password123!", "role": "VIEWER"},
    )

    # Valid login
    login_res = client.post(
        "/api/v1/auth/login/json",
        json={"email": "loginuser@smartgrid.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    assert login_res.json()["token_type"] == "bearer"

    # Invalid login
    bad_res = client.post(
        "/api/v1/auth/login/json",
        json={"email": "loginuser@smartgrid.com", "password": "WrongPassword!"},
    )
    assert bad_res.status_code == 401


def test_rbac_admin_vs_viewer_permissions(client: TestClient, admin_auth_headers, viewer_auth_headers):
    """Verify ADMIN role can access /api/v1/users while VIEWER is denied (403 Forbidden)."""
    # Admin access -> 200 OK
    admin_res = client.get("/api/v1/users", headers=admin_auth_headers)
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)

    # Viewer access -> 403 Forbidden
    viewer_res = client.get("/api/v1/users", headers=viewer_auth_headers)
    assert viewer_res.status_code == 403
    assert "Operation not permitted" in viewer_res.json()["detail"]


def test_users_me_endpoint(client: TestClient, viewer_auth_headers):
    """Verify /api/v1/users/me returns authenticated user's profile."""
    res = client.get("/api/v1/users/me", headers=viewer_auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "testviewer@smartgrid.com"
