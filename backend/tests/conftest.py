"""
Pytest configuration and shared test fixtures.
Provides an isolated in-memory async SQLite engine with clean tables for each test session,
and dependency overrides for FastAPI TestClient.
"""
import asyncio
import os
import sys
from typing import AsyncGenerator
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.config import Settings, get_settings
from app.core.database import Base, get_db

# Test in-memory SQLite engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all database tables once before any tests run."""
    async def init_models():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_models())
    yield
    async def drop_models():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()
    asyncio.run(drop_models())


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override providing test DB session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client for API integration tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Fixture providing loaded settings."""
    return get_settings()


@pytest.fixture(autouse=True, scope="session")
def mock_celery_delay():
    """Prevent tests from attempting to connect to live Redis broker."""
    from unittest.mock import MagicMock, patch
    with patch("app.workers.tasks.ingest_document_task.delay", return_value=MagicMock(id="mock-ingest-id")), \
         patch("app.workers.tasks.generate_feedback_task.delay", return_value=MagicMock(id="mock-feedback-id")), \
         patch("app.workers.tasks.evaluate_answer_task.delay", return_value=MagicMock(id="mock-eval-id")), \
         patch("app.workers.tasks.transcribe_audio_task.delay", return_value=MagicMock(id="mock-transcribe-id")):
        yield
