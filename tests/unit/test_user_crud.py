"""Tests for UserRepository CRUD operations."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.repositories.tenant_repo import TenantRepository
from deepvu.repositories.user_repo import UserRepository

tenant_repo = TenantRepository()
user_repo = UserRepository()


async def _make_tenant(session: AsyncSession, slug: str | None = None) -> "Tenant":  # noqa: F821
    """Helper: create and flush a tenant so it can be used as a FK target."""
    from deepvu.models.tenant import Tenant  # noqa: F811

    data = {
        "name": "Test Tenant",
        "slug": slug or f"tenant-{uuid.uuid4().hex[:8]}",
        "advertiser_id": "ADV-TEST",
    }
    tenant = await tenant_repo.create(session, data)
    await session.flush()
    return tenant


# ── Create ───────────────────────────────────────────────────────


async def test_create_user(db_session: AsyncSession):
    tenant = await _make_tenant(db_session, slug="user-create-t")
    user = await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "alice@example.com", "name": "Alice"},
    )
    await db_session.commit()

    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.name == "Alice"
    assert user.tenant_id == tenant.id
    assert user.role == "viewer"
    assert user.auth_provider == "google"
    assert user.is_active is True


# ── Get by id (tenant-scoped) ───────────────────────────────────


async def test_get_by_id(db_session: AsyncSession):
    tenant = await _make_tenant(db_session, slug="user-getid-t")
    user = await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "bob@example.com", "name": "Bob"},
    )
    await db_session.commit()

    found = await user_repo.get_by_id(db_session, user.id, tenant.id)
    assert found is not None
    assert found.id == user.id


async def test_get_by_id_wrong_tenant(db_session: AsyncSession):
    tenant = await _make_tenant(db_session, slug="user-getid-wrong-t")
    user = await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "carol@example.com", "name": "Carol"},
    )
    await db_session.commit()

    result = await user_repo.get_by_id(db_session, user.id, uuid.uuid4())
    assert result is None


# ── Get by email (tenant-scoped) ────────────────────────────────


async def test_get_by_email(db_session: AsyncSession):
    tenant = await _make_tenant(db_session, slug="user-email-t")
    await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "dave@example.com", "name": "Dave"},
    )
    await db_session.commit()

    found = await user_repo.get_by_email(db_session, "dave@example.com", tenant.id)
    assert found is not None
    assert found.name == "Dave"


async def test_get_by_email_wrong_tenant(db_session: AsyncSession):
    tenant = await _make_tenant(db_session, slug="user-email-wrong-t")
    await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "eve@example.com", "name": "Eve"},
    )
    await db_session.commit()

    result = await user_repo.get_by_email(db_session, "eve@example.com", uuid.uuid4())
    assert result is None


# ── List by tenant ───────────────────────────────────────────────


async def test_list_by_tenant(db_session: AsyncSession):
    tenant = await _make_tenant(db_session, slug="user-list-t")
    await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "u1@example.com", "name": "User1"},
    )
    await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "u2@example.com", "name": "User2"},
    )
    await db_session.commit()

    users = await user_repo.list_by_tenant(db_session, tenant.id)
    assert len(users) == 2
    names = {u.name for u in users}
    assert names == {"User1", "User2"}


# ── Update ───────────────────────────────────────────────────────


async def test_update_user(db_session: AsyncSession):
    tenant = await _make_tenant(db_session, slug="user-update-t")
    user = await user_repo.create(
        db_session,
        {"tenant_id": tenant.id, "email": "frank@example.com", "name": "Frank"},
    )
    await db_session.commit()

    updated = await user_repo.update(
        db_session, user.id, tenant.id, {"name": "Franklin", "role": "admin"}
    )
    await db_session.commit()

    assert updated.name == "Franklin"
    assert updated.role == "admin"

    refreshed = await user_repo.get_by_id(db_session, user.id, tenant.id)
    assert refreshed is not None
    assert refreshed.name == "Franklin"


async def test_update_user_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="not found"):
        await user_repo.update(db_session, uuid.uuid4(), uuid.uuid4(), {"name": "Ghost"})


# ── Tenant scoping isolation ────────────────────────────────────


async def test_tenant_scoping_isolation(db_session: AsyncSession):
    """User created under tenant A must not be visible when querying tenant B."""
    tenant_a = await _make_tenant(db_session, slug="scope-a")
    tenant_b = await _make_tenant(db_session, slug="scope-b")

    user_a = await user_repo.create(
        db_session,
        {"tenant_id": tenant_a.id, "email": "shared@example.com", "name": "Shared User"},
    )
    await db_session.commit()

    # Visible under tenant A
    found_a = await user_repo.get_by_id(db_session, user_a.id, tenant_a.id)
    assert found_a is not None

    # Invisible under tenant B
    found_b = await user_repo.get_by_id(db_session, user_a.id, tenant_b.id)
    assert found_b is None

    # By email: invisible under tenant B
    by_email_b = await user_repo.get_by_email(db_session, "shared@example.com", tenant_b.id)
    assert by_email_b is None

    # List: tenant B has no users
    list_b = await user_repo.list_by_tenant(db_session, tenant_b.id)
    assert len(list_b) == 0
