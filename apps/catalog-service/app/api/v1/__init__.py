from fastapi import APIRouter
from .ingestion import router as ingestion_router

router = APIRouter()
router.include_router(ingestion_router)
