import json
import uuid
import httpx
from datetime import datetime, UTC
from typing import Any, Dict, Optional
import aio_pika
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from showbook_common.database import transaction_scope

from app.core.config import settings
from app.models.payment import PaymentTransaction
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentInitiateRequest
from app.core.exceptions import *

logger = structlog.get_logger(__name__)

class MQPublisher:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.exchange: Optional[aio_pika.RobustExchange] = None

    async def connect(self):
        logger.info("rabbitmq_connecting", url=settings.RABBITMQ_URL)
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            "showbook.events", 
            aio_pika.ExchangeType.TOPIC, 
            durable=True
        )
        logger.info("rabbitmq_connected")

    async def publish(self, routing_key: str, message: Dict[str, Any]):
        if not self.exchange:
            raise RuntimeError("RabbitMQ publisher not connected")
        
        body = json.dumps(message).encode("utf-8")
        await self.exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )
        logger.info("event_published", routing_key=routing_key, event_id=message.get("event_id"))

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

publisher = MQPublisher()

class PaymentService:
    @classmethod
    async def initiate(
        cls, db: AsyncSession, payload: PaymentInitiateRequest, user_id: uuid.UUID
    ) -> PaymentTransaction:
        if payload.idempotency_key:
            existing = await PaymentRepository.get_by_idempotency_key(db, payload.idempotency_key)
            if existing:
                logger.info("payment_initiate_idempotent_replay", txn_id=existing.id)
                return existing
        
        row = await PaymentRepository.get_booking_by_ref(db, payload.booking_ref)
        if not row:
            raise BookingNotFoundException()
        
        booking_id, b_user_id, status, final_amount_paise, currency = row
        
        # Validate that the booking belongs to the current user
        if b_user_id != user_id:
            raise AccessDeniedException()
            
        amount_rupees = float(final_amount_paise) / 100.0

        async with transaction_scope(db):
            txn = PaymentTransaction(
                booking_id=booking_id,
                user_id=user_id,
                idempotency_key=payload.idempotency_key,
                gateway=payload.gateway,
                amount=amount_rupees,
                currency=currency,
                status="INITIATED"
            )
            await PaymentRepository.create_transaction(db, txn)
            
        return txn

    @classmethod
    async def get_payment_txn(cls, db: AsyncSession, txn_id: uuid.UUID) -> PaymentTransaction:
        txn = await PaymentRepository.get_by_id(db, txn_id)
        if not txn:
            raise PaymentTransactionNotFoundException()
        return txn

    @classmethod
    async def process_callback(
        cls, db: AsyncSession, txn_id: uuid.UUID, callback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        txn = await PaymentRepository.get_by_id(db, txn_id)
        if not txn:
            raise PaymentTransactionNotFoundException()

        if txn.status in ("SUCCESS", "FAILED"):
            return {"status": "ignored", "message": f"Transaction already in terminal state {txn.status}"}

        async with transaction_scope(db):
            txn.status = callback_data["status"]
            txn.gateway_txn_id = callback_data["gateway_txn_id"]
            txn.failure_reason = callback_data.get("failure_reason")
            txn.completed_at = datetime.now(UTC)
            txn.raw_response = callback_data

        user_email = ""
        user_name = "Customer"
        user_phone = ""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.USER_SERVICE_URL}/api/internal/users/{txn.user_id}",
                    headers={"X-Internal-Service": "true"},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    profile = resp.json()
                    user_email = profile.get("email") or ""
                    user_name = profile.get("name") or "Customer"
                    user_phone = profile.get("phone") or ""
                else:
                    logger.error("failed_fetching_user_profile_for_payment_event", status=resp.status_code)
        except Exception as e:
            logger.error("error_fetching_user_profile_for_payment_event", error=str(e))
            
        event_type = f"payment.{txn.status.lower()}"
        event_payload = {
            "payment_txn_id": str(txn.id),
            "booking_ref": callback_data["booking_ref"],
            "user_id": str(txn.user_id),
            "user_email": user_email,
            "user_name": user_name,
            "user_phone": user_phone,
            "gateway": txn.gateway,
            "amount": float(txn.amount),
        }
        if txn.status == "SUCCESS":
            event_payload["gateway_txn_id"] = txn.gateway_txn_id
            event_payload["currency"] = txn.currency
        else:
            event_payload["failure_reason"] = txn.failure_reason

        envelope = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_version": 1,
            "occurred_at": datetime.now(UTC).isoformat(),
            "producer": "payment-service",
            "correlation_id": str(uuid.uuid4()),
            "payload": event_payload
        }
        
        await publisher.publish(event_type, envelope)
        return {"status": txn.status, "message": "Callback verified and event published"}

    @classmethod
    async def get_mock_payment_details(cls, db: AsyncSession, txn_id: str) -> PaymentTransaction:
        try:
            uuid_txn_id = uuid.UUID(txn_id)
        except ValueError:
            raise PaymentTransactionNotFoundException(details={"message": "Invalid transaction ID format"})

        txn = await PaymentRepository.get_by_id(db, uuid_txn_id)
        if not txn:
            raise PaymentTransactionNotFoundException()
        return txn

    @classmethod
    async def process_mock_payment(
        cls,
        db: AsyncSession,
        txn_id: str,
        background_tasks: Any
    ) -> dict:
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
        try:
            real_ref = await PaymentRepository.get_booking_ref_by_id(db, txn.booking_id)
            if real_ref:
                booking_ref = real_ref
                logger.info("fetched_real_booking_ref_for_callback", booking_ref=booking_ref)
        except Exception as e:
            logger.error("failed_to_fetch_booking_ref_for_callback", error=str(e))

        from app.api.v1.payments import simulate_gateway_payment
        background_tasks.add_task(
            simulate_gateway_payment,
            txn.id,
            booking_ref,
            txn.user_id,
            txn.gateway,
            float(txn.amount)
        )

        return {"status": "processing", "message": "Redirecting and processing payment..."}
