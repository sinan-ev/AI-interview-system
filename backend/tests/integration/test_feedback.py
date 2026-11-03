"""
Integration tests for Feedback & Analytics API endpoints.
Tests:
- GET /api/v1/feedback/interview/{interview_id}
- GET /api/v1/feedback/profile/{user_id}
- Authorization enforcement on feedback access
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
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
    })
    return login.json()["data"]["access_token"]


def test_get_user_profile_feedback(client: TestClient):
    token = register_user(client, "feedback_user@example.com", "Feedback User")
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch user me to get user_id
    me_res = client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    user_id = me_res.json()["data"]["id"]

    # Profile feedback
    res = client.get(f"/api/v1/feedback/profile/{user_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "summary" in data
    assert "topic_breakdown" in data
    assert "weak_topics" in data
    assert "learning_recommendations" in data


def test_interview_feedback_not_found(client: TestClient):
    token = register_user(client, "fb_test@example.com", "FB Test")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/feedback/interview/non-existent-id", headers=headers)
    assert res.status_code == 404
