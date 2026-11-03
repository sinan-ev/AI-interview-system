"""
Celery Background Tasks.
Section 46: Async tasks for heavy AI workloads: evaluation, transcription, ingestion, feedback.
"""
import asyncio
from typing import Any, Dict, List, Optional

from app.workers.celery_app import celery_app
from app.core.logging import logger
from app.core.database import AsyncSessionLocal


def run_async(coroutine):
    """Run an async coroutine from within a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.workers.tasks.evaluate_answer_task",
    max_retries=3,
    default_retry_delay=5,
)
def evaluate_answer_task(
    self,
    answer_id: str,
    question_text: str,
    topic: str,
    difficulty: str,
    expected_concepts: List[str],
    evaluation_rubric: Dict[str, Any],
    transcript: str,
    duration_seconds: float = 0.0,
) -> Dict[str, Any]:
    """
    Background task: Run full multi-agent evaluation pipeline for an answer.
    Persists results to the evaluations table.
    """
    try:
        logger.info(f"[Task] Starting evaluation for answer_id={answer_id}")

        async def _evaluate():
            from app.ai.agents.answer_evaluator import AnswerEvaluatorAgent
            from app.ai.agents.communication_analyzer import CommunicationAnalyzerAgent
            from app.ai.llm.provider import get_llm_provider
            from app.ai.workflows.evaluation_workflow import EvaluationWorkflow
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            llm = get_llm_provider()
            workflow = EvaluationWorkflow(
                answer_evaluator=AnswerEvaluatorAgent(llm),
                communication_analyzer=CommunicationAnalyzerAgent(llm),
            )

            result = await workflow.run(
                question_text=question_text,
                topic=topic,
                difficulty=difficulty,
                expected_concepts=expected_concepts,
                evaluation_rubric=evaluation_rubric,
                transcript=transcript,
                duration_seconds=duration_seconds,
            )

            # Persist evaluation to database
            async with AsyncSessionLocal() as db:
                import uuid
                from datetime import datetime, timezone

                eval_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)

                await db.execute(
                    text("""
                        INSERT INTO evaluations (
                            id, answer_id,
                            technical_score, accuracy_score, completeness_score, reasoning_score,
                            grammar_score, communication_score, fluency_score, clarity_score,
                            pronunciation_score, confidence_estimate,
                            filler_word_count, pause_count, speaking_rate,
                            overall_score, strengths, weaknesses, missing_concepts, feedback,
                            evaluator_version, created_at, updated_at
                        ) VALUES (
                            :id, :answer_id,
                            :technical_score, :accuracy_score, :completeness_score, :reasoning_score,
                            :grammar_score, :communication_score, :fluency_score, :clarity_score,
                            :pronunciation_score, :confidence_estimate,
                            :filler_word_count, :pause_count, :speaking_rate,
                            :overall_score, :strengths, :weaknesses, :missing_concepts, :feedback,
                            :evaluator_version, :created_at, :updated_at
                        )
                    """),
                    {
                        "id": eval_id,
                        "answer_id": answer_id,
                        "technical_score": result["technical_score"],
                        "accuracy_score": result["accuracy_score"],
                        "completeness_score": result["completeness_score"],
                        "reasoning_score": result["reasoning_score"],
                        "grammar_score": result["grammar_score"],
                        "communication_score": result["communication_score"],
                        "fluency_score": result["fluency_score"],
                        "clarity_score": result["clarity_score"],
                        "pronunciation_score": result.get("pronunciation_score", 70.0),
                        "confidence_estimate": result["confidence_estimate"],
                        "filler_word_count": result["filler_word_count"],
                        "pause_count": result["pause_count"],
                        "speaking_rate": result["speaking_rate_wpm"],
                        "overall_score": result["overall_score"],
                        "strengths": result["strengths"],
                        "weaknesses": result["weaknesses"],
                        "missing_concepts": result["missing_concepts"],
                        "feedback": {
                            "grammar_errors": result["grammar_errors"],
                            "grammar_corrections": result["grammar_corrections"],
                            "structure_feedback": result["structure_feedback"],
                            "incorrect_claims": result["incorrect_claims"],
                        },
                        "evaluator_version": result["evaluator_version"],
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                await db.commit()

            return {"status": "completed", "answer_id": answer_id, "overall_score": result["overall_score"]}

        return run_async(_evaluate())

    except Exception as exc:
        logger.error(f"[Task] Evaluation failed for answer_id={answer_id}: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.transcribe_audio_task",
    max_retries=2,
    default_retry_delay=3,
)
def transcribe_audio_task(
    self,
    answer_id: str,
    audio_file_path: str,
    content_type: str = "audio/webm",
    duration_seconds: float = 0.0,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background task: Transcribe audio file using Whisper STT provider.
    Updates the answer record with the transcript and queues evaluation.
    """
    try:
        logger.info(f"[Task] Starting STT transcription for answer_id={answer_id}")

        async def _transcribe():
            from app.audio.transcription import get_stt_provider
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            import os

            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

            with open(audio_file_path, "rb") as f:
                audio_bytes = f.read()

            stt = get_stt_provider()
            filename = os.path.basename(audio_file_path)
            transcript, confidence = await stt.transcribe_bytes(
                audio_bytes=audio_bytes,
                filename=filename,
                content_type=content_type,
            )

            # Update answer with transcript
            async with AsyncSessionLocal() as db:
                from datetime import datetime, timezone
                await db.execute(
                    text("""
                        UPDATE answers SET
                            transcript = :transcript,
                            text_answer = COALESCE(text_answer, :transcript),
                            updated_at = :now
                        WHERE id = :answer_id
                    """),
                    {
                        "transcript": transcript,
                        "answer_id": answer_id,
                        "now": datetime.now(timezone.utc),
                    }
                )
                await db.commit()

            return {
                "status": "transcribed",
                "answer_id": answer_id,
                "transcript_length": len(transcript),
                "confidence": confidence,
            }

        return run_async(_transcribe())

    except Exception as exc:
        logger.error(f"[Task] STT transcription failed for answer_id={answer_id}: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingest_document_task",
    max_retries=2,
    default_retry_delay=5,
)
def ingest_document_task(
    self,
    document_id: str,
    file_path: str,
    content_type: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Background task: Extract, chunk, embed, and store a user-uploaded document.
    """
    try:
        logger.info(f"[Task] Starting document ingestion for document_id={document_id}")

        async def _ingest():
            from app.ai.embeddings.provider import get_embedding_provider
            from app.core.database import AsyncSessionLocal
            from app.rag.document_processor import DocumentProcessor
            from app.rag.rag_service import RAGService
            from app.rag.vector_store import VectorStore
            import os
            from io import BytesIO
            from fastapi import UploadFile

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document file not found: {file_path}")

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            async with AsyncSessionLocal() as db:
                embedding_provider = get_embedding_provider()
                vector_store = VectorStore(db)
                rag_service = RAGService(
                    embedding_provider=embedding_provider,
                    vector_store=vector_store,
                )

                # Process using processor directly (avoid UploadFile dependency)
                processor = DocumentProcessor()
                if content_type == "application/pdf":
                    text = processor.extract_text_from_pdf(file_bytes)
                elif "word" in content_type:
                    text = processor.extract_text_from_docx(file_bytes)
                elif "presentation" in content_type:
                    text = processor.extract_text_from_pptx(file_bytes)
                else:
                    text = file_bytes.decode("utf-8", errors="replace")

                chunks = processor.chunk_text(text, document_id)
                texts = [c.text for c in chunks]
                embeddings = await embedding_provider.embed_batch(texts)

                for chunk, embedding in zip(chunks, embeddings):
                    await vector_store.upsert_chunk_embedding(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        text=chunk.text,
                        chunk_index=chunk.chunk_index,
                        embedding=embedding,
                        user_id=user_id,
                    )

                # Update document status to 'ready'
                from sqlalchemy import text as sql_text
                from datetime import datetime, timezone
                await db.execute(
                    sql_text("UPDATE documents SET status='ready', chunk_count=:count, updated_at=:now WHERE id=:doc_id"),
                    {"count": len(chunks), "now": datetime.now(timezone.utc), "doc_id": document_id}
                )
                await db.commit()

            return {"status": "ready", "document_id": document_id, "chunks": len(chunks)}

        return run_async(_ingest())

    except Exception as exc:
        logger.error(f"[Task] Document ingestion failed for document_id={document_id}: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.generate_feedback_task",
    max_retries=2,
    default_retry_delay=3,
)
def generate_feedback_task(self, interview_id: str, user_id: str) -> Dict[str, Any]:
    """
    Background task: Generate comprehensive interview feedback and learning recommendations.
    """
    try:
        logger.info(f"[Task] Generating feedback for interview_id={interview_id}")

        async def _generate_feedback():
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text as sql_text
            from datetime import datetime, timezone
            import uuid

            async with AsyncSessionLocal() as db:
                # Fetch all evaluations for this interview
                evals_result = await db.execute(
                    sql_text("""
                        SELECT e.* FROM evaluations e
                        JOIN answers a ON e.answer_id = a.id
                        JOIN interview_questions iq ON a.question_id = iq.id
                        WHERE iq.interview_id = :interview_id
                    """),
                    {"interview_id": interview_id}
                )
                evaluations = evals_result.fetchall()

                if not evaluations:
                    return {"status": "no_evaluations", "interview_id": interview_id}

                total = len(evaluations)
                avg_overall = sum(e.overall_score for e in evaluations) / total

                # Insert one summary feedback row
                now = datetime.now(timezone.utc)
                await db.execute(
                    sql_text("""
                        INSERT INTO feedback (id, interview_id, category, severity, feedback_text, created_at)
                        VALUES (:id, :interview_id, :category, :severity, :feedback_text, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "interview_id": interview_id,
                        "category": "overall",
                        "severity": "info",
                        "feedback_text": f"Interview completed. Overall score: {round(avg_overall, 2)}. Questions evaluated: {total}.",
                        "now": now,
                    }
                )
                await db.commit()

            return {
                "status": "completed",
                "interview_id": interview_id,
                "overall_score": round(avg_overall, 2),
                "questions_evaluated": total,
            }

        return run_async(_generate_feedback())

    except Exception as exc:
        logger.error(f"[Task] Feedback generation failed for interview_id={interview_id}: {str(exc)}")
        raise self.retry(exc=exc)
