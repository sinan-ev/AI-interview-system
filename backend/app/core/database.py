"""
Database Engine & Async Session Lifecycle.
SQLAlchemy 2.x with asyncpg, pgvector support, and dialect-agnostic type fallbacks.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON, TypeDecorator

from app.core.config import settings
from app.core.logging import logger

# Dialect-agnostic JSONB type
class JSONBCompat(TypeDecorator):
    """Platform-independent JSONB type. Uses PostgreSQL JSONB when available, falls back to JSON."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


# Create async engine with dialect compatibility
is_sqlite = "sqlite" in settings.DATABASE_URL
engine_kwargs: dict[str, Any] = {
    "echo": settings.DB_ECHO,
    "future": True,
}
if not is_sqlite:
    engine_kwargs["pool_pre_ping"] = True
else:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
async_session_factory = AsyncSessionLocal


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base with common columns."""
    pass


class TimestampMixin:
    """Provides standard created_at and updated_at UTC timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


def generate_uuid() -> str:
    """Generate canonical UUID4 string for primary keys."""
    return str(uuid.uuid4())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
