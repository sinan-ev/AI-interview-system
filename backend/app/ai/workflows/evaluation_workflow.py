"""
Evaluation Orchestration Workflow.
Section 13-23: Full answer evaluation pipeline coordinating all evaluator agents.
"""
import asyncio
from typing import Any, Dict, List, Optional

from app.ai.agents.answer_evaluator import AnswerEvaluatorAgent
from app.ai.agents.communication_analyzer import CommunicationAnalyzerAgent
from app.ai.evaluation.scoring import compute_overall_score, compute_technical_score
from app.core.logging import logger
from app.schemas.evaluation import (
    CommunicationEvidence,
    GrammarEvidence,
    TechnicalEvidence,
)


class EvaluationWorkflow:
    """
    Orchestrates the complete answer evaluation pipeline:
    1. Technical accuracy evaluation (LLM-based)
    2. Grammar evaluation (LLM-based)
    3. Communication quality evaluation (LLM-based)
    4. Speech feature extraction (rule-based)
    5. Confidence estimation (rule-based)
    6. Score aggregation and overall score computation

    Runs steps 1-3 in parallel using asyncio.gather() for minimum latency.
    """

    def __init__(
        self,
        answer_evaluator: AnswerEvaluatorAgent,
        communication_analyzer: CommunicationAnalyzerAgent,
    ):
        self.answer_evaluator = answer_evaluator
        self.communication_analyzer = communication_analyzer

    async def run(
        self,
        question_text: str,
        topic: str,
        difficulty: str,
        expected_concepts: List[str],
        evaluation_rubric: Dict[str, Any],
        transcript: str,
        duration_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Execute the full multi-agent evaluation pipeline for a single answer.
        Returns a comprehensive evaluation result dict ready for DB persistence.
        """
        logger.info(
            f"Starting evaluation pipeline for topic='{topic}', difficulty='{difficulty}'",
            extra={"workflow": "EvaluationWorkflow", "topic": topic}
        )

        # --- Step 1-3: Parallel LLM evaluation calls ---
        tech_eval_task = self.answer_evaluator.evaluate_answer(
            question_text=question_text,
            topic=topic,
            difficulty=difficulty,
            expected_concepts=expected_concepts,
            evaluation_rubric=evaluation_rubric,
            candidate_answer=transcript,
        )

        comm_eval_task = self.communication_analyzer.analyze_communication(
            transcript=transcript,
            question_text=question_text,
            topic=topic,
        )

        grammar_eval_task = self.communication_analyzer.analyze_grammar(
            transcript=transcript,
        )

        tech_evidence, comm_evidence, grammar_evidence = await asyncio.gather(
            tech_eval_task,
            comm_eval_task,
            grammar_eval_task,
        )

        # --- Step 4-5: Rule-based speech and confidence analysis ---
        speech_features = self.communication_analyzer.analyze_speech_features(
            transcript=transcript,
            duration_seconds=duration_seconds,
        )
        confidence_score = self.communication_analyzer.estimate_confidence(
            transcript=transcript,
            duration_seconds=duration_seconds,
        )

        # --- Step 6: Score aggregation ---
        technical_score = compute_technical_score(tech_evidence)
        overall_score = compute_overall_score(
            technical_score=technical_score,
            grammar_score=grammar_evidence.grammar_score,
            communication_score=comm_evidence.communication_score,
            fluency_score=speech_features.get("estimated_fluency_score", 70.0),
        )

        result = {
            # Technical scores
            "technical_score": technical_score,
            "accuracy_score": tech_evidence.correctness,
            "completeness_score": tech_evidence.completeness,
            "reasoning_score": tech_evidence.reasoning,
            "concept_coverage_score": tech_evidence.concept_coverage,

            # Communication scores
            "grammar_score": grammar_evidence.grammar_score,
            "communication_score": comm_evidence.communication_score,
            "clarity_score": comm_evidence.clarity_score,
            "structure_score": comm_evidence.structure_score,
            "relevance_score": comm_evidence.relevance_score,
            "conciseness_score": comm_evidence.conciseness_score,

            # Speech / fluency
            "fluency_score": speech_features.get("estimated_fluency_score", 70.0),
            "speaking_rate_wpm": speech_features.get("speaking_rate_wpm", 0.0),
            "filler_word_count": speech_features.get("filler_word_count", 0),
            "pause_count": speech_features.get("pause_count", 0),
            "word_count": speech_features.get("word_count", 0),

            # Confidence
            "confidence_estimate": confidence_score,
            "pronunciation_score": 70.0,  # placeholder; STT models may provide this

            # Overall
            "overall_score": overall_score,

            # Qualitative
            "strengths": tech_evidence.strengths,
            "weaknesses": tech_evidence.weaknesses,
            "missing_concepts": tech_evidence.missing_concepts,
            "incorrect_claims": tech_evidence.incorrect_claims,
            "grammar_errors": grammar_evidence.errors,
            "grammar_corrections": grammar_evidence.corrections,
            "structure_feedback": comm_evidence.structure_feedback,

            # Meta
            "evaluator_confidence": tech_evidence.confidence,
            "needs_human_review": tech_evidence.needs_human_review,
            "evaluator_version": "1.0.0",
        }

        logger.info(
            f"Evaluation pipeline complete: overall={overall_score:.1f}, "
            f"technical={technical_score:.1f}, communication={comm_evidence.communication_score:.1f}",
            extra={"workflow": "EvaluationWorkflow", "overall_score": overall_score}
        )
        return result
