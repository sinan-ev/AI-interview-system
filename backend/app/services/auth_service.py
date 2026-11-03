"""
Authentication Service.
Handles registration, credential validation, token rotation, and revocation.
"""
from datetime import datetime, timedelta, timezone
from typing import Tuple

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    NotFoundException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, data: RegisterRequest) -> Tuple[User, TokenResponse]:
        """Register a new user, ensuring email uniqueness, and issue initial tokens."""
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' already exists.")

        hashed_password = get_password_hash(data.password)
        user = await self.user_repo.create(
            name=data.name,
            email=data.email,
            password_hash=hashed_password,
            role=data.role,
        )

        tokens = await self._issue_tokens(user)
        return user, tokens

    async def login(self, email: str, password: str) -> Tuple[User, TokenResponse]:
        """Authenticate user by email and password, returning tokens on success."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationException("Account is inactive. Please contact support.")

        tokens = await self._issue_tokens(user)
        return user, tokens

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        """
        Validate refresh token, check revocation, perform token rotation
        by revoking the old refresh token and issuing a new token pair.
        """
        # 1. Decode & verify JWT structure and expiration
        payload = decode_token(refresh_token_str, expected_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationException("Invalid token payload: subject missing.")

        # 2. Check token record in database
        hashed = hash_token(refresh_token_str)
        token_record = await self.user_repo.get_refresh_token(hashed)
        if not token_record or token_record.is_revoked:
            # Possible token reuse attack; revoke all tokens for this user for security
            if token_record:
                await self.user_repo.revoke_all_user_tokens(user_id)
            raise AuthenticationException("Refresh token is invalid or has been revoked.")

        now_utc = datetime.now(timezone.utc)
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now_utc:
            raise AuthenticationException("Refresh token has expired.")

        # 3. Retrieve user
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationException("User not found or inactive.")

        # 4. Revoke used refresh token (Token Rotation)
        token_record.is_revoked = True

        # 5. Issue fresh token pair
        return await self._issue_tokens(user)

    async def logout(self, refresh_token_str: str) -> bool:
        """Revoke the provided refresh token."""
        if not refresh_token_str:
            return False
        hashed = hash_token(refresh_token_str)
        return await self.user_repo.revoke_refresh_token(hashed)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        """Internal helper to mint access & refresh tokens and persist refresh token hash."""
        access_token = create_access_token(
            subject=user.id,
            role=user.role,
        )
        refresh_token = create_refresh_token(subject=user.id)

        # Store hashed refresh token in database
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.user_repo.store_refresh_token(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )
