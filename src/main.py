from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.config import settings
from src.api.v1.router import router as v1_router

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

app.include_router(v1_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}
