import uuid
from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from showbook_common.models.base import Base, TimestampMixin


class Showtime(Base, TimestampMixin):
    __tablename__ = "showtimes"
    __table_args__ = (
        UniqueConstraint(
            "screen_id",
            "show_date",
            "start_time",
            name="uq_showtimes_screen_slot",
        ),
        CheckConstraint(
            "catalog_type IN ('MOVIE', 'EVENT')",
            name="check_catalog_type",
        ),
        CheckConstraint(
            "status IN ('SCHEDULED', 'OPEN', 'SOLD_OUT', 'CANCELLED', 'COMPLETED')",
            name="check_showtime_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    screen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screens.id", ondelete="RESTRICT"),
        nullable=False,
    )
    venue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("venues.id", ondelete="RESTRICT"),
        nullable=False,
    )
    catalog_ref_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    catalog_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    show_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    format: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String,
        default="SCHEDULED",
        nullable=False,
    )
    booking_open_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    screen = relationship("Screen", backref="showtimes")
    venue = relationship("Venue", backref="showtimes")


class ShowtimeSeatPricing(Base):
    __tablename__ = "showtime_seat_pricing"
    __table_args__ = (
        UniqueConstraint(
            "showtime_id",
            "seat_type_id",
            name="uq_showtime_seat_pricing",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    showtime_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("showtimes.id", ondelete="CASCADE"),
        nullable=False,
    )
    seat_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seat_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    convenience_fee: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
    )

    showtime = relationship("Showtime", backref="pricing")
    seat_type = relationship("SeatType", backref="pricing")