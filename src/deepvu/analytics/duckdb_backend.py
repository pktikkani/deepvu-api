"""DuckDB-based analytics backend with RLS enforcement."""

import asyncio

import duckdb

from deepvu.analytics.rls_injector import inject_rls
from deepvu.analytics.rls_validator import reject_unsafe_sql, validate_rls


class DuckDBAnalyticsBackend:
    """In-process DuckDB analytics backend implementing AnalyticsQueryService.

    Uses duckdb for fast columnar analytics.  Every query goes through
    RLS injection and validation before execution.

    Args:
        db_path: Path to the DuckDB database file, or ":memory:" for in-memory.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = duckdb.connect(db_path)

    async def execute_query(
        self, query: str, params: dict, rls_advertiser_id: str
    ) -> list[dict]:
        """Execute a query with RLS enforcement.

        The query is first checked for unsafe DML/DDL, then the
        advertiser_id filter is injected, and finally the result
        is validated before execution.

        Args:
            query: SQL SELECT query.
            params: Query parameters (reserved for future use).
            rls_advertiser_id: Advertiser ID for tenant isolation.

        Returns:
            List of result rows as dictionaries.

        Raises:
            ValueError: If the query is unsafe or RLS was not applied.
        """
        reject_unsafe_sql(query)
        secured = inject_rls(query, rls_advertiser_id)
        if not validate_rls(secured, rls_advertiser_id):
            raise ValueError("RLS filter not applied")

        def _run() -> list[dict]:
            result = self._conn.execute(secured)
            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row)) for row in result.fetchall()]

        return await asyncio.to_thread(_run)

    async def list_tables(self) -> list[str]:
        """Return a list of table names in the database."""

        def _run() -> list[str]:
            result = self._conn.execute("SHOW TABLES")
            return [row[0] for row in result.fetchall()]

        return await asyncio.to_thread(_run)

    async def get_table_schema(self, table_name: str) -> list[dict]:
        """Return column name and type information for a table.

        Args:
            table_name: The table to describe.

        Returns:
            List of dicts with 'name' and 'type' keys.
        """

        def _run() -> list[dict]:
            result = self._conn.execute(f"DESCRIBE {table_name}")
            return [{"name": row[0], "type": row[1]} for row in result.fetchall()]

        return await asyncio.to_thread(_run)
