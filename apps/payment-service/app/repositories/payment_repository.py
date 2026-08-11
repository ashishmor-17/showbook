import uuid

from sqlalchemy import select, text
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

    @staticmethod
    async def get_booking_by_ref(db: AsyncSession, booking_ref: str):
        query = text(
            "SELECT id, user_id, status, final_amount_paise, currency "
            "FROM bookings WHERE booking_ref = :ref"
        )
        result = await db.execute(query, {"ref": booking_ref})
        return result.fetchone()

    @staticmethod
    async def get_booking_ref_by_id(db: AsyncSession, booking_id: uuid.UUID) -> str | None:
        query = text(
            "SELECT booking_ref FROM bookings WHERE id = :booking_id"
        )
        result = await db.execute(query, {"booking_id": booking_id})
        row = result.fetchone()
        return row[0] if row else None
