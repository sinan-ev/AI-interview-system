"""
Feedback & Learning Recommendations API.
Section 23-26: Interview feedback, performance reports, weak-topic detection, and learning recommendations.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import create_api_response, require_active_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.common import APIResponse

router = APIRouter(prefix="/feedback", tags=["Feedback & Analytics"])


@router.get(
    "/interview/{interview_id}",
    response_model=APIResponse,
    summary="Get comprehensive feedback for an interview",
)
async def get_interview_feedback(
    interview_id: str,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve comprehensive evaluation feedback for a completed interview.
    If feedback is not yet generated, triggers background generation.
    """
    from sqlalchemy import text

    # Verify interview ownership
    int_result = await db.execute(
        text("SELECT id, user_id, status FROM interviews WHERE id = :interview_id"),
        {"interview_id": interview_id}
    )
    interview = int_result.fetchone()
    if not interview:
        raise NotFoundException(f"Interview '{interview_id}' not found.")

    from app.core.exceptions import AuthorizationException
    if str(interview.user_id) != str(current_user.id) and current_user.role != "admin":
        raise AuthorizationException("Not authorized to access this interview's feedback.")

    # Fetch existing feedback
    fb_result = await db.execute(
        text("SELECT * FROM feedback WHERE interview_id = :interview_id"),
        {"interview_id": interview_id}
    )
    feedback = fb_result.fetchone()

    if not feedback:
        # Trigger background feedback generation
        try:
            from app.workers.tasks import generate_feedback_task
            generate_feedback_task.delay(
                interview_id=interview_id,
                user_id=str(current_user.id),
            )
            return create_api_response(
                data={"status": "generating", "interview_id": interview_id},
                message="Feedback is being generated. Please check back shortly.",
            )
        except Exception:
            raise NotFoundException("Feedback not yet available for this interview.")

    return create_api_response(
        data={
            "interview_id": interview_id,
            "overall_score": feedback.overall_interview_score,
            "average_technical_score": feedback.average_technical_score,
            "average_communication_score": feedback.average_communication_score,
            "average_grammar_score": feedback.average_grammar_score,
            "average_fluency_score": feedback.average_fluency_score,
            "average_confidence_score": feedback.average_confidence_score,
            "total_questions_evaluated": feedback.total_questions_evaluated,
            "strengths_summary": feedback.strengths_summary or [],
            "weaknesses_summary": feedback.weaknesses_summary or [],
            "missing_concepts_summary": feedback.missing_concepts_summary or [],
            "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
        },
        message="Interview feedback retrieved successfully.",
    )


