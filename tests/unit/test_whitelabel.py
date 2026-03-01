"""Phase 7 – Whitelabel API endpoint tests.

Tests the /api/v1/whitelabel/config endpoints through the full middleware stack.
GET is a public path (no auth required), but PUT requires advertiser_admin role.
"""

import uuid

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import TEST_JWT_PRIVATE_KEY, TEST_JWT_PUBLIC_KEY
from deepvu.models import Tenant


# ---------------------------------------------------------------------------
# JWT settings patch (autouse)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_jwt_settings():
    mock = MagicMock()
    mock.JWT_PRIVATE_KEY = TEST_JWT_PRIVATE_KEY
    mock.JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY
    mock.JWT_ALGORITHM = "RS256"
    mock.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
    mock.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    with patch("deepvu.auth.jwt_handler.settings", mock):
        yield


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_token(user_id: str, tenant_id: str, role: str, email: str) -> str:
    from deepvu.auth.jwt_handler import create_access_token
    return create_access_token(
        user_id=user_id, tenant_id=tenant_id, role=role, email=email,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def test_tenant(db_session):
    tenant = Tenant(name="WL Corp", slug="wl-corp", advertiser_id="adv_wl")
    db_session.add(tenant)
    await db_session.flush()
    await db_session.commit()
    return tenant


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetWhitelabelConfig:
    """GET /api/v1/whitelabel/config – public path in AuthMiddleware"""

    async def test_get_whitelabel_config_default(self, client, test_tenant):
        """When no branding exists, return default values."""
        resp = await client.get(
            "/api/v1/whitelabel/config",
            headers={"X-Tenant-ID": str(test_tenant.id)},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # Default whitelabel response when no branding row exists
        assert data["primary_color"] == "#000000"
        assert data["secondary_color"] == "#FFFFFF"
        assert data["logo_url"] is None
        assert data["custom_css"] is None

    async def test_get_whitelabel_config_no_tenant_header(self, client):
        """Without X-Tenant-ID header, the tenant_id dependency should fail."""
        resp = await client.get("/api/v1/whitelabel/config")
        # The get_tenant_id dependency raises UnauthorizedError (401) when
        # there is no tenant context.
        assert resp.status_code == 401


class TestUpdateWhitelabelConfig:
    """PUT /api/v1/whitelabel/config – requires advertiser_admin"""

    async def test_update_whitelabel_config(self, client, test_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="advertiser_admin",
            email="admin@example.com",
        )
        resp = await client.put(
            "/api/v1/whitelabel/config",
            json={
                "logo_url": "https://cdn.example.com/logo.png",
                "primary_color": "#FF5733",
                "secondary_color": "#335BFF",
                "custom_css": "body { font-family: Arial; }",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["logo_url"] == "https://cdn.example.com/logo.png"
        assert data["primary_color"] == "#FF5733"
        assert data["secondary_color"] == "#335BFF"
        assert data["custom_css"] == "body { font-family: Arial; }"
        assert data["tenant_id"] == str(test_tenant.id)

    async def test_update_then_get_whitelabel(self, client, test_tenant, fake_redis):
        """After an update, GET should return the updated branding."""
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="advertiser_admin",
            email="admin@example.com",
        )
        # First, PUT to create branding
        put_resp = await client.put(
            "/api/v1/whitelabel/config",
            json={
                "primary_color": "#AABBCC",
                "secondary_color": "#CCBBAA",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert put_resp.status_code == 200

        # Clear redis cache so GET hits the DB
        await fake_redis.flushall()

        # Then, GET
        get_resp = await client.get(
            "/api/v1/whitelabel/config",
            headers={"X-Tenant-ID": str(test_tenant.id)},
        )
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["primary_color"] == "#AABBCC"
        assert data["secondary_color"] == "#CCBBAA"

    async def test_update_whitelabel_forbidden_for_viewer(self, client, test_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.put(
            "/api/v1/whitelabel/config",
            json={
                "primary_color": "#000000",
                "secondary_color": "#FFFFFF",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 403

    async def test_update_whitelabel_sanitizes_css(self, client, test_tenant):
        """CSS containing dangerous patterns should be sanitized."""
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="advertiser_admin",
            email="admin@example.com",
        )
        resp = await client.put(
            "/api/v1/whitelabel/config",
            json={
                "primary_color": "#000000",
                "secondary_color": "#FFFFFF",
                "custom_css": "body { background: url(http://evil.com/x.js); }",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # The url( pattern should have been replaced by sanitize_css
        assert "url(" not in data["custom_css"]
        assert "/* removed */" in data["custom_css"]
