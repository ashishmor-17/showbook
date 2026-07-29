from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.city_repository import CityRepository
from app.schemas.venues import CityListResponse, CityResponse

class CityService:
    @staticmethod
    async def list_cities(db: AsyncSession) -> CityListResponse:
        cities = await CityRepository.get_active_cities(db)
        return CityListResponse(
            cities=[
                CityResponse(id=c.id, name=c.name, slug=c.slug, state=c.state)
                for c in cities
            ]
        )
