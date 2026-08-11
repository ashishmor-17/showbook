import httpx
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from redis.asyncio import Redis

from app.api.deps import get_db
from app.core.redis import get_redis
from app.services.movie import MovieService
from app.schemas.movies import MovieResponseSchema, MoviePaginationResponseSchema

router = APIRouter(prefix="/catalog/movies", tags=["movies"])

@router.get("", response_model=MoviePaginationResponseSchema)
async def list_movies(
    language: Optional[str] = None,
    genre: Optional[str] = None,
    release_date: Optional[str] = None,
    city: Optional[str] = None,
    city_id: Optional[uuid.UUID] = None,
    date: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    items, next_cursor = await MovieService.get_movies(
        db=db,
        language=language,
        genre=genre,
        release_date=release_date,
        city=city,
        city_id=city_id,
        date=date,
        cursor=cursor,
        limit=limit
    )
    return {
        "items": items,
        "next_cursor": next_cursor
    }

@router.get("/search", response_model=List[MovieResponseSchema])
async def search_movies(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db)
):
    return await MovieService.search_movies(db, q)

@router.get("/{slug}", response_model=MovieResponseSchema)
async def get_movie_detail(
    slug: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await MovieService.get_movie_detail(db, redis, slug)

@router.get("/id/{movie_id}", response_model=MovieResponseSchema)
async def get_movie_by_id(
    movie_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await MovieService.get_movie_by_id(db, movie_id)
