import uuid
from datetime import date
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

class CastMemberSchema(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = Field(default="Actor")

class CrewMemberSchema(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)

class MovieIngestSchema(BaseModel):
    title: str = Field(..., min_length=1)
    slug: str = Field(..., pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = None
    language: str = Field(..., min_length=2)
    genre: List[str] = Field(..., min_items=1)
    duration_minutes: int = Field(..., gt=0, lt=600)
    rating: Literal["U", "UA", "A", "S"]
    release_date: Optional[date] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    trailer_url: Optional[str] = None
    cast: List[CastMemberSchema]
    crew: List[CrewMemberSchema]
    source: str
    ingestion_id: str
    is_active: bool = True

    @field_validator("poster_url", "banner_url", "trailer_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Optional[str]:
        if v == "":
            return None
        return v

class MovieResponseSchema(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    description: Optional[str] = None
    language: str
    genre: List[str]
    duration_minutes: int
    rating: str
    release_date: Optional[date] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    trailer_url: Optional[str] = None
    cast: List[dict]
    crew: List[dict]
    is_active: bool
    class Config:
        from_attributes = True
class MoviePaginationResponseSchema(BaseModel):
    items: List[MovieResponseSchema]
    next_cursor: Optional[str] = None