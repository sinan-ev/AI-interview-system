"""
Domain Exceptions & Global Error Handling.
Conforms to Section 44:
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable description",
        "details": {}
    },
    "request_id": "..."
}
"""
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger, request_id_ctx


class AppException(Exception):
    """Base application exception."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"

    def __init__(self, message: str = "Requested resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class ValidationException(AppException):
    status_code = 422  # HTTP_422_UNPROCESSABLE_CONTENT (avoids starlette version mismatch)
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class AuthenticationException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication failed or token invalid", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class AuthorizationException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"

    def __init__(self, message: str = "Insufficient permissions to perform this action", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "RESOURCE_CONFLICT"

    def __init__(self, message: str = "Resource conflict occurred", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class RateLimitException(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message: str = "Too many requests. Please try again later.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class AIServiceException(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "AI_SERVICE_ERROR"

    def __init__(self, message: str = "AI service provider failure", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class AudioProcessingException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "AUDIO_PROCESSING_ERROR"

    def __init__(self, message: str = "Audio processing or transcription failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class DocumentProcessingException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "DOCUMENT_PROCESSING_ERROR"

    def __init__(self, message: str = "Document parsing or ingestion failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


def format_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    req_id: Optional[str] = None
) -> JSONResponse:
    """Standardized JSON error envelope per Section 44."""
    req_id = req_id or request_id_ctx.get() or "unknown"
    content = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {}
        },
        "request_id": req_id
    }
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get())
        logger.warning(
            f"AppException [{exc.error_code}]: {exc.message}",
            extra={"error_code": exc.error_code, "status": exc.status_code, "request_id": req_id}
        )
        return format_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            req_id=req_id
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get())
        # Clean up pydantic errors
        clean_errors = []
        for err in exc.errors():
            loc = " -> ".join([str(p) for p in err.get("loc", [])])
            clean_errors.append({
                "field": loc,
                "message": err.get("msg", "Invalid field"),
                "type": err.get("type", "value_error")
            })
        logger.info(f"Validation error on {request.url.path}", extra={"request_id": req_id})
        return format_error_response(
            status_code=422,  # HTTP_422_UNPROCESSABLE_CONTENT
            error_code="VALIDATION_ERROR",
            message="Input data validation failed",
            details={"errors": clean_errors},
            req_id=req_id
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get())
        error_code = "HTTP_ERROR"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            error_code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            error_code = "FORBIDDEN"

        return format_error_response(
            status_code=exc.status_code,
            error_code=error_code,
            message=str(exc.detail),
            details={},
            req_id=req_id
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get())
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True,
            extra={"request_id": req_id, "status": 500}
        )
        # Never expose internal stack traces to the client
        return format_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            details={},
            req_id=req_id
        )
