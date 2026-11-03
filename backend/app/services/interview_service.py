"""
Interview Service.
Business logic orchestrator for interviews.
"""
from typing import List, Optional, Tuple
from app.core.exceptions import (
    AuthorizationException,
    NotFoundException,
    ValidationException,
)
from app.models.interview import Interview
from app.models.user import User
from app.repositories.interview_repository import InterviewRepository
from app.schemas.interview import InterviewCreateRequest


class InterviewService:
    def __init__(self, interview_repo: InterviewRepository):
        self.interview_repo = interview_repo

    async def create_interview(self, user: User, data: InterviewCreateRequest) -> Interview:
        """Create new interview session without pre-generating all questions immediately."""
        if not data.topics:
            raise ValidationException("At least one topic must be specified.")

        configuration = {
            "topics": data.topics,
            "mode": data.mode.value,
            "difficulty": data.difficulty.value,
            "company_style": data.company_style,
            "document_ids": data.document_ids or [],
        }

        interview = await self.interview_repo.create(
            user_id=user.id,
            role=data.role,
            interview_type=data.interview_type.value,
            difficulty=data.difficulty.value,
            total_questions=data.question_count,
            configuration=configuration,
        )
        return interview

    async def get_interview(self, interview_id: str, current_user: User) -> Interview:
        """Fetch interview ensuring authorization boundary."""
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise NotFoundException(f"Interview with ID '{interview_id}' not found.")

        # Candidate can only access their own interviews
        if interview.user_id != current_user.id and current_user.role != "admin":
            raise AuthorizationException("You are not authorized to access this interview session.")

        return interview

    async def list_user_interviews(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Interview], int]:
        """List paginated interviews for current user."""
        return await self.interview_repo.list_by_user(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
        )

    async def start_interview(self, interview_id: str, current_user: User) -> Interview:
        """Start the interview session."""
        interview = await self.get_interview(interview_id, current_user)
        if interview.status == "completed":
            raise ValidationException("Cannot restart an already completed interview.")

        if interview.status != "in_progress":
            interview = await self.interview_repo.start(interview)

        return interview

    async def complete_interview(self, interview_id: str, current_user: User) -> Interview:
        """Explicitly end the interview session."""
        interview = await self.get_interview(interview_id, current_user)
        if interview.status == "completed":
            return interview

        return await self.interview_repo.complete(interview)
