import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import PaymentTransaction
from app.models.refund import Refund

class PaymentRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, txn_id: uuid.UUID) -> PaymentTransaction | None:
        result = await db.execute(select(PaymentTransaction).where(PaymentTransaction.id == txn_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_idempotency_key(db: AsyncSession, key: str) -> PaymentTransaction | None:
        result = await db.execute(select(PaymentTransaction).where(PaymentTransaction.idempotency_key == key))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_transaction(db: AsyncSession, txn: PaymentTransaction) -> PaymentTransaction:
        db.add(txn)
        return txn

    @staticmethod
    async def create_refund(db: AsyncSession, refund: Refund) -> Refund:
        db.add(refund)
        return refund
