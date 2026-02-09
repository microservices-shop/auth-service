from fastapi import APIRouter, status, HTTPException
import uuid

from src.api.dependencies import UserServiceDep
from src.schemas.user import UserResponseSchema
from src.exceptions import UserNotFoundException

router = APIRouter(prefix="/users", tags=["Internal Users API"])


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
) -> UserResponseSchema:
    """Получение пользователя по ID для межсервисного взаимодействия.

    Internal API эндпоинт для других сервисов (Cart, Order).
    Не требует JWT токена, доступен только внутри Docker-сети.

    Args:
        user_id: UUID пользователя
        user_service: Зависимость сервиса пользователей

    Returns:
        UserResponseSchema с данными пользователя

    Raises:
        HTTPException: 404 Not Found, если пользователь не найден
    """
    try:
        return await user_service.get_by_id(user_id)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )


@router.get("/{user_id}/exists", status_code=status.HTTP_200_OK)
async def check_user_exists(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
) -> dict[str, bool]:
    """Проверка существования пользователя по ID для межсервисного взаимодействия.

    Internal API эндпоинт для других сервисов (Cart, Order).
    Не требует JWT токена, доступен только внутри Docker-сети.

    Args:
        user_id: UUID пользователя
        user_service: Зависимость сервиса пользователей

    Returns:
        {"exists": true} если пользователь существует, иначе {"exists": false}
    """
    exists = await user_service.exists(user_id)
    return {"exists": exists}
