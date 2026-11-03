#!/bin/bash
set -e

echo "Starting Celery Worker for background tasks..."
exec celery -A app.workers.celery_app.celery worker \
  --loglevel=info \
  --concurrency=4 \
  -Q evaluation_queue,speech_queue,rag_queue,feedback_queue,celery
