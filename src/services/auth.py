import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.config import settings
from src.logger import get_logger
from src.constants import UserRole
from src.exceptions import (
    InvalidTokenException,
    RefreshTokenRevokedException,
    ExpiredTokenException,
    UserNotFoundException,
    RefreshTokenNotFoundException,
)
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.user import UserRepository
from src.schemas.oauth import TokenResponseSchema
from src.schemas.user import UserCreateSchema, UserUpdateSchema

from src.security.oauth import GoogleOAuthClient
from src.security.jwt_service import JWTService


logger = get_logger(__name__)


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        jwt_service: JWTService,
        oauth_client: GoogleOAuthClient,
    ):
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.jwt_service = jwt_service
        self.oauth_client = oauth_client

    async def authenticate_google(
        self, request: Request, user_agent: str | None, ip_address: str | None
    ) -> str:
        """
        Выполняет вход через Google OAuth: обменивает код на данные профиля,
        регистрирует или обновляет пользователя и генерирует токены.

        Args:
            request: Объект запроса FastAPI с кодом авторизации
            user_agent: User-Agent клиента
            ip_address: IP-адрес клиента

        Returns:
            str: Refresh токен

        Raises:
            OAuthAuthenticationException: Если аутентификация через Google не удалась
            AuthServiceException: При внутренних ошибках сервиса
        """
        logger.info("google_oauth_started")
        token = await self.oauth_client.authorize_access_token(request)
        google_user = self.oauth_client.get_user_info(token)

        user = await self.user_repo.get_by_google_id(google_user.sub)

        if user is None:
            logger.info("user_registering", email=google_user.email)
            user_schema = UserCreateSchema(
                email=google_user.email,
                name=google_user.name,
                picture_url=google_user.picture_url,
                google_id=google_user.sub,
                role=UserRole.USER,
            )

            user = await self.user_repo.create(user_schema)
        else:
            logger.info("user_profile_updating")
            update_schema = UserUpdateSchema(
                name=google_user.name,
                picture_url=google_user.picture_url,
            )
            user = await self.user_repo.update(user.id, update_schema)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = self.jwt_service.create_refresh_token(
            user_id=user.id, iat=now, expires_at=expires_at
        )

        # Save hashed refresh token to database
        await self.token_repo.create(
            user_id=user.id,
            token=refresh_token,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
        )

        await self.session.commit()

        logger.info("user_authenticated")
        return refresh_token

    async def refresh_tokens(
        self, refresh_token: str, user_agent: str | None, ip_address: str | None
    ) -> tuple[TokenResponseSchema, str]:
        """Обновление access_token и refresh_token (ротация токенов).

        Args:
            refresh_token: Текущий JWT refresh токен
            user_agent: User-agent браузера/устройства пользователя
            ip_address: IP-адрес пользователя

        Returns:
            Кортеж из (TokenResponse с новым access_token, новый JWT refresh_token)

        Raises:
            InvalidTokenException: Если токен невалиден или поврежден
            ExpiredTokenException: Если срок действия токена истек
            RefreshTokenRevokedException: Если токен был отозван
            UserNotFoundException: Если пользователь не найден
        """
        logger.info("token_refresh_started")
        # Проверка подписи JWT и декодирование
        payload = self.jwt_service.verify_refresh_token(refresh_token)
        user_id_str = payload.get("sub")

        if not user_id_str:
            raise InvalidTokenException("User ID is missing from the token")

        user_id = uuid.UUID(user_id_str)

        # Проверка токена в базе данных
        token_record = await self.token_repo.get_by_token(refresh_token)

        if token_record is None:
            raise InvalidTokenException("Refresh token not found in the database")

        if token_record.is_revoked:
            raise RefreshTokenRevokedException()

        # Проверка срока действия (запись в БД)
        if token_record.expires_at < datetime.now(timezone.utc):
            raise ExpiredTokenException()

        # Получение пользователя
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundException(f"Пользователь {user_id} не найден")

        # Отзыв старого refresh токена (ротация токенов)
        await self.token_repo.revoke(refresh_token)

        # Расчет времени истечения
        now = datetime.now(timezone.utc)
        access_expires_at = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        refresh_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Генерация новых токенов
        new_access_token = self.jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            iat=now,
            expires_at=access_expires_at,
        )
        new_refresh_token = self.jwt_service.create_refresh_token(
            user_id=user.id, iat=now, expires_at=refresh_expires_at
        )

        # Сохранение нового refresh токена
        await self.token_repo.create(
            user_id=user.id,
            token=new_refresh_token,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=refresh_expires_at,
        )

        await self.session.commit()

        token_response = TokenResponseSchema(
            access_token=new_access_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        logger.info("token_refreshed")
        return token_response, new_refresh_token

    async def logout(self, refresh_token: str) -> None:
        """Выход пользователя путем отзыва refresh токена.

        Args:
            refresh_token: Refresh токен для отзыва

        Raises:
            InvalidTokenException: Если токен не найден
        """
        # Проверка существования токена в базе данных
        token_record = await self.token_repo.get_by_token(refresh_token)

        if token_record is None:
            raise RefreshTokenNotFoundException()

        # Отзыв токена
        await self.token_repo.revoke(refresh_token)
        await self.session.commit()
        logger.info("token_revoked")

    async def logout_all(self, user_id: uuid.UUID) -> None:
        """Выход пользователя со всех устройств путем отзыва всех refresh токенов.

        Args:
            user_id: Уникальный идентификатор пользователя
        """
        await self.token_repo.revoke_all_for_user(user_id)
        await self.session.commit()
        logger.info("all_tokens_revoked")
