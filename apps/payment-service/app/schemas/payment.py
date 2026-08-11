import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class PaymentInitiateRequest(BaseModel):
    booking_ref: str
    gateway: str  # 'MOCK_RAZORPAY', 'MOCK_STRIPE', 'MOCK_PAYU'
    idempotency_key: Optional[str] = None

class PaymentInitiateResponse(BaseModel):
    payment_txn_id: uuid.UUID
    redirect_url: str
    status: str

class CallbackPayload(BaseModel):
    payment_txn_id: uuid.UUID
    booking_ref: str
    user_id: uuid.UUID
    gateway: str
    gateway_txn_id: str
    amount: float
    status: str  # 'SUCCESS' or 'FAILED'
    failure_reason: Optional[str] = None
    signature: str

class PaymentTxnResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    gateway: str
    gateway_txn_id: Optional[str] = None
    amount: float
    status: str
    failure_reason: Optional[str] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
