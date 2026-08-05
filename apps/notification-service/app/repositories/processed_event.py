import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.processed_event import ProcessedEvent

class ProcessedEventRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, event_id: uuid.UUID) -> ProcessedEvent | None:
        result = await db.execute(select(ProcessedEvent).where(ProcessedEvent.event_id == event_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, processed_event: ProcessedEvent) -> ProcessedEvent:
        db.add(processed_event)
        return processed_event
