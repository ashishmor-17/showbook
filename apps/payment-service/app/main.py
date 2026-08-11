import structlog

from contextlib import asynccontextmanager
from fastapi import FastAPI

from showbook_common.database import db_manager
from showbook_common.logger import setup_logging
from showbook_common.middleware import CorrelationIDMiddleware
from showbook_common.errors import register_exception_handlers

from app.core.config import settings
from app.api.v1 import router as api_router
from app.api.mock_gateway import router as mock_gateway_router
from app.services.payment_service import publisher

setup_logging(service_name="payment-service", level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = settings.DATABASE_URL.get_secret_value()
    db_manager.init(database_url=db_url, testing=settings.TESTING)
    logger.info("database_ready")
    
    await publisher.connect()
    logger.info("rabbitmq_connected")
    
    yield
    
    logger.info("rabbitmq_closing")
    await publisher.close()
    
    logger.info("database_closing")
    await db_manager.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(CorrelationIDMiddleware)
register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(mock_gateway_router)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "payment-service"
    }
