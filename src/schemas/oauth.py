from pydantic import BaseModel, EmailStr, Field, ConfigDict
from src.schemas.user import UrlStr


class GoogleUserSchema(BaseModel):
    """
    Схема данных пользователя, полученных напрямую из Google OpenID Connect.
    """

    sub: str = Field(
        ...,
        description="Unique Google user identifier",
    )
    email: EmailStr = Field(...)
    name: str
    picture_url: UrlStr = Field(description="URL аватара пользователя")

    model_config = ConfigDict(
        from_attributes=True,
    )


class TokenResponseSchema(BaseModel):
    """
    Схема успешного ответа при выдаче JWT-токенов.

    Используется для передачи данных авторизации клиенту. Access-токен
    предназначен для передачи в заголовке Authorization (Bearer), а
    время истечения позволяет фронтенду рассчитать момент для
    автоматического обновления сессии.
    """

    access_token: str = Field(
        ..., description="Краткосрочный JWT токен для аутентификации запросов к API"
    )
    token_type: str = Field(
        default="Bearer", description="Схема аутентификации (всегда 'Bearer')"
    )
    expires_in: int = Field(..., description="Срок жизни access_token в секундах")

    model_config = ConfigDict(from_attributes=True)
