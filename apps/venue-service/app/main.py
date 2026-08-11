import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from showbook_common.database import db_manager
from showbook_common.logger import setup_logging
from showbook_common.middleware import CorrelationIDMiddleware
from showbook_common.errors import register_exception_handlers

from app.core.config import settings
from app.core.http import http_client
from app.api.v1 import router as api_router

setup_logging(service_name="venue-service", level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = settings.DATABASE_URL.get_secret_value()
    db_manager.init(database_url=db_url, testing=settings.TESTING)
    logger.info("database_ready")
    
    http_client.start()
    logger.info("http_client_started")
    
    yield
    
    logger.info("http_client_closing")
    await http_client.close()
    
    logger.info("database_closing")
    await db_manager.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Enable correlation tracking for downstream traces
app.add_middleware(CorrelationIDMiddleware)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "venue-service"
    }

@app.get("/live")
async def liveness_check():
    return {
        "status": "up",
        "service": "venue-service"
    }

@app.get("/ready")
async def readiness_check():
    try:
        await db_manager.check_db_connection()
    except Exception:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {
        "status": "up",
        "service": "venue-service"
    }
