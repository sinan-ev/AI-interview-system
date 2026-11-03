"""
Speech-to-Text API.
Section 15-17: Audio upload endpoint for standalone STT transcription.
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import create_api_response, require_active_user
from app.core.exceptions import ValidationException
from app.core.logging import logger
from app.models.user import User
from app.schemas.common import APIResponse

router = APIRouter(prefix="/speech", tags=["Speech & Audio"])


@router.post(
    "/transcribe",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio to text",
)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'en', 'es'). Auto-detected if not specified."),
    current_user: User = Depends(require_active_user),
):
    """
    Transcribe an audio file to text using Whisper STT.
    Supports WebM, OGG, WAV, MP3, MP4, M4A audio formats.
    """
    from app.audio.transcription import validate_audio_file, get_stt_provider

    content_type = audio_file.content_type or ""
    audio_bytes = await audio_file.read()
    file_size = len(audio_bytes)

    validate_audio_file(content_type=content_type, file_size=file_size)

    stt = get_stt_provider()
    if language:
        stt.language = language

    transcript, confidence = await stt.transcribe_bytes(
        audio_bytes=audio_bytes,
        filename=audio_file.filename or "audio.webm",
        content_type=content_type,
    )

    logger.info(
        f"STT transcription completed: {len(transcript)} chars, confidence={confidence:.2f}",
        extra={"user_id": str(current_user.id), "file_size": file_size}
    )

    return create_api_response(
        data={
            "transcript": transcript,
            "confidence": round(confidence, 3),
            "character_count": len(transcript),
            "word_count": len(transcript.split()) if transcript else 0,
            "language_hint": language or "auto-detected",
        },
        message="Audio transcribed successfully.",
    )


@router.post(
    "/analyze",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze speech features from transcript",
)
async def analyze_speech_features(
    transcript: str = Form(..., description="Transcript text to analyze"),
    duration_seconds: float = Form(default=60.0, description="Audio duration in seconds"),
    current_user: User = Depends(require_active_user),
):
    """
    Perform speech feature analysis on a provided transcript.
    Returns fluency score, speaking rate, filler word detection, and confidence estimate.
    """
    from app.ai.agents.communication_analyzer import CommunicationAnalyzerAgent
    from app.ai.llm.provider import get_llm_provider

    if not transcript.strip():
        raise ValidationException("Transcript cannot be empty.")

    llm = get_llm_provider()
    analyzer = CommunicationAnalyzerAgent(llm)

    speech_features = analyzer.analyze_speech_features(
        transcript=transcript,
        duration_seconds=duration_seconds,
    )
    confidence_score = analyzer.estimate_confidence(
        transcript=transcript,
        duration_seconds=duration_seconds,
    )

    return create_api_response(
        data={
            "speech_features": speech_features,
            "confidence_estimate": confidence_score,
            "duration_seconds": duration_seconds,
        },
        message="Speech features analyzed successfully.",
    )
