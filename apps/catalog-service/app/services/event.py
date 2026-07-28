from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.event import EventRepository
from app.models.events import Event
from app.core.exceptions import EventNotFoundException

class EventService:
    @staticmethod
    async def get_events(
        db: AsyncSession,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> tuple[List[Event], Optional[str]]:
        items = await EventRepository.get_events(db=db, cursor=cursor, limit=limit)
        
        next_cursor = None
        if len(items) == limit:
            next_cursor = str(items[-1].id)
            
        return items, next_cursor

    @staticmethod
    async def get_event_detail(db: AsyncSession, slug: str) -> Event:
        event = await EventRepository.get_by_slug(db, slug)
        if not event:
            raise EventNotFoundException(slug)
        return event
