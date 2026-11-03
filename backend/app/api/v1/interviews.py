"""
Interview API Endpoints.
Implements Section 6 & Section 31 specs:
- POST /api/v1/interviews
- GET /api/v1/interviews
- GET /api/v1/interviews/{id}
- POST /api/v1/interviews/{id}/start
- POST /api/v1/interviews/{id}/complete
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import (
    create_api_response,
    get_current_user,
    get_interview_service,
    get_question_service,
)
from app.models.user import User
from app.schemas.interview import (
    InterviewCreateRequest,
    InterviewDetailResponse,
    InterviewResponse,
)
from app.schemas.question import QuestionResponse
from app.services.interview_service import InterviewService
from app.services.question_service import QuestionService

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post(
    "",
    summary="Create a new interview session",
    description="Validates configuration, role, topics, and difficulty. Does NOT generate all questions immediately.",
    status_code=status.HTTP_201_CREATED,
)
async def create_interview(
    request: Request,
    payload: InterviewCreateRequest,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    interview = await interview_service.create_interview(current_user, payload)
    return create_api_response(InterviewResponse.model_validate(interview).model_dump(), request)


@router.get(
    "",
    summary="List interviews for current user",
    description="Returns paginated list of interviews belonging to the authenticated candidate.",
    status_code=status.HTTP_200_OK,
)
async def list_interviews(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    items, total = await interview_service.list_user_interviews(
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
    )
    serialized_items = [InterviewResponse.model_validate(item).model_dump() for item in items]
    data = {
        "items": serialized_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return create_api_response(data, request)


@router.get(
    "/{interview_id}",
    summary="Get interview details",
    description="Returns complete details for an interview including all generated questions.",
    status_code=status.HTTP_200_OK,
)
async def get_interview_detail(
    interview_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    interview = await interview_service.get_interview(interview_id, current_user)
    return create_api_response(InterviewDetailResponse.model_validate(interview).model_dump(), request)


@router.post(
    "/{interview_id}/start",
    summary="Start an interview session",
    description="Transitions an interview status from 'created' to 'in_progress'.",
    status_code=status.HTTP_200_OK,
)
async def start_interview(
    interview_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    interview = await interview_service.start_interview(interview_id, current_user)
    return create_api_response(InterviewResponse.model_validate(interview).model_dump(), request)


@router.get(
    "/{interview_id}/current-question",
    summary="Get or generate current active question",
    description="Returns the active unanswered question, or dynamically generates the next question via AI agents.",
    status_code=status.HTTP_200_OK,
)
async def get_current_question(
    interview_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    question_service: QuestionService = Depends(get_question_service),
):
    question = await question_service.get_or_generate_current_question(interview_id, current_user)
    return create_api_response(QuestionResponse.model_validate(question).model_dump(), request)


@router.post(
    "/{interview_id}/complete",
    summary="Complete an interview session",
    description="Explicitly finishes an active interview session and records completion timestamp.",
    status_code=status.HTTP_200_OK,
)
async def complete_interview(
    interview_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    interview = await interview_service.complete_interview(interview_id, current_user)
    return create_api_response(InterviewResponse.model_validate(interview).model_dump(), request)
