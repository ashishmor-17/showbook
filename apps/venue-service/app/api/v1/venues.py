import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.city_service import CityService
from app.services.venue_service import VenueService
from app.services.showtime_service import ShowtimeService
from app.schemas.venues import CityListResponse, VenueListResponse, ShowtimeQueryResponse, SeatMapResponse

router = APIRouter()

@router.get("/cities", response_model=CityListResponse)
async def get_cities(db: AsyncSession = Depends(get_db)):
    return await CityService.list_cities(db)

@router.get("/cities/{city_slug}/venues", response_model=VenueListResponse)
async def get_venues(city_slug: str, db: AsyncSession = Depends(get_db)):
    return await VenueService.list_venues_by_city(db, city_slug)

@router.get("/showtimes", response_model=ShowtimeQueryResponse)
async def get_showtimes(
    catalog_ref_id: uuid.UUID = Query(...),
    catalog_type: str = Query(...),
    city_id: uuid.UUID = Query(...),
    date: date = Query(...),
    db: AsyncSession = Depends(get_db)
):
    return await ShowtimeService.get_showtimes(
        db=db,
        catalog_ref_id=catalog_ref_id,
        catalog_type=catalog_type,
        city_id=city_id,
        show_date=date
    )

@router.get("/showtimes/{showtime_id}/seats", response_model=SeatMapResponse)
async def get_seat_map(showtime_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await ShowtimeService.get_seat_map(db, showtime_id)
