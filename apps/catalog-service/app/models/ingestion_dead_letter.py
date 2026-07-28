import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from showbook_common.models.base import Base, TimestampMixin

class IngestionDeadLetter(Base, TimestampMixin):
    __tablename__ = "ingestion_dead_letter"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion_runs.id"),
        nullable=False,
    )
    raw_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "stage IN ('NORMALIZER', 'VALIDATOR', 'IMPORTER')",
            name="check_failed_record_stage",
        ),
    )