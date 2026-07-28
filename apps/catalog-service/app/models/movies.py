import uuid
from datetime import date

from sqlalchemy import String, Date, Boolean, Text, Integer, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from showbook_common.models.base import Base, TimestampMixin

class Movie(Base, TimestampMixin):
    __tablename__ = "movies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    language: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    genre: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    rating: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    release_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    poster_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    banner_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    trailer_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    cast: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    crew: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    source: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    ingestion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    __table_args__ = (
        CheckConstraint(
            "rating IN ('U', 'UA', 'A', 'S')",
            name="check_movie_rating",
        ),
        CheckConstraint(
            "source IN ('SCRAPED', 'MANUAL', 'PARTNER_API')",
            name="check_movie_source",
        ),

        Index(
            "idx_movies_slug",
            "slug",
        ),
        Index(
            "idx_movies_release_date",
            "release_date",
            postgresql_where=text("is_active = TRUE"),
        ),
        Index(
            "idx_movies_language",
            "language",
            postgresql_where=text("is_active = TRUE"),
        ),
        Index(
            "idx_movies_genre",
            "genre",
            postgresql_using="gin",
        ),
    )