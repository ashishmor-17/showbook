import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from showbook_common.models.base import Base


class SeatType(Base):
    __tablename__ = "seat_types"
    __table_args__ = (
        UniqueConstraint(
            "screen_id",
            "name",
            name="uq_seat_types_screen_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    screen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screens.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    total_seats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    color_hex: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    screen = relationship("Screen", backref="seat_types")


class SeatLayout(Base):
    __tablename__ = "seat_layout"
    __table_args__ = (
        UniqueConstraint(
            "screen_id",
            "seat_code",
            name="uq_seat_layout_screen_seat_code",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    screen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screens.id", ondelete="CASCADE"),
        nullable=False,
    )
    seat_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seat_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    row_label: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    seat_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    seat_code: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    screen = relationship("Screen", backref="seats")
    seat_type = relationship("SeatType", backref="seats")