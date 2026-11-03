"""
Interview Question Generation Workflow.
Section 9-12: Full question generation pipeline with adaptive difficulty and RAG.
"""
from typing import Any, Dict, List, Optional

from app.ai.agents.interview_manager import InterviewManagerAgent
from app.ai.agents.question_generator import QuestionGeneratorAgent
from app.core.logging import logger
from app.schemas.question import GeneratedQuestion, InterviewManagerDecision, ManagerAction


class QuestionGenerationWorkflow:
    """
    Coordinates adaptive question generation using the InterviewManager + QuestionGenerator agents.
    Implements Sections 9 (generation), 10 (follow-ups), 11 (difficulty adjustment), 12 (topic switching).
    """

    def __init__(
        self,
        interview_manager: InterviewManagerAgent,
        question_generator: QuestionGeneratorAgent,
    ):
        self.interview_manager = interview_manager
        self.question_generator = question_generator

    async def generate_next_question(
        self,
        interview_id: str,
        role: str,
        interview_type: str,
        topics: List[str],
        current_topic: str,
        difficulty: str,
        questions_answered: int,
        total_questions: int,
        previous_questions: List[str],
        last_score: Optional[float] = None,
        last_feedback: Optional[str] = None,
        rag_context: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        End-to-end question generation:
        1. InterviewManager decides: new question, follow-up, topic switch, difficulty adjust, or complete.
        2. QuestionGenerator produces the actual question with rubric.
        Returns a dict with the generated question and manager decision metadata.
        """

        # Step 1: Manager decides next action
        decision: InterviewManagerDecision = await self.interview_manager.decide_next_action(
            role=role,
            interview_type=interview_type,
            topics=topics,
            current_topic=current_topic,
            difficulty=difficulty,
            questions_answered=questions_answered,
            total_questions=total_questions,
            previous_questions=previous_questions,
            last_score=last_score,
            last_feedback=last_feedback,
        )

        # Interview complete: no question needed
        if decision.action == ManagerAction.COMPLETE_INTERVIEW:
            logger.info(
                f"InterviewManager signaled COMPLETE for interview '{interview_id}'",
                extra={"workflow": "QuestionGenerationWorkflow", "interview_id": interview_id}
            )
            return {
                "action": "complete",
                "decision": decision,
                "question": None,
            }

        # Step 2: Generate the question based on manager decision
        effective_topic = decision.topic or current_topic
        effective_difficulty = decision.difficulty or difficulty
        is_follow_up = (decision.action == ManagerAction.GENERATE_FOLLOW_UP)
        follow_up_guidance = decision.reason if is_follow_up else None

        generated_question: GeneratedQuestion = await self.question_generator.generate_question(
            role=role,
            topic=effective_topic,
            difficulty=effective_difficulty,
            interview_type=interview_type,
            subtopic=None,
            previous_questions=previous_questions,
            is_follow_up=is_follow_up,
            follow_up_guidance=follow_up_guidance,
            rag_context=rag_context,
        )

        logger.info(
            f"Question #{questions_answered + 1} generated for '{effective_topic}' [{effective_difficulty}]",
            extra={
                "workflow": "QuestionGenerationWorkflow",
                "interview_id": interview_id,
                "action": decision.action.value,
                "topic": effective_topic,
            }
        )

        return {
            "action": decision.action.value,
            "decision": decision,
            "question": generated_question,
            "effective_topic": effective_topic,
            "effective_difficulty": effective_difficulty,
            "is_follow_up": is_follow_up,
        }
