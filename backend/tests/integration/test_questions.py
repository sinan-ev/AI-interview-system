"""
Integration and Unit Tests for Question Generation & Agents.
Tests Section 8, 9, and 31:
- GET /api/v1/interviews/{id}/current-question
- GET /api/v1/questions/{id}`
- Dynamic question generation on-demand
- Idempotency when question is pending answer
- Duplicate question prevention
"""
import pytest
from starlette.testclient import TestClient

from app.ai.agents.question_generator import QuestionGeneratorAgent
from app.ai.llm.provider import MockLLMProvider
from app.schemas.question import GeneratedQuestion


def get_auth_token(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/register", json={
        "name": "Q Candidate",
        "email": email,
        "password": "Password123!",
        "role": "candidate",
    })
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return login.json()["data"]["access_token"]


def test_question_generation_lifecycle(client: TestClient):
    token = get_auth_token(client, "qcandidate1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create interview session
    create_res = client.post("/api/v1/interviews", json={
        "role": "Machine Learning Engineer",
        "interview_type": "technical",
        "difficulty": "intermediate",
        "topics": ["Machine Learning", "Python"],
        "question_count": 3,
        "mode": "text"
    }, headers=headers)
    assert create_res.status_code == 201
    interview_id = create_res.json()["data"]["id"]

    # 2. Fetch current question (should trigger first question generation)
    curr_res = client.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
    assert curr_res.status_code == 200

    q_res = client.get(f"/api/v1/interviews/{interview_id}/current-question", headers=headers)
    assert q_res.status_code == 200
    q_data = q_res.json()["data"]
    question_id = q_data["id"]

    assert q_data["interview_id"] == interview_id
    assert q_data["question_number"] == 1
    assert len(q_data["question_text"]) > 10
    # Client representation must not expose answers or rubrics
    assert "evaluation_rubric" not in q_data

    # 3. Requesting current-question again before answering must return the same question (idempotent)
    q_res_repeat = client.get(f"/api/v1/interviews/{interview_id}/current-question", headers=headers)
    assert q_res_repeat.status_code == 200
    assert q_res_repeat.json()["data"]["id"] == question_id

    # 4. Fetch question by ID
    get_q = client.get(f"/api/v1/questions/{question_id}", headers=headers)
    assert get_q.status_code == 200
    assert get_q.json()["data"]["id"] == question_id
    assert get_q.json()["data"]["question_number"] == 1


@pytest.mark.asyncio
async def test_question_generator_agent_unit():
    mock_llm = MockLLMProvider()
    agent = QuestionGeneratorAgent(mock_llm)

    generated = await agent.generate_question(
        role="Senior Backend Architect",
        topic="Python",
        difficulty="advanced",
        interview_type="technical",
        previous_questions=[]
    )

    assert isinstance(generated, GeneratedQuestion)
    assert generated.topic == "Python"
    assert len(generated.expected_concepts) >= 1
    assert "accuracy_criteria" in generated.evaluation_rubric
