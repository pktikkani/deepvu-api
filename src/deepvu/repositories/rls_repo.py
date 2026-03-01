"""Repository layer for RLSPolicy model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.models.rls import RLSPolicy


class RLSPolicyRepository:
    """Data-access methods for row-level security policies."""

    async def create(self, session: AsyncSession, rls_data: dict) -> RLSPolicy:
        """Create a new RLS policy and flush to obtain the generated id."""
        policy = RLSPolicy(**rls_data)
        session.add(policy)
        await session.flush()
        return policy

    async def get_by_tenant(
        self, session: AsyncSession, tenant_id: uuid.UUID
    ) -> list[RLSPolicy]:
        """Return all RLS policies for a tenant."""
        stmt = (
            select(RLSPolicy)
            .where(RLSPolicy.tenant_id == tenant_id)
            .order_by(RLSPolicy.created_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_by_tenant(
        self, session: AsyncSession, tenant_id: uuid.UUID
    ) -> list[RLSPolicy]:
        """Return only active RLS policies for a tenant."""
        stmt = (
            select(RLSPolicy)
            .where(RLSPolicy.tenant_id == tenant_id, RLSPolicy.is_active.is_(True))
            .order_by(RLSPolicy.created_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
