import uuid
from datetime import date
from pydantic import BaseModel

class CityResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    state: str

    class Config:
        from_attributes = True

class CityListResponse(BaseModel):
    cities: list[CityResponse]


class VenueResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    address: str
    amenities: list[str]

    class Config:
        from_attributes = True

class VenueListResponse(BaseModel):
    venues: list[VenueResponse]


class ShowResponse(BaseModel):
    showtime_id: uuid.UUID
    screen_name: str
    screen_type: str
    start_time: str
    end_time: str
    language: str | None
    format: str | None
    status: str
    available_seats: int

class VenueShowtimesResponse(BaseModel):
    venue_id: uuid.UUID
    venue_name: str
    shows: list[ShowResponse]

class ShowtimeQueryResponse(BaseModel):
    date: date
    showtimes: list[VenueShowtimesResponse]


class SeatResponse(BaseModel):
    seat_code: str
    status: str

class RowResponse(BaseModel):
    row: str
    seats: list[SeatResponse]

class CategorySeatsResponse(BaseModel):
    id: uuid.UUID
    name: str
    price_paise: int
    rows: list[RowResponse]

class SeatMapResponse(BaseModel):
    showtime_id: uuid.UUID
    screen_type: str
    status: str
    categories: list[CategorySeatsResponse]
