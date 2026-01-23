import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_maker
from src.exceptions import (
    InvalidTokenException,
    ExpiredTokenException,
)
from src.schemas.client import ClientInfo
from src.schemas.user import CurrentUserSchema
from src.security.jwt_service import JWTService
from src.security.oauth import GoogleOAuthClient
from src.services.auth import AuthService
from src.services.user import UserService

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
    token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )
    return token


def get_client_info(request: Request) -> ClientInfo:
    """Извлекает информацию о клиенте (User-Agent, IP).

    Args:
        request: Объект запроса FastAPI

    Returns:
        ClientInfo: Объект с user-agent и ip-адресом
    """
    user_agent = request.headers.get("user-agent")

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.headers.get("x-real-ip") or (
            request.client.host if request.client else None
        )

    return ClientInfo(user_agent=user_agent, ip_address=ip_address)


JWTServiceDep = Annotated[JWTService, Depends(get_jwt_service)]


def get_current_user_from_token(
    jwt_service: JWTServiceDep,
    authorization: str | None = Header(None),
) -> CurrentUserSchema:
    """Извлекает текущего пользователя из Bearer токена.

    Args:
        authorization: Заголовок Authorization с Bearer токеном
        jwt_service: Зависимость сервиса JWT

    Returns:
        Словарь пользователя с id, email, role

    Raises:
        HTTPException: 401 Unauthorized, если токен невалиден, просрочен или отсутствует
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    # Извлечение токена из "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = parts[1]

    try:
        payload = jwt_service.verify_access_token(token)
    except InvalidTokenException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
        )
    except ExpiredTokenException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
        )

    return CurrentUserSchema(
        id=payload["sub"],
        email=payload["email"],
        role=payload["role"],
    )


def get_current_user(
    request: Request,
    jwt_service: JWTServiceDep,
    authorization: str | None = Header(None),
) -> CurrentUserSchema:
    """Получает текущего пользователя из заголовков Gateway или Bearer токена.

    Поддерживает два метода аутентификации:
    1. Заголовки Gateway (X-User-ID, X-User-Email, X-User-Role)
    2. Bearer токен в заголовке Authorization

    Args:
        request: Объект запроса FastAPI
        authorization: Заголовок Authorization
        jwt_service: Зависимость сервиса JWT

    Returns:
        Словарь пользователя с id, email, role

    Raises:
        HTTPException: 401, если аутентификация не удалась
    """
    # Сначала пробуем заголовки Gateway
    user_id = request.headers.get("X-User-ID")
    user_email = request.headers.get("X-User-Email")
    user_role = request.headers.get("X-User-Role")

    if user_id and user_email and user_role:
        return CurrentUserSchema(
            id=uuid.UUID(user_id),
            email=user_email,
            role=user_role,
        )

    # Резервный вариант — Bearer токен
    if authorization:
        return get_current_user_from_token(
            authorization=authorization, jwt_service=jwt_service
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (gateway headers or Bearer token)",
    )


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserService:
    return UserService(session=session)


SessionDep = Annotated[AsyncSession, Depends(get_db)]
OAuthClientDep = Annotated[GoogleOAuthClient, Depends(get_oauth_client)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
RefreshTokenDep = Annotated[str, Depends(get_refresh_token_from_cookie)]
ClientInfoDep = Annotated[ClientInfo, Depends(get_client_info)]
CurrentUserDep = Annotated[CurrentUserSchema, Depends(get_current_user)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
