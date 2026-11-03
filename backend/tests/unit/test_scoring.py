"""
Unit Tests: Evaluation Scoring Engine.
Section 17, 22, 48: Deterministic score computation.
"""
import pytest

from app.ai.evaluation.scoring import (
    TechnicalWeights,
    OverallWeights,
    calculate_technical_score,
    calculate_overall_score,
    compute_technical_score,
    compute_overall_score,
)
from app.schemas.evaluation import TechnicalEvidence


class TestTechnicalScoring:

    def test_default_weights_produce_expected_score(self):
        score = calculate_technical_score(
            correctness=80.0,
            concept_coverage=70.0,
            completeness=75.0,
            reasoning=65.0,
        )
        # w = (0.40 * 80) + (0.25 * 70) + (0.20 * 75) + (0.15 * 65) = 32+17.5+15+9.75 = 74.25
        assert score == pytest.approx(74.25, abs=0.01)

    def test_perfect_scores(self):
        score = calculate_technical_score(100.0, 100.0, 100.0, 100.0)
        assert score == pytest.approx(100.0, abs=0.01)

    def test_zero_scores(self):
        score = calculate_technical_score(0.0, 0.0, 0.0, 0.0)
        assert score == pytest.approx(0.0, abs=0.01)

    def test_clamping_above_100(self):
        score = calculate_technical_score(110.0, 105.0, 101.0, 100.0)
        assert score <= 100.0

    def test_custom_weights(self):
        weights = TechnicalWeights(correctness=1.0, concept_coverage=0.0, completeness=0.0, reasoning=0.0)
        score = calculate_technical_score(60.0, 0.0, 0.0, 0.0, weights=weights)
        assert score == pytest.approx(60.0, abs=0.01)

    def test_compute_technical_score_from_evidence(self):
        evidence = TechnicalEvidence(
            correctness=90.0,
            concept_coverage=85.0,
            completeness=80.0,
            reasoning=75.0,
            missing_concepts=[],
            incorrect_claims=[],
            strengths=[],
            weaknesses=[],
        )
        score = compute_technical_score(evidence)
        assert 0.0 <= score <= 100.0
        # 0.40*90 + 0.25*85 + 0.20*80 + 0.15*75 = 36+21.25+16+11.25 = 84.5
        assert score == pytest.approx(84.5, abs=0.01)


class TestOverallScoring:

    def test_default_weights_balanced_scores(self):
        score = calculate_overall_score(
            technical_score=80.0,
            communication_score=75.0,
            grammar_score=85.0,
            fluency_score=70.0,
            completeness_score=78.0,
            confidence_estimate=72.0,
        )
        # w: (0.50*80)+(0.15*75)+(0.10*85)+(0.10*70)+(0.10*78)+(0.05*72)
        # = 40 + 11.25 + 8.5 + 7 + 7.8 + 3.6 = 78.15
        assert score == pytest.approx(78.15, abs=0.01)

    def test_overall_perfect_score(self):
        score = calculate_overall_score(100, 100, 100, 100, 100, 100)
        assert score == pytest.approx(100.0, abs=0.01)

    def test_overall_zero_score(self):
        score = calculate_overall_score(0, 0, 0, 0, 0, 0)
        assert score == pytest.approx(0.0, abs=0.01)

    def test_overall_clamping(self):
        score = calculate_overall_score(150, 150, 150, 150, 150, 150)
        assert score <= 100.0

    def test_compute_overall_score_wrapper(self):
        score = compute_overall_score(
            technical_score=80.0,
            grammar_score=70.0,
            communication_score=75.0,
            fluency_score=65.0,
        )
        assert 0.0 <= score <= 100.0

    def test_high_technical_dominates(self):
        """Technical score (weight 0.5) should dominate the overall score."""
        high_tech = calculate_overall_score(
            technical_score=100.0,
            communication_score=0.0,
            grammar_score=0.0,
            fluency_score=0.0,
            completeness_score=0.0,
            confidence_estimate=0.0,
        )
        assert high_tech == pytest.approx(50.0, abs=0.01)


class TestWeightModels:

    def test_technical_weights_sum_to_one(self):
        w = TechnicalWeights()
        total = w.correctness + w.concept_coverage + w.completeness + w.reasoning
        assert total == pytest.approx(1.0, abs=0.01)

    def test_overall_weights_sum_to_one(self):
        w = OverallWeights()
        total = (w.technical + w.communication + w.grammar
                 + w.fluency + w.completeness + w.confidence_estimate)
        assert total == pytest.approx(1.0, abs=0.01)
