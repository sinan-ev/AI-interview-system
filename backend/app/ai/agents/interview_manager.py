"""
Interview Manager Agent.
Implements Section 8: State evaluation and next action decision.
"""
from typing import Any, Dict, List, Optional

from app.ai.llm.base import LLMProvider
from app.ai.prompts.interview_manager import (
    INTERVIEW_MANAGER_SYSTEM_PROMPT,
    INTERVIEW_MANAGER_USER_TEMPLATE,
)
from app.core.logging import logger
from app.schemas.question import InterviewManagerDecision, ManagerAction


class InterviewManagerAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def decide_next_action(
        self,
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
    ) -> InterviewManagerDecision:
        """Evaluate session state and return structured decision."""

        # Deterministic boundary check: if quota reached, complete immediately
        if questions_answered >= total_questions:
            return InterviewManagerDecision(
                action=ManagerAction.COMPLETE_INTERVIEW,
                topic=current_topic,
                difficulty=difficulty,
                reason="Question quota reached for this session.",
                follow_up=False,
            )

        # For initial question, start on first topic
        if questions_answered == 0:
            first_topic = topics[0] if topics else current_topic
            return InterviewManagerDecision(
                action=ManagerAction.GENERATE_NEW_QUESTION,
                topic=first_topic,
                difficulty=difficulty,
                reason="Initial interview question.",
                follow_up=False,
            )

        prompt = INTERVIEW_MANAGER_USER_TEMPLATE.format(
            role=role,
            interview_type=interview_type,
            topics=", ".join(topics),
            current_topic=current_topic,
            difficulty=difficulty,
            questions_answered=questions_answered,
            total_questions=total_questions,
            previous_questions="\n- ".join(previous_questions) if previous_questions else "None",
            last_score=f"{last_score:.1f}" if last_score is not None else "N/A",
            last_feedback=last_feedback or "N/A",
        )

        decision = await self.llm.generate_structured(
            prompt=prompt,
            response_model=InterviewManagerDecision,
            system_prompt=INTERVIEW_MANAGER_SYSTEM_PROMPT,
            temperature=0.1,
        )

        logger.info(
            f"InterviewManager decision: {decision.action} on {decision.topic} [{decision.difficulty}]",
            extra={"agent": "InterviewManager", "action": decision.action.value}
        )
        return decision
