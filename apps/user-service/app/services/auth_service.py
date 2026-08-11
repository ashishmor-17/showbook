import uuid
import secrets
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from showbook_common.database import transaction_scope

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.redis import redis_manager
from app.core.exceptions import *
from app.models.user import User
from app.models.profile import UserProfile
from app.models.token import RefreshToken
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.auth import TokenResponse, MessageResponse

class AuthService:
    @classmethod
    async def register(cls, db: AsyncSession, email: str, password_raw: str, name: str | None = None) -> MessageResponse:
        async with transaction_scope(db):
            existing = await UserRepository.get_by_email(db, email)
            if existing:
                raise UserAlreadyExistsException()
            
            hashed = hash_password(password_raw)
            user = User(email=email, hashed_password=hashed)
            profile = UserProfile(user=user, name=name)
            user.profile = profile
            await UserRepository.create(db, user)
            
        await cls.send_otp(email)
        return MessageResponse(message="User registered successfully")

    @classmethod
    async def login(cls, db: AsyncSession, email: str, password_raw: str) -> TokenResponse:
        user = await UserRepository.get_by_email(db, email)
        if not user or not verify_password(password_raw, user.hashed_password):
            raise InvalidCredentialsException()
        
        if not user.is_verified:
            raise EmailNotVerifiedException()
        
        return await cls._generate_tokens(db, user.id)

    @classmethod
    async def refresh_token(cls, db: AsyncSession, token_str: str) -> TokenResponse:
        db_token = await TokenRepository.get_by_token(db, token_str)
        if not db_token:
            raise InvalidTokenException()

        if db_token.is_used or db_token.is_revoked or db_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            if db_token.is_used:
                async with transaction_scope(db):
                    db_token.is_revoked = True
                raise TokenReusedException()
            raise InvalidTokenException()

        async with transaction_scope(db):
            db_token.is_used = True
            
        return await cls._generate_tokens(db, db_token.user_id)

    @classmethod
    async def logout(cls, db: AsyncSession, token_str: str) -> MessageResponse:
        db_token = await TokenRepository.get_by_token(db, token_str)
        if db_token:
            async with transaction_scope(db):
                db_token.is_revoked = True
        return MessageResponse(message="Logged out successfully")

    @staticmethod
    async def send_otp(email: str) -> MessageResponse:
        otp = "".join(secrets.choice("0123456789") for _ in range(6))
        
        redis_manager.client.set(f"otp:{email}", otp, ex=300)
        
        def _send():
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM
            msg["To"] = email
            msg["Subject"] = "ShowBook - Verification OTP"
            
            body = f"Hello,\n\nYour verification code is: {otp}\n\nThis OTP is valid for 5 minutes."
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.send_message(msg)
                
        try:
            await asyncio.to_thread(_send)
        except Exception as e:
            print(f"[OTP SERVICE ERROR] Failed to send email via SMTP: {e}", flush=True)
            
        # print(f"\n[OTP SERVICE] Generated OTP for {email}: {otp}\n", flush=True)
        return MessageResponse(message="OTP sent successfully")

    @classmethod
    async def verify_otp(cls, db: AsyncSession, email: str, otp: str) -> MessageResponse:
        cached_otp = redis_manager.client.get(f"otp:{email}")
        if not cached_otp or cached_otp != otp:
            raise InvalidOTPException()

        user = await UserRepository.get_by_email(db, email)
        if user:
            async with transaction_scope(db):
                user.is_verified = True

        redis_manager.client.delete(f"otp:{email}")
        return MessageResponse(message="OTP verified successfully. User account activated.")

    @staticmethod
    async def _generate_tokens(db: AsyncSession, user_id: uuid.UUID) -> TokenResponse:
        access_token = create_access_token(str(user_id))
        
        refresh_token_str = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRY)
        
        db_token = RefreshToken(
            token=refresh_token_str,
            user_id=user_id,
            expires_at=expires_at.replace(tzinfo=None)
        )
        async with transaction_scope(db):
            await TokenRepository.create(db, db_token)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)
