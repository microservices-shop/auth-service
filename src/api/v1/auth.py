from fastapi import APIRouter, status, Response, HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.api.dependencies import (
    OAuthClientDep,
    AuthServiceDep,
    RefreshTokenDep,
    ClientInfoDep,
    CurrentUserDep,
)
from src.config import settings
from src.constants import (
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_MAX_AGE,
    REFRESH_TOKEN_COOKIE_PATH,
)
from src.exceptions import UserNotFoundException
from src.schemas.oauth import TokenResponseSchema

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get(
    "/google",
    status_code=status.HTTP_302_FOUND,
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "description": "Ошибка подключения к серверу Google"
        },
    },
)
async def google_login(request: Request, oauth_client: OAuthClientDep):
    """
    Инициирует процесс авторизации через Google OAuth.

    Перенаправляет пользователя на страницу авторизации Google.

    Raises:
        OAuthAuthenticationException: 502 Bad Gateway, если не удалось подключиться к серверу Google.
    """
    return await oauth_client.get_authorization_url(request)


@router.get(
    "/google/callback",
    name="google_callback",
    status_code=status.HTTP_302_FOUND,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Google вернул ошибку (например, access_denied)"
        },
        status.HTTP_502_BAD_GATEWAY: {
            "description": "Сетевая ошибка подключения к Google"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Внутренняя ошибка авторизации"
        },
    },
)
async def google_callback(
    request: Request,
    auth_service: AuthServiceDep,
    client_info: ClientInfoDep,
):
    """Обрабатывает обратный вызов (callback) от Google OAuth.

    Преобразует код авторизации от Google, аутентифицирует/создает пользователя,
    устанавливает refresh токен в HttpOnly куку и перенаправляет на фронтенд.

    Args:
        request: Объект запроса FastAPI с кодом авторизации
        auth_service: Зависимость сервиса аутентификации
        client_info: Информация о клиенте (IP, User-Agent)

    Returns:
        RedirectResponse: Перенаправление на фронтенд с кукой refresh токена

    Raises:
        OAuthProviderException: 400 Bad Request, если Google вернул ошибку
        OAuthAuthenticationException: 502 Bad Gateway, если сетевая ошибка
        AuthServiceException: 500 Internal Server Error, если внутренняя ошибка
    """
    # Аутентификация пользователя через Google OAuth
    refresh_token = await auth_service.authenticate_google(
        request=request,
        user_agent=client_info.user_agent,
        ip_address=client_info.ip_address,
    )

    # Создание ответа перенаправления на фронтенд
    redirect_url = f"{settings.FRONTEND_URL}/auth/success"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    # Установка refresh токена в HttpOnly куку
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=REFRESH_TOKEN_COOKIE_MAX_AGE,
        path=REFRESH_TOKEN_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    return response


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Токен невалиден, просрочен или отозван, или пользователь не найден"
        },
    },
)
async def refresh_tokens(
    request: Request,
    response: Response,
    refresh_token: RefreshTokenDep,
    auth_service: AuthServiceDep,
    client_info: ClientInfoDep,
) -> TokenResponseSchema:
    """Обновление токенов доступа и обновления.

    Реализует ротацию токенов: старый refresh токен отзывается,
    выдается новый refresh токен и устанавливается в куку.

    Args:
        request: Объект запроса FastAPI
        response: Объект ответа для установки куки
        refresh_token: Refresh токен из куки
        auth_service: Зависимость сервиса аутентификации
        client_info: Информация о клиенте (IP, User-Agent)

    Returns:
        TokenResponseSchema: Схема с новым токеном доступа

    Raises:
        HTTPException: 401 Unauthorized, если токен невалиден, просрочен, отозван или пользователь не найден
    """
    try:
        # Обновление токенов (с ротацией)
        token_response, new_refresh_token = await auth_service.refresh_tokens(
            refresh_token=refresh_token,
            user_agent=client_info.user_agent,
            ip_address=client_info.ip_address,
        )
    except UserNotFoundException as e:
        # Специальный случай: UserNotFoundException - 401 (не 404, как в глобальном хендлере),
        # потому что отсутствие пользователя при обновлении токена - ошибка аутентификации
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
        )

    # Установка новой куки refresh токена
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=new_refresh_token,
        max_age=REFRESH_TOKEN_COOKIE_MAX_AGE,
        path=REFRESH_TOKEN_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    return token_response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Токен не найден или невалиден"},
    },
)
async def logout(
    response: Response,
    refresh_token: RefreshTokenDep,
    auth_service: AuthServiceDep,
):
    """Выход пользователя путем отзыва refresh токена.

    Args:
        response: Объект ответа FastAPI для очистки куки
        refresh_token: Refresh токен из куки
        auth_service: Зависимость сервиса аутентификации

    Returns:
        None: Возвращает 204 No Content

    Raises:
        RefreshTokenNotFoundException: 401 Unauthorized, если токен не найден
        InvalidTokenException: 401 Unauthorized, если токен невалиден
    """
    # Отзыв токена
    await auth_service.logout(refresh_token)

    # Очистка куки
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path=REFRESH_TOKEN_COOKIE_PATH,
    )


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(current_user: CurrentUserDep, auth_service: AuthServiceDep):
    await auth_service.logout_all(current_user.id)
