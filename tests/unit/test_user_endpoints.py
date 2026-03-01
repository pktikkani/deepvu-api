"""Phase 7 – User API endpoint tests.

Tests the /api/v1/users endpoints through the full middleware stack.
Each test creates a tenant first (users are scoped to tenants).
"""

import uuid

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import TEST_JWT_PRIVATE_KEY, TEST_JWT_PUBLIC_KEY
from deepvu.models import Tenant, User


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
    tenant = Tenant(name="User Test Corp", slug="user-test-corp", advertiser_id="adv_ut")
    db_session.add(tenant)
    await db_session.flush()
    await db_session.commit()
    return tenant


@pytest.fixture
async def existing_user(db_session, test_tenant):
    user = User(
        tenant_id=test_tenant.id,
        email="existing@example.com",
        name="Existing User",
        role="viewer",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateUser:
    """POST /api/v1/users"""

    async def test_create_user_as_advertiser_admin(self, client, test_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="advertiser_admin",
            email="admin@example.com",
        )
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "newuser@example.com",
                "name": "New User",
                "role": "viewer",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert data["role"] == "viewer"
        assert data["is_active"] is True
        assert data["tenant_id"] == str(test_tenant.id)

    async def test_create_user_forbidden_for_viewer(self, client, test_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "anotheruser@example.com",
                "name": "Another User",
                "role": "viewer",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 403

    async def test_create_user_forbidden_for_analyst(self, client, test_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="analyst",
            email="analyst@example.com",
        )
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "user2@example.com",
                "name": "User 2",
                "role": "viewer",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 403

    async def test_create_user_unauthenticated(self, client):
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "noauth@example.com",
                "name": "No Auth",
                "role": "viewer",
            },
        )
        assert resp.status_code == 401


class TestListUsers:
    """GET /api/v1/users"""

    async def test_list_users_as_advertiser_admin(
        self, client, test_tenant, existing_user
    ):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="advertiser_admin",
            email="admin@example.com",
        )
        resp = await client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        emails = {u["email"] for u in data}
        assert "existing@example.com" in emails

    async def test_list_users_as_platform_admin(
        self, client, test_tenant, existing_user
    ):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="platform_admin",
            email="padmin@example.com",
        )
        resp = await client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_users_forbidden_for_viewer(self, client, test_tenant):
        token = make_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(test_tenant.id),
            role="viewer",
            email="viewer@example.com",
        )
        resp = await client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(test_tenant.id),
            },
        )
        assert resp.status_code == 403

    async def test_list_users_unauthenticated(self, client):
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 401
