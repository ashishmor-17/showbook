import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.notification import NotificationFeedResponse
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("/notifications", response_model=NotificationFeedResponse)
async def get_my_notifications(
    x_user_id: uuid.UUID = Header(..., alias="X-User-Id"),
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    notifications, next_cursor = await NotificationService.get_notifications_for_user(
        db=db, 
        user_id=x_user_id, 
        limit=limit, 
        cursor=cursor
    )

    return {
        "items": notifications,
        "next_cursor": next_cursor
    }
