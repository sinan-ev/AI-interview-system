"""
Answer Database Model.
Section 4: answers table.
"""
from typing import Optional
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class Answer(Base, TimestampMixin):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    question = relationship("InterviewQuestion", back_populates="answers")
    user = relationship("User", back_populates="answers")
    evaluation = relationship("Evaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")
