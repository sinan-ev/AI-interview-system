"""
Core Dependencies & Authentication Providers.
Provides user identity extraction, role verification, and service factory dependencies.
"""
from typing import Any, Callable, List, Optional, TypeVar
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.logging import logger, request_id_ctx, user_id_ctx
from app.core.security import decode_token
from app.models.user import User
from app.ai.llm.base import LLMProvider
from app.ai.llm.provider import get_llm_provider
from app.ai.agents.question_generator import QuestionGeneratorAgent
from app.ai.agents.interview_manager import InterviewManagerAgent
from app.repositories.user_repository import UserRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.answer_repository import AnswerRepository
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.interview_service import InterviewService
from app.services.question_service import QuestionService
from app.services.answer_service import AnswerService

T = TypeVar("T")

# HTTP Bearer security scheme
security_scheme = HTTPBearer(auto_error=False)


def get_current_request_id(request: Request) -> str:
    """Retrieve the correlation request ID from request state or context."""
    req_id = getattr(request.state, "request_id", None)
    if not req_id:
        req_id = request_id_ctx.get() or "unknown-request"
    return req_id


def create_api_response(
    data: Any,
    request: Optional[Request] = None,
    message: Optional[str] = None,
) -> dict:
    """Helper to package payload inside standard success envelope."""
    req_id: str
    if request is not None:
        req_id = get_current_request_id(request)
    else:
        req_id = request_id_ctx.get() or "unknown-request"
    result: dict = {
        "success": True,
        "data": data,
        "request_id": req_id,
    }
    if message is not None:
        result["message"] = message
    return result


# AI Provider & Agent Dependencies
def get_ai_llm_provider() -> LLMProvider:
    return get_llm_provider()


def get_question_generator_agent(
    llm: LLMProvider = Depends(get_ai_llm_provider),
) -> QuestionGeneratorAgent:
    return QuestionGeneratorAgent(llm)


def get_interview_manager_agent(
    llm: LLMProvider = Depends(get_ai_llm_provider),
) -> InterviewManagerAgent:
    return InterviewManagerAgent(llm)


# Repository Providers
async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_interview_repository(db: AsyncSession = Depends(get_db)) -> InterviewRepository:
    return InterviewRepository(db)


async def get_question_repository(db: AsyncSession = Depends(get_db)) -> QuestionRepository:
    return QuestionRepository(db)


async def get_answer_repository(db: AsyncSession = Depends(get_db)) -> AnswerRepository:
    return AnswerRepository(db)


# Service Providers
async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo)


async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repo)


async def get_interview_service(
    interview_repo: InterviewRepository = Depends(get_interview_repository),
) -> InterviewService:
    return InterviewService(interview_repo)


async def get_question_service(
    question_repo: QuestionRepository = Depends(get_question_repository),
    interview_repo: InterviewRepository = Depends(get_interview_repository),
    question_generator: QuestionGeneratorAgent = Depends(get_question_generator_agent),
    interview_manager: InterviewManagerAgent = Depends(get_interview_manager_agent),
) -> QuestionService:
    return QuestionService(
        question_repo=question_repo,
        interview_repo=interview_repo,
        question_generator=question_generator,
        interview_manager=interview_manager,
    )


async def get_answer_service(
    answer_repo: AnswerRepository = Depends(get_answer_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    interview_repo: InterviewRepository = Depends(get_interview_repository),
) -> AnswerService:
    return AnswerService(
        answer_repo=answer_repo,
        question_repo=question_repo,
        interview_repo=interview_repo,
    )


# User Authentication Dependency
async def get_current_user(
    request: Request,
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """Authenticate request using Bearer JWT token."""
    if not auth_credentials or not auth_credentials.credentials:
        raise AuthenticationException("Authentication required. Missing Bearer token.")

    token = auth_credentials.credentials
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid authentication token: missing subject.")

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationException("User account associated with this token not found.")

    if not user.is_active:
        raise AuthenticationException("User account is inactive.")

    # Set user ID in request context for structured logging
    user_id_ctx.set(user.id)
    request.state.user = user

    return user


def require_role(*allowed_roles: str) -> Callable:
    """Role-Based Access Control (RBAC) dependency factory."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Unauthorized role access attempt: user {current_user.id} has role '{current_user.role}', required {allowed_roles}"
            )
            raise AuthorizationException(
                f"Access forbidden: role '{current_user.role}' not authorized for this resource."
            )
        return current_user

    return role_checker


# Convenience alias: require_active_user = get_current_user
# (active check is already enforced inside get_current_user)
async def require_active_user(
    request: Request,
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """Alias for get_current_user — enforces active account status."""
    return await get_current_user(
        request=request,
        auth_credentials=auth_credentials,
        user_repo=user_repo,
    )
