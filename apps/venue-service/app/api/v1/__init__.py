from fastapi import APIRouter
from app.api.v1.venues import router as venues_router

router = APIRouter()
router.include_router(venues_router, prefix="/venues")
