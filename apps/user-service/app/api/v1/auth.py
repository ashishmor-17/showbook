from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.exceptions import RateLimitExceededException
from app.core.redis import redis_manager
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    SendOTPRequest,
    VerifyOTPRequest,
    MessageResponse
)
from app.models.user import User

router = APIRouter()

def rate_limit_login(request: Request):
    ip = request.client.host
    allowed = redis_manager.check_rate_limit(ip, capacity=5, refill_rate=5, refill_period=60)
    if not allowed:
        raise RateLimitExceededException()

@router.post("/register", response_model=MessageResponse)
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.register(db, payload.email, payload.password)

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_login)])
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(db, payload.email, payload.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh_token(db, payload.refresh_token)

@router.post("/logout", response_model=MessageResponse)
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.logout(db, payload.refresh_token)

@router.post("/send-otp", response_model=MessageResponse)
async def send_otp(payload: SendOTPRequest):
    return await AuthService.send_otp(payload.email)

@router.post("/verify-otp", response_model=MessageResponse)
async def verify_otp(payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.verify_otp(db, payload.email, payload.otp)

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified
    }
