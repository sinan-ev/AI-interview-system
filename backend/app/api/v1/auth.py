"""
Authentication Endpoints.
Implements Section 5 & Section 31 specs:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
"""
from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import (
    create_api_response,
    get_auth_service,
    get_current_user,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    summary="Register a new user account",
    description="Registers a candidate, interviewer, or admin user. Issues initial access and refresh tokens.",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    _, tokens = await auth_service.register(payload)
    return create_api_response(tokens.model_dump(), request)


@router.post(
    "/login",
    summary="User login and token issuance",
    description="Authenticates credentials and returns JWT access and refresh tokens.",
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    _, tokens = await auth_service.login(payload.email, payload.password)
    return create_api_response(tokens.model_dump(), request)


@router.post(
    "/refresh",
    summary="Rotate refresh token and issue new access token",
    description="Validates active refresh token, revokes it, and issues a fresh token pair.",
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.refresh_tokens(payload.refresh_token)
    return create_api_response(tokens.model_dump(), request)


@router.post(
    "/logout",
    summary="User logout and token revocation",
    description="Revokes the provided refresh token so it cannot be used again.",
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    payload: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    revoked = False
    if payload.refresh_token:
        revoked = await auth_service.logout(payload.refresh_token)
    return create_api_response({"revoked": revoked, "message": "Successfully logged out."}, request)


@router.get(
    "/me",
    summary="Get current authenticated user profile",
    description="Returns profile information for the Bearer-authenticated user.",
    status_code=status.HTTP_200_OK,
)
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return create_api_response(UserResponse.model_validate(current_user).model_dump(), request)
