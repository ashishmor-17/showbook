import json
import logging
import uuid
from typing import List, Optional
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.repositories.movie import MovieRepository
from app.schemas.movies import MovieResponseSchema
from app.models.movies import Movie
from app.core.exceptions import MovieNotFoundException, ServiceUnavailableException
from app.core.config import settings

from app.core.http import http_client

logger = logging.getLogger(__name__)

class MovieService:
    @staticmethod
    async def get_movies(
        db: AsyncSession,
        language: Optional[str] = None,
        genre: Optional[str] = None,
        release_date: Optional[str] = None,
        city: Optional[str] = None,
        city_id: Optional[uuid.UUID] = None,
        date: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> tuple[List[Movie], Optional[str]]:
        
        movie_ids = None
        movie_slugs = None
        
        resolved_city_id = city_id
        if city and not resolved_city_id:
            try:
                response = await http_client.get(f"{settings.VENUE_SERVICE_URL}/api/v1/venues/cities")
                if response.status_code == 200:
                    cities_list = response.json().get("cities", [])
                    for c in cities_list:
                        if c.get("slug", "").lower() == city.lower():
                            resolved_city_id = uuid.UUID(c.get("id"))
                            break
            except Exception:
                logger.exception("Failed to resolve city slug to id")

        if resolved_city_id:
            filter_date = date or release_date
            if not filter_date:
                from datetime import date as dt_date
                filter_date = dt_date.today().isoformat()
            try:
                response = await http_client.get(
                    f"{settings.VENUE_SERVICE_URL}/api/v1/venues/cities/{resolved_city_id}/catalog-refs",
                    params={"date": filter_date, "catalog_type": "MOVIE"}
                )
                if response.status_code == 200:
                    raw_ids = response.json().get("catalog_ref_ids", [])
                    movie_ids = [uuid.UUID(rid) for rid in raw_ids]
                else:
                    raise ServiceUnavailableException("venue-service")
            except Exception:
                logger.exception(f"Failed to fetch catalog-refs for city_id {resolved_city_id} from venue-service")
                raise ServiceUnavailableException("venue-service")

        items = await MovieRepository.get_movies(
            db=db,
            language=language,
            genre=genre,
            release_date=release_date,
            movie_slugs=movie_slugs,
            movie_ids=movie_ids,
            cursor=cursor,
            limit=limit
        )

        next_cursor = None
        if len(items) == limit:
            next_cursor = str(items[-1].id)

        return items, next_cursor

    @staticmethod
    async def get_movie_detail(
        db: AsyncSession,
        redis: Redis,
        slug: str
    ) -> dict:
        cache_key = f"movie:{slug}"

        try:
            cached_data = await redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            logger.exception("Failed to read from Redis cache")

        movie = await MovieRepository.get_by_slug(db, slug)
        if not movie:
            raise MovieNotFoundException(slug)

        movie_dict = MovieResponseSchema.model_validate(movie).model_dump(mode="json")
        try:
            await redis.set(cache_key, json.dumps(movie_dict), ex=300)
        except Exception:
            logger.exception("Failed to write to Redis cache")

        return movie_dict

    @staticmethod
    async def search_movies(db: AsyncSession, query_str: str) -> List[Movie]:
        return await MovieRepository.search_movies(db, query_str)

    @staticmethod
    async def get_movie_by_id(db: AsyncSession, movie_id: uuid.UUID) -> dict:
        movie = await MovieRepository.get_by_id(db, movie_id)
        if not movie:
            raise MovieNotFoundException(str(movie_id))
        return MovieResponseSchema.model_validate(movie).model_dump(mode="json")