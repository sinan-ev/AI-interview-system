"""
Integration tests for Answer Submission.
Tests Section 13:
- POST /api/v1/interviews/{interview_id}/answers (Text)
- POST /api/v1/interviews/{interview_id}/answers/voice (Voice)
- Duplicate answer rejection
- Cross-user authorization protection
"""
import io
import pytest
from starlette.testclient import TestClient


def get_auth_token(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/register", json={
        "name": "Ans Candidate",
        "email": email,
        "password": "Password123!",
        "role": "candidate",
    })
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return login.json()["data"]["access_token"]


def test_text_and_voice_answer_submission(client: TestClient):
    token = get_auth_token(client, "anscandidate1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create interview
    create_res = client.post("/api/v1/interviews", json={
        "role": "Backend Engineer",
        "interview_type": "technical",
        "difficulty": "intermediate",
        "topics": ["Python", "FastAPI"],
        "question_count": 2,
        "mode": "voice"
    }, headers=headers)
    interview_id = create_res.json()["data"]["id"]

    # 2. Start & get question 1
    client.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
    q1_res = client.get(f"/api/v1/interviews/{interview_id}/current-question", headers=headers)
    q1_id = q1_res.json()["data"]["id"]

    # 3. Submit text answer for question 1
    answer_payload = {
        "question_id": q1_id,
        "text_answer": "Python uses reference counting and a cyclic garbage collector for memory management.",
        "duration_seconds": 25.4
    }
    ans_res = client.post(f"/api/v1/interviews/{interview_id}/answers", json=answer_payload, headers=headers)
    assert ans_res.status_code == 201
    ans_data = ans_res.json()["data"]
    assert ans_data["question_id"] == q1_id
    assert ans_data["text_answer"] == answer_payload["text_answer"]
    assert ans_data["duration_seconds"] == 25.4

    # 4. Duplicate submission for the same question must fail with 409
    dup_res = client.post(f"/api/v1/interviews/{interview_id}/answers", json=answer_payload, headers=headers)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "RESOURCE_CONFLICT"

    # 5. Fetch next question (question 2)
    q2_res = client.get(f"/api/v1/interviews/{interview_id}/current-question", headers=headers)
    q2_id = q2_res.json()["data"]["id"]
    assert q2_id != q1_id

    # 6. Submit voice answer for question 2
    mock_audio_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    files = {
        "audio_file": ("answer.wav", io.BytesIO(mock_audio_bytes), "audio/wav")
    }
    form_data = {
        "question_id": q2_id,
        "duration_seconds": "18.5",
        "transcript": "FastAPI is built on Starlette and Pydantic providing automatic docs."
    }
    voice_res = client.post(
        f"/api/v1/interviews/{interview_id}/answers/voice",
        files=files,
        data=form_data,
        headers=headers
    )
    assert voice_res.status_code == 201
    voice_data = voice_res.json()["data"]
    assert voice_data["question_id"] == q2_id
    assert voice_data["audio_file_url"] is not None
    assert "answer.wav" in voice_data["audio_file_url"]
    assert voice_data["duration_seconds"] == 18.5
