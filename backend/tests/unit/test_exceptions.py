"""
Unit tests for domain exceptions and error envelope formatting.
"""
from app.core.exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    AuthenticationException,
    format_error_response
)


def test_exception_properties():
    exc = NotFoundException("Interview session not found", details={"interview_id": "test-123"})
    assert exc.status_code == 404
    assert exc.error_code == "RESOURCE_NOT_FOUND"
    assert exc.message == "Interview session not found"
    assert exc.details["interview_id"] == "test-123"


def test_error_response_envelope():
    response = format_error_response(
        status_code=400,
        error_code="INVALID_INPUT",
        message="Invalid payload supplied",
        details={"field": "topics"},
        req_id="req-abc-999"
    )
    assert response.status_code == 400
    import json
    data = json.loads(response.body.decode("utf-8"))
    assert data["success"] is False
    assert data["request_id"] == "req-abc-999"
    assert data["error"]["code"] == "INVALID_INPUT"
    assert data["error"]["message"] == "Invalid payload supplied"
    assert data["error"]["details"]["field"] == "topics"
