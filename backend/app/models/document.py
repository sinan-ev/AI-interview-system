"""
Document Database Model.
Section 4: documents table.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBCompat, TimestampMixin, generate_uuid


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, docx, pptx, txt, md
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False, index=True)  # uploaded, processing, ready, failed
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONBCompat, default=dict, nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")
