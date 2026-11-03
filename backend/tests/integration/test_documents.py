"""
Integration tests for Document Management & RAG upload endpoints.
Tests:
- POST /api/v1/documents/upload
- GET /api/v1/documents/
- GET /api/v1/documents/{id}
- DELETE /api/v1/documents/{id}
- Validation on unsupported MIME types
"""
import io
import pytest
from starlette.testclient import TestClient


def get_token(client: TestClient) -> str:
    res = client.post("/api/v1/auth/register", json={
        "name": "Doc Tester",
        "email": "doc_test@example.com",
        "password": "Password123!",
        "role": "candidate",
    })
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login = client.post("/api/v1/auth/login", json={
        "email": "doc_test@example.com",
        "password": "Password123!",
    })
    return login.json()["data"]["access_token"]


def test_upload_and_list_documents(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Upload a TXT document
    txt_content = b"Python is a multi-paradigm programming language. It supports OOP and functional styles."
    files = {
        "file": ("system_design.txt", io.BytesIO(txt_content), "text/plain")
    }
    data = {
        "title": "System Design Notes",
        "description": "Overview of Python paradigms"
    }

    res_upload = client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data,
        headers=headers,
    )
    assert res_upload.status_code == 202
    body = res_upload.json()["data"]
    assert "document_id" in body
    doc_id = body["document_id"]
    assert body["title"] == "System Design Notes"

    # List documents
    res_list = client.get("/api/v1/documents/", headers=headers)
    assert res_list.status_code == 200
    list_body = res_list.json()["data"]
    assert list_body["total"] >= 1
    found = any(d["document_id"] == doc_id for d in list_body["documents"])
    assert found

    # Get single document
    res_get = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert res_get.status_code == 200
    doc_data = res_get.json()["data"]
    assert doc_data["document_id"] == doc_id
    assert doc_data["title"] == "System Design Notes"

    # Delete document
    res_del = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["data"]["deleted"] is True

    # Verify deleted
    res_get_again = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert res_get_again.status_code == 404


def test_upload_unsupported_document_type(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": ("script.sh", io.BytesIO(b"echo 'hello'"), "application/x-sh")
    }
    data = {"title": "Shell Script"}

    res = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert res.status_code in (400, 422)
