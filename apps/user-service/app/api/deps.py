import uuid
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from showbook_common.database import db_manager

from app.core.config import settings
from app.core.exceptions import InvalidTokenException
from app.repositories.user_repository import UserRepository
from app.models.user import User

security_scheme = HTTPBearer()

async def get_db():
    async with db_manager.get_db_context() as session:
        yield session

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(
            token.credentials, 
            settings.JWT_SECRET.get_secret_value(), 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not user_id_str or token_type != "access":
            raise InvalidTokenException()
    except JWTError:
        raise InvalidTokenException()

    user = await UserRepository.get_by_id(db, uuid.UUID(user_id_str))
    if not user or not user.is_active:
        raise InvalidTokenException()
        
    return user
