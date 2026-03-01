from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis

from deepvu.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    rotate_refresh_token,
)
from deepvu.config import settings
from deepvu.database import get_db
from deepvu.exceptions import UnauthorizedError
from deepvu.redis import get_redis
from deepvu.repositories.user_repo import UserRepository
from deepvu.schemas.auth import RefreshRequest, TokenResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
user_repo = UserRepository()


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Placeholder for Google OAuth callback. Full implementation requires Google OAuth flow."""
    raise UnauthorizedError("Google OAuth not yet configured")


@router.post("/sso/callback", response_model=TokenResponse)
async def sso_callback(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Placeholder for SSO callback. Full implementation requires SSO provider integration."""
    raise UnauthorizedError("SSO not yet configured")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Rotate a refresh token and issue a new access + refresh token pair."""
    try:
        new_refresh, user_id = await rotate_refresh_token(
            body.refresh_token, redis_client
        )
    except ValueError:
        raise UnauthorizedError("Invalid or expired refresh token")

    # Look up user to get tenant_id and role
    user = await user_repo.get_by_id(db, user_id, tenant_id=None)
    if user is None:
        raise UnauthorizedError("User not found")

    access = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
        email=user.email,
    )

    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
