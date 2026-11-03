"""
Answer Evaluator Agent.
Section 18: Evaluates technical claims, concept coverage, completeness, and reasoning.
"""
from typing import Any, Dict, List, Optional
import json

from app.ai.llm.base import LLMProvider
from app.ai.prompts.answer_evaluator import (
    ANSWER_EVALUATOR_SYSTEM_PROMPT,
    ANSWER_EVALUATOR_USER_TEMPLATE,
)
from app.core.logging import logger
from app.schemas.evaluation import TechnicalEvidence


class AnswerEvaluatorAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def evaluate_answer(
        self,
        question_text: str,
        topic: str,
        difficulty: str,
        expected_concepts: List[str],
        evaluation_rubric: Dict[str, Any],
        candidate_answer: str,
    ) -> TechnicalEvidence:
        """Run rubric-based structured technical evaluation."""
        prompt = ANSWER_EVALUATOR_USER_TEMPLATE.format(
            question_text=question_text,
            topic=topic,
            difficulty=difficulty,
            expected_concepts="\n- ".join(expected_concepts) if expected_concepts else "None specified",
            evaluation_rubric=json.dumps(evaluation_rubric, indent=2),
            candidate_answer=candidate_answer.strip() if candidate_answer else "[Candidate provided empty answer]",
        )

        evidence: TechnicalEvidence = await self.llm.generate_structured(
            prompt=prompt,
            response_model=TechnicalEvidence,
            system_prompt=ANSWER_EVALUATOR_SYSTEM_PROMPT,
            temperature=0.1,
        )

        logger.info(
            f"Technical evaluation generated: correctness={evidence.correctness}, coverage={evidence.concept_coverage}",
            extra={"agent": "AnswerEvaluator", "correctness": evidence.correctness}
        )
        return evidence
