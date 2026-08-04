import uuid
import asyncio

from datetime import date
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ShowtimeNotFoundException
from app.clients.inventory_client import InventoryClient
from app.repositories.showtime_repository import ShowtimeRepository
from app.repositories.seat_repository import SeatRepository
from app.builders.seat_map_builder import SeatMapBuilder
from app.schemas.venues import ShowtimeQueryResponse, VenueShowtimesResponse, ShowResponse, SeatMapResponse

class ShowtimeService:
    @classmethod
    async def get_showtimes(
        cls,
        db: AsyncSession,
        catalog_ref_id: uuid.UUID,
        catalog_type: str,
        city_id: uuid.UUID,
        show_date: date
    ) -> ShowtimeQueryResponse:
        showtimes = await ShowtimeRepository.get_showtimes_by_catalog_and_city(
            db=db,
            catalog_ref_id=catalog_ref_id,
            catalog_type=catalog_type,
            city_id=city_id,
            show_date=show_date
        )

        # Fetch seat capacities concurrently
        tasks = [
            InventoryClient.get_available_seats(show.id, show.screen.total_capacity)
            for show in showtimes
        ]
        available_seats_list = await asyncio.gather(*tasks)

        # Group showtimes by venue
        venue_shows = defaultdict(list)
        for show, avail_seats in zip(showtimes, available_seats_list):
            venue_key = (show.venue.id, show.venue.name)
            venue_shows[venue_key].append(
                ShowResponse(
                    showtime_id=show.id,
                    screen_name=show.screen.name,
                    screen_type=show.screen.screen_type,
                    start_time=show.start_time.strftime("%H:%M"),
                    end_time=show.end_time.strftime("%H:%M"),
                    language=show.language,
                    format=show.format,
                    status=show.status,
                    available_seats=avail_seats
                )
            )

        showtimes_grouped = [
            VenueShowtimesResponse(
                venue_id=venue_id,
                venue_name=venue_name,
                shows=shows
            )
            for (venue_id, venue_name), shows in venue_shows.items()
        ]

        return ShowtimeQueryResponse(
            date=show_date,
            showtimes=showtimes_grouped
        )

    @classmethod
    async def get_seat_map(cls, db: AsyncSession, showtime_id: uuid.UUID) -> SeatMapResponse:
        showtime = await ShowtimeRepository.get_showtime_with_details(db, showtime_id)
        if not showtime:
            raise ShowtimeNotFoundException(f"Showtime '{showtime_id}' not found")

        # Concurrently query details from database repositories and inventory service
        pricing_task = ShowtimeRepository.get_showtime_pricing(db, showtime_id)
        types_task = SeatRepository.get_screen_seat_types(db, showtime.screen_id)
        layout_task = SeatRepository.get_screen_seat_layouts(db, showtime.screen_id)
        status_task = InventoryClient.get_seat_statuses(showtime_id)

        pricing, seat_types, physical_seats, live_statuses = await asyncio.gather(
            pricing_task, types_task, layout_task, status_task
        )

        return SeatMapBuilder.build(
            showtime_id=showtime_id,
            screen_type=showtime.screen.screen_type,
            status=showtime.status,
            pricing=pricing,
            seat_types=seat_types,
            physical_seats=physical_seats,
            live_statuses=live_statuses
        )

    @classmethod
    async def get_showtime_details(cls, db: AsyncSession, showtime_id: uuid.UUID) -> dict:
        import datetime
        showtime = await ShowtimeRepository.get_showtime_with_details(db, showtime_id)
        if not showtime:
            raise ShowtimeNotFoundException(f"Showtime '{showtime_id}' not found")
            
        start_dt = datetime.datetime.combine(showtime.show_date, showtime.start_time)
        return {
            "id": showtime.id,
            "show_date": showtime.show_date.isoformat(),
            "start_time": showtime.start_time.strftime("%H:%M:%S"),
            "start_datetime": start_dt.isoformat(),
            "status": showtime.status,
            "venue_name": showtime.venue.name,
            "movie_id": showtime.catalog_ref_id
    }
