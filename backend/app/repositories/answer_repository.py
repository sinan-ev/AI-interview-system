"""
Answer Database Repository.
Handles answer storage and retrieval.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.answer import Answer
from app.models.interview_question import InterviewQuestion


class AnswerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        question_id: str,
        user_id: str,
        text_answer: Optional[str] = None,
        audio_file_url: Optional[str] = None,
        transcript: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> Answer:
        """Create and persist an answer record."""
        answer = Answer(
            question_id=question_id,
            user_id=user_id,
            text_answer=text_answer,
            audio_file_url=audio_file_url,
            transcript=transcript,
            duration_seconds=duration_seconds,
        )
        self.db.add(answer)
        await self.db.flush()
        return answer

    async def get_by_id(self, answer_id: str) -> Optional[Answer]:
        """Fetch answer by ID with evaluation and question eagerly loaded."""
        stmt = (
            select(Answer)
            .options(
                selectinload(Answer.evaluation),
                selectinload(Answer.question)
            )
            .where(Answer.id == answer_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_question_id(self, question_id: str) -> Optional[Answer]:
        """Fetch first answer for a question."""
        stmt = (
            select(Answer)
            .options(selectinload(Answer.evaluation))
            .where(Answer.question_id == question_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_interview(self, interview_id: str) -> List[Answer]:
        """List all answers belonging to questions in an interview."""
        stmt = (
            select(Answer)
            .join(InterviewQuestion, Answer.question_id == InterviewQuestion.id)
            .where(InterviewQuestion.interview_id == interview_id)
            .order_by(InterviewQuestion.question_number.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
