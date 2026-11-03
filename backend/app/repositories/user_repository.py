"""
User & RefreshToken Database Repository.
Encapsulates all database operations for users and refresh tokens.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.refresh_token import RefreshToken


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by primary key ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by lowercase unique email."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, name: str, email: str, password_hash: str, role: str = "candidate") -> User:
        """Create and persist a new user."""
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def store_refresh_token(self, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        """Store hashed refresh token record."""
        token_record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.add(token_record)
        await self.db.flush()
        return token_record

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Find refresh token record by token hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a specific refresh token."""
        token_record = await self.get_refresh_token(token_hash)
        if token_record:
            token_record.is_revoked = True
            await self.db.flush()
            return True
        return False

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all active refresh tokens belonging to a user."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
        )
        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.rowcount
