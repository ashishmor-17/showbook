import json
import uuid
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
        cls, db: AsyncSession, payload: PaymentInitiateRequest
    ) -> PaymentTransaction:
        if payload.idempotency_key:
            existing = await PaymentRepository.get_by_idempotency_key(db, payload.idempotency_key)
            if existing:
                logger.info("payment_initiate_idempotent_replay", txn_id=existing.id)
                return existing

        async with transaction_scope(db):
            txn = PaymentTransaction(
                booking_id=payload.booking_id,
                user_id=payload.user_id,
                idempotency_key=payload.idempotency_key,
                gateway=payload.gateway,
                amount=payload.amount,
                currency=payload.currency,
                status="INITIATED"
            )
            await PaymentRepository.create_transaction(db, txn)
            
        return txn

    @classmethod
    async def process_callback(
        cls, db: AsyncSession, txn: PaymentTransaction, callback_data: Dict[str, Any]
    ) -> PaymentTransaction:
        async with transaction_scope(db):
            txn.status = callback_data["status"]
            txn.gateway_txn_id = callback_data["gateway_txn_id"]
            txn.failure_reason = callback_data.get("failure_reason")
            txn.completed_at = datetime.now(UTC)
            txn.raw_response = callback_data
            
        event_type = f"payment.{txn.status.lower()}"
        event_payload = {
            "payment_txn_id": str(txn.id),
            "booking_ref": callback_data["booking_ref"],
            "user_id": str(txn.user_id),
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
        return txn
