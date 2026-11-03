"""
Celery Worker Application.
Section 46: Async background tasks for evaluation, STT, and document ingestion.
"""
from celery import Celery
from app.core.config import settings


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    celery_app = Celery(
        "ai_interview_worker",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_routes={
            "app.workers.tasks.evaluate_answer_task": {"queue": "evaluation"},
            "app.workers.tasks.transcribe_audio_task": {"queue": "transcription"},
            "app.workers.tasks.ingest_document_task": {"queue": "ingestion"},
            "app.workers.tasks.generate_feedback_task": {"queue": "feedback"},
        },
        task_soft_time_limit=120,
        task_time_limit=180,
        result_expires=86400,  # Results expire after 24 hours
        broker_connection_retry_on_startup=False,
        broker_connection_max_retries=1,
    )

    return celery_app


celery_app = create_celery_app()
