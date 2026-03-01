import uuid
from datetime import UTC, datetime, timedelta

import jwt
import redis.asyncio as redis

from deepvu.config import settings


def create_access_token(
    user_id: str,
    tenant_id: str,
    role: str,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "email": email,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_PUBLIC_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


async def create_refresh_token(
    user_id: str,
    redis_client: redis.Redis,
) -> str:
    token_id = str(uuid.uuid4())
    ttl = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    await redis_client.setex(f"refresh:{token_id}", int(ttl.total_seconds()), user_id)
    return token_id


async def rotate_refresh_token(
    refresh_token: str,
    redis_client: redis.Redis,
) -> tuple[str, str]:
    """Consume the old refresh token and issue a new one. Returns (new_token, user_id)."""
    key = f"refresh:{refresh_token}"
    user_id = await redis_client.get(key)
    if user_id is None:
        raise ValueError("Invalid or expired refresh token")

    # Single-use: delete the old token
    await redis_client.delete(key)

    new_token = await create_refresh_token(user_id, redis_client)
    return new_token, user_id


async def revoke_refresh_token(
    refresh_token: str,
    redis_client: redis.Redis,
) -> None:
    await redis_client.delete(f"refresh:{refresh_token}")
