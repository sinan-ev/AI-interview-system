"""
Evaluation Schemas.
Implements Section 18, 19, 20, 21, 22, 23 specifications.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TechnicalEvidence(BaseModel):
    """Section 18: Structured technical assessment output from LLM."""
    correctness: float = Field(..., ge=0.0, le=100.0, description="Correctness percentage (0-100)")
    concept_coverage: float = Field(..., ge=0.0, le=100.0, description="Concept coverage percentage (0-100)")
    completeness: float = Field(..., ge=0.0, le=100.0, description="Completeness percentage (0-100)")
    reasoning: float = Field(..., ge=0.0, le=100.0, description="Logical reasoning quality (0-100)")
    missing_concepts: List[str] = Field(default_factory=list, description="Expected concepts omitted by candidate")
    incorrect_claims: List[str] = Field(default_factory=list, description="Factual or conceptual errors identified")
    strengths: List[str] = Field(default_factory=list, description="Demonstrated strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified areas for technical growth")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Evaluator certainty score (0-1)")
    needs_human_review: bool = Field(default=False, description="Flagged true if evidence is insufficient or ambiguous")


class GrammarEvidence(BaseModel):
    """Section 19: Grammar assessment output."""
    grammar_score: float = Field(..., ge=0.0, le=100.0)
    errors: List[str] = Field(default_factory=list)
    corrections: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class CommunicationEvidence(BaseModel):
    """Section 20: Communication and clarity assessment output."""
    clarity_score: float = Field(..., ge=0.0, le=100.0)
    structure_score: float = Field(..., ge=0.0, le=100.0)
    relevance_score: float = Field(..., ge=0.0, le=100.0)
    conciseness_score: float = Field(..., ge=0.0, le=100.0)
    communication_score: float = Field(..., ge=0.0, le=100.0)
    structure_feedback: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Full persisted evaluation report for an answer."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    answer_id: str

    # Sub-scores (0-100)
    technical_score: float
    accuracy_score: float
    completeness_score: float
    reasoning_score: float
    grammar_score: float
    communication_score: float
    fluency_score: float
    clarity_score: float
    pronunciation_score: float

    # Speech signals
    confidence_estimate: float
    filler_word_count: int
    pause_count: int
    speaking_rate: float

    # Deterministic overall score
    overall_score: float

    # Qualitative details
    strengths: List[str]
    weaknesses: List[str]
    missing_concepts: List[str]
    feedback: Dict[str, Any]

    # Section 23: Versioning metadata
    evaluator_version: str
    created_at: datetime


class InterviewEvaluationSummary(BaseModel):
    """Aggregate evaluation metrics across an entire interview session."""
    interview_id: str
    total_answers_evaluated: int
    average_technical_score: float
    average_communication_score: float
    average_grammar_score: float
    average_fluency_score: float
    average_confidence_estimate: float
    overall_interview_score: float
    strengths_summary: List[str]
    weaknesses_summary: List[str]
    missing_concepts_summary: List[str]
