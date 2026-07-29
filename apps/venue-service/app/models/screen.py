import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from showbook_common.models.base import Base


class Screen(Base):
    __tablename__ = "screens"
    __table_args__ = (
        CheckConstraint(
            "screen_type IN ('2D', '3D', 'IMAX', 'DOLBY', '4DX')",
            name="check_screen_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    venue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    total_capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    screen_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    venue = relationship("Venue", backref="screens")