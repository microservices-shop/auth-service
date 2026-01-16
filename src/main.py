from fastapi import FastAPI

from src.config import settings

app = FastAPI(
    title="Auth Service",
    description="Authentication microservice with Google OAuth 2.0 and JWT",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}
