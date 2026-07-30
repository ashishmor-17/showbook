import time
import redis
from app.core.config import settings

# Token Bucket Lua Script
# ARGV: [1] capacity, [2] refill_rate, [3] refill_period (secs), [4] current_timestamp
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local refill_period = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local rate = refill_rate / refill_period
local data = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if tokens == nil then
    tokens = capacity
    last_updated = now
else
    local elapsed = now - last_updated
    if elapsed > 0 then
        tokens = math.min(capacity, tokens + (elapsed * rate))
        last_updated = now
    end
end

if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
    redis.call('EXPIRE', key, math.ceil(refill_period))
    return 1 -- Allowed
else
    return 0 -- Rate limit exceeded
end
"""

class RedisManager:
    def __init__(self):
        self.client: redis.Redis | None = None
        self._rate_limit_script = None

    def init(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self._rate_limit_script = self.client.register_script(TOKEN_BUCKET_LUA)

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self._rate_limit_script = None

    def check_rate_limit(
        self,
        ip: str,
        capacity: int = 5,
        refill_rate: int = 5,
        refill_period: int = 60
    ) -> bool:
        if not self.client or not self._rate_limit_script:
            return True  # Fail open if Redis is down
            
        key = f"rate:login:{ip}"
        now = time.time()
        
        result = self._rate_limit_script(
            keys=[key],
            args=[capacity, refill_rate, refill_period, now]
        )
        return result == 1

redis_manager = RedisManager()
