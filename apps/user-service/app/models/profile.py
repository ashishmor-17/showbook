import uuid
from typing import Optional, Dict, Any
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from showbook_common.models.base import Base, TimestampMixin

class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    avatar: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True
    )
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile"
    )
