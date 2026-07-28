import json
import logging
from typing import List, Optional
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.repositories.movie import MovieRepository
from app.schemas.movies import MovieResponseSchema
from app.models.movies import Movie
from app.core.exceptions import MovieNotFoundException, ServiceUnavailableException

logger = logging.getLogger(__name__)

class MovieService:
    @staticmethod
    async def get_movies(
        db: AsyncSession,
        http_client: httpx.AsyncClient,
        language: Optional[str] = None,
        genre: Optional[str] = None,
        release_date: Optional[str] = None,
        city: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> tuple[List[Movie], Optional[str]]:
        
        movie_slugs = None
        if city:
            try:
                response = await http_client.get(
                    f"http://localhost:8000/api/v1/venues/cities/{city}/movies"
                )
                if response.status_code == 200:
                    movie_slugs = response.json().get("movie_slugs", [])
                else:
                    raise ServiceUnavailableException("venue-service")
            except Exception:
                logger.exception(f"Failed to fetch movies for city {city} from venue-service")
                raise ServiceUnavailableException("venue-service")

        items = await MovieRepository.get_movies(
            db=db,
            language=language,
            genre=genre,
            release_date=release_date,
            movie_slugs=movie_slugs,
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
