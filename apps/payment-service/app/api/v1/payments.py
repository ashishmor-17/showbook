import uuid
import asyncio
import random
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Header, status, HTTPException
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
    
    url = f"{settings.PAYMENT_SERVICE_URL}{settings.API_V1_STR}/payments/webhook/{gateway.lower()}"
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
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_uuid = uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header format")

    if payload.gateway not in ("MOCK_RAZORPAY", "MOCK_STRIPE", "MOCK_PAYU"):
        raise InvalidGatewayException()
        
    txn = await PaymentService.initiate(db, payload, user_uuid)
    redirect_url = f"{settings.PAYMENT_SERVICE_URL}/mock-gateway/pay?txn_id={txn.id}"
    
    return PaymentInitiateResponse(
        payment_txn_id=txn.id,
        redirect_url=redirect_url,
        status=txn.status
    )

@router.post("/webhook/{gateway}")
@router.post("/callback")
async def payment_callback(
    payload: CallbackPayload,
    gateway: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    if gateway:
        expected_gw = gateway.upper()
        payload_gw = payload.gateway.upper()
        if expected_gw != payload_gw and f"MOCK_{expected_gw}" != payload_gw:
            raise InvalidGatewayException(details={"message": f"Gateway mismatch: {gateway} vs {payload.gateway}"})

    signature_ok = verify_gateway_signature(
        payload.model_dump(mode="json", exclude_none=True), 
        payload.signature, 
        settings.GATEWAY_SECRET
    )
    if not signature_ok:
        logger.warn("callback_signature_mismatch", txn_id=str(payload.payment_txn_id))
        raise SignatureValidationFailedException()

    res = await PaymentService.process_callback(
        db, payload.payment_txn_id, payload.model_dump(mode="json", exclude_none=True)
    )
    return res

@router.get("/{payment_txn_id}", response_model=PaymentTxnResponse)
async def get_payment_status(
    payment_txn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await PaymentService.get_payment_txn(db, payment_txn_id)
