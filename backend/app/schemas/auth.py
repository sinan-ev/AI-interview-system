"""
Authentication Schemas.
Request validation and token response representations.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="John Candidate")
    email: EmailStr = Field(..., example="candidate@example.com")
    password: str = Field(..., min_length=8, max_length=128, example="P@ssw0rdSecure!")
    role: str = Field(default="candidate", pattern="^(candidate|interviewer|admin)$")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="candidate@example.com")
    password: str = Field(..., example="P@ssw0rdSecure!")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
