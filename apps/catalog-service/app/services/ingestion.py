import os
import json
import asyncio
import uuid
import structlog
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from showbook_common.database import transaction_scope

from app.repositories.movie import MovieRepository
from app.repositories.ingestion import IngestionRepository
from app.ingestion.normalizer import normalize_movie
from app.ingestion.validator import validate_normalized_movies

logger = structlog.get_logger(__name__)

# Resolve workspace root dynamically (4 levels up from this file)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", ".."))

class IngestionService:
    async def run_pipeline(self, db: AsyncSession, source: str, file_path: str) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        log = logger.bind(ingestion_run_id=run_id)
        
        # Standardize and resolve path relative to workspace root if it references the data directory
        normalized_path = file_path.replace("\\", "/")
        if "data/" in normalized_path:
            relative_data_path = normalized_path.split("data/")[-1]
            resolved_path = os.path.join(WORKSPACE_ROOT, "data", relative_data_path)
        else:
            resolved_path = os.path.abspath(file_path)

        log.info("ingestion_pipeline_started", source=source, file_path=resolved_path)

        def load_file():
            with open(resolved_path, "r", encoding="utf-8") as f:
                return json.load(f)

        try:
            raw_movies = await asyncio.to_thread(load_file)
        except Exception as e:
            log.error("failed_to_read_ingestion_file", error=str(e), path=resolved_path)
            raise ValueError(f"Failed to read ingestion file: {str(e)}")

        await IngestionRepository.create_run(db, run_id, len(raw_movies))

        try:
            normalized = [normalize_movie(movie, run_id, source) for movie in raw_movies]
            valid_schemas, failed_records = validate_normalized_movies(normalized)
            
            log.info(
                "ingestion_validation_complete",
                valid_count=len(valid_schemas),
                failed_count=len(failed_records)
            )

            async with transaction_scope(db):
                await MovieRepository.upsert_bulk(db, valid_schemas)

                for raw_data, err_msg in failed_records:
                    await IngestionRepository.create_dead_letter(
                        db=db,
                        run_id=run_id,
                        stage="VALIDATOR",
                        error_message=err_msg,
                        raw_payload=raw_data
                    )

                await IngestionRepository.update_run_status(
                    db=db,
                    run_id=run_id,
                    status="COMPLETED",
                    imported=len(valid_schemas),
                    failed=len(failed_records)
                )

            log.info(
                "ingestion_pipeline_success",
                imported=len(valid_schemas),
                failed=len(failed_records)
            )
            return {
                "status": "COMPLETED",
                "ingestion_run_id": run_id,
                "imported": len(valid_schemas),
                "failed": len(failed_records)
            }

        except Exception as e:
            log.exception("ingestion_pipeline_critical_failure")
            
            await IngestionRepository.update_run_status(
                db=db,
                run_id=run_id,
                status="FAILED",
                imported=0,
                failed=len(raw_movies)
            )
            await db.commit()
            raise e
