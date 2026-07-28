import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import Event

class EventRepository:
    @staticmethod
    async def get_events(
        db: AsyncSession,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> List[Event]:
        
        query = select(Event).where(Event.is_active == True)
        
        if cursor:
            try:
                cursor_uuid = uuid.UUID(cursor)
                query = query.where(Event.id > cursor_uuid)
            except ValueError:
                pass
                
        query = query.order_by(Event.id.asc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Event]:
        query = select(Event).where(Event.slug == slug, Event.is_active == True)
        result = await db.execute(query)
        return result.scalar_one_or_none()
