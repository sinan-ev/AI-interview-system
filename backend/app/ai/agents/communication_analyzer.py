"""
Communication Analyzer Agent.
Section 20-22: Grammar, communication clarity, fluency, and speech analysis.
"""
from typing import List, Optional

from app.ai.llm.base import LLMProvider
from app.ai.prompts.communication_analyzer import (
    COMMUNICATION_ANALYZER_SYSTEM_PROMPT,
    COMMUNICATION_ANALYZER_USER_TEMPLATE,
    GRAMMAR_ANALYZER_SYSTEM_PROMPT,
    GRAMMAR_ANALYZER_USER_TEMPLATE,
)
from app.core.logging import logger
from app.schemas.evaluation import CommunicationEvidence, GrammarEvidence


class CommunicationAnalyzerAgent:
    """
    Agentic evaluator for communication quality, grammar, and language proficiency.
    Implements Section 19 (Grammar), 20 (Communication), 21 (Fluency), 22 (Confidence).
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def analyze_communication(
        self,
        transcript: str,
        question_text: str,
        topic: str,
    ) -> CommunicationEvidence:
        """Evaluate clarity, structure, relevance, conciseness, and overall communication."""
        prompt = COMMUNICATION_ANALYZER_USER_TEMPLATE.format(
            question_text=question_text,
            topic=topic,
            transcript=transcript.strip() if transcript else "[Empty response]",
        )

        evidence: CommunicationEvidence = await self.llm.generate_structured(
            prompt=prompt,
            response_model=CommunicationEvidence,
            system_prompt=COMMUNICATION_ANALYZER_SYSTEM_PROMPT,
            temperature=0.1,
        )

        logger.info(
            f"Communication analysis complete: clarity={evidence.clarity_score:.1f}, "
            f"structure={evidence.structure_score:.1f}, overall={evidence.communication_score:.1f}",
            extra={"agent": "CommunicationAnalyzer", "communication_score": evidence.communication_score},
        )
        return evidence

    async def analyze_grammar(
        self,
        transcript: str,
        language: str = "English",
    ) -> GrammarEvidence:
        """Evaluate grammatical accuracy, identify errors, and provide corrections."""
        prompt = GRAMMAR_ANALYZER_USER_TEMPLATE.format(
            transcript=transcript.strip() if transcript else "[Empty response]",
            language=language,
        )

        evidence: GrammarEvidence = await self.llm.generate_structured(
            prompt=prompt,
            response_model=GrammarEvidence,
            system_prompt=GRAMMAR_ANALYZER_SYSTEM_PROMPT,
            temperature=0.1,
        )

        logger.info(
            f"Grammar analysis complete: score={evidence.grammar_score:.1f}, errors={len(evidence.errors)}",
            extra={"agent": "CommunicationAnalyzer", "grammar_score": evidence.grammar_score},
        )
        return evidence

    def analyze_speech_features(
        self,
        transcript: str,
        duration_seconds: float,
    ) -> dict:
        """
        Rule-based speech feature extraction (no LLM needed).
        Implements Section 21: Fluency, speaking rate, filler words.
        """
        if not transcript or duration_seconds <= 0:
            return {
                "word_count": 0,
                "speaking_rate_wpm": 0.0,
                "filler_word_count": 0,
                "filler_words_found": [],
                "pause_count": 0,
                "estimated_fluency_score": 0.0,
            }

        filler_words = [
            "um", "uh", "er", "ah", "like", "you know", "basically",
            "literally", "actually", "so", "right", "okay", "hmm",
        ]

        words = transcript.lower().split()
        word_count = len(words)
        duration_minutes = duration_seconds / 60.0
        speaking_rate_wpm = round(word_count / duration_minutes, 1) if duration_minutes > 0 else 0.0

        filler_count = 0
        found_fillers = []
        for word in words:
            clean = word.strip(".,?!;:")
            if clean in filler_words:
                filler_count += 1
                found_fillers.append(clean)

        # Pause count: estimated via ellipsis and long punctuation markers
        pause_markers = transcript.count("...") + transcript.count("  ") + transcript.count("—")

        # Fluency score heuristic (penalize excessive fillers and very slow/fast rate)
        filler_penalty = min(filler_count * 2, 40)
        rate_penalty = 0
        if speaking_rate_wpm < 80:
            rate_penalty = 20
        elif speaking_rate_wpm > 180:
            rate_penalty = 10
        fluency_score = max(0.0, 100.0 - filler_penalty - rate_penalty)

        return {
            "word_count": word_count,
            "speaking_rate_wpm": speaking_rate_wpm,
            "filler_word_count": filler_count,
            "filler_words_found": list(set(found_fillers)),
            "pause_count": pause_markers,
            "estimated_fluency_score": round(fluency_score, 1),
        }

    def estimate_confidence(self, transcript: str, duration_seconds: float) -> float:
        """
        Section 22: Heuristic confidence estimate from text features.
        Returns a score between 0.0 and 100.0.
        """
        if not transcript:
            return 0.0

        words = transcript.lower().split()
        hedging_phrases = [
            "i think", "i believe", "maybe", "perhaps", "not sure",
            "i guess", "probably", "i don't know", "i'm not certain", "i'm unsure",
        ]
        text_lower = transcript.lower()
        hedge_count = sum(text_lower.count(phrase) for phrase in hedging_phrases)

        speech_features = self.analyze_speech_features(transcript, duration_seconds)
        filler_count = speech_features.get("filler_word_count", 0)
        word_count = speech_features.get("word_count", 1)

        hedge_penalty = min(hedge_count * 5, 30)
        filler_ratio = filler_count / max(word_count, 1)
        filler_penalty = min(filler_ratio * 100, 30)
        length_bonus = min(word_count / 50 * 10, 10)  # max 10pt bonus for thorough answers

        confidence_score = max(0.0, min(100.0, 70.0 + length_bonus - hedge_penalty - filler_penalty))
        return round(confidence_score, 1)
