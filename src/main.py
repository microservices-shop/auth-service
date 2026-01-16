from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.exceptions import AuthServiceException
from src.api.v1.router import router as v1_router

app = FastAPI(
    title="Auth Service",
    description="Authentication microservice with Google OAuth 2.0 and JWT",
    version="0.1.0",
    debug=settings.DEBUG,
)

app.include_router(v1_router)


@app.exception_handler(AuthServiceException)
async def auth_exception_handler(request: Request, exc: AuthServiceException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}
