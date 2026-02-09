from fastapi import APIRouter

from src.api.internal.users import router as users_router

router = APIRouter(prefix="/internal")
router.include_router(users_router)
