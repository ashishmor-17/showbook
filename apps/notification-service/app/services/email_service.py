import aiosmtplib
import structlog
from email.mime.text import MIMEText

from app.core.config import settings

logger = structlog.get_logger(__name__)

class EmailService:
    @staticmethod
    async def send_email(recipient: str, subject: str, content: str) -> None:
        message = MIMEText(content, "plain")
        message["From"] = settings.SMTP_SENDER
        message["To"] = recipient
        message["Subject"] = subject

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=False
            )
            logger.info("email_sent", recipient=recipient, subject=subject)
        except Exception as e:
            logger.error("email_send_failed", recipient=recipient, error=str(e))
            raise e
