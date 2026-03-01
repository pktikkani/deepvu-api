"""Tests for TenantRepository CRUD operations."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.models.tenant import TenantDomain
from deepvu.repositories.tenant_repo import TenantRepository

repo = TenantRepository()


def _tenant_data(**overrides) -> dict:
    """Build minimal valid tenant data, merging any overrides."""
    base = {
        "name": "Acme Corp",
        "slug": f"acme-{uuid.uuid4().hex[:8]}",
        "advertiser_id": "ADV-001",
    }
    base.update(overrides)
    return base


# ── Create ───────────────────────────────────────────────────────


async def test_create_tenant(db_session: AsyncSession):
    data = _tenant_data(slug="acme-create")
    tenant = await repo.create(db_session, data)
    await db_session.commit()

    assert tenant.id is not None
    assert tenant.name == "Acme Corp"
    assert tenant.slug == "acme-create"
    assert tenant.advertiser_id == "ADV-001"
    assert tenant.is_active is True
    assert tenant.dashboard_type == "comprehensive"


# ── Get by id ────────────────────────────────────────────────────


async def test_get_by_id(db_session: AsyncSession):
    tenant = await repo.create(db_session, _tenant_data(slug="acme-byid"))
    await db_session.commit()

    found = await repo.get_by_id(db_session, tenant.id)
    assert found is not None
    assert found.id == tenant.id


async def test_get_by_id_not_found(db_session: AsyncSession):
    result = await repo.get_by_id(db_session, uuid.uuid4())
    assert result is None


# ── Get by slug ──────────────────────────────────────────────────


async def test_get_by_slug(db_session: AsyncSession):
    tenant = await repo.create(db_session, _tenant_data(slug="acme-slug-test"))
    await db_session.commit()

    found = await repo.get_by_slug(db_session, "acme-slug-test")
    assert found is not None
    assert found.id == tenant.id


async def test_get_by_slug_not_found(db_session: AsyncSession):
    result = await repo.get_by_slug(db_session, "nonexistent-slug")
    assert result is None


# ── Get by domain ────────────────────────────────────────────────


async def test_get_by_domain(db_session: AsyncSession):
    tenant = await repo.create(db_session, _tenant_data(slug="acme-domain"))
    await db_session.flush()

    domain = TenantDomain(tenant_id=tenant.id, domain="acme.example.com", is_primary=True)
    db_session.add(domain)
    await db_session.commit()

    found = await repo.get_by_domain(db_session, "acme.example.com")
    assert found is not None
    assert found.id == tenant.id


async def test_get_by_domain_not_found(db_session: AsyncSession):
    result = await repo.get_by_domain(db_session, "unknown.example.com")
    assert result is None


# ── List all ─────────────────────────────────────────────────────


async def test_list_all(db_session: AsyncSession):
    await repo.create(db_session, _tenant_data(slug="list-a"))
    await repo.create(db_session, _tenant_data(slug="list-b"))
    await db_session.commit()

    tenants = await repo.list_all(db_session)
    slugs = {t.slug for t in tenants}
    assert "list-a" in slugs
    assert "list-b" in slugs
    assert len(tenants) >= 2


# ── Update ───────────────────────────────────────────────────────


async def test_update_tenant(db_session: AsyncSession):
    tenant = await repo.create(db_session, _tenant_data(slug="acme-update"))
    await db_session.commit()

    updated = await repo.update(db_session, tenant.id, {"name": "Acme Inc"})
    await db_session.commit()

    assert updated.name == "Acme Inc"

    refreshed = await repo.get_by_id(db_session, tenant.id)
    assert refreshed is not None
    assert refreshed.name == "Acme Inc"


async def test_update_tenant_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="not found"):
        await repo.update(db_session, uuid.uuid4(), {"name": "Ghost"})


# ── Branding ─────────────────────────────────────────────────────


async def test_create_and_get_branding(db_session: AsyncSession):
    tenant = await repo.create(db_session, _tenant_data(slug="acme-brand"))
    await db_session.flush()

    branding = await repo.create_branding(
        db_session,
        tenant.id,
        {
            "logo_url": "https://cdn.example.com/logo.png",
            "primary_color": "#FF0000",
            "secondary_color": "#00FF00",
        },
    )
    await db_session.commit()

    assert branding.primary_color == "#FF0000"
    assert branding.secondary_color == "#00FF00"
    assert branding.logo_url == "https://cdn.example.com/logo.png"

    fetched = await repo.get_branding(db_session, tenant.id)
    assert fetched is not None
    assert fetched.id == branding.id


async def test_update_branding(db_session: AsyncSession):
    tenant = await repo.create(db_session, _tenant_data(slug="acme-brand-upd"))
    await db_session.flush()
    await repo.create_branding(
        db_session,
        tenant.id,
        {"primary_color": "#111111", "secondary_color": "#222222"},
    )
    await db_session.commit()

    updated = await repo.update_branding(
        db_session, tenant.id, {"primary_color": "#AAAAAA"}
    )
    await db_session.commit()

    assert updated.primary_color == "#AAAAAA"
    assert updated.secondary_color == "#222222"


async def test_get_branding_not_found(db_session: AsyncSession):
    result = await repo.get_branding(db_session, uuid.uuid4())
    assert result is None
