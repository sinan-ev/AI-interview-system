"""
Feedback Database Model.
Section 4: feedback table. Categorized insights, evidence, and actionable recommendations.
"""
from typing import Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # technical, communication, structure, fluency
    severity: Mapped[str] = mapped_column(String(50), default="info", nullable=False)  # praise, info, minor, critical
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    interview = relationship("Interview", back_populates="feedbacks")
