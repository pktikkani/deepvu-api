"""Phase 7 – Tenant API endpoint tests.

Tests the /api/v1/tenants endpoints through the full middleware stack
(AuthMiddleware, TenantResolverMiddleware, etc.) using the shared test app.
"""

import uuid

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import TEST_JWT_PRIVATE_KEY, TEST_JWT_PUBLIC_KEY
from deepvu.models import Tenant


# ---------------------------------------------------------------------------
# JWT settings patch (autouse – active for every test in this module)
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
# Helper – create a JWT for testing
# ---------------------------------------------------------------------------

def make_token(user_id: str, tenant_id: str, role: str, email: str) -> str:
    """Create a JWT token using the test RSA keys (already patched by autouse fixture)."""
    from deepvu.auth.jwt_handler import create_access_token
    return create_access_token(
        user_id=user_id, tenant_id=tenant_id, role=role, email=email,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def seed_tenant(db_session):
    """Insert a tenant directly into the DB so endpoint tests can reference it."""
    tenant = Tenant(name="Seed Corp", slug="seed-corp", advertiser_id="adv_seed")
    db_session.add(tenant)
    await db_session.flush()
    await db_session.commit()
    return tenant


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateTenant:
    """POST /api/v1/tenants"""

    async def test_create_tenant_as_platform_admin(self, client):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            role="platform_admin",
            email="admin@example.com",
        )
        resp = await client.post(
            "/api/v1/tenants",
            json={
                "name": "New Tenant",
                "slug": "new-tenant",
                "advertiser_id": "ADV-NEW",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "New Tenant"
        assert data["slug"] == "new-tenant"
        assert data["advertiser_id"] == "ADV-NEW"
        assert data["dashboard_type"] == "comprehensive"
        assert data["is_active"] is True
        # Verify UUID id was assigned
        uuid.UUID(data["id"])

    async def test_create_tenant_forbidden_for_viewer(self, client):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.post(
            "/api/v1/tenants",
            json={
                "name": "Forbidden Tenant",
                "slug": "forbidden-tenant",
                "advertiser_id": "ADV-FORBIDDEN",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 403

    async def test_create_tenant_forbidden_for_advertiser_admin(self, client):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            role="advertiser_admin",
            email="advadmin@example.com",
        )
        resp = await client.post(
            "/api/v1/tenants",
            json={
                "name": "Forbidden Tenant 2",
                "slug": "forbidden-tenant-2",
                "advertiser_id": "ADV-FORBIDDEN2",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 403

    async def test_create_tenant_unauthenticated(self, client):
        resp = await client.post(
            "/api/v1/tenants",
            json={
                "name": "No Auth Tenant",
                "slug": "no-auth-tenant",
                "advertiser_id": "ADV-NOAUTH",
            },
        )
        assert resp.status_code == 401


class TestCreateDuplicateSlug:
    """POST /api/v1/tenants with duplicate slug → 409"""

    async def test_duplicate_slug_returns_409(self, client, seed_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            role="platform_admin",
            email="admin@example.com",
        )
        resp = await client.post(
            "/api/v1/tenants",
            json={
                "name": "Duplicate",
                "slug": seed_tenant.slug,
                "advertiser_id": "ADV-DUP",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 409, resp.text
        assert "already exists" in resp.json()["detail"]


class TestListTenants:
    """GET /api/v1/tenants"""

    async def test_list_tenants_as_platform_admin(self, client, seed_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            role="platform_admin",
            email="admin@example.com",
        )
        resp = await client.get(
            "/api/v1/tenants",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        slugs = {t["slug"] for t in data}
        assert seed_tenant.slug in slugs

    async def test_list_tenants_forbidden_for_viewer(self, client):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.get(
            "/api/v1/tenants",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 403

    async def test_list_tenants_unauthenticated(self, client):
        resp = await client.get("/api/v1/tenants")
        assert resp.status_code == 401
