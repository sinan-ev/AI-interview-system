"""
Integration Tests: Full Evaluation Workflow.
End-to-end test of the evaluation pipeline with Mock LLM.
"""
import pytest
from app.ai.agents.answer_evaluator import AnswerEvaluatorAgent
from app.ai.agents.communication_analyzer import CommunicationAnalyzerAgent
from app.ai.llm.provider import MockLLMProvider
from app.ai.workflows.evaluation_workflow import EvaluationWorkflow


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def evaluation_workflow(mock_llm):
    return EvaluationWorkflow(
        answer_evaluator=AnswerEvaluatorAgent(mock_llm),
        communication_analyzer=CommunicationAnalyzerAgent(mock_llm),
    )


class TestEvaluationWorkflow:

    @pytest.mark.asyncio
    async def test_full_workflow_returns_complete_result(self, evaluation_workflow):
        """Test the complete evaluation pipeline produces all required fields."""
        result = await evaluation_workflow.run(
            question_text="Explain Python's GIL and how asyncio addresses concurrency limitations.",
            topic="Python",
            difficulty="intermediate",
            expected_concepts=["GIL", "asyncio", "threading", "event loop"],
            evaluation_rubric={
                "accuracy_criteria": "Must correctly describe GIL and asyncio",
                "concept_coverage_weight": 0.35,
                "completeness_weight": 0.35,
                "reasoning_weight": 0.30,
            },
            transcript=(
                "The GIL is a mutex in CPython that prevents multiple threads from executing Python "
                "bytecode simultaneously. For I/O-bound tasks, asyncio uses an event loop to handle "
                "concurrency without the overhead of thread switching, working effectively within GIL constraints."
            ),
            duration_seconds=45.0,
        )

        # Verify all required score fields are present
        required_score_fields = [
            "technical_score", "accuracy_score", "completeness_score", "reasoning_score",
            "grammar_score", "communication_score", "fluency_score", "clarity_score",
            "overall_score", "confidence_estimate",
        ]
        for field in required_score_fields:
            assert field in result, f"Missing field: {field}"
            assert isinstance(result[field], float), f"{field} should be float"
            assert 0.0 <= result[field] <= 100.0, f"{field} out of range: {result[field]}"

        # Verify speech metrics
        assert "speaking_rate_wpm" in result
        assert "filler_word_count" in result
        assert "word_count" in result
        assert result["word_count"] > 0

        # Verify qualitative fields
        assert isinstance(result["strengths"], list)
        assert isinstance(result["weaknesses"], list)
        assert isinstance(result["missing_concepts"], list)

        # Verify evaluator metadata
        assert result["evaluator_version"] == "1.0.0"
        assert isinstance(result["needs_human_review"], bool)

    @pytest.mark.asyncio
    async def test_workflow_with_empty_transcript(self, evaluation_workflow):
        """Empty transcript should still complete without errors."""
        result = await evaluation_workflow.run(
            question_text="What is polymorphism?",
            topic="OOP",
            difficulty="easy",
            expected_concepts=["polymorphism", "inheritance"],
            evaluation_rubric={},
            transcript="",
            duration_seconds=0.0,
        )
        assert result is not None
        assert result["word_count"] == 0
        assert result["speaking_rate_wpm"] == 0.0
        assert result["overall_score"] >= 0.0

    @pytest.mark.asyncio
    async def test_workflow_parallel_execution(self, evaluation_workflow):
        """Verify workflow completes in reasonable time (parallelism test)."""
        import time
        start = time.time()

        await evaluation_workflow.run(
            question_text="Explain CAP theorem.",
            topic="System Design",
            difficulty="hard",
            expected_concepts=["Consistency", "Availability", "Partition Tolerance"],
            evaluation_rubric={"accuracy_criteria": "Must explain trade-offs"},
            transcript="CAP theorem states that distributed systems can only guarantee two of the three: Consistency, Availability, Partition Tolerance.",
            duration_seconds=30.0,
        )

        elapsed = time.time() - start
        # With mock LLM, should complete in under 5 seconds
        assert elapsed < 5.0, f"Evaluation took too long: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_workflow_score_clamping(self, evaluation_workflow):
        """All scores must be in [0, 100] range regardless of inputs."""
        result = await evaluation_workflow.run(
            question_text="Test question",
            topic="Test",
            difficulty="easy",
            expected_concepts=[],
            evaluation_rubric={},
            transcript="Short answer.",
            duration_seconds=5.0,
        )
        for key in ["technical_score", "grammar_score", "communication_score",
                    "fluency_score", "overall_score", "confidence_estimate"]:
            assert 0.0 <= result[key] <= 100.0, f"{key}={result[key]} out of range"


class TestQuestionGenerationWorkflow:

    @pytest.fixture
    def question_workflow(self, mock_llm):
        from app.ai.agents.interview_manager import InterviewManagerAgent
        from app.ai.agents.question_generator import QuestionGeneratorAgent
        from app.ai.workflows.question_workflow import QuestionGenerationWorkflow
        return QuestionGenerationWorkflow(
            interview_manager=InterviewManagerAgent(mock_llm),
            question_generator=QuestionGeneratorAgent(mock_llm),
        )

    @pytest.mark.asyncio
    async def test_initial_question_generation(self, question_workflow):
        result = await question_workflow.generate_next_question(
            interview_id="test-interview-001",
            role="Software Engineer",
            interview_type="technical",
            topics=["Python", "FastAPI"],
            current_topic="Python",
            difficulty="intermediate",
            questions_answered=0,
            total_questions=5,
            previous_questions=[],
        )
        assert result["action"] != "complete"
        assert result["question"] is not None
        assert result["question"].question
        assert result["effective_topic"]

    @pytest.mark.asyncio
    async def test_quota_reached_returns_complete(self, question_workflow):
        result = await question_workflow.generate_next_question(
            interview_id="test-interview-002",
            role="Software Engineer",
            interview_type="technical",
            topics=["Python"],
            current_topic="Python",
            difficulty="intermediate",
            questions_answered=5,
            total_questions=5,
            previous_questions=["Q1", "Q2", "Q3", "Q4", "Q5"],
        )
        assert result["action"] == "complete"
        assert result["question"] is None
