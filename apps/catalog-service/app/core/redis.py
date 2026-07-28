import redis.asyncio as aioredis

from app.core.config import settings

if settings.REDIS_PASSWORD:
    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
else:
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

redis_client = aioredis.from_url(redis_url, decode_responses=True)

async def get_redis():
    yield redis_client