from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.ingestion import IngestionService
from pydantic import BaseModel

router = APIRouter()

class IngestionTriggerRequest(BaseModel):
    source: str
    file_path: str

@router.post("/admin/catalog/ingestion/trigger")
async def trigger_ingestion(
    payload: IngestionTriggerRequest,
    db: AsyncSession = Depends(get_db)
):
    service = IngestionService()
    return await service.run_pipeline(db, payload.source, payload.file_path)
