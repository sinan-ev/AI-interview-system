"""
Integration tests for Authentication & Authorization.
Tests Section 5 & Section 31 endpoints:
- Registration
- Login & Credential Verification
- Profile (/me)
- Token Rotation on Refresh
- Token Revocation on Logout
- RBAC and Invalid/Expired Token Handling
"""
import pytest
from datetime import timedelta
from starlette.testclient import TestClient

from app.core.security import create_access_token


def test_register_and_login_flow(client: TestClient):
    # 1. Register candidate
    reg_payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com",
        "password": "Password123!",
        "role": "candidate",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    tokens = data["data"]
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["user"]["email"] == "sarah.connor@example.com"
    assert "password_hash" not in tokens["user"]

    # 2. Duplicate registration should return 409 Conflict
    res_dup = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_dup.status_code == 409
    dup_data = res_dup.json()
    assert dup_data["success"] is False
    assert dup_data["error"]["code"] == "RESOURCE_CONFLICT"

    # 3. Login with correct credentials
    login_payload = {
        "email": "sarah.connor@example.com",
        "password": "Password123!",
    }
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert login_data["success"] is True
    access_token = login_data["data"]["access_token"]
    refresh_token = login_data["data"]["refresh_token"]

    # 4. Login with invalid password returns 401
    bad_login = {
        "email": "sarah.connor@example.com",
        "password": "WrongPassword999!",
    }
    res_bad = client.post("/api/v1/auth/login", json=bad_login)
    assert res_bad.status_code == 401
    assert res_bad.json()["error"]["code"] == "UNAUTHORIZED"

    # 5. Access /me endpoint with Bearer token
    headers = {"Authorization": f"Bearer {access_token}"}
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == "sarah.connor@example.com"

    # 6. Access /users/me endpoint
    res_user_me = client.get("/api/v1/users/me", headers=headers)
    assert res_user_me.status_code == 200
    assert res_user_me.json()["data"]["name"] == "Sarah Connor"


def test_token_rotation_and_revocation(client: TestClient):
    # Register separate user
    reg = client.post("/api/v1/auth/register", json={
        "name": "Kyle Reese",
        "email": "kyle@example.com",
        "password": "SecurePassword456!",
        "role": "candidate",
    })
    tokens = reg.json()["data"]
    initial_refresh = tokens["refresh_token"]

    # Rotate refresh token
    rotate_res = client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert rotate_res.status_code == 200
    rotated_data = rotate_res.json()["data"]
    new_refresh = rotated_data["refresh_token"]
    new_access = rotated_data["access_token"]
    assert new_refresh != initial_refresh

    # Using the old refresh token MUST fail now (token rotation)
    stale_res = client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert stale_res.status_code == 401

    # Verify the new access token works
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert res_me.status_code == 200

    # Logout to revoke the active refresh token
    logout_res = client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["revoked"] is True

    # Attempting to refresh with the logged out token MUST fail
    logged_out_res = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert logged_out_res.status_code == 401


def test_unauthorized_and_expired_tokens(client: TestClient):
    # Request without token
    res_no_auth = client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401
    assert res_no_auth.json()["error"]["code"] == "UNAUTHORIZED"

    # Request with invalid token string
    res_bad_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.string"})
    assert res_bad_token.status_code == 401

    # Request with expired token
    expired_token = create_access_token(
        subject="test-user-id",
        expires_delta=timedelta(seconds=-10)  # Expired in past
    )
    res_expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["error"]["message"].lower()
