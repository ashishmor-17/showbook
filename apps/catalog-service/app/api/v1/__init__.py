from fastapi import APIRouter
from .ingestion import router as ingestion_router
from .movies import router as movies_router
from .events import router as events_router

router = APIRouter()
router.include_router(ingestion_router)
router.include_router(movies_router)
router.include_router(events_router)
