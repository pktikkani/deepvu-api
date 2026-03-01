from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

PUBLIC_PATHS = {
    "/docs",
    "/openapi.json",
    "/health",
    "/api/v1/auth/google/callback",
    "/api/v1/auth/sso/callback",
    "/api/v1/auth/refresh",
}


class TenantResolverMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Try to resolve tenant from hostname
        hostname = request.headers.get("host", "").split(":")[0]

        # Check Redis cache first
        redis_client = (
            request.app.state.redis if hasattr(request.app.state, "redis") else None
        )
        tenant_id = None

        if redis_client:
            cached = await redis_client.get(f"domain:{hostname}")
            if cached:
                tenant_id = cached

        if tenant_id is None:
            # Try subdomain extraction: e.g., "acme.deepvu.io" -> slug "acme"
            parts = hostname.split(".")
            if len(parts) >= 3:
                request.state.tenant_slug = parts[0]

            # Also check X-Tenant-ID header as fallback
            tenant_id = request.headers.get("X-Tenant-ID")

        request.state.tenant_id = tenant_id
        return await call_next(request)
