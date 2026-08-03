import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seat import SeatType, SeatLayout

class SeatRepository:
    @staticmethod
    async def get_screen_seat_types(db: AsyncSession, screen_id: uuid.UUID) -> list[SeatType]:
        result = await db.execute(
            select(SeatType).where(SeatType.screen_id == screen_id).order_by(SeatType.display_order.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_screen_seat_layouts(db: AsyncSession, screen_id: uuid.UUID) -> list[SeatLayout]:
        result = await db.execute(
            select(SeatLayout)
            .where(SeatLayout.screen_id == screen_id, SeatLayout.is_active.is_(True))
            .order_by(SeatLayout.row_label, SeatLayout.seat_number)
        )
        return list(result.scalars().all())
