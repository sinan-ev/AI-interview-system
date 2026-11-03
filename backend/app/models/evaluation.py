"""
Evaluation Database Model.
Section 4: evaluations table.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBCompat, TimestampMixin, generate_uuid


class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    answer_id: Mapped[str] = mapped_column(String(36), ForeignKey("answers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Technical sub-scores (0-100)
    technical_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reasoning_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Communication & Speech sub-scores (0-100)
    grammar_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    communication_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fluency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    clarity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pronunciation_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Speech analysis signals
    confidence_estimate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100 estimate
    filler_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    speaking_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # words per minute

    # Deterministic composite score
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Detailed structured feedback & evidence
    strengths: Mapped[List[str]] = mapped_column(JSONBCompat, default=list, nullable=False)
    weaknesses: Mapped[List[str]] = mapped_column(JSONBCompat, default=list, nullable=False)
    missing_concepts: Mapped[List[str]] = mapped_column(JSONBCompat, default=list, nullable=False)
    feedback: Mapped[Dict[str, Any]] = mapped_column(JSONBCompat, default=dict, nullable=False)

    # Evaluation versioning metadata
    evaluator_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)

    # Relationships
    answer = relationship("Answer", back_populates="evaluation")
