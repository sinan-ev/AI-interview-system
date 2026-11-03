"""
Question Generator Agent.
Implements Section 9: Context-aware question generation with rubrics and duplicate prevention.
"""
from typing import List, Optional

from app.ai.llm.base import LLMProvider
from app.ai.prompts.question_generator import (
    QUESTION_GENERATOR_SYSTEM_PROMPT,
    QUESTION_GENERATOR_USER_TEMPLATE,
)
from app.core.exceptions import AIServiceException
from app.core.logging import logger
from app.schemas.question import GeneratedQuestion


class QuestionGeneratorAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_question(
        self,
        role: str,
        topic: str,
        difficulty: str,
        interview_type: str = "technical",
        subtopic: Optional[str] = None,
        previous_questions: Optional[List[str]] = None,
        is_follow_up: bool = False,
        follow_up_guidance: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> GeneratedQuestion:
        """Formulate a structured question with rubrics and verify uniqueness."""
        prev_list = previous_questions or []
        prev_formatted = "\n- ".join(prev_list) if prev_list else "None (First question)"

        prompt = QUESTION_GENERATOR_USER_TEMPLATE.format(
            role=role,
            topic=topic,
            subtopic=subtopic or "Core concepts",
            difficulty=difficulty,
            interview_type=interview_type,
            previous_questions=prev_formatted,
            is_follow_up=is_follow_up,
            follow_up_guidance=follow_up_guidance or "N/A",
            rag_context=rag_context or "No external document context provided.",
        )

        # Retry generation if generated text duplicates any previous question
        max_attempts = 3
        for attempt in range(max_attempts):
            generated: GeneratedQuestion = await self.llm.generate_structured(
                prompt=prompt,
                response_model=GeneratedQuestion,
                system_prompt=QUESTION_GENERATOR_SYSTEM_PROMPT,
                temperature=0.2 + (0.1 * attempt),
            )

            # Deduplication validation
            is_duplicate = any(
                generated.question.lower().strip() == pq.lower().strip()
                for pq in prev_list
            )

            if not is_duplicate:
                logger.info(
                    f"Generated question #{len(prev_list) + 1} for topic '{topic}' [{difficulty}]",
                    extra={"agent": "QuestionGenerator", "topic": topic, "difficulty": difficulty}
                )
                return generated

            logger.warning(
                f"Duplicate question detected on attempt {attempt + 1}. Retrying question generation...",
                extra={"agent": "QuestionGenerator", "attempt": attempt + 1}
            )

        raise AIServiceException("QuestionGenerator failed to produce a unique question after multiple attempts.")
