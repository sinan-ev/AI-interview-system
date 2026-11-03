"""
DocumentChunk Database Model.
Section 4: document_chunks table with vector embeddings for RAG retrieval.
"""
from typing import Any, Dict, List, Optional
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text, TypeDecorator, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONBCompat, TimestampMixin, generate_uuid


class VectorCompat(TypeDecorator):
    """Dialect-compatible vector type. Uses pgvector on PostgreSQL and JSON elsewhere."""
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 1536, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONBCompat, default=dict, nullable=False)
    embedding = mapped_column(VectorCompat(1536), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")
