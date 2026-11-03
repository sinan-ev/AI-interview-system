"""
Deterministic Scoring Engine & Rubric Calculation.
Section 17, 22, 48:
- Strictly separate LLM evidence extraction from score calculation.
- LLM -> Structured evaluation evidence -> Validation -> Deterministic scoring engine -> Final score.
- Configurable weights for technical and overall composite scores.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TechnicalWeights(BaseModel):
    correctness: float = 0.40
    concept_coverage: float = 0.25
    completeness: float = 0.20
    reasoning: float = 0.15


class OverallWeights(BaseModel):
    technical: float = 0.50
    communication: float = 0.15
    grammar: float = 0.10
    fluency: float = 0.10
    completeness: float = 0.10
    confidence_estimate: float = 0.05


def calculate_technical_score(
    correctness: float,
    concept_coverage: float,
    completeness: float,
    reasoning: float,
    weights: Optional[TechnicalWeights] = None,
) -> float:
    """
    Deterministic calculation of technical score based on sub-metric evidence.
    Clamped strictly between 0.0 and 100.0.
    """
    w = weights or TechnicalWeights()
    raw = (
        (correctness * w.correctness)
        + (concept_coverage * w.concept_coverage)
        + (completeness * w.completeness)
        + (reasoning * w.reasoning)
    )
    return round(max(0.0, min(100.0, raw)), 2)


def calculate_overall_score(
    technical_score: float,
    communication_score: float,
    grammar_score: float,
    fluency_score: float,
    completeness_score: float,
    confidence_estimate: float,
    weights: Optional[OverallWeights] = None,
) -> float:
    """
    Section 22 & 48:
    Calculates deterministic composite score across all evaluated dimensions.
    """
    w = weights or OverallWeights()
    raw = (
        (technical_score * w.technical)
        + (communication_score * w.communication)
        + (grammar_score * w.grammar)
        + (fluency_score * w.fluency)
        + (completeness_score * w.completeness)
        + (confidence_estimate * w.confidence_estimate)
    )
    return round(max(0.0, min(100.0, raw)), 2)


# ---------------------------------------------------------------------------
# Convenience wrappers used by EvaluationWorkflow
# ---------------------------------------------------------------------------

def compute_technical_score(tech_evidence) -> float:
    """Compute technical score from a TechnicalEvidence object."""
    return calculate_technical_score(
        correctness=tech_evidence.correctness,
        concept_coverage=tech_evidence.concept_coverage,
        completeness=tech_evidence.completeness,
        reasoning=tech_evidence.reasoning,
    )


def compute_overall_score(
    technical_score: float,
    grammar_score: float,
    communication_score: float,
    fluency_score: float,
    completeness_score: float = 75.0,
    confidence_estimate: float = 70.0,
) -> float:
    """Compute overall score given all sub-dimension scores."""
    return calculate_overall_score(
        technical_score=technical_score,
        communication_score=communication_score,
        grammar_score=grammar_score,
        fluency_score=fluency_score,
        completeness_score=completeness_score,
        confidence_estimate=confidence_estimate,
    )
