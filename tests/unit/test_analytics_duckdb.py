"""Tests for the DuckDB analytics backend with RLS enforcement."""

import pytest

from deepvu.analytics.duckdb_backend import DuckDBAnalyticsBackend


@pytest.fixture
def backend():
    """Create an in-memory DuckDB backend with test data."""
    b = DuckDBAnalyticsBackend(":memory:")
    b._conn.execute(
        """
        CREATE TABLE ads (
            id INTEGER,
            advertiser_id VARCHAR,
            campaign VARCHAR,
            clicks INTEGER
        )
        """
    )
    b._conn.execute(
        """
        INSERT INTO ads VALUES
            (1, 'adv1', 'campaign_a', 100),
            (2, 'adv1', 'campaign_b', 200),
            (3, 'adv2', 'campaign_c', 300),
            (4, 'adv2', 'campaign_d', 400)
        """
    )
    return b


class TestRLSEnforcement:
    @pytest.mark.asyncio
    async def test_rls_enforcement(self, backend):
        """Querying with advertiser_id 'adv1' returns only adv1 rows."""
        rows = await backend.execute_query(
            "SELECT * FROM ads", {}, rls_advertiser_id="adv1"
        )
        assert len(rows) == 2
        for row in rows:
            assert row["advertiser_id"] == "adv1"

    @pytest.mark.asyncio
    async def test_injection_prevention(self, backend):
        """Attempting to bypass RLS with OR still filters to the correct tenant."""
        rows = await backend.execute_query(
            "SELECT * FROM ads WHERE 1=1 OR advertiser_id = 'adv2'",
            {},
            rls_advertiser_id="adv1",
        )
        for row in rows:
            assert row["advertiser_id"] == "adv1"

    @pytest.mark.asyncio
    async def test_dml_rejected(self, backend):
        """INSERT and DELETE statements are rejected."""
        with pytest.raises(ValueError, match="Unsafe"):
            await backend.execute_query(
                "INSERT INTO ads VALUES (5, 'adv1', 'x', 0)",
                {},
                rls_advertiser_id="adv1",
            )
        with pytest.raises(ValueError, match="Unsafe"):
            await backend.execute_query(
                "DELETE FROM ads", {}, rls_advertiser_id="adv1"
            )


class TestMetadata:
    @pytest.mark.asyncio
    async def test_list_tables(self, backend):
        tables = await backend.list_tables()
        assert "ads" in tables

    @pytest.mark.asyncio
    async def test_get_table_schema(self, backend):
        schema = await backend.get_table_schema("ads")
        col_names = [c["name"] for c in schema]
        assert "id" in col_names
        assert "advertiser_id" in col_names
        assert "campaign" in col_names
        assert "clicks" in col_names
        # Check that types are present
        for col in schema:
            assert "type" in col
            assert col["type"]  # not empty
