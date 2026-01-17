from typing import Annotated

from fastapi import Depends
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_maker
from src.exceptions import RefreshTokenNotFoundException
from src.schemas.client import ClientInfo
from src.security.jwt_service import JWTService
from src.security.oauth import GoogleOAuthClient
from src.services.auth import AuthService

from src.constants import REFRESH_TOKEN_COOKIE_NAME


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


def get_oauth_client() -> GoogleOAuthClient:
    return GoogleOAuthClient()


def get_jwt_service() -> JWTService:
    return JWTService()


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    oauth_client: Annotated[GoogleOAuthClient, Depends(get_oauth_client)],
) -> AuthService:
    return AuthService(
        session=session,
        jwt_service=jwt_service,
        oauth_client=oauth_client,
    )


def get_refresh_token_from_cookie(request: Request) -> str:
    """Извлекает refresh токен из куки.

    Args:
        request: Объект запроса FastAPI

    Returns:
        Строка refresh токена

    Raises:
        HTTPException: 401, если кука отсутствует
    """

    token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not token:
        raise RefreshTokenNotFoundException()
    return token


def get_client_info(request: Request) -> ClientInfo:
    """Извлекает информацию о клиенте (User-Agent, IP).

    Args:
        request: Объект запроса FastAPI

    Returns:
        ClientInfo: Информация о клиенте
    """
    user_agent = request.headers.get("user-agent")

    # Вся "грязная" логика теперь живет только здесь
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.headers.get("x-real-ip") or (
            request.client.host if request.client else None
        )

    return ClientInfo(user_agent=user_agent, ip_address=ip_address)


SessionDep = Annotated[AsyncSession, Depends(get_db)]
OAuthClientDep = Annotated[GoogleOAuthClient, Depends(get_oauth_client)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
RefreshTokenDep = Annotated[str, Depends(get_refresh_token_from_cookie)]
ClientInfoDep = Annotated[ClientInfo, Depends(get_client_info)]
