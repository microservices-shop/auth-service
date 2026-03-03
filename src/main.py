from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import structlog

from src.config import settings
from src.api.v1.router import router as v1_router
from src.api.internal.router import router as internal_router
from src.logger import setup_logging, get_logger
from src.middleware.request_logger import RequestLoggingMiddleware
from src.exceptions import (
    UserNotFoundException,
    InvalidTokenException,
    ExpiredTokenException,
    RefreshTokenRevokedException,
    RefreshTokenNotFoundException,
    OAuthAuthenticationException,
    OAuthProviderException,
    AuthServiceException,
)

logger = get_logger(__name__)

setup_logging()

app = FastAPI(
    title="Auth Service",
    description="Authentication microservice with Google OAuth 2.0 and JWT",
    version="0.1.0",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(v1_router)
app.include_router(internal_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}


@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


@app.exception_handler(RefreshTokenNotFoundException)
@app.exception_handler(RefreshTokenRevokedException)
@app.exception_handler(InvalidTokenException)
@app.exception_handler(ExpiredTokenException)
async def unauthorized_handler(request: Request, exc: AuthServiceException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
    )


@app.exception_handler(OAuthProviderException)
async def oauth_provider_handler(request: Request, exc: OAuthProviderException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(OAuthAuthenticationException)
async def oauth_authentication_handler(
    request: Request, exc: OAuthAuthenticationException
):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": exc.detail},
    )


@app.exception_handler(AuthServiceException)
async def auth_service_handler(request: Request, exc: AuthServiceException):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # request_id АВТОМАТИЧЕСКИ добавляется в логи из контекста structlog
    logger.exception("unhandled_exception")
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error. Please report this ID to support.",
            "request_id": request_id,
        },
    )
