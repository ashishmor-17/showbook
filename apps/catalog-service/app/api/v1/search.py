import uuid
import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from app.api.deps import get_db
from app.services.search_service import SearchService

router = APIRouter(prefix="/catalog/search", tags=["search"])

class SearchResultItemSchema(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    type: Literal["MOVIE", "EVENT"]
    description: Optional[str] = None
    poster_url: Optional[str] = None
    language: Optional[str] = None

@router.get("", response_model=List[SearchResultItemSchema])
async def search_catalog(
    q: str = Query(..., min_length=2),
    type: Literal["MOVIE", "EVENT", "ALL"] = Query("ALL"),
    city_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    return await SearchService.search(
        db=db,
        q=q,
        type=type,
        city_id=city_id,
        limit=limit
    )
