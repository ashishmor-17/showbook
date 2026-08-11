import uuid
from typing import List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movies import Movie
from app.schemas.movies import MovieIngestSchema

class MovieRepository:
    @staticmethod
    async def upsert_bulk(db: AsyncSession, movies: List[MovieIngestSchema]) -> int:
        if not movies:
            return 0

        insert_data = [movie.model_dump() for movie in movies]
        query = insert(Movie).values(insert_data)
        
        upsert_query = query.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "title": query.excluded.title,
                "description": query.excluded.description,
                "language": query.excluded.language,
                "genre": query.excluded.genre,
                "duration_minutes": query.excluded.duration_minutes,
                "rating": query.excluded.rating,
                "release_date": query.excluded.release_date,
                "poster_url": query.excluded.poster_url,
                "banner_url": query.excluded.banner_url,
                "trailer_url": query.excluded.trailer_url,
                "cast": query.excluded.cast,
                "crew": query.excluded.crew,
                "ingestion_id": query.excluded.ingestion_id,
                "is_active": query.excluded.is_active,
            }
        )

        result = await db.execute(upsert_query)
        return result.rowcount

    @staticmethod
    async def get_movies(
        db: AsyncSession,
        language: Optional[str] = None,
        genre: Optional[str] = None,
        release_date: Optional[str] = None,
        movie_slugs: Optional[List[str]] = None,
        movie_ids: Optional[List[uuid.UUID]] = None,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> List[Movie]:

        query = select(Movie).where(Movie.is_active == True)

        if language:
            query = query.where(Movie.language == language)
        if genre:
            query = query.where(Movie.genre.any(genre))
        if release_date:
            query = query.where(Movie.release_date >= release_date)
        if movie_slugs is not None:
            query = query.where(Movie.slug.in_(movie_slugs))
        if movie_ids is not None:
            query = query.where(Movie.id.in_(movie_ids))
        if cursor:
            try:
                cursor_uuid = uuid.UUID(cursor)
                query = query.where(Movie.id > cursor_uuid)
            except ValueError:
                pass

        query = query.order_by(Movie.id.asc()).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Movie]:
        query = select(Movie).where(Movie.slug == slug, Movie.is_active == True)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def search_movies(
        db: AsyncSession,
        query_str: str,
        allowed_ids: Optional[set] = None,
        limit: int = 10
    ) -> List[Movie]:
        query = select(Movie).where(
            and_(
                Movie.is_active == True,
                or_(
                    Movie.title.ilike(f"%{query_str}%"),
                    Movie.description.ilike(f"%{query_str}%")
                )
            )
        )
        if allowed_ids is not None:
            query = query.where(Movie.id.in_(allowed_ids))
        query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, movie_id: uuid.UUID) -> Optional[Movie]:
        query = select(Movie).where(Movie.id == movie_id, Movie.is_active == True)
        result = await db.execute(query)
        return result.scalar_one_or_none()
