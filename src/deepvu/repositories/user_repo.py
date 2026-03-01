"""Repository layer for User model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.models.user import User


class UserRepository:
    """Data-access methods for User, always scoped by tenant_id."""

    async def create(self, session: AsyncSession, user_data: dict) -> User:
        """Create a new user and flush to obtain the generated id."""
        user = User(**user_data)
        session.add(user)
        await session.flush()
        return user

    async def get_by_id(
        self, session: AsyncSession, user_id: uuid.UUID, tenant_id: uuid.UUID | None = None
    ) -> User | None:
        """Return a user by primary key, optionally scoped to a tenant."""
        stmt = select(User).where(User.id == user_id)
        if tenant_id is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(
        self, session: AsyncSession, email: str, tenant_id: uuid.UUID
    ) -> User | None:
        """Return a user by email within a specific tenant, or None."""
        stmt = select(User).where(User.email == email, User.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self, session: AsyncSession, tenant_id: uuid.UUID
    ) -> list[User]:
        """Return all users belonging to a tenant."""
        stmt = (
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: dict,
    ) -> User:
        """Update a user scoped by tenant. Raises ValueError when not found."""
        user = await self.get_by_id(session, user_id, tenant_id)
        if user is None:
            raise ValueError(f"User {user_id} not found in tenant {tenant_id}")
        for key, value in data.items():
            setattr(user, key, value)
        await session.flush()
        return user
