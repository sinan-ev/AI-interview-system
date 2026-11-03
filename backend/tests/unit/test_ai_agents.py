"""
Unit Tests: AI Agents.
Tests for QuestionGeneratorAgent, AnswerEvaluatorAgent, CommunicationAnalyzerAgent,
InterviewManagerAgent with Mock LLM provider.
"""
import pytest

from app.ai.agents.answer_evaluator import AnswerEvaluatorAgent
from app.ai.agents.communication_analyzer import CommunicationAnalyzerAgent
from app.ai.agents.interview_manager import InterviewManagerAgent
from app.ai.agents.question_generator import QuestionGeneratorAgent
from app.ai.llm.provider import MockLLMProvider
from app.schemas.question import ManagerAction


@pytest.fixture
def llm():
    return MockLLMProvider()


@pytest.fixture
def question_generator(llm):
    return QuestionGeneratorAgent(llm)


@pytest.fixture
def answer_evaluator(llm):
    return AnswerEvaluatorAgent(llm)


@pytest.fixture
def communication_analyzer(llm):
    return CommunicationAnalyzerAgent(llm)


@pytest.fixture
def interview_manager(llm):
    return InterviewManagerAgent(llm)


# ─────────────────────────────────────────────────────────────────────────────
# QuestionGeneratorAgent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestQuestionGeneratorAgent:

    @pytest.mark.asyncio
    async def test_generate_question_returns_generated_question(self, question_generator):
        result = await question_generator.generate_question(
            role="Software Engineer",
            topic="Python",
            difficulty="intermediate",
            interview_type="technical",
        )
        assert result is not None
        assert result.question
        assert len(result.question) > 10
        assert result.topic
        assert result.difficulty in ("easy", "intermediate", "hard", "beginner", "advanced")
        assert isinstance(result.expected_concepts, list)
        assert isinstance(result.evaluation_rubric, dict)

    @pytest.mark.asyncio
    async def test_generate_question_deduplication(self, question_generator):
        """Same previous question text should trigger retry (mock always produces unique)."""
        # With mock, deduplication check logic still runs without error
        prev_qs = ["Explain Python memory management."]
        result = await question_generator.generate_question(
            role="Backend Engineer",
            topic="Python",
            difficulty="intermediate",
            previous_questions=prev_qs,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_followup_question(self, question_generator):
        result = await question_generator.generate_question(
            role="Data Scientist",
            topic="Machine Learning",
            difficulty="hard",
            is_follow_up=True,
            follow_up_guidance="Probe deeper on regularization techniques.",
        )
        assert result is not None
        assert result.question

    @pytest.mark.asyncio
    async def test_generate_question_with_rag_context(self, question_generator):
        rag_ctx = "Transformers use self-attention mechanisms with key, query, value matrices."
        result = await question_generator.generate_question(
            role="ML Engineer",
            topic="Machine Learning",
            difficulty="hard",
            rag_context=rag_ctx,
        )
        assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# AnswerEvaluatorAgent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAnswerEvaluatorAgent:

    @pytest.mark.asyncio
    async def test_evaluate_answer_returns_technical_evidence(self, answer_evaluator):
        result = await answer_evaluator.evaluate_answer(
            question_text="Explain Python's GIL and its impact on concurrency.",
            topic="Python",
            difficulty="intermediate",
            expected_concepts=["GIL", "threading", "multiprocessing", "async"],
            evaluation_rubric={
                "accuracy_criteria": "Must describe GIL correctly",
                "concept_coverage_weight": 0.35,
                "completeness_weight": 0.35,
                "reasoning_weight": 0.30,
            },
            candidate_answer="The GIL prevents multiple threads from executing Python bytecode simultaneously.",
        )
        assert result is not None
        assert 0.0 <= result.correctness <= 100.0
        assert 0.0 <= result.concept_coverage <= 100.0
        assert 0.0 <= result.completeness <= 100.0
        assert 0.0 <= result.reasoning <= 100.0
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)
        assert isinstance(result.missing_concepts, list)

    @pytest.mark.asyncio
    async def test_evaluate_empty_answer(self, answer_evaluator):
        result = await answer_evaluator.evaluate_answer(
            question_text="What is polymorphism?",
            topic="OOP",
            difficulty="easy",
            expected_concepts=["polymorphism", "inheritance", "method overriding"],
            evaluation_rubric={},
            candidate_answer="",  # Empty answer
        )
        # Should still return a valid TechnicalEvidence (mock handles this)
        assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# CommunicationAnalyzerAgent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCommunicationAnalyzerAgent:

    @pytest.mark.asyncio
    async def test_analyze_communication_returns_evidence(self, communication_analyzer):
        result = await communication_analyzer.analyze_communication(
            transcript="I believe the answer involves memory management and GIL in Python.",
            question_text="Explain Python concurrency.",
            topic="Python",
        )
        assert result is not None
        assert 0.0 <= result.clarity_score <= 100.0
        assert 0.0 <= result.structure_score <= 100.0
        assert 0.0 <= result.relevance_score <= 100.0
        assert 0.0 <= result.conciseness_score <= 100.0
        assert 0.0 <= result.communication_score <= 100.0

    @pytest.mark.asyncio
    async def test_analyze_grammar_returns_evidence(self, communication_analyzer):
        result = await communication_analyzer.analyze_grammar(
            transcript="The memory is manage by reference counting in Python.",
            language="English",
        )
        assert result is not None
        assert 0.0 <= result.grammar_score <= 100.0
        assert isinstance(result.errors, list)
        assert isinstance(result.corrections, list)

    def test_analyze_speech_features_normal_speech(self, communication_analyzer):
        transcript = "I think Python is great for data science because it has many libraries."
        result = communication_analyzer.analyze_speech_features(
            transcript=transcript,
            duration_seconds=30.0,
        )
        assert result["word_count"] == 13
        assert result["speaking_rate_wpm"] > 0
        assert isinstance(result["filler_word_count"], int)
        assert 0.0 <= result["estimated_fluency_score"] <= 100.0

    def test_analyze_speech_features_empty_transcript(self, communication_analyzer):
        result = communication_analyzer.analyze_speech_features(
            transcript="",
            duration_seconds=0.0,
        )
        assert result["word_count"] == 0
        assert result["speaking_rate_wpm"] == 0.0
        assert result["estimated_fluency_score"] == 0.0

    def test_analyze_speech_features_filler_detection(self, communication_analyzer):
        transcript = "Um, I think, uh, like, you know, basically the GIL is um a lock."
        result = communication_analyzer.analyze_speech_features(
            transcript=transcript,
            duration_seconds=15.0,
        )
        assert result["filler_word_count"] >= 4  # um, uh, like, basically

    def test_estimate_confidence_high(self, communication_analyzer):
        transcript = "The GIL is a mutex that protects Python objects. It prevents CPU-bound multi-threading."
        score = communication_analyzer.estimate_confidence(transcript, 30.0)
        assert 0.0 <= score <= 100.0
        assert score > 50.0  # confident, no hedging

    def test_estimate_confidence_low_hedging(self, communication_analyzer):
        transcript = "I think maybe it is probably related to memory, I'm not sure though, perhaps garbage collection."
        score = communication_analyzer.estimate_confidence(transcript, 20.0)
        # Heavy hedging should reduce confidence
        assert score < 80.0


