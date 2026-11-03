"""
User Schemas.
Never exposes password_hash.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Jane Doe")
    email: EmailStr = Field(..., example="jane.doe@example.com")
    role: str = Field(default="candidate", pattern="^(candidate|interviewer|admin)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Minimum 8 characters")


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
