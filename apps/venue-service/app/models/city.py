import uuid

from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from showbook_common.models.base import Base

class City(Base):
    __tablename__ = "cities"

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
    state: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    country: Mapped[str] = mapped_column(
        String,
        default="IN",
        nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String,
        default="Asia/Kolkata",
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
