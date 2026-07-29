import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.venue import Venue

class VenueRepository:
    @staticmethod
    async def get_venues_by_city(db: AsyncSession, city_id: uuid.UUID) -> list[Venue]:
        result = await db.execute(
            select(Venue).where(Venue.city_id == city_id, Venue.is_active.is_(True)).order_by(Venue.name.asc())
        )
        return list(result.scalars().all())
