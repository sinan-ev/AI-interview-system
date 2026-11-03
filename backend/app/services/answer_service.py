"""
Answer Service.
Implements Section 13: Processing and storage for Text, Voice, and Voice+Transcript answers.
"""
from typing import Optional
from fastapi import UploadFile

from app.core.exceptions import (
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.answer import Answer
from app.models.interview import Interview
from app.models.interview_question import InterviewQuestion
from app.models.user import User
from app.repositories.answer_repository import AnswerRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.question_repository import QuestionRepository
from app.schemas.answer import TextAnswerSubmission
from app.utils.files import save_uploaded_file


class AnswerService:
    def __init__(
        self,
        answer_repo: AnswerRepository,
        question_repo: QuestionRepository,
        interview_repo: InterviewRepository,
    ):
        self.answer_repo = answer_repo
        self.question_repo = question_repo
        self.interview_repo = interview_repo

    async def submit_text_answer(
        self,
        interview_id: str,
        current_user: User,
        data: TextAnswerSubmission,
    ) -> Answer:
        """Submit and validate text-based answer to an interview question."""
        interview, question = await self._validate_submission_context(
            interview_id=interview_id,
            question_id=data.question_id,
            current_user=current_user,
        )

        clean_text = data.text_answer.strip()
        if not clean_text:
            raise ValidationException("Text answer cannot be empty or solely whitespace.")

        answer = await self.answer_repo.create(
            question_id=question.id,
            user_id=current_user.id,
            text_answer=clean_text,
            transcript=clean_text,
            duration_seconds=data.duration_seconds or 0.0,
        )
        return answer

    async def submit_voice_answer(
        self,
        interview_id: str,
        question_id: str,
        current_user: User,
        audio_file: UploadFile,
        duration_seconds: Optional[float] = None,
        provided_transcript: Optional[str] = None,
    ) -> Answer:
        """Submit voice answer, saving audio file and preparing for STT / evaluation."""
        interview, question = await self._validate_submission_context(
            interview_id=interview_id,
            question_id=question_id,
            current_user=current_user,
        )

        # 1. Validate and store audio file securely
        audio_url, file_size = await save_uploaded_file(
            file=audio_file,
            subfolder="audio",
        )

        # 2. Use provided transcript or default to pending transcription
        transcript = (provided_transcript or "").strip() or None

        answer = await self.answer_repo.create(
            question_id=question.id,
            user_id=current_user.id,
            text_answer=transcript,
            audio_file_url=audio_url,
            transcript=transcript,
            duration_seconds=duration_seconds or 0.0,
        )
        return answer

    async def _validate_submission_context(
        self,
        interview_id: str,
        question_id: str,
        current_user: User,
    ) -> tuple[Interview, InterviewQuestion]:
        """Validate interview ownership, question linkage, and duplicate answer prevention."""
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise NotFoundException(f"Interview '{interview_id}' not found.")

        if interview.user_id != current_user.id and current_user.role != "admin":
            raise AuthorizationException("You are not authorized to submit answers for this interview.")

        if interview.status == "completed":
            raise ValidationException("Cannot submit answers to an already completed interview.")

        question = await self.question_repo.get_by_id(question_id)
        if not question or question.interview_id != interview.id:
            raise NotFoundException(f"Question '{question_id}' does not belong to this interview.")

        # Check if question has already been answered
        existing_answer = await self.answer_repo.get_by_question_id(question_id)
        if existing_answer:
            raise ConflictException(f"Question '{question_id}' has already been answered.")

        return interview, question
