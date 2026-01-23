from fastapi import APIRouter, status, HTTPException

from src.api.dependencies import CurrentUserDep, UserServiceDep
from src.schemas.user import UserResponseSchema, UserUpdateSchema
from src.exceptions import UserNotFoundException

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserResponseSchema:
    """Получение профиля текущего пользователя.

    Требует аутентификации через заголовки Gateway или Bearer токен.

    Args:
        current_user: Текущий пользователь из аутентификации
        user_service: Зависимость сервиса пользователей

    Returns:
        UserResponseSchema с полным профилем

    Raises:
        HTTPException: 404 Not Found, если пользователь не найден
    """
    try:
        user_id = current_user.id
        return await user_service.get_by_id(user_id)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )


@router.patch("/me", status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    update_data: UserUpdateSchema,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserResponseSchema:
    """Обновление профиля текущего пользователя.

    Требует аутентификации через заголовки Gateway или Bearer токен.

    Args:
        update_data: Данные для обновления
        current_user: Текущий пользователь из аутентификации
        user_service: Зависимость сервиса пользователей

    Returns:
        Обновленная UserResponseSchema

    Raises:
        HTTPException: 404 Not Found, если пользователь не найден
    """
    try:
        user_id = current_user.id
        return await user_service.update_profile(user_id, update_data)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
