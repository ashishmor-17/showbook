import asyncio
import uuid
from datetime import datetime, UTC
import httpx
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from showbook_common.database import transaction_scope
from app.core.config import settings
from app.core.http import http_client
from app.models.notification import Notification
from app.models.processed_event import ProcessedEvent
from app.repositories.notification import NotificationRepository
from app.repositories.processed_event import ProcessedEventRepository
from app.services.email_service import EmailService
from app.api.deps import db_manager

logger = structlog.get_logger(__name__)

class NotificationService:
    @classmethod
    async def get_notifications_for_user(
        cls, 
        db: AsyncSession, 
        user_id: uuid.UUID, 
        limit: int, 
        cursor: str | None = None
    ) -> tuple[list[Notification], str | None]:
        cursor_dt = None
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
            except ValueError:
                pass
                
        notifications = await NotificationRepository.get_by_user_id_paginated(db, user_id, limit, cursor_dt)
        
        next_cursor = None
        if notifications and len(notifications) == limit:
            next_cursor = notifications[-1].created_at.isoformat()
            
        return notifications, next_cursor

    @classmethod
    async def process_event(cls, event: dict, db: AsyncSession) -> None:
        event_id = uuid.UUID(event["event_id"])
        event_type = event["event_type"]
        payload = event["payload"]
        
        # Deduplication check
        existing = await ProcessedEventRepository.get_by_id(db, event_id)
        if existing:
            logger.info("event_already_processed", event_id=str(event_id))
            return

        user_id = payload.get("user_id")
        if not user_id:
            logger.warn("event_missing_user_id", event_id=str(event_id))
            return

        recipient_email = payload.get("user_email")
        recipient_name = payload.get("user_name") or "Customer"
        recipient_phone = payload.get("user_phone") or ""

        if not recipient_email:
            logger.warn("event_missing_recipient_email", event_id=str(event_id), user_id=str(user_id))
            return

        # Create ProcessedEvent entry
        processed_event = ProcessedEvent(
            event_id=event_id,
            event_type=event_type
        )
        
        # Generate notification(s)
        notifications_to_create = []
        booking_ref = payload.get("booking_ref")
        
        if event_type == "booking.confirmed":
            # Email Notification
            email_subject = f"Your booking is confirmed! 🎬 {payload['movie_title']}"
            email_body = f"Hi {recipient_name},\n\nYour booking is confirmed!\n\n" \
                         f"Movie: {payload['movie_title']}\n" \
                         f"Venue: {payload['venue_name']}\n" \
                         f"Date: {payload['show_date']} at {payload['start_time']}\n" \
                         f"Seats: {', '.join(payload['seat_codes'])}\n" \
                         f"Booking Ref: {booking_ref}\n" \
                         f"Amount Paid: ₹{payload['total_amount']:.2f}\n\nEnjoy the show!"
            
            notifications_to_create.append(Notification(
                user_id=uuid.UUID(user_id),
                recipient=recipient_email,
                type=event_type,
                channel="EMAIL",
                subject=email_subject,
                body=email_body,
                notification_payload=payload,
                status="PENDING"
            ))

            # SMS Notification
            sms_body = f"Hi {recipient_name}, booking {booking_ref} confirmed! Seats: {', '.join(payload['seat_codes'])}. Enjoy!"
            print(f"\n [MOCK SMS TO {recipient_phone or 'N/A'}]: {sms_body}\n")
            
            notifications_to_create.append(Notification(
                user_id=uuid.UUID(user_id),
                recipient=recipient_phone,
                type=event_type,
                channel="SMS",
                subject=None,
                body=sms_body,
                notification_payload=payload,
                status="SENT",
                sent_at=datetime.now(UTC)
            ))

        elif event_type == "booking.cancelled":
            email_subject = "Your booking has been cancelled."
            email_body = f"Hi {recipient_name},\n\nYour booking ({booking_ref}) has been cancelled.\n" \
                         f"Reason: {payload.get('cancellation_reason', 'System Cancelled')}\n"
            if payload.get("refund_eligible"):
                email_body += f"Refund amount of ₹{payload.get('refund_amount', 0.0):.2f} has been initiated."
            
            notifications_to_create.append(Notification(
                user_id=uuid.UUID(user_id),
                recipient=recipient_email,
                type=event_type,
                channel="EMAIL",
                subject=email_subject,
                body=email_body,
                notification_payload=payload,
                status="PENDING"
            ))

        elif event_type == "payment.failed":
            email_subject = "Payment Failed for your booking."
            email_body = f"Hi {recipient_name},\n\nPayment attempt failed for booking {booking_ref}.\n" \
                         f"Reason: {payload.get('failure_reason', 'Declined by Bank')}.\n" \
                         f"Please try initiating the booking again."
            
            notifications_to_create.append(Notification(
                user_id=uuid.UUID(user_id),
                recipient=recipient_email,
                type=event_type,
                channel="EMAIL",
                subject=email_subject,
                body=email_body,
                notification_payload=payload,
                status="PENDING"
            ))

        elif event_type == "payment.refunded":
            email_subject = "Refund Processed successfully."
            email_body = f"Hi {recipient_name},\n\nRefund for booking {booking_ref} has been processed successfully.\n" \
                         f"Amount: ₹{payload.get('refund_amount', 0.0):.2f}."
            
            notifications_to_create.append(Notification(
                user_id=uuid.UUID(user_id),
                recipient=recipient_email,
                type=event_type,
                channel="EMAIL",
                subject=email_subject,
                body=email_body,
                notification_payload=payload,
                status="PENDING"
            ))

        if not notifications_to_create:
            logger.info("unhandled_event_type_skipping", event_type=event_type)
            return

        # Persist processed event and notifications atomically
        async with transaction_scope(db):
            await ProcessedEventRepository.create(db, processed_event)
            for notification in notifications_to_create:
                await NotificationRepository.create(db, notification)

        # Dispatch EMAIL notifications asynchronously
        for notification in notifications_to_create:
            if notification.channel == "EMAIL" and notification.status == "PENDING":
                asyncio.create_task(cls.dispatch_email_with_retries(notification.id))

    @classmethod
    async def dispatch_email_with_retries(cls, notification_id: uuid.UUID) -> None:
        for attempt in range(1, 4):
            async with db_manager.get_db_context() as db:
                notification = await NotificationRepository.get_by_id(db, notification_id)
                if not notification:
                    return

                try:
                    await EmailService.send_email(
                        recipient=notification.recipient,
                        subject=notification.subject,
                        content=notification.body
                    )
                    async with transaction_scope(db):
                        notification.status = "SENT"
                        notification.sent_at = datetime.now(UTC)
                        notification.retry_count = attempt - 1
                    return
                except Exception as e:
                    logger.warn("delivery_attempt_failed", attempt=attempt, error=str(e))
                    async with transaction_scope(db):
                        notification.retry_count = attempt
                        if attempt == 3:
                            notification.status = "FAILED"
            
            if attempt < 3:
                # Exponential backoff (2s, 4s, 8s)
                await asyncio.sleep(2 ** attempt)
