import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from deepvu.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        redis_client = getattr(request.app.state, "redis", None)
        if redis_client is None:
            return await call_next(request)

        # Get identifiers
        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        now = int(time.time())
        window = 60  # 1 minute window

        # Per-user rate limit
        if user_id:
            key = f"ratelimit:user:{user_id}"
            count = await self._check_rate(redis_client, key, now, window)
            if count > settings.RATE_LIMIT_PER_USER:
                retry_after = window - (now % window)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)},
                )

        # Per-tenant rate limit
        if tenant_id:
            key = f"ratelimit:tenant:{tenant_id}"
            count = await self._check_rate(redis_client, key, now, window)
            if count > settings.RATE_LIMIT_PER_TENANT:
                retry_after = window - (now % window)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Tenant rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)},
                )

        return await call_next(request)

    async def _check_rate(self, redis_client, key: str, now: int, window: int) -> int:
        pipe = redis_client.pipeline()
        window_start = now - window
        # Use a unique member per request so each request is counted
        member = f"{now}:{uuid.uuid4().hex}"
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {member: now})
        pipe.zcard(key)
        pipe.expire(key, window * 2)
        results = await pipe.execute()
        return results[2]  # zcard result
