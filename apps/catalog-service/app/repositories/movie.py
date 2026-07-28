from typing import List
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
        stmt = insert(Movie).values(insert_data)
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "language": stmt.excluded.language,
                "genre": stmt.excluded.genre,
                "duration_minutes": stmt.excluded.duration_minutes,
                "rating": stmt.excluded.rating,
                "release_date": stmt.excluded.release_date,
                "poster_url": stmt.excluded.poster_url,
                "banner_url": stmt.excluded.banner_url,
                "trailer_url": stmt.excluded.trailer_url,
                "cast": stmt.excluded.cast,
                "crew": stmt.excluded.crew,
                "ingestion_id": stmt.excluded.ingestion_id,
                "is_active": stmt.excluded.is_active,
            }
        )

        result = await db.execute(upsert_stmt)
        return result.rowcount
