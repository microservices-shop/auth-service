"""Сервис профиля пользователя с бизнес-логикой."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import UserNotFoundException
from src.repositories.user import UserRepository
from src.schemas.user import UserResponseSchema, UserUpdateSchema


class UserService:
    """Сервис для операций с профилем пользователя."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_by_id(self, user_id: uuid.UUID) -> UserResponseSchema:
        """Получение пользователя по ID.

        Args:
            user_id: Уникальный идентификатор пользователя

        Returns:
            UserResponseSchema с данными пользователя

        Raises:
            UserNotFoundException: Если пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)

        if user is None:
            raise UserNotFoundException()

        return UserResponseSchema.model_validate(user)

    async def update_profile(
        self, user_id: uuid.UUID, data: UserUpdateSchema
    ) -> UserResponseSchema:
        """Обновление профиля пользователя.

        Args:
            user_id: Уникальный идентификатор пользователя
            data: Данные для обновления

        Returns:
            Обновленный экземпляр UserResponseSchema

        Raises:
            UserNotFoundException: Если пользователь не найден
        """
        # Обновление пользователя
        user = await self.user_repo.update(user_id, data)
        await self.session.commit()

        return UserResponseSchema.model_validate(user)
