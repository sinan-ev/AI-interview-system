"""
Answer Schemas.
Implements validation for Section 13: Text, Voice, and Voice + Transcript submission.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TextAnswerSubmission(BaseModel):
    """Payload for submitting text-based interview answer."""
    question_id: str = Field(..., description="ID of the question being answered")
    text_answer: str = Field(..., min_length=2, max_length=10000, description="Candidate response text")
    duration_seconds: Optional[float] = Field(None, ge=0.0, description="Time spent answering in seconds")


class AnswerResponse(BaseModel):
    """Answer response returned to client."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    user_id: str
    text_answer: Optional[str]
    audio_file_url: Optional[str]
    transcript: Optional[str]
    duration_seconds: Optional[float]
    created_at: datetime
