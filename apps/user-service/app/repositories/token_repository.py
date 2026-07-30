from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import RefreshToken

class TokenRepository:
    @staticmethod
    async def get_by_token(db: AsyncSession, token: str) -> RefreshToken | None:
        result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, refresh_token: RefreshToken) -> RefreshToken:
        db.add(refresh_token)
        return refresh_token
