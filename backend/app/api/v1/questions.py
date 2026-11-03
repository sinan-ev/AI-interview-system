"""
Question Endpoints.
Implements Section 31: GET /api/v1/questions/{id}
"""
from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import (
    create_api_response,
    get_current_user,
    get_question_service,
)
from app.models.user import User
from app.schemas.question import QuestionResponse
from app.services.question_service import QuestionService

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get(
    "/{question_id}",
    summary="Get question details",
    description="Returns public question representation for candidate.",
    status_code=status.HTTP_200_OK,
)
async def get_question(
    question_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    question_service: QuestionService = Depends(get_question_service),
):
    question = await question_service.get_question(question_id, current_user)
    return create_api_response(QuestionResponse.model_validate(question).model_dump(), request)
