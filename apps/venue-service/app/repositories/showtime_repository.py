import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.showtime import Showtime, ShowtimeSeatPricing
from app.models.venue import Venue
from app.core.enums import ShowtimeStatus

class ShowtimeRepository:
    @staticmethod
    async def get_showtimes_by_catalog_and_city(
        db: AsyncSession,
        catalog_ref_id: uuid.UUID,
        catalog_type: str,
        city_id: uuid.UUID,
        show_date: date
    ) -> list[Showtime]:
        result = await db.execute(
            select(Showtime)
            .join(Venue, Showtime.venue_id == Venue.id)
            .where(
                Showtime.catalog_ref_id == catalog_ref_id,
                Showtime.catalog_type == catalog_type,
                Showtime.show_date == show_date,
                Venue.city_id == city_id,
                Showtime.status != ShowtimeStatus.CANCELLED.value
            )
            .options(
                joinedload(Showtime.venue),
                joinedload(Showtime.screen)
            )
            .order_by(Showtime.start_time.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_showtime_with_details(db: AsyncSession, showtime_id: uuid.UUID) -> Showtime | None:
        result = await db.execute(
            select(Showtime)
            .where(Showtime.id == showtime_id)
            .options(joinedload(Showtime.screen), joinedload(Showtime.venue))
        )
        return result.scalar_one_or_none()


    @staticmethod
    async def get_showtime_pricing(db: AsyncSession, showtime_id: uuid.UUID) -> list[ShowtimeSeatPricing]:
        result = await db.execute(
            select(ShowtimeSeatPricing).where(ShowtimeSeatPricing.showtime_id == showtime_id)
        )
        return list(result.scalars().all())
