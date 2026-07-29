from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City

class CityRepository:
    @staticmethod
    async def get_active_cities(db: AsyncSession) -> list[City]:
        result = await db.execute(
            select(City).where(City.is_active.is_(True)).order_by(City.name.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> City | None:
        result = await db.execute(
            select(City).where(City.slug == slug)
        )
        return result.scalar_one_or_none()
