import uuid
import logging
import httpx
from datetime import date as dt_date
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.movie import MovieRepository
from app.repositories.event import EventRepository
from app.core.config import settings
from app.core.http import http_client

logger = logging.getLogger(__name__)

class SearchService:
    @staticmethod
    async def search(
        db: AsyncSession,
        q: str,
        type: str = "ALL",
        city_id: Optional[uuid.UUID] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        
        allowed_ids = None
        if city_id:
            today_str = dt_date.today().isoformat()
            
            allowed_movie_ids = []
            try:
                response = await http_client.get(
                    f"{settings.VENUE_SERVICE_URL}/api/v1/venues/cities/{city_id}/catalog-refs",
                    params={"date": today_str, "catalog_type": "MOVIE"}
                )
                if response.status_code == 200:
                    raw_ids = response.json().get("catalog_ref_ids", [])
                    allowed_movie_ids = [uuid.UUID(rid) for rid in raw_ids]
            except Exception:
                logger.exception("Failed fetching movie catalog refs for search")

            allowed_event_ids = []
            try:
                response = await http_client.get(
                    f"{settings.VENUE_SERVICE_URL}/api/v1/venues/cities/{city_id}/catalog-refs",
                    params={"date": today_str, "catalog_type": "EVENT"}
                )
                if response.status_code == 200:
                    raw_ids = response.json().get("catalog_ref_ids", [])
                    allowed_event_ids = [uuid.UUID(rid) for rid in raw_ids]
            except Exception:
                logger.exception("Failed fetching event catalog refs for search")
            
            allowed_ids = set(allowed_movie_ids + allowed_event_ids)

        results = []
        
        if type in ("MOVIE", "ALL"):
            movies = await MovieRepository.search_movies(
                db=db,
                query_str=q,
                allowed_ids=allowed_ids,
                limit=limit
            )
            for m in movies:
                results.append({
                    "id": str(m.id),
                    "title": m.title,
                    "slug": m.slug,
                    "type": "MOVIE",
                    "description": m.description,
                    "poster_url": m.poster_url,
                    "language": m.language
                })

        if type in ("EVENT", "ALL"):
            events = await EventRepository.search_events(
                db=db,
                query_str=q,
                allowed_ids=allowed_ids,
                limit=limit
            )
            for e in events:
                results.append({
                    "id": str(e.id),
                    "title": e.title,
                    "slug": e.slug,
                    "type": "EVENT",
                    "description": e.description,
                    "poster_url": e.poster_url,
                    "language": e.language
                })

        return results[:limit]
