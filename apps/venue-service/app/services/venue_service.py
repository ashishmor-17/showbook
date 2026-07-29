from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.city_repository import CityRepository
from app.repositories.venue_repository import VenueRepository
from app.schemas.venues import VenueListResponse, VenueResponse
from app.core.exceptions import CityNotFoundException

class VenueService:
    @staticmethod
    async def list_venues_by_city(db: AsyncSession, city_slug: str) -> VenueListResponse:
        city = await CityRepository.get_by_slug(db, city_slug)
        if not city or not city.is_active:
            raise CityNotFoundException(f"City '{city_slug}' not found")
        
        venues = await VenueRepository.get_venues_by_city(db, city.id)
        return VenueListResponse(
            venues=[
                VenueResponse(id=v.id, name=v.name, slug=v.slug, address=v.address, amenities=v.amenities)
                for v in venues
            ]
        )
