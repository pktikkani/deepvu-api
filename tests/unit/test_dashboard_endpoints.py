"""Phase 7 – Dashboard API endpoint tests.

Tests the /api/v1/dashboards endpoint through the full middleware stack.
The dashboard configuration is determined by the tenant's dashboard_type.
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
async def comprehensive_tenant(db_session):
    tenant = Tenant(
        name="Comprehensive Corp",
        slug="comp-corp",
        advertiser_id="adv_comp",
        dashboard_type="comprehensive",
    )
    db_session.add(tenant)
    await db_session.flush()
    await db_session.commit()
    return tenant


@pytest.fixture
async def limited_tenant(db_session):
    tenant = Tenant(
        name="Limited Corp",
        slug="limited-corp",
        advertiser_id="adv_lim",
        dashboard_type="limited",
    )
    db_session.add(tenant)
    await db_session.flush()
    await db_session.commit()
    return tenant


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetDashboardConfig:
    """GET /api/v1/dashboards"""

    async def test_get_dashboard_comprehensive(self, client, comprehensive_tenant):
        """Comprehensive dashboard type should return 6 tabs."""
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(comprehensive_tenant.id),
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.get(
            "/api/v1/dashboards",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(comprehensive_tenant.id),
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["dashboard_type"] == "comprehensive"
        assert len(data["tabs"]) == 6

        tab_keys = [t["key"] for t in data["tabs"]]
        assert tab_keys == [
            "campaign_overview",
            "reach_frequency",
            "device_type",
            "geo_trends",
            "placements",
            "creative",
        ]

    async def test_get_dashboard_limited(self, client, limited_tenant):
        """Limited dashboard type should return 3 tabs."""
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(limited_tenant.id),
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.get(
            "/api/v1/dashboards",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(limited_tenant.id),
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["dashboard_type"] == "limited"
        assert len(data["tabs"]) == 3

        tab_keys = [t["key"] for t in data["tabs"]]
        assert tab_keys == [
            "campaign_overview",
            "geo_trends",
            "placements",
        ]

    async def test_get_dashboard_unauthenticated(self, client):
        """Unauthenticated requests should get 401."""
        resp = await client.get("/api/v1/dashboards")
        assert resp.status_code == 401

    async def test_get_dashboard_nonexistent_tenant(self, client):
        """Authenticated but with a non-existent tenant_id should get 404."""
        fake_tenant_id = str(uuid.uuid4())
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=fake_tenant_id,
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.get(
            "/api/v1/dashboards",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": fake_tenant_id,
            },
        )
        assert resp.status_code == 404

    async def test_get_dashboard_any_role_allowed(self, client, comprehensive_tenant):
        """Dashboard config should be accessible by any authenticated role."""
        for role in ("platform_admin", "advertiser_admin", "analyst", "viewer"):
            token = make_token(
                user_id=str(uuid.uuid4()),
                tenant_id=str(comprehensive_tenant.id),
                role=role,
                email=f"{role}@example.com",
            )
            resp = await client.get(
                "/api/v1/dashboards",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": str(comprehensive_tenant.id),
                },
            )
            assert resp.status_code == 200, f"Role {role} got {resp.status_code}"
