"""Repository layer for Tenant and related models."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.models.tenant import Tenant, TenantBranding, TenantDomain, TenantSSOConfig


class TenantRepository:
    """Data-access methods for Tenant, TenantBranding, and TenantDomain."""

    # ── Tenant CRUD ──────────────────────────────────────────────

    async def create(self, session: AsyncSession, tenant_data: dict) -> Tenant:
        """Create a new tenant and flush to obtain the generated id."""
        tenant = Tenant(**tenant_data)
        session.add(tenant)
        await session.flush()
        return tenant

    async def get_by_id(self, session: AsyncSession, tenant_id: uuid.UUID) -> Tenant | None:
        """Return a tenant by primary key, or None."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Tenant | None:
        """Return a tenant by its unique slug, or None."""
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_domain(self, session: AsyncSession, domain: str) -> Tenant | None:
        """Lookup a tenant through TenantDomain, or None."""
        stmt = (
            select(Tenant)
            .join(TenantDomain, TenantDomain.tenant_id == Tenant.id)
            .where(TenantDomain.domain == domain)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, session: AsyncSession) -> list[Tenant]:
        """Return every tenant."""
        stmt = select(Tenant).order_by(Tenant.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, session: AsyncSession, tenant_id: uuid.UUID, data: dict
    ) -> Tenant:
        """Update an existing tenant. Raises ValueError when not found."""
        tenant = await self.get_by_id(session, tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        for key, value in data.items():
            setattr(tenant, key, value)
        await session.flush()
        return tenant

    # ── Branding ─────────────────────────────────────────────────

    async def create_branding(
        self, session: AsyncSession, tenant_id: uuid.UUID, branding_data: dict
    ) -> TenantBranding:
        """Create branding for a tenant."""
        branding = TenantBranding(tenant_id=tenant_id, **branding_data)
        session.add(branding)
        await session.flush()
        return branding

    async def update_branding(
        self, session: AsyncSession, tenant_id: uuid.UUID, branding_data: dict
    ) -> TenantBranding:
        """Update branding for a tenant. Raises ValueError when not found."""
        branding = await self.get_branding(session, tenant_id)
        if branding is None:
            raise ValueError(f"Branding for tenant {tenant_id} not found")
        for key, value in branding_data.items():
            setattr(branding, key, value)
        await session.flush()
        return branding

    async def get_branding(
        self, session: AsyncSession, tenant_id: uuid.UUID
    ) -> TenantBranding | None:
        """Return branding for a tenant, or None."""
        stmt = select(TenantBranding).where(TenantBranding.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
