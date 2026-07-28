from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.event import EventService
from app.schemas.events import EventResponseSchema, EventPaginationResponseSchema

router = APIRouter(prefix="/catalog/events", tags=["events"])

@router.get("", response_model=EventPaginationResponseSchema)
async def list_events(
    cursor: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    items, next_cursor = await EventService.get_events(db=db, cursor=cursor, limit=limit)
    return {
        "items": items,
        "next_cursor": next_cursor
    }

@router.get("/{slug}", response_model=EventResponseSchema)
async def get_event_detail(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    return await EventService.get_event_detail(db, slug)
