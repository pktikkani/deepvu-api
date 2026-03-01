"""Repository layer for TenantSSOConfig model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.models.tenant import TenantSSOConfig


class SSOConfigRepository:
    """Data-access methods for tenant SSO configuration."""

    async def create(
        self, session: AsyncSession, sso_data: dict
    ) -> TenantSSOConfig:
        """Create a new SSO configuration and flush to obtain the generated id."""
        sso_config = TenantSSOConfig(**sso_data)
        session.add(sso_config)
        await session.flush()
        return sso_config

    async def get_by_tenant(
        self, session: AsyncSession, tenant_id: uuid.UUID
    ) -> TenantSSOConfig | None:
        """Return the SSO configuration for a tenant, or None."""
        stmt = select(TenantSSOConfig).where(TenantSSOConfig.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self, session: AsyncSession, tenant_id: uuid.UUID, data: dict
    ) -> TenantSSOConfig:
        """Update SSO config for a tenant. Raises ValueError when not found."""
        sso_config = await self.get_by_tenant(session, tenant_id)
        if sso_config is None:
            raise ValueError(f"SSO config for tenant {tenant_id} not found")
        for key, value in data.items():
            setattr(sso_config, key, value)
        await session.flush()
        return sso_config
