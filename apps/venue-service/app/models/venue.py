import uuid

from sqlalchemy import String, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from showbook_common.models.base import Base, TimestampMixin

class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id",ondelete="RESTRICT"),
        nullable=False
    )
    address: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    latitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )
    amenities: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )
    partner_code: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    city = relationship("City", backref="venues")