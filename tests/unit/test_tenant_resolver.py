import fakeredis.aioredis
import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from deepvu.middleware.tenant_resolver import TenantResolverMiddleware


def _create_app(redis_client=None):
    app = FastAPI(docs_url=None, redoc_url=None)
    app.add_middleware(TenantResolverMiddleware)

    if redis_client is not None:
        app.state.redis = redis_client

    @app.get("/docs")
    async def docs():
        return {"page": "docs"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/test")
    async def test_endpoint(request: Request):
        return {
            "tenant_id": getattr(request.state, "tenant_id", None),
            "tenant_slug": getattr(request.state, "tenant_slug", None),
        }

    return app


class TestTenantResolver:
    async def test_public_path_skips(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/docs")
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == "docs"

    async def test_x_tenant_id_header(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/test", headers={"X-Tenant-ID": "tenant-123"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] == "tenant-123"

    async def test_subdomain_extraction(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/test", headers={"host": "acme.deepvu.io"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["tenant_slug"] == "acme"

    async def test_redis_cached_domain(self):
        redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        await redis_client.set("domain:custom.example.com", "tenant-from-cache")

        app = _create_app(redis_client=redis_client)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/test", headers={"host": "custom.example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] == "tenant-from-cache"

    async def test_no_tenant_info_when_absent(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/test")
            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] is None
