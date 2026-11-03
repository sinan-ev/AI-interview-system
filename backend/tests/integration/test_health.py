"""
Integration tests for Health and Readiness probes.
"""
from starlette.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "request_id" in data
    assert data["data"]["status"] == "healthy"
    assert "version" in data["data"]
    # Check headers
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-Ms" in response.headers


def test_readiness_check_endpoint(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ready"
    assert "services" in data["data"]


def test_api_v1_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
