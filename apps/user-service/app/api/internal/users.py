import uuid
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.user import UserProfileResponse
from app.services.user_service import UserService

router = APIRouter()

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile_internal(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    if request.headers.get("X-Internal-Service") != "true":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only internal services can access this endpoint."
        )
    return await UserService.get_profile(db, user_id)
