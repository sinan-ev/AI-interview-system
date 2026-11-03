"""
User Profile Endpoints.
Implements Section 31: GET /api/v1/users/me and profile updates.
"""
from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import (
    create_api_response,
    get_current_user,
    get_user_service,
)
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    summary="Get user profile",
    description="Returns detailed profile information for the authenticated user.",
    status_code=status.HTTP_200_OK,
)
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return create_api_response(UserResponse.model_validate(current_user).model_dump(), request)


@router.put(
    "/me",
    summary="Update user profile",
    description="Updates name or email for the authenticated user.",
    status_code=status.HTTP_200_OK,
)
async def update_my_profile(
    request: Request,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    updated = await user_service.update_profile(current_user, payload)
    return create_api_response(UserResponse.model_validate(updated).model_dump(), request)
