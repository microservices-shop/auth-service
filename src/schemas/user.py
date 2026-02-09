import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
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
    picture_url: str | None = Field(None, description="URL аватара пользователя")
    role: UserRole = Field(UserRole.USER, description="Роль пользователя в системе")

    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(BaseModel):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор пользователя")
    email: EmailStr = Field(..., description="Адрес электронной почты пользователя")
    name: str = Field(..., description="Отображаемое имя пользователя")
    picture_url: str | None = Field(
        None, description="URL фотографии профиля пользователя"
    )
    role: str = Field(..., description="Роль пользователя (user, admin)")
    is_active: bool = Field(..., description="Активен ли аккаунт пользователя")
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Новое отображаемое имя",
        examples=["Александр"],
    )
    picture_url: str | None = Field(
        None,
        description="Новый URL аватара пользователя",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class CurrentUserSchema(BaseModel):
    """Схема текущего пользователя (используется в зависимостях)."""

    id: uuid.UUID = Field(..., description="Уникальный идентификатор пользователя")
    email: EmailStr = Field(..., description="Адрес электронной почты пользователя")
    role: str = Field(..., description="Роль пользователя (user, admin)")

    model_config = ConfigDict(from_attributes=True)
