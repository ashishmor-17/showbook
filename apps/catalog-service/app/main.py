from fastapi import FastAPI
from contextlib import asynccontextmanager
import structlog

from showbook_common.logger import setup_logging
from showbook_common.middleware import CorrelationIDMiddleware
from showbook_common.errors import register_exception_handlers

from app.core.config import settings
from app.core.database import db_manager
from app.core.redis import redis_client
from app.core.http import http_client
from app.api.v1 import router as api_v1_router

setup_logging(service_name="catalog-service", level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("database_ready")
    yield
    logger.info("database_closing")
    await db_manager.close()
    await redis_client.close()
    await http_client.aclose()

app = FastAPI(
    title="ShowBook Catalog Service",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(CorrelationIDMiddleware)
register_exception_handlers(app)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "catalog-service"
    }
