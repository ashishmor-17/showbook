import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI

from showbook_common.logger import setup_logging
from showbook_common.middleware import CorrelationIDMiddleware
from showbook_common.errors import register_exception_handlers

from app.core.config import settings
from app.api.deps import db_manager
from app.core.consumer import consumer
from app.core.http import http_client
from app.api.v1.router import router as api_router

setup_logging(service_name="notification-service", level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = settings.DATABASE_URL.get_secret_value()
    db_manager.init(database_url=db_url, testing=settings.TESTING)
    logger.info("database_ready")
    
    http_client.start()
    await consumer.start()
    
    yield
    
    await consumer.stop()
    await http_client.close()
    await db_manager.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(CorrelationIDMiddleware)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "notification-service"
    }
