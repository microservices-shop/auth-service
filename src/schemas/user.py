from pydantic import BaseModel, EmailStr, Field, HttpUrl, ConfigDict, AfterValidator
from typing import Annotated, Optional
from src.db.models import UserRole

# Тип, который валидируется как URL, но преобразуется в строку
UrlStr = Annotated[HttpUrl, AfterValidator(str)]


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
    picture_url: UrlStr = Field(description="URL аватара пользователя")
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
    picture_url: Optional[UrlStr] = Field(
        None,
        description="Новый URL аватара пользователя",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")
