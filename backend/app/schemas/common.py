"""
Common Pydantic Schemas.
Implements Section 44 and Section 45 standard response structures.
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetails(BaseModel):
    code: str = Field(..., description="Unique error identifier code, e.g. INVALID_REQUEST")
    message: str = Field(..., description="Human-readable explanation of error")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured error context")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard success API response envelope."""
    success: bool = Field(default=True, description="Always true for successful requests")
    data: DataT = Field(..., description="Response payload")
    request_id: str = Field(..., description="Correlation request ID")


class ErrorResponse(BaseModel):
    """Standard error API response envelope."""
    success: bool = Field(default=False, description="Always false for failed requests")
    error: ErrorDetails = Field(..., description="Error descriptor")
    request_id: str = Field(..., description="Correlation request ID")


class PaginationMeta(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total_count: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: List[DataT]
    pagination: PaginationMeta


class HealthStatus(BaseModel):
    status: str = Field(default="healthy", description="'healthy' or 'degraded'")
    version: str
    environment: str
    services: Dict[str, str] = Field(default_factory=dict)
