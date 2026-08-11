import uuid
from typing import List, Optional

from sqlalchemy import select, and_, or_
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

    @staticmethod
    async def search_events(
        db: AsyncSession,
        query_str: str,
        allowed_ids: Optional[set] = None,
        limit: int = 10
    ) -> List[Event]:
        query = select(Event).where(
            and_(
                Event.is_active == True,
                or_(
                    Event.title.ilike(f"%{query_str}%"),
                    Event.description.ilike(f"%{query_str}%")
                )
            )
        )
        if allowed_ids is not None:
            query = query.where(Event.id.in_(allowed_ids))
        query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
