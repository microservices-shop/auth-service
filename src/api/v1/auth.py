from fastapi import APIRouter, status, Response
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.api.dependencies import (
    OAuthClientDep,
    AuthServiceDep,
    RefreshTokenDep,
    ClientInfoDep,
)
from src.config import settings
from src.constants import (
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_MAX_AGE,
    REFRESH_TOKEN_COOKIE_PATH,
)
from src.schemas.oauth import TokenResponseSchema

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google", status_code=status.HTTP_302_FOUND)
async def google_login(request: Request, oauth_client: OAuthClientDep):
    """
    Инициирует процесс авторизации через Google OAuth.

    Перенаправляет пользователя на страницу авторизации Google.
    """
    return await oauth_client.get_authorization_url(request)


@router.get(
    "/google/callback", name="google_callback", status_code=status.HTTP_302_FOUND
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

    Returns:
        Ответ перенаправления на фронтенд с кукой refresh токена
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


@router.post("/refresh", status_code=status.HTTP_200_OK)
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
        refresh_token: Refresh токен из куки
        auth_service: Зависимость сервиса аутентификации

    Returns:
        TokenResponse с новым токеном доступа
    """

    # Обновление токенов (с ротацией)
    token_response, new_refresh_token = await auth_service.refresh_tokens(
        refresh_token=refresh_token,
        user_agent=client_info.user_agent,
        ip_address=client_info.ip_address,
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