# ─────────────────────────────────────────────────────────────────────────────
# InterviewManagerAgent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestInterviewManagerAgent:

    @pytest.mark.asyncio
    async def test_initial_question_decision(self, interview_manager):
        """First question should be deterministic GENERATE_NEW_QUESTION."""
        result = await interview_manager.decide_next_action(
            role="Software Engineer",
            interview_type="technical",
            topics=["Python", "FastAPI"],
            current_topic="Python",
            difficulty="intermediate",
            questions_answered=0,
            total_questions=5,
            previous_questions=[],
        )
        assert result.action == ManagerAction.GENERATE_NEW_QUESTION
        assert result.topic == "Python"

    @pytest.mark.asyncio
    async def test_quota_reached_completes_interview(self, interview_manager):
        """When questions_answered >= total_questions, must return COMPLETE."""
        result = await interview_manager.decide_next_action(
            role="Software Engineer",
            interview_type="technical",
            topics=["Python"],
            current_topic="Python",
            difficulty="intermediate",
            questions_answered=5,
            total_questions=5,
            previous_questions=["Q1", "Q2", "Q3", "Q4", "Q5"],
        )
        assert result.action == ManagerAction.COMPLETE_INTERVIEW

    @pytest.mark.asyncio
    async def test_mid_interview_decision(self, interview_manager):
        """Mid-interview should return a valid manager action via LLM."""
        result = await interview_manager.decide_next_action(
            role="Data Scientist",
            interview_type="technical",
            topics=["Python", "Machine Learning"],
            current_topic="Python",
            difficulty="intermediate",
            questions_answered=2,
            total_questions=10,
            previous_questions=["Q1: Explain GIL", "Q2: What is a decorator?"],
            last_score=72.0,
            last_feedback="Good but could provide concrete examples.",
        )
        assert result.action in list(ManagerAction)
        assert result.topic
