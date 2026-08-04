import os
import structlog
import uuid

from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from showbook_common.database import db_manager
from showbook_common.logger import setup_logging
from showbook_common.middleware import CorrelationIDMiddleware
from showbook_common.errors import register_exception_handlers
from showbook_common.database import transaction_scope

from app.core.config import settings
from app.core.exceptions import PaymentTransactionNotFoundException, TransactionAlreadyProcessedException
from app.api.deps import get_db
from app.api.v1 import router as api_router
from app.repositories.payment_repository import PaymentRepository
from app.services.payment_service import publisher
from app.api.v1.payments import simulate_gateway_payment

setup_logging(service_name="payment-service", level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

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

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "payment-service"
    }

# Mock Gateway HTML Route
@app.get("/mock-gateway/pay", response_class=HTMLResponse)
async def get_mock_payment_page(request: Request, txn_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uuid_txn_id = uuid.UUID(txn_id)
    except ValueError:
        raise PaymentTransactionNotFoundException(details={"message": "Invalid transaction ID format"})

    txn = await PaymentRepository.get_by_id(db, uuid_txn_id)
    if not txn:
        raise PaymentTransactionNotFoundException()

    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request,
            "txn_id": str(txn.id),
            "gateway": txn.gateway,
            "amount": float(txn.amount)
        }
    )

# Mock Gateway Action Submit Route
@app.post("/mock-gateway/pay")
async def post_mock_payment_process(
    txn_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        uuid_txn_id = uuid.UUID(txn_id)
    except ValueError:
        raise PaymentTransactionNotFoundException(details={"message": "Invalid transaction ID format"})

    txn = await PaymentRepository.get_by_id(db, uuid_txn_id)
    if not txn:
        raise PaymentTransactionNotFoundException()
        
    if txn.status != "INITIATED":
        raise TransactionAlreadyProcessedException()

    async with transaction_scope(db):
        txn.status = "PENDING"

    booking_ref = f"SHB-{txn.initiated_at.strftime('%Y%m%d')}-{txn.id.hex[:6].upper()}"
    background_tasks.add_task(
        simulate_gateway_payment,
        txn.id,
        booking_ref,
        txn.user_id,
        txn.gateway,
        float(txn.amount)
    )

    return {"status": "processing", "message": "Redirecting and processing payment..."}
