"""
Unit tests for Celery background tasks.
Validates task logic, fallback handling, and task signatures.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.workers.tasks import (
    evaluate_answer_task,
    transcribe_audio_task,
    ingest_document_task,
    generate_feedback_task,
    run_async,
)


def test_run_async_helper():
    async def sample_coro():
        return 42

    result = run_async(sample_coro())
    assert result == 42


def test_task_signatures():
    """Verify all Celery tasks are properly registered with Celery app."""
    assert evaluate_answer_task.name == "app.workers.tasks.evaluate_answer_task"
    assert transcribe_audio_task.name == "app.workers.tasks.transcribe_audio_task"
    assert ingest_document_task.name == "app.workers.tasks.ingest_document_task"
    assert generate_feedback_task.name == "app.workers.tasks.generate_feedback_task"


def test_transcribe_audio_task_missing_file():
    """Ensure missing file triggers task retry."""
    with patch.object(transcribe_audio_task, "retry", side_effect=RuntimeError("Retry called")) as mock_retry:
        with pytest.raises(RuntimeError, match="Retry called"):
            transcribe_audio_task(
                answer_id="non-existent-answer",
                audio_file_path="non/existent/path.wav",
                user_id="user-123",
            )
        assert mock_retry.called
