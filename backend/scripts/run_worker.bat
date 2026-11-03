@echo off
REM Start Celery Worker for Windows (pool=solo on Windows)
echo Starting Celery Worker...
celery -A app.workers.celery_app.celery worker --loglevel=info --pool=solo -Q evaluation_queue,speech_queue,rag_queue,feedback_queue,celery
