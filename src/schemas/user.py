from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, ConfigDict
from src.db.models import UserRole


class UserCreateSchema(BaseModel):
    email: EmailStr = Field(
        ..., description="Электронная почта пользователя", examples=["user@example.com"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Отображаемое имя",
        examples=["Иван"],
    )
    google_id: str = Field(
        ...,
        description="Уникальный идентификатор из Google OAuth",
    )
    picture_url: HttpUrl | None = Field(
        None,
        description="URL аватара пользователя",
    )
    role: UserRole = Field(UserRole.USER, description="Роль пользователя в системе")

    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Новое отображаемое имя",
        examples=["Александр"],
    )
    picture_url: Optional[HttpUrl] = Field(
        None,
        description="Новый URL аватара пользователя",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")
