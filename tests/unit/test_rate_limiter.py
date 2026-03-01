from unittest.mock import patch

import fakeredis.aioredis
import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from starlette.middleware.base import BaseHTTPMiddleware

from deepvu.middleware.rate_limiter import RateLimitMiddleware


class _InjectUserMiddleware(BaseHTTPMiddleware):
    """Test middleware that simulates auth setting user/tenant on request.state."""

    async def dispatch(self, request, call_next):
        request.state.user_id = request.headers.get("X-Test-User-ID")
        request.state.tenant_id = request.headers.get("X-Test-Tenant-ID")
        return await call_next(request)


def _create_app(redis_client):
    app = FastAPI()

    # Middleware added via add_middleware runs outermost-first (last added = outermost).
    # We want: request -> InjectUser -> RateLimiter -> route
    # So add RateLimiter first, then InjectUser (which wraps it).
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(_InjectUserMiddleware)
    app.state.redis = redis_client

    @app.get("/api/v1/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


class TestRateLimiter:
    async def test_allows_under_limit(self):
        redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        app = _create_app(redis_client)
        transport = ASGITransport(app=app)

        with patch("deepvu.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.RATE_LIMIT_PER_USER = 100
            mock_settings.RATE_LIMIT_PER_TENANT = 1000

            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/test",
                    headers={
                        "X-Test-User-ID": "user-1",
                        "X-Test-Tenant-ID": "tenant-1",
                    },
                )
                assert response.status_code == 200

    async def test_blocks_over_limit(self):
        redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        app = _create_app(redis_client)
        transport = ASGITransport(app=app)

        with patch("deepvu.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.RATE_LIMIT_PER_USER = 5
            mock_settings.RATE_LIMIT_PER_TENANT = 1000

            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Make requests up to the limit + 1
                for i in range(6):
                    response = await client.get(
                        "/api/v1/test",
                        headers={
                            "X-Test-User-ID": "user-1",
                            "X-Test-Tenant-ID": "tenant-1",
                        },
                    )

                # The 6th request (count=6 > limit=5) should be blocked
                assert response.status_code == 429
                assert response.json()["detail"] == "Rate limit exceeded"

    async def test_429_has_retry_after(self):
        redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        app = _create_app(redis_client)
        transport = ASGITransport(app=app)

        with patch("deepvu.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.RATE_LIMIT_PER_USER = 1
            mock_settings.RATE_LIMIT_PER_TENANT = 1000

            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # First request passes (count=1, not > 1)
                await client.get(
                    "/api/v1/test",
                    headers={
                        "X-Test-User-ID": "user-1",
                        "X-Test-Tenant-ID": "tenant-1",
                    },
                )
                # Second request blocked (count=2 > 1)
                response = await client.get(
                    "/api/v1/test",
                    headers={
                        "X-Test-User-ID": "user-1",
                        "X-Test-Tenant-ID": "tenant-1",
                    },
                )
                assert response.status_code == 429
                assert "retry-after" in response.headers

    async def test_no_redis_passes_through(self):
        """When redis is not available, requests should pass through."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware)
        # Explicitly do NOT set app.state.redis

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"status": "ok"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/test")
            assert response.status_code == 200

    async def test_tenant_rate_limit(self):
        redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        app = _create_app(redis_client)
        transport = ASGITransport(app=app)

        with patch("deepvu.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.RATE_LIMIT_PER_USER = 1000  # High user limit
            mock_settings.RATE_LIMIT_PER_TENANT = 3  # Low tenant limit

            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                for i in range(4):
                    response = await client.get(
                        "/api/v1/test",
                        headers={
                            "X-Test-User-ID": f"user-{i}",  # Different users
                            "X-Test-Tenant-ID": "tenant-1",  # Same tenant
                        },
                    )

                assert response.status_code == 429
                assert response.json()["detail"] == "Tenant rate limit exceeded"
