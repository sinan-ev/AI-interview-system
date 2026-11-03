"""
Interview Database Model.
Section 4: interviews table.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBCompat, TimestampMixin, generate_uuid


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(50), nullable=False)  # technical, hr, company_style, etc.
    difficulty: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)  # beginner, intermediate, advanced
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False, index=True)  # created, in_progress, completed, abandoned
    total_questions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    current_question: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSONBCompat, default=dict, nullable=False)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    user = relationship("User", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewQuestion.question_number")
    feedbacks = relationship("Feedback", back_populates="interview", cascade="all, delete-orphan")
    session_state = relationship("InterviewSession", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    learning_recommendations = relationship("LearningRecommendation", back_populates="interview", cascade="all, delete-orphan")
