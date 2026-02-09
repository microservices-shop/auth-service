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
