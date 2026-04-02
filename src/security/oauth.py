import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.config import settings
from src.exceptions import (
    AuthServiceException,
    OAuthAuthenticationException,
    OAuthProviderException,
)
from src.logger import get_logger
from src.schemas.oauth import GoogleUserSchema
import asyncio

logger = get_logger(__name__)


oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    },
)


class GoogleOAuthClient:
    """
    Интерфейс для работы с Google OAuth 2.0.

    Использует предварительно зарегистрированный oauth.
    """

    def __init__(self):
        self._client = oauth.google

    async def get_authorization_url(self, request: Request) -> RedirectResponse:
        """
        Создает объект RedirectResponse для перенаправления пользователя на страницу Google.

        Raises:
            OAuthAuthenticationException: Если не удалось подключиться к серверу Google.
        """
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                return await self._client.authorize_redirect(
                    request, settings.GOOGLE_REDIRECT_URI
                )
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                logger.warning(
                    "google_oauth_connect_error",
                    method="authorize_redirect",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2**attempt))
                else:
                    raise OAuthAuthenticationException(
                        detail="Failed to connect to Google OAuth server after multiple attempts. Please try again later."
                    )

    async def authorize_access_token(self, request: Request) -> dict:
        """
        Обменивает временный код (code), полученный от Google в callback-запросе,
        на реальные токены доступа (библиотека под капотом автоматически парсит
        полученный id_token и возвращает его содержимое в поле userinfo).

        Пример возвращаемого словаря (dict):
        {
            'access_token': 'ya29...',      # Токен Google для доступа к его API (нам не нужен)
            'id_token': 'eyJhbGci...',      # JWT с данными профиля пользователя
            'userinfo': {                   # Расшифрованные данные из id_token
                'sub': '102938...',         # Уникальный Google ID пользователя
                'email': 'user@gmail.com',  # Email из Google-аккаунта
                'name': 'Ivan Ivanov',      # Отображаемое имя
                'picture': 'https://...'    # URL аватара
            },
            'expires_in': 3599              # Время жизни access_token в секундах
        }

        Raises:
            OAuthAuthenticationException: Если возникла сетевая ошибка при подключении к Google.
            OAuthProviderException: Если Google вернул ошибку (например, неверный code).
        """
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                token = await self._client.authorize_access_token(request)
                if not token:
                    raise OAuthAuthenticationException(
                        detail="Failed to receive token from Google"
                    )
                return token
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                logger.warning(
                    "google_oauth_connect_error",
                    method="authorize_access_token",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2**attempt))
                else:
                    raise OAuthAuthenticationException(
                        detail="Failed to connect to Google OAuth server after multiple attempts. Please try again later."
                    )
            except OAuthError as e:
                raise OAuthProviderException(detail=f"Google OAuth error: {e.error}")

    def get_user_info(self, token: dict) -> GoogleUserSchema:
        """
        Распаковывает и типизирует данные пользователя из id_token.
        """
        user_info = token.get("userinfo")
        if not user_info:
            raise AuthServiceException(detail="No user information provided by Google")

        return GoogleUserSchema(
            sub=user_info.get("sub"),
            email=user_info.get("email"),
            name=user_info.get("name"),
            picture_url=user_info.get("picture"),
        )
