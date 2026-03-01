import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from deepvu.models.base import Base

EXPECTED_TABLES = {
    "tenants",
    "tenant_branding",
    "tenant_domains",
    "users",
    "tenant_sso_config",
    "rls_policies",
}


@pytest.fixture
async def inspectable_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


class TestMigrations:
    async def test_all_tables_created(self, inspectable_engine):
        async with inspectable_engine.connect() as conn:
            table_names = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        assert EXPECTED_TABLES.issubset(set(table_names))

    async def test_tenants_columns(self, inspectable_engine):
        async with inspectable_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("tenants")
                }
            )
        assert {"id", "name", "slug", "advertiser_id", "dashboard_type", "is_active", "created_at", "updated_at"}.issubset(columns)

    async def test_users_columns(self, inspectable_engine):
        async with inspectable_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("users")
                }
            )
        assert {"id", "tenant_id", "email", "name", "role", "auth_provider", "is_active"}.issubset(columns)

    async def test_rls_policies_columns(self, inspectable_engine):
        async with inspectable_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("rls_policies")
                }
            )
        assert {"id", "tenant_id", "table_name", "filter_column", "filter_value"}.issubset(columns)
