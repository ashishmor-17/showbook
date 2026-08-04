import uuid

from sqlalchemy import String, CheckConstraint, ForeignKey, DateTime, Index, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from showbook_common.models.base import Base, TimestampMixin


class PaymentTransaction(Base, TimestampMixin):
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        Text,
        unique=True,
        nullable=True,
    )
    gateway: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    gateway_txn_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="INR",
    )
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="INITIATED",
    )
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    initiated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    raw_response: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    __table_args__ = (
            CheckConstraint(
                "gateway IN ('MOCK_RAZORPAY', 'MOCK_STRIPE', 'MOCK_PAYU')",
                name="ck_payment_transactions_gateway",
            ),
            CheckConstraint(
                "status IN ('INITIATED', 'PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')",
                name="ck_payment_transactions_status",
            ),
            Index(
                "idx_payment_booking_id",
                "booking_id",
            ),
            Index(
                "idx_payment_status",
                "status",
                postgresql_where=text("status IN ('INITIATED', 'PENDING')"),
            ),
        )