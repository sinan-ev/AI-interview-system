"""
Question & Agent Schemas.
Implements Section 8 (Interview Manager) and Section 9 (Question Generator) strict Pydantic schemas.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ManagerAction(str, Enum):
    GENERATE_NEW_QUESTION = "GENERATE_NEW_QUESTION"
    GENERATE_FOLLOW_UP = "GENERATE_FOLLOW_UP"
    INCREASE_DIFFICULTY = "INCREASE_DIFFICULTY"
    DECREASE_DIFFICULTY = "DECREASE_DIFFICULTY"
    CHANGE_TOPIC = "CHANGE_TOPIC"
    COMPLETE_INTERVIEW = "COMPLETE_INTERVIEW"


class InterviewManagerDecision(BaseModel):
    """Section 8: Interview Manager Agent Decision Contract."""
    action: ManagerAction = Field(..., description="Workflow decision action")
    topic: str = Field(..., description="Target subject topic")
    difficulty: str = Field(..., description="Target question difficulty: beginner, intermediate, advanced")
    question_type: str = Field(default="conceptual", description="conceptual, practical, architectural, or behavioral")
    reason: str = Field(..., description="Candidate performance rationale for decision")
    follow_up: bool = Field(default=False, description="True if next question is a follow-up")


class GeneratedQuestion(BaseModel):
    """Section 9: Question Generator Output Contract."""
    question: str = Field(..., min_length=10, description="The formulated interview question")
    topic: str = Field(..., min_length=2, description="Target topic name")
    subtopic: Optional[str] = Field(None, description="Specific subtopic area")
    difficulty: str = Field(..., description="Target difficulty")
    question_type: str = Field(default="conceptual", description="Question category")
    expected_concepts: List[str] = Field(..., min_length=1, description="Expected core concepts required for answer")
    evaluation_rubric: Dict[str, Any] = Field(..., description="Scoring criteria, required concepts, common mistakes")
    source_document_ids: List[str] = Field(default_factory=list, description="Referenced document IDs if RAG grounded")


class QuestionResponse(BaseModel):
    """Client-facing Question representation (never exposes rubric or answers to the candidate)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    interview_id: str
    question_number: int
    topic: str
    subtopic: Optional[str]
    difficulty: str
    question_text: str
    is_follow_up: bool
    created_at: datetime


class QuestionDetailInternal(QuestionResponse):
    """Internal model including evaluation criteria for backend evaluators."""
    expected_concepts: List[str]
    evaluation_rubric: Dict[str, Any]
    source_document_ids: List[str]
    parent_question_id: Optional[str]
