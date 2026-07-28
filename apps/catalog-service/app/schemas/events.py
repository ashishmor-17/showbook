import uuid
from typing import List, Optional
from pydantic import BaseModel

class EventResponseSchema(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    type: str
    description: Optional[str] = None
    language: Optional[str] = None
    duration_minutes: Optional[int] = None
    age_restriction: Optional[str] = None
    poster_url: Optional[str] = None
    is_active: bool
    class Config:
        from_attributes = True

class EventPaginationResponseSchema(BaseModel):
    items: List[EventResponseSchema]
    next_cursor: Optional[str] = None