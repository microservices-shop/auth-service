from pydantic import BaseModel, EmailStr, Field, HttpUrl, ConfigDict


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
    picture_url: HttpUrl = Field(description="URL аватара пользователя")

    model_config = ConfigDict(
        from_attributes=True,
    )
