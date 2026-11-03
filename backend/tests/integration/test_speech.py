"""
Integration tests for Speech & Audio endpoints.
Tests:
- POST /api/v1/speech/transcribe
- POST /api/v1/speech/analyze
"""
import io
import pytest
from starlette.testclient import TestClient


def get_token(client: TestClient) -> str:
    res = client.post("/api/v1/auth/register", json={
        "name": "Speech Tester",
        "email": "speech_test@example.com",
        "password": "Password123!",
        "role": "candidate",
    })
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login = client.post("/api/v1/auth/login", json={
        "email": "speech_test@example.com",
        "password": "Password123!",
    })
    return login.json()["data"]["access_token"]


def test_transcribe_audio_endpoint(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create dummy audio file (RIFF WAV format header)
    riff_wav = b"RIFF" + b"\x00" * 36 + b"data" + b"\x00" * 100
    files = {
        "audio_file": ("test.wav", io.BytesIO(riff_wav), "audio/wav")
    }

    res = client.post("/api/v1/speech/transcribe", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "transcript" in data
    assert "confidence" in data
    assert data["confidence"] > 0


def test_transcribe_invalid_audio_type(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "audio_file": ("test.exe", io.BytesIO(b"binary_payload"), "application/octet-stream")
    }

    res = client.post("/api/v1/speech/transcribe", files=files, headers=headers)
    assert res.status_code in (400, 422)


def test_analyze_speech_features_endpoint(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        "transcript": "I believe Python provides an intuitive syntax and great library ecosystem.",
        "duration_seconds": "30.0",
    }

    res = client.post("/api/v1/speech/analyze", data=data, headers=headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert "speech_features" in body
    assert "confidence_estimate" in body
    assert body["speech_features"]["word_count"] > 0