@router.get(
    "/answer/{answer_id}",
    response_model=APIResponse,
    summary="Get evaluation details for a specific answer",
)
async def get_answer_evaluation(
    answer_id: str,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed multi-dimensional evaluation for a specific answer."""
    from sqlalchemy import text

    # Verify ownership via join
    eval_result = await db.execute(
        text("""
            SELECT e.*, a.user_id
            FROM evaluations e
            JOIN answers a ON e.answer_id = a.id
            WHERE e.answer_id = :answer_id
        """),
        {"answer_id": answer_id}
    )
    evaluation = eval_result.fetchone()

    if not evaluation:
        raise NotFoundException(f"Evaluation for answer '{answer_id}' not found.")

    from app.core.exceptions import AuthorizationException
    if str(evaluation.user_id) != str(current_user.id) and current_user.role != "admin":
        raise AuthorizationException("Not authorized to access this evaluation.")

    return create_api_response(
        data={
            "evaluation_id": str(evaluation.id),
            "answer_id": answer_id,
            "scores": {
                "technical": evaluation.technical_score,
                "accuracy": evaluation.accuracy_score,
                "completeness": evaluation.completeness_score,
                "reasoning": evaluation.reasoning_score,
                "grammar": evaluation.grammar_score,
                "communication": evaluation.communication_score,
                "fluency": evaluation.fluency_score,
                "clarity": evaluation.clarity_score,
                "confidence": evaluation.confidence_estimate,
                "overall": evaluation.overall_score,
            },
            "speech_metrics": {
                "filler_word_count": evaluation.filler_word_count,
                "pause_count": evaluation.pause_count,
                "speaking_rate_wpm": evaluation.speaking_rate,
            },
            "qualitative": {
                "strengths": evaluation.strengths or [],
                "weaknesses": evaluation.weaknesses or [],
                "missing_concepts": evaluation.missing_concepts or [],
                "feedback": evaluation.feedback or {},
            },
            "meta": {
                "evaluator_version": evaluation.evaluator_version,
                "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
            }
        },
        message="Answer evaluation retrieved successfully.",
    )


@router.get(
    "/profile/{user_id}",
    response_model=APIResponse,
    summary="Get user performance profile and learning recommendations",
)
async def get_user_performance_profile(
    user_id: str,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Section 24-26: Retrieve aggregated performance profile with weak-topic detection
    and personalized learning recommendations.
    """
    from sqlalchemy import text
    from app.core.exceptions import AuthorizationException

    if user_id != str(current_user.id) and current_user.role != "admin":
        raise AuthorizationException("Not authorized to view this profile.")

    # Aggregate scores across all interviews
    agg_result = await db.execute(
        text("""
            SELECT
                COUNT(DISTINCT i.id) as total_interviews,
                COUNT(DISTINCT e.id) as total_evaluations,
                AVG(e.technical_score) as avg_technical,
                AVG(e.communication_score) as avg_communication,
                AVG(e.grammar_score) as avg_grammar,
                AVG(e.fluency_score) as avg_fluency,
                AVG(e.confidence_estimate) as avg_confidence,
                AVG(e.overall_score) as avg_overall
            FROM interviews i
            JOIN interview_questions iq ON iq.interview_id = i.id
            JOIN answers a ON a.question_id = iq.id
            JOIN evaluations e ON e.answer_id = a.id
            WHERE i.user_id = :user_id
        """),
        {"user_id": user_id}
    )
    agg = agg_result.fetchone()

    # Topic-level breakdown
    topic_result = await db.execute(
        text("""
            SELECT
                iq.topic,
                COUNT(*) as question_count,
                AVG(e.technical_score) as avg_score,
                AVG(e.overall_score) as avg_overall
            FROM interview_questions iq
            JOIN interviews i ON i.id = iq.interview_id
            JOIN answers a ON a.question_id = iq.id
            JOIN evaluations e ON e.answer_id = a.id
            WHERE i.user_id = :user_id
            GROUP BY iq.topic
            ORDER BY avg_score ASC
        """),
        {"user_id": user_id}
    )
    topics = topic_result.fetchall()

    topic_breakdown = [
        {
            "topic": t.topic,
            "question_count": t.question_count,
            "average_score": round(float(t.avg_score or 0), 2),
            "average_overall": round(float(t.avg_overall or 0), 2),
        }
        for t in topics
    ]

    # Weak topics: bottom 3 by average score
    weak_topics = [t for t in topic_breakdown if t["average_score"] < 70.0][:3]

    # Learning recommendations based on weak topics
    recommendations = _generate_recommendations(weak_topics)

    # Recent improvements trend
    trend_result = await db.execute(
        text("""
            SELECT DATE(i.created_at) as date, AVG(e.overall_score) as avg_score
            FROM interviews i
            JOIN interview_questions iq ON iq.interview_id = i.id
            JOIN answers a ON a.question_id = iq.id
            JOIN evaluations e ON e.answer_id = a.id
            WHERE i.user_id = :user_id
            GROUP BY DATE(i.created_at)
            ORDER BY date DESC
            LIMIT 30
        """),
        {"user_id": user_id}
    )
    trend = [
        {"date": str(r.date), "average_score": round(float(r.avg_score or 0), 2)}
        for r in trend_result.fetchall()
    ]

    return create_api_response(
        data={
            "user_id": user_id,
            "summary": {
                "total_interviews": agg.total_interviews or 0,
                "total_evaluations": agg.total_evaluations or 0,
                "average_technical_score": round(float(agg.avg_technical or 0), 2),
                "average_communication_score": round(float(agg.avg_communication or 0), 2),
                "average_grammar_score": round(float(agg.avg_grammar or 0), 2),
                "average_fluency_score": round(float(agg.avg_fluency or 0), 2),
                "average_confidence_score": round(float(agg.avg_confidence or 0), 2),
                "average_overall_score": round(float(agg.avg_overall or 0), 2),
            },
            "topic_breakdown": topic_breakdown,
            "weak_topics": weak_topics,
            "learning_recommendations": recommendations,
            "progress_trend": trend,
        },
        message="Performance profile retrieved successfully.",
    )


def _generate_recommendations(weak_topics: list) -> list:
    """Section 25-26: Generate learning recommendations from weak topics."""
    resource_map = {
        "python": ["Python Official Documentation", "Fluent Python (Book)", "Real Python tutorials"],
        "fastapi": ["FastAPI Official Docs", "Building APIs with Python & FastAPI (Course)"],
        "machine learning": ["Hands-On ML with Scikit-Learn (Book)", "fast.ai Course", "Kaggle Learn"],
        "sql": ["SQLZoo", "Mode Analytics SQL Tutorial", "PostgreSQL Official Docs"],
        "algorithms": ["Introduction to Algorithms (CLRS)", "LeetCode Patterns", "Grokking Algorithms"],
        "system design": ["System Design Interview (Book)", "Designing Data-Intensive Applications", "High Scalability blog"],
        "data structures": ["Visualgo.net", "CS50 Data Structures", "LeetCode"],
        "react": ["React Official Docs", "Full Stack Open", "Scrimba React Course"],
        "databases": ["Database Internals (Book)", "Use The Index, Luke", "PostgreSQL Docs"],
    }

    recommendations = []
    for topic_data in weak_topics:
        topic = topic_data["topic"].lower()
        score = topic_data["average_score"]

        # Find matching resources
        matching_resources = []
        for key, resources in resource_map.items():
            if key in topic:
                matching_resources = resources
                break
        if not matching_resources:
            matching_resources = ["Practice more problems on this topic", "Review core concepts via documentation"]

        recommendations.append({
            "topic": topic_data["topic"],
            "current_score": score,
            "priority": "high" if score < 50 else "medium",
            "resources": matching_resources[:2],
            "suggestion": (
                f"Your score in '{topic_data['topic']}' ({score:.0f}/100) needs improvement. "
                f"Focus on foundational concepts and practice with real examples."
            ),
        })

    return recommendations
