"""
InterviewQuestion Database Model.
Section 4: interview_questions table.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBCompat, TimestampMixin, generate_uuid


class InterviewQuestion(Base, TimestampMixin):
    __tablename__ = "interview_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subtopic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_concepts: Mapped[List[str]] = mapped_column(JSONBCompat, default=list, nullable=False)
    evaluation_rubric: Mapped[Dict[str, Any]] = mapped_column(JSONBCompat, default=dict, nullable=False)
    source_document_ids: Mapped[List[str]] = mapped_column(JSONBCompat, default=list, nullable=False)
    parent_question_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("interview_questions.id", ondelete="SET NULL"), nullable=True)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    interview = relationship("Interview", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan", lazy="selectin")
    follow_up_questions = relationship("InterviewQuestion", backref="parent_question", remote_side=[id])
