"""
Unit Tests: Audio Transcription Module.
Tests for validation, mock transcription, and speech feature detection.
"""
import pytest
from app.audio.transcription import (
    validate_audio_file,
    WhisperTranscriptionProvider,
    ALLOWED_AUDIO_MIME_TYPES,
    MAX_AUDIO_SIZE_BYTES,
)
from app.core.exceptions import ValidationException


class TestAudioValidation:

    def test_valid_webm_passes(self):
        validate_audio_file("audio/webm", 1024 * 1024)  # 1MB

    def test_valid_wav_passes(self):
        validate_audio_file("audio/wav", 5 * 1024 * 1024)  # 5MB

    def test_valid_mp3_passes(self):
        validate_audio_file("audio/mpeg", 2 * 1024 * 1024)

    def test_invalid_mime_type_raises(self):
        with pytest.raises(ValidationException) as exc_info:
            validate_audio_file("application/pdf", 1024)
        assert "Unsupported" in str(exc_info.value)

    def test_file_too_large_raises(self):
        with pytest.raises(ValidationException) as exc_info:
            validate_audio_file("audio/webm", MAX_AUDIO_SIZE_BYTES + 1)
        assert "exceeds" in str(exc_info.value).lower()

    def test_exact_max_size_passes(self):
        validate_audio_file("audio/wav", MAX_AUDIO_SIZE_BYTES)

    def test_all_allowed_types_pass(self):
        for mime_type in ALLOWED_AUDIO_MIME_TYPES:
            validate_audio_file(mime_type, 1024)


class TestWhisperTranscriptionProvider:

    @pytest.fixture
    def mock_provider(self):
        return WhisperTranscriptionProvider(api_key=None)  # No key = mock mode

    @pytest.mark.asyncio
    async def test_transcribe_without_api_key_returns_mock(self, mock_provider):
        audio_bytes = b"\x00" * (50 * 1000)  # 50KB fake audio
        transcript, confidence = await mock_provider.transcribe_bytes(
            audio_bytes=audio_bytes,
            filename="test.webm",
            content_type="audio/webm",
        )
        assert isinstance(transcript, str)
        assert len(transcript) > 0
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_transcribe_small_audio(self, mock_provider):
        audio_bytes = b"\x00" * 100  # 100 bytes
        transcript, confidence = await mock_provider.transcribe_bytes(audio_bytes)
        assert isinstance(transcript, str)
        # Small audio should produce at least minimal transcript
        assert len(transcript) >= 20

    def test_mock_transcription_word_count(self, mock_provider):
        """Mock transcript length should scale with audio size."""
        transcript = mock_provider._mock_transcription(10000)
        words = transcript.split()
        # 10000 bytes / 1000 = 10 words minimum, max(20, 10) = 20
        assert len(words) >= 20

    def test_mock_transcription_large_audio(self, mock_provider):
        """Large audio should produce longer transcript."""
        small = mock_provider._mock_transcription(5000)
        large = mock_provider._mock_transcription(50000)
        # Large should be significantly longer
        assert len(large.split()) > len(small.split())
