from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from deepvu.auth.jwt_handler import create_access_token
from deepvu.middleware.auth import AuthMiddleware
from tests.conftest import TEST_JWT_PRIVATE_KEY, TEST_JWT_PUBLIC_KEY


@pytest.fixture(autouse=True)
def _patch_jwt_settings():
    with patch("deepvu.auth.jwt_handler.settings") as mock_settings:
        mock_settings.JWT_PRIVATE_KEY = TEST_JWT_PRIVATE_KEY
        mock_settings.JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY
        mock_settings.JWT_ALGORITHM = "RS256"
        mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
        yield mock_settings


def _create_app():
    app = FastAPI(docs_url=None, redoc_url=None)
    app.add_middleware(AuthMiddleware)

    @app.get("/docs")
    async def docs():
        return {"page": "docs"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/test")
    async def test_endpoint(request: Request):
        return {
            "user_id": getattr(request.state, "user_id", None),
            "user_email": getattr(request.state, "user_email", None),
            "user_role": getattr(request.state, "user_role", None),
            "user_tenant_id": getattr(request.state, "user_tenant_id", None),
        }

    return app


class TestAuthMiddleware:
    async def test_public_path_no_auth(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/docs")
            assert response.status_code == 200
            assert response.json()["page"] == "docs"

    async def test_bearer_token_sets_user(self):
        app = _create_app()
        transport = ASGITransport(app=app)

        token = create_access_token(
            user_id="user-42",
            tenant_id="tenant-7",
            role="admin",
            email="admin@example.com",
        )

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/test",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user-42"
            assert data["user_email"] == "admin@example.com"
            assert data["user_role"] == "admin"
            assert data["user_tenant_id"] == "tenant-7"

    async def test_invalid_token_ignored(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/test",
                headers={"Authorization": "Bearer invalid.token.here"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] is None
            assert data["user_email"] is None

    async def test_no_token_leaves_user_unset(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/test")
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] is None

    async def test_options_request_skips_auth(self):
        app = _create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.options("/api/v1/test")
            # OPTIONS may return 405 from FastAPI (no OPTIONS handler), but
            # the middleware should not block it
            assert response.status_code in (200, 405)

    async def test_cookie_token_sets_user(self):
        app = _create_app()
        transport = ASGITransport(app=app)

        token = create_access_token(
            user_id="user-99",
            tenant_id="tenant-5",
            role="viewer",
            email="viewer@example.com",
        )

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/test",
                cookies={"access_token": token},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user-99"
