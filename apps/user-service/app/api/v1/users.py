from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserProfileResponse, UserProfileUpdateRequest, ChangePasswordRequest
from app.schemas.auth import MessageResponse
from app.services.user_service import UserService

router = APIRouter()

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await UserService.get_profile(db, user.id)

@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    payload: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await UserService.update_profile(db, user.id, payload)

@router.post("/me/change-password", response_model=MessageResponse)
async def change_my_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await UserService.change_password(db, user.id, payload.old_password, payload.new_password)
