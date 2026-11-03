"""
Integration tests for Interview CRUD operations.
Tests Section 6, 7, and 31 endpoints:
- POST /api/v1/interviews
- GET /api/v1/interviews
- GET /api/v1/interviews/{id}
- POST /api/v1/interviews/{id}/start
- POST /api/v1/interviews/{id}/complete
- Authorization enforcement between users
"""
import pytest
from starlette.testclient import TestClient


def get_auth_token_for_user(client: TestClient, email: str, name: str) -> str:
    """Helper to register/login user and return Bearer access token."""
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": "Password123!",
        "role": "candidate",
    })
    if res.status_code == 201:
        return res.json()["data"]["access_token"]

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
    })
    return login_res.json()["data"]["access_token"]


def test_interview_lifecycle_flow(client: TestClient):
    token = get_auth_token_for_user(client, "interviewee1@example.com", "Interviewee One")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create interview
    create_payload = {
        "role": "Data Scientist",
        "interview_type": "technical",
        "difficulty": "intermediate",
        "topics": ["Python", "Pandas", "Machine Learning", "Statistics"],
        "question_count": 5,
        "mode": "voice"
    }
    res_create = client.post("/api/v1/interviews", json=create_payload, headers=headers)
    assert res_create.status_code == 201
    created_data = res_create.json()["data"]
    interview_id = created_data["id"]

    assert created_data["role"] == "Data Scientist"
    assert created_data["status"] == "created"
    assert created_data["total_questions"] == 5
    assert created_data["current_question"] == 0
    assert created_data["started_at"] is None
    assert created_data["completed_at"] is None

    # 2. Get interview details
    res_get = client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
    assert res_get.status_code == 200
    detail_data = res_get.json()["data"]
    assert detail_data["id"] == interview_id
    assert "questions" in detail_data
    assert len(detail_data["questions"]) == 0  # Not pre-generated immediately!

    # 3. List interviews for user
    res_list = client.get("/api/v1/interviews", headers=headers)
    assert res_list.status_code == 200
    list_data = res_list.json()["data"]
    assert list_data["total"] >= 1
    assert any(item["id"] == interview_id for item in list_data["items"])

    # 4. Start interview
    res_start = client.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
    assert res_start.status_code == 200
    start_data = res_start.json()["data"]
    assert start_data["status"] == "in_progress"
    assert start_data["started_at"] is not None

    # 5. Complete interview
    res_complete = client.post(f"/api/v1/interviews/{interview_id}/complete", headers=headers)
    assert res_complete.status_code == 200
    complete_data = res_complete.json()["data"]
    assert complete_data["status"] == "completed"
    assert complete_data["completed_at"] is not None


def test_interview_validation_rules(client: TestClient):
    token = get_auth_token_for_user(client, "interviewee2@example.com", "Interviewee Two")
    headers = {"Authorization": f"Bearer {token}"}

    # Empty topics should be rejected
    invalid_topics = {
        "role": "Data Scientist",
        "interview_type": "technical",
        "difficulty": "intermediate",
        "topics": [],
        "question_count": 5,
        "mode": "voice"
    }
    res = client.post("/api/v1/interviews", json=invalid_topics, headers=headers)
    assert res.status_code == 422

    # Negative or 0 question count should be rejected
    invalid_count = {
        "role": "Backend Engineer",
        "interview_type": "technical",
        "difficulty": "intermediate",
        "topics": ["Python"],
        "question_count": 0,
        "mode": "text"
    }
    res_count = client.post("/api/v1/interviews", json=invalid_count, headers=headers)
    assert res_count.status_code == 422


def test_cross_user_interview_authorization(client: TestClient):
    token_user_a = get_auth_token_for_user(client, "usera@example.com", "User A")
    token_user_b = get_auth_token_for_user(client, "userb@example.com", "User B")

    # User A creates interview
    res = client.post("/api/v1/interviews", json={
        "role": "QA Engineer",
        "interview_type": "technical",
        "difficulty": "beginner",
        "topics": ["Testing", "Selenium"],
        "question_count": 3,
        "mode": "text"
    }, headers={"Authorization": f"Bearer {token_user_a}"})
    interview_id = res.json()["data"]["id"]

    # User B tries to view User A's interview -> 403 Forbidden
    res_b_view = client.get(f"/api/v1/interviews/{interview_id}", headers={"Authorization": f"Bearer {token_user_b}"})
    assert res_b_view.status_code == 403
    assert res_b_view.json()["error"]["code"] == "FORBIDDEN"

    # User B tries to start User A's interview -> 403 Forbidden
    res_b_start = client.post(f"/api/v1/interviews/{interview_id}/start", headers={"Authorization": f"Bearer {token_user_b}"})
    assert res_b_start.status_code == 403
