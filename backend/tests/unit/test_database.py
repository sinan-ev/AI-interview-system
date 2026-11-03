"""
Unit tests for Database Models and Schema creation.
Verifies table definitions, relationships, constraints, and session execution.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import Base
from app.models import (
    User, RefreshToken, Interview, InterviewQuestion,
    Answer, Evaluation, Skill, UserSkill, Document,
    DocumentChunk, Feedback, LearningRecommendation, InterviewSession
)


@pytest.fixture
async def test_db_session():
    """Create an isolated in-memory SQLite database session for unit tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_query_user(test_db_session: AsyncSession):
    user = User(
        name="Alex Smith",
        email="alex@example.com",
        password_hash="argon2_hashed_secret",
        role="candidate",
        is_active=True,
    )
    test_db_session.add(user)
    await test_db_session.commit()

    stmt = select(User).where(User.email == "alex@example.com")
    result = await test_db_session.execute(stmt)
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.name == "Alex Smith"
    assert found.role == "candidate"
    assert found.id is not None
    assert found.created_at is not None


@pytest.mark.asyncio
async def test_interview_question_answer_evaluation_cascade(test_db_session: AsyncSession):
    user = User(
        name="Sam Tech",
        email="sam@example.com",
        password_hash="hashed_secret",
        role="candidate",
    )
    test_db_session.add(user)
    await test_db_session.flush()

    interview = Interview(
        user_id=user.id,
        role="Backend Engineer",
        interview_type="technical",
        difficulty="intermediate",
        status="in_progress",
        total_questions=5,
        current_question=1,
        configuration={"topics": ["Python", "FastAPI"]},
    )
    test_db_session.add(interview)
    await test_db_session.flush()

    question = InterviewQuestion(
        interview_id=interview.id,
        question_number=1,
        topic="Python",
        subtopic="AsyncIO",
        difficulty="intermediate",
        question_text="Explain the event loop in Python.",
        expected_concepts=["single-threaded", "coroutine", "event loop", "non-blocking"],
        evaluation_rubric={"concept_weight": 0.4, "accuracy_weight": 0.4},
        source_document_ids=[],
    )
    test_db_session.add(question)
    await test_db_session.flush()

    answer = Answer(
        question_id=question.id,
        user_id=user.id,
        text_answer="The Python event loop coordinates asynchronous tasks non-blockingly.",
        duration_seconds=12.5,
    )
    test_db_session.add(answer)
    await test_db_session.flush()

    evaluation = Evaluation(
        answer_id=answer.id,
        technical_score=85.0,
        accuracy_score=90.0,
        completeness_score=80.0,
        reasoning_score=85.0,
        grammar_score=95.0,
        communication_score=88.0,
        fluency_score=85.0,
        clarity_score=90.0,
        pronunciation_score=92.0,
        confidence_estimate=84.0,
        filler_word_count=2,
        pause_count=1,
        speaking_rate=135.0,
        overall_score=86.5,
        strengths=["Clear concise explanation", "Accurate non-blocking reference"],
        weaknesses=["Could expand on task scheduling"],
        missing_concepts=["coroutine yield"],
        feedback={"summary": "Strong conceptual foundation"},
        evaluator_version="1.0.0",
    )
    test_db_session.add(evaluation)
    await test_db_session.commit()

    # Query back via Answer
    stmt = select(Answer).options(selectinload(Answer.evaluation)).where(Answer.id == answer.id)
    res = await test_db_session.execute(stmt)
    saved_answer = res.scalar_one()

    assert saved_answer.question_id == question.id
    assert saved_answer.evaluation.overall_score == 86.5
    assert saved_answer.evaluation.filler_word_count == 2


@pytest.mark.asyncio
async def test_document_and_chunks(test_db_session: AsyncSession):
    user = User(
        name="Doc User",
        email="docuser@example.com",
        password_hash="hashed_secret",
    )
    test_db_session.add(user)
    await test_db_session.flush()

    doc = Document(
        user_id=user.id,
        filename="resume.pdf",
        file_type="pdf",
        file_size=102400,
        status="ready",
        metadata_={"pages": 2},
    )
    test_db_session.add(doc)
    await test_db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Senior Python Developer with 5 years experience.",
        metadata_={"page": 1},
        embedding=[0.1] * 1536,
    )
    test_db_session.add(chunk)
    await test_db_session.commit()

    stmt = select(Document).options(selectinload(Document.chunks)).where(Document.id == doc.id)
    res = await test_db_session.execute(stmt)
    saved_doc = res.scalar_one()

    assert saved_doc.filename == "resume.pdf"
    assert len(saved_doc.chunks) == 1
    assert saved_doc.chunks[0].chunk_index == 0
