from datetime import datetime, UTC
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ingestion_runs import IngestionRun
from app.models.ingestion_dead_letter import IngestionDeadLetter

class IngestionRepository:
    @staticmethod
    async def create_run(db: AsyncSession, run_id: str, total_records: int) -> IngestionRun:
        run_record = IngestionRun(
            id=run_id,
            status="RUNNING",
            source="SCRAPER",
            records_scraped=total_records,
            records_imported=0,
            records_failed=0,
        )
        db.add(run_record)
        await db.flush()
        return run_record

    @staticmethod
    async def update_run_status(
        db: AsyncSession, run_id: str, status: str, imported: int, failed: int
    ) -> None:
        run_record = await db.get(IngestionRun, run_id)
        if run_record:
            run_record.status = status
            run_record.records_imported = imported
            run_record.records_failed = failed
            run_record.completed_at = datetime.now(UTC)

    @staticmethod
    async def create_dead_letter(
        db: AsyncSession, run_id: str, stage: str, error_message: str, raw_payload: Dict[str, Any]
    ) -> None:
        dead_letter = IngestionDeadLetter(
            run_id=run_id,
            stage=stage,
            error_message=error_message,
            raw_payload=raw_payload,
        )
        db.add(dead_letter)
