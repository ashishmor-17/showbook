import uuid
import asyncio
import random
import httpx
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.deps import get_db
from app.core.config import settings
from app.core.utils import calculate_hmac, verify_gateway_signature
from app.core.exceptions import (
    InvalidGatewayException,
    SignatureValidationFailedException,
    PaymentTransactionNotFoundException,
    TransactionAlreadyProcessedException
)
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    CallbackPayload,
    PaymentTxnResponse,
)
from app.services.payment_service import PaymentService

logger = structlog.get_logger(__name__)
router = APIRouter()

async def simulate_gateway_payment(
    txn_id: uuid.UUID,
    booking_ref: str,
    user_id: uuid.UUID,
    gateway: str,
    amount: float
):
    await asyncio.sleep(2.0)  # Simulate gateway delay
    
    success = random.random() > 0.1
    status_result = "SUCCESS" if success else "FAILED"
    fail_reason = None if success else "INSUFFICIENT_FUNDS"
    gw_txn_id = f"gw-txn-{uuid.uuid4().hex[:12]}"
    
    callback_data = {
        "payment_txn_id": str(txn_id),
        "booking_ref": booking_ref,
        "user_id": str(user_id),
        "gateway": gateway,
        "gateway_txn_id": gw_txn_id,
        "amount": amount,
        "status": status_result,
    }
    if fail_reason:
        callback_data["failure_reason"] = fail_reason
        
    signature = calculate_hmac(callback_data, settings.GATEWAY_SECRET)
    callback_data["signature"] = signature
    
    url = f"{settings.PAYMENT_SERVICE_URL}{settings.API_V1_STR}/payments/callback"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            logger.info("triggering_mock_gateway_callback", url=url, txn_id=str(txn_id))
            resp = await client.post(url, json=callback_data)
            logger.info("mock_gateway_callback_response", status_code=resp.status_code, response=resp.text)
        except Exception as e:
            logger.error("failed_to_post_callback", error=str(e))

@router.post(
    "/initiate",
    response_model=PaymentInitiateResponse,
    status_code=status.HTTP_201_CREATED
)
async def initiate_payment(
    payload: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db)
):
    if payload.gateway not in ("MOCK_RAZORPAY", "MOCK_STRIPE", "MOCK_PAYU"):
        raise InvalidGatewayException()
        
    txn = await PaymentService.initiate(db, payload)
    redirect_url = f"{settings.PAYMENT_SERVICE_URL}/mock-gateway/pay?txn_id={txn.id}"
    
    return PaymentInitiateResponse(
        payment_txn_id=txn.id,
        redirect_url=redirect_url,
        status=txn.status
    )

@router.post("/callback")
async def payment_callback(
    payload: CallbackPayload,
    db: AsyncSession = Depends(get_db)
):
    signature_ok = verify_gateway_signature(
        payload.model_dump(mode="json", exclude_none=True), 
        payload.signature, 
        settings.GATEWAY_SECRET
    )
    if not signature_ok:
        logger.warn("callback_signature_mismatch", txn_id=str(payload.payment_txn_id))
        raise SignatureValidationFailedException()

    txn = await PaymentRepository.get_by_id(db, payload.payment_txn_id)
    if not txn:
        raise PaymentTransactionNotFoundException()

    if txn.status in ("SUCCESS", "FAILED"):
        return {"status": "ignored", "message": f"Transaction already in terminal state {txn.status}"}

    await PaymentService.process_callback(db, txn, payload.model_dump(mode="json", exclude_none=True))
    return {"status": txn.status, "message": "Callback verified and event published"}

@router.get("/{payment_txn_id}", response_model=PaymentTxnResponse)
async def get_payment_status(
    payment_txn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    txn = await PaymentRepository.get_by_id(db, payment_txn_id)
    if not txn:
        raise PaymentTransactionNotFoundException()
    return txn
