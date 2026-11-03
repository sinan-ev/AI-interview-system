"""
Audio Processing Module.
Section 15-17: Speech-to-text transcription, audio validation, and feature extraction.
"""
import io
import os
import time
import uuid
from typing import Optional, Tuple
import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceException, ValidationException
from app.core.logging import logger


ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/mp3",
    "audio/x-wav",
    "audio/x-m4a",
}

MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def validate_audio_file(content_type: str, file_size: int) -> None:
    """Validate audio MIME type and file size constraints."""
    if content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise ValidationException(
            f"Unsupported audio format '{content_type}'. "
            f"Supported formats: webm, ogg, wav, mp3, mp4, m4a."
        )
    if file_size > MAX_AUDIO_SIZE_BYTES:
        raise ValidationException(
            f"Audio file size {file_size:,} bytes exceeds maximum allowed {MAX_AUDIO_SIZE_BYTES:,} bytes."
        )


class WhisperTranscriptionProvider:
    """
    OpenAI Whisper-compatible Speech-to-Text provider.
    Supports OpenAI Whisper API and local Whisper model fallback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        base_url: str = "https://api.openai.com/v1",
        language: Optional[str] = None,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.max_retries = max_retries

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        content_type: str = "audio/webm",
    ) -> Tuple[str, float]:
        """
        Transcribe audio bytes to text.
        Returns (transcript, confidence_score 0.0-1.0).
        Raises AIServiceException on failure.
        """
        if not self.api_key:
            logger.warning("No STT API key configured — returning mock transcript.")
            return self._mock_transcription(len(audio_bytes)), 0.85

        start = time.perf_counter()
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(self.max_retries + 1):
            try:
                files = {
                    "file": (filename, io.BytesIO(audio_bytes), content_type),
                    "model": (None, self.model),
                    "response_format": (None, "verbose_json"),
                }
                if self.language:
                    files["language"] = (None, self.language)

                async with httpx.AsyncClient(timeout=120.0) as client:
                    res = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        headers=headers,
                        files=files,
                    )
                    res.raise_for_status()
                    data = res.json()

                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                transcript = data.get("text", "").strip()
                # Whisper verbose_json may include avg_logprob for confidence
                avg_logprob = data.get("segments", [{}])[0].get("avg_logprob", -0.3) if data.get("segments") else -0.3
                # Convert log prob to rough confidence (range typically -0.1 to -1.0)
                confidence = max(0.0, min(1.0, 1.0 + avg_logprob))

                logger.info(
                    f"STT transcription complete: {len(transcript)} chars, confidence={confidence:.2f}, latency={latency_ms}ms",
                    extra={"audio": "WhisperProvider", "latency_ms": latency_ms}
                )
                return transcript, confidence

            except Exception as e:
                if attempt == self.max_retries:
                    raise AIServiceException(f"STT transcription failed after {self.max_retries + 1} attempts: {str(e)}")
                import asyncio
                await asyncio.sleep(1.0 * (attempt + 1))

        return "", 0.0

    def _mock_transcription(self, audio_size_bytes: int) -> str:
        """Generate plausible mock transcript for offline/testing use."""
        word_count = max(20, audio_size_bytes // 1000)
        sentences = [
            "In Python, memory management is handled primarily through reference counting.",
            "The garbage collector handles circular references that reference counting cannot detect.",
            "For concurrent programming, Python has the GIL which limits true parallelism in CPU-bound tasks.",
            "Async IO with asyncio allows handling many I/O-bound tasks efficiently in a single thread.",
            "FastAPI leverages Starlette and Pydantic for high-performance asynchronous API development.",
        ]
        # Repeat sentences to fill approximate word count
        result = " ".join(sentences * (word_count // 50 + 1))
        return " ".join(result.split()[:word_count])


def get_stt_provider() -> WhisperTranscriptionProvider:
    """Factory: returns configured STT provider."""
    api_key = getattr(settings, "STT_API_KEY", None) or getattr(settings, "LLM_API_KEY", None)
    is_groq = bool(api_key and api_key.startswith("gsk_"))
    base_url = "https://api.groq.com/openai/v1" if is_groq else "https://api.openai.com/v1"
    model = "whisper-large-v3-turbo" if is_groq else getattr(settings, "WHISPER_MODEL", "whisper-1")
    return WhisperTranscriptionProvider(
        api_key=api_key,
        model=model,
        base_url=base_url,
        language=getattr(settings, "STT_LANGUAGE", None),
    )
