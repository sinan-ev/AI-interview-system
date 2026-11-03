"""
Question Service.
Orchestrates AI agents, question repository, and interview session state.
"""
from typing import Optional
from app.ai.agents.question_generator import QuestionGeneratorAgent
from app.ai.agents.interview_manager import InterviewManagerAgent
from app.core.exceptions import (
    AuthorizationException,
    NotFoundException,
    ValidationException,
)
from app.models.interview import Interview
from app.models.interview_question import InterviewQuestion
from app.models.user import User
from app.repositories.interview_repository import InterviewRepository
from app.repositories.question_repository import QuestionRepository
from app.schemas.question import GeneratedQuestion


class QuestionService:
    def __init__(
        self,
        question_repo: QuestionRepository,
        interview_repo: InterviewRepository,
        question_generator: QuestionGeneratorAgent,
        interview_manager: InterviewManagerAgent,
    ):
        self.question_repo = question_repo
        self.interview_repo = interview_repo
        self.question_generator = question_generator
        self.interview_manager = interview_manager

    async def get_question(self, question_id: str, current_user: User) -> InterviewQuestion:
        """Fetch question ensuring user ownership of the parent interview."""
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise NotFoundException(f"Question with ID '{question_id}' not found.")

        interview = await self.interview_repo.get_by_id(question.interview_id)
        if not interview:
            raise NotFoundException("Associated interview not found.")

        if interview.user_id != current_user.id and current_user.role != "admin":
            raise AuthorizationException("You are not authorized to view this question.")

        return question

    async def get_or_generate_current_question(
        self,
        interview_id: str,
        current_user: User,
    ) -> InterviewQuestion:
        """
        Retrieves the active unanswered question, or dynamically generates
        the next question using the QuestionGenerator agent.
        """
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise NotFoundException(f"Interview with ID '{interview_id}' not found.")

        if interview.user_id != current_user.id and current_user.role != "admin":
            raise AuthorizationException("You are not authorized to access this interview.")

        if interview.status == "completed":
            raise ValidationException("Interview is already completed. No more questions available.")

        # If created, start the interview
        if interview.status == "created":
            await self.interview_repo.start(interview)

        # Check existing questions
        questions = await self.question_repo.list_by_interview(interview_id)

        # Check if the latest question has not been answered yet
        if questions:
            latest = questions[-1]
            # If latest question has no answers, return it
            if not latest.answers:
                return latest

        # Check if quota has been reached
        if len(questions) >= interview.total_questions:
            await self.interview_repo.complete(interview)
            raise ValidationException("All interview questions have been completed.")

        # Determine next topic and difficulty
        config_topics = interview.configuration.get("topics", ["Technical Skills"])
        next_question_idx = len(questions)
        target_topic = config_topics[next_question_idx % len(config_topics)]

        # Collect list of previous questions to guarantee deduplication
        previous_texts = [q.question_text for q in questions]

        # Generate structured question
        generated: GeneratedQuestion = await self.question_generator.generate_question(
            role=interview.role,
            topic=target_topic,
            difficulty=interview.difficulty,
            interview_type=interview.interview_type,
            previous_questions=previous_texts,
            is_follow_up=False,
        )

        # Persist generated question in database
        question_number = len(questions) + 1
        saved_question = await self.question_repo.create(
            interview_id=interview.id,
            question_number=question_number,
            topic=generated.topic,
            subtopic=generated.subtopic,
            difficulty=generated.difficulty,
            question_text=generated.question,
            expected_concepts=generated.expected_concepts,
            evaluation_rubric=generated.evaluation_rubric,
            source_document_ids=generated.source_document_ids,
            is_follow_up=False,
        )

        interview.current_question = question_number
        await self.interview_repo.db.flush()

        return saved_question
