"""
Integration tests for User Profile operations.
Tests:
- GET /api/v1/users/me
- PUT /api/v1/users/me
- Unauthorized access rejection
"""
import pytest
from starlette.testclient import TestClient


def register_user(client: TestClient, email: str, name: str) -> str:
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": "Password123!",
        "role": "candidate",
    })
    assert res.status_code == 201
    return res.json()["data"]["access_token"]


def test_get_current_user_profile(client: TestClient):
    token = register_user(client, "profile_test@example.com", "Profile User")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["email"] == "profile_test@example.com"
    assert data["name"] == "Profile User"
    assert data["role"] == "candidate"
    assert data["is_active"] is True


def test_get_profile_unauthorized(client: TestClient):
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401


def test_update_user_profile(client: TestClient):
    token = register_user(client, "update_test@example.com", "Old Name")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {"name": "New Upgraded Name"}
    res = client.put("/api/v1/users/me", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "New Upgraded Name"
    assert data["email"] == "update_test@example.com"
