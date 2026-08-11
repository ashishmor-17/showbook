from fastapi import APIRouter
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.movies import router as movies_router
from app.api.v1.events import router as events_router
from app.api.v1.search import router as search_router

router = APIRouter()
router.include_router(ingestion_router)
router.include_router(movies_router)
router.include_router(events_router)
router.include_router(search_router)
