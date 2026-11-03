"""
Interview Repository.
Database interactions for Interviews and Interview Sessions.
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview import Interview
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        role: str,
        interview_type: str,
        difficulty: str,
        total_questions: int,
        configuration: dict,
    ) -> Interview:
        """Create new interview record."""
        interview = Interview(
            user_id=user_id,
            role=role.strip(),
            interview_type=interview_type,
            difficulty=difficulty,
            status="created",
            total_questions=total_questions,
            current_question=0,
            configuration=configuration,
        )
        self.db.add(interview)
        await self.db.flush()

        # Initialize session state machine
        session_state = InterviewSession(
            interview_id=interview.id,
            current_state="INITIALIZED",
            state_metadata={"created_at": datetime.now(timezone.utc).isoformat()},
        )
        self.db.add(session_state)
        await self.db.flush()

        return interview

    async def get_by_id(self, interview_id: str) -> Optional[Interview]:
        """Fetch interview with questions eagerly loaded."""
        stmt = (
            select(Interview)
            .options(
                selectinload(Interview.questions),
                selectinload(Interview.session_state)
            )
            .where(Interview.id == interview_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Interview], int]:
        """Fetch paginated interviews for a user."""
        query = select(Interview).where(Interview.user_id == user_id)
        if status_filter:
            query = query.where(Interview.status == status_filter)

        count_query = select(func.count(Interview.id)).where(Interview.user_id == user_id)
        if status_filter:
            count_query = count_query.where(Interview.status == status_filter)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar() or 0

        query = query.order_by(desc(Interview.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def start(self, interview: Interview) -> Interview:
        """Transition interview to in_progress state."""
        interview.status = "in_progress"
        interview.started_at = datetime.now(timezone.utc)
        if interview.session_state:
            interview.session_state.current_state = "IN_PROGRESS"
        await self.db.flush()
        return interview

    async def complete(self, interview: Interview, overall_score: Optional[float] = None) -> Interview:
        """Mark interview as completed."""
        interview.status = "completed"
        interview.completed_at = datetime.now(timezone.utc)
        if overall_score is not None:
            interview.overall_score = overall_score
        if interview.session_state:
            interview.session_state.current_state = "COMPLETED"
        await self.db.flush()
        return interview
