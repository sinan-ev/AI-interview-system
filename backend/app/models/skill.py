"""
Skill Database Model.
Section 4: skills table.
"""
from typing import Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # technical, soft_skill, domain
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_skill_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    sub_skills = relationship("Skill", backref="parent_skill", remote_side=[id])
    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")
