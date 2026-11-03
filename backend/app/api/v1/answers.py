"""
Answer Submission Endpoints.
Implements Section 13:
- POST /api/v1/interviews/{interview_id}/answers (Text submission)
- POST /api/v1/interviews/{interview_id}/answers/voice (Audio file submission)
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from app.core.dependencies import (
    create_api_response,
    get_answer_service,
    get_current_user,
)
from app.models.user import User
from app.schemas.answer import AnswerResponse, TextAnswerSubmission
from app.services.answer_service import AnswerService

router = APIRouter(prefix="/interviews", tags=["Answers"])


@router.post(
    "/{interview_id}/answers",
    summary="Submit text-based interview answer",
    description="Submits candidate text response for an interview question.",
    status_code=status.HTTP_201_CREATED,
)
async def submit_text_answer(
    interview_id: str,
    payload: TextAnswerSubmission,
    request: Request,
    current_user: User = Depends(get_current_user),
    answer_service: AnswerService = Depends(get_answer_service),
):
    answer = await answer_service.submit_text_answer(
        interview_id=interview_id,
        current_user=current_user,
        data=payload,
    )
    return create_api_response(AnswerResponse.model_validate(answer).model_dump(), request)


@router.post(
    "/{interview_id}/answers/voice",
    summary="Submit audio voice interview answer",
    description="Uploads audio response (WAV, MP3, WEBM, M4A, OGG), stores file, and links to question.",
    status_code=status.HTTP_201_CREATED,
)
async def submit_voice_answer(
    interview_id: str,
    request: Request,
    question_id: str = Form(..., description="ID of the question being answered"),
    audio_file: UploadFile = File(..., description="Recorded audio file"),
    duration_seconds: Optional[float] = Form(None, description="Recorded audio duration in seconds"),
    transcript: Optional[str] = Form(None, description="Optional client-side transcript"),
    current_user: User = Depends(get_current_user),
    answer_service: AnswerService = Depends(get_answer_service),
):
    answer = await answer_service.submit_voice_answer(
        interview_id=interview_id,
        question_id=question_id,
        current_user=current_user,
        audio_file=audio_file,
        duration_seconds=duration_seconds,
        provided_transcript=transcript,
    )
    return create_api_response(AnswerResponse.model_validate(answer).model_dump(), request)
