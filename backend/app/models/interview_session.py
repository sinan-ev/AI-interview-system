"""
InterviewSession Database Model.
Section 4: interview_sessions table. Manages active agent state machine state.
"""
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBCompat, TimestampMixin, generate_uuid


class InterviewSession(Base, TimestampMixin):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    current_state: Mapped[str] = mapped_column(String(50), default="INITIALIZING", nullable=False)
    state_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONBCompat, default=dict, nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    interview = relationship("Interview", back_populates="session_state")
