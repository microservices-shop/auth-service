import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import UserModel
from src.schemas.user import UserCreateSchema, UserUpdateSchema


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        query = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> UserModel | None:
        query = select(UserModel).where(UserModel.google_id == google_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def exists(self, user_id: uuid.UUID) -> bool:
        """Проверка существования пользователя по ID.

        Args:
            user_id: UUID пользователя

        Returns:
            True если пользователь существует, False иначе
        """
        query = select(UserModel.id).where(UserModel.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def create(self, user_schema: UserCreateSchema) -> UserModel:
        user = UserModel(**user_schema.model_dump())
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(
        self, user_id: uuid.UUID, update_data: UserUpdateSchema
    ) -> UserModel:
        # Использует exclude_unset, чтобы обновлять только присланные поля
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            user = await self.get_by_id(user_id)
            if user is None:
                raise ValueError(f"User with id {user_id} not found")
            return user

        query = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**update_dict)
            .returning(UserModel)
        )

        result = await self.session.execute(query)
        updated_user = result.scalar_one_or_none()

        if updated_user is None:
            raise ValueError(f"User with id {user_id} not found")

        return updated_user
