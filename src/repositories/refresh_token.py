import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import RefreshTokenModel


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def create(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshTokenModel:
        """
        Создает новую запись refresh токена в базе данных.

        Токен автоматически хешируется перед сохранением.
        """
        token_hash = self._hash_token(token)

        refresh_token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
        )

        self.session.add(refresh_token)
        await self.session.flush()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_by_token(self, token: str) -> RefreshTokenModel | None:
        """
        Ищет запись по незахешированному токену.

        Внутри метода токен хешируется для поиска в БД.
        Возвращает модель токена или None, если не найдено.
        """
        token_hash = self._hash_token(token)
        query = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke(self, token: str):
        """
        Отзывает (помечает как is_revoked=True) конкретный токен.
        """
        token_hash = self._hash_token(token)
        query = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .where(RefreshTokenModel.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        await self.session.execute(query)

    async def revoke_all_for_user(self, user_id: uuid.UUID):
        """
        Отзывает все активные токены пользователя (выход со всех устройств).

        Возвращает:
            int: Количество отозванных токенов.
        """
        query = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .where(RefreshTokenModel.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        await self.session.execute(query)

    async def delete_expired(self):
        """
        Удаляет из базы данных все просроченные токены.

        Возвращает:
            int: Количество удаленных записей.
        """
        now = datetime.now(timezone.utc)
        query = delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < now)
        result = await self.session.execute(query)
        return result.rowcoun
