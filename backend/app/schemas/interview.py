"""
Interview Schemas.
Implements validation for Section 6, Section 7, and Section 31 specs.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InterviewType(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    HR = "hr"
    COMPANY_STYLE = "company_style"
    TOPIC_SPECIFIC = "topic_specific"
    RESUME_BASED = "resume_based"
    DOCUMENT_BASED = "document_based"
    MIXED = "mixed"


class InterviewDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class InterviewMode(str, Enum):
    VOICE = "voice"
    TEXT = "text"


class InterviewStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewCreateRequest(BaseModel):
    role: str = Field(..., min_length=2, max_length=100, example="Data Scientist")
    interview_type: InterviewType = Field(default=InterviewType.TECHNICAL, example="technical")
    difficulty: InterviewDifficulty = Field(default=InterviewDifficulty.INTERMEDIATE, example="intermediate")
    topics: List[str] = Field(..., min_length=1, max_length=20, example=["Python", "Pandas", "Machine Learning", "Statistics"])
    question_count: int = Field(default=5, ge=1, le=50, example=10)
    mode: InterviewMode = Field(default=InterviewMode.VOICE, example="voice")
    company_style: Optional[str] = Field(None, example="ExampleCorp", description="Optional company format")
    document_ids: Optional[List[str]] = Field(default_factory=list, description="Associated documents for document-based interviews")


class InterviewQuestionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_number: int
    topic: str
    subtopic: Optional[str]
    difficulty: str
    question_text: str
    is_follow_up: bool
    created_at: datetime


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    role: str
    interview_type: str
    difficulty: str
    status: str
    total_questions: int
    current_question: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    configuration: Dict[str, Any]
    overall_score: Optional[float]
    created_at: datetime


class InterviewDetailResponse(InterviewResponse):
    questions: List[InterviewQuestionSummary] = []


class InterviewListResponse(BaseModel):
    items: List[InterviewResponse]
    total: int
    page: int
    page_size: int
