from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.config import settings
from src.exceptions import AuthServiceException, OAuthAuthenticationException
from src.schemas.oauth import GoogleUserSchema

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
        """
        return await self._client.authorize_redirect(
            request, settings.GOOGLE_REDIRECT_URI
        )

    async def authorize_access_token(self, request: Request) -> dict:
        """
        Обменивает полученный от Google код на токены (access_token, id_token).

        Raises:
            AuthServiceException: Если обмен не удался.
        """
        try:
            token = await self._client.authorize_access_token(request)
            if not token:
                raise OAuthAuthenticationException(
                    detail="Failed to receive token from Google"
                )
            return token
        except OAuthError as e:
            raise AuthServiceException(detail=f"Google OAuth error: {e.error}")

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
