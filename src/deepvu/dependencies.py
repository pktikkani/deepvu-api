import uuid

from fastapi import Depends, Header, Request

from deepvu.analytics.duckdb_backend import DuckDBAnalyticsBackend
from deepvu.analytics.protocol import AnalyticsQueryService
from deepvu.auth.jwt_handler import decode_access_token
from deepvu.exceptions import ForbiddenError, UnauthorizedError

# Singleton analytics backend (replaced per-request in tests)
_analytics_backend: AnalyticsQueryService | None = None


def get_analytics_service() -> AnalyticsQueryService:
    global _analytics_backend
    if _analytics_backend is None:
        _analytics_backend = DuckDBAnalyticsBackend(seed=True)
    return _analytics_backend


def get_current_user(request: Request) -> dict:
    """Extract current user from request state (set by AuthMiddleware) or raise 401."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise UnauthorizedError()
    return {
        "user_id": request.state.user_id,
        "email": getattr(request.state, "user_email", ""),
        "role": getattr(request.state, "user_role", ""),
        "tenant_id": getattr(request.state, "user_tenant_id", ""),
    }


def require_role(*allowed_roles: str):
    """Dependency factory that checks the user has one of the allowed roles."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise ForbiddenError(f"Role '{user['role']}' not authorized")
        return user

    return checker


def get_tenant_id(request: Request) -> uuid.UUID:
    """Get tenant_id from request state or X-Tenant-ID header, returned as UUID."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        tenant_id = getattr(request.state, "user_tenant_id", None)
    if tenant_id is None:
        raise UnauthorizedError("Tenant not resolved")
    if isinstance(tenant_id, uuid.UUID):
        return tenant_id
    try:
        return uuid.UUID(str(tenant_id))
    except ValueError:
        raise UnauthorizedError("Invalid tenant ID format")
