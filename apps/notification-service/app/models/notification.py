import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Index, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from showbook_common.models.base import Base, TimestampMixin

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    recipient: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    type: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    channel: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    subject: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    notification_payload: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="PENDING"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


    __table_args__ = (

        CheckConstraint(
            "channel IN ('EMAIL','SMS','IN_APP')",
            name="notification_channel_check"
        ),

        CheckConstraint(
            "status IN ('PENDING','SENT','FAILED','SKIPPED')",
            name="notification_status_check"
        ),

        Index(
            "idx_notifications_user_created",
            "user_id",
            "created_at"
        ),

        Index(
            "idx_notifications_pending",
            "status",
            "retry_count",
            postgresql_where=(
                status.in_(["PENDING", "FAILED"])
            )
        )
    )