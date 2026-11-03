"""
Question Database Repository.
Handles persistence and retrieval of interview questions.
"""
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview_question import InterviewQuestion


class QuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        interview_id: str,
        question_number: int,
        topic: str,
        subtopic: Optional[str],
        difficulty: str,
        question_text: str,
        expected_concepts: List[str],
        evaluation_rubric: dict,
        source_document_ids: Optional[List[str]] = None,
        parent_question_id: Optional[str] = None,
        is_follow_up: bool = False,
    ) -> InterviewQuestion:
        """Create and persist an interview question."""
        question = InterviewQuestion(
            interview_id=interview_id,
            question_number=question_number,
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty,
            question_text=question_text.strip(),
            expected_concepts=expected_concepts,
            evaluation_rubric=evaluation_rubric,
            source_document_ids=source_document_ids or [],
            parent_question_id=parent_question_id,
            is_follow_up=is_follow_up,
        )
        self.db.add(question)
        await self.db.flush()
        return question

    async def get_by_id(self, question_id: str) -> Optional[InterviewQuestion]:
        """Fetch question by ID with answers eagerly loaded."""
        stmt = (
            select(InterviewQuestion)
            .options(selectinload(InterviewQuestion.answers))
            .where(InterviewQuestion.id == question_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_interview(self, interview_id: str) -> List[InterviewQuestion]:
        """List all questions for an interview ordered by question number."""
        stmt = (
            select(InterviewQuestion)
            .options(selectinload(InterviewQuestion.answers))
            .where(InterviewQuestion.interview_id == interview_id)
            .order_by(InterviewQuestion.question_number.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_question(self, interview_id: str) -> Optional[InterviewQuestion]:
        """Fetch the most recently created question for an interview."""
        stmt = (
            select(InterviewQuestion)
            .options(selectinload(InterviewQuestion.answers))
            .where(InterviewQuestion.id == InterviewQuestion.id)  # standard pattern
            .where(InterviewQuestion.interview_id == interview_id)
            .order_by(desc(InterviewQuestion.question_number))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
