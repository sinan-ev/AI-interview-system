"""
User Service.
Handles profile retrieval and updates.
"""
from typing import Optional
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_by_id(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found.")
        return user

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        if data.name is not None:
            user.name = data.name.strip()
        if data.email is not None:
            user.email = data.email.lower().strip()
        await self.user_repo.db.flush()
        return user
