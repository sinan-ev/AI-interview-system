"""
UserSkill Database Model.
Section 4: user_skills table. Tracks skill progression and confidence over time.
"""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class UserSkill(Base, TimestampMixin):
    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")
