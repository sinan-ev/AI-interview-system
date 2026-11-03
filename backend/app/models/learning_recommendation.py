"""
LearningRecommendation Database Model.
Section 4: learning_recommendations table.
"""
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class LearningRecommendation(Base, TimestampMixin):
    __tablename__ = "learning_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=True, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1 = Highest, 2, 3...
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    user = relationship("User", back_populates="learning_recommendations")
    interview = relationship("Interview", back_populates="learning_recommendations")
