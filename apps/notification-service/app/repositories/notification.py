import uuid
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification

class NotificationRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, notification_id: uuid.UUID) -> Notification | None:
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, notification: Notification) -> Notification:
        db.add(notification)
        return notification

    @staticmethod
    async def get_by_user_id_paginated(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        limit: int, 
        cursor: datetime | None = None
    ) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if cursor:
            query = query.where(Notification.created_at < cursor)
        query = query.order_by(desc(Notification.created_at)).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
