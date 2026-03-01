"""Analytics query service protocol for multi-tenant ad analytics."""

from typing import Protocol


class AnalyticsQueryService(Protocol):
    """Protocol defining the interface for analytics query backends.

    All implementations must enforce row-level security (RLS) via
    advertiser_id filtering before executing any query.
    """

    async def execute_query(
        self, query: str, params: dict, rls_advertiser_id: str
    ) -> list[dict]:
        """Execute an analytics query with RLS enforcement.

        Args:
            query: SQL query string.
            params: Query parameters.
            rls_advertiser_id: The advertiser ID to enforce as an RLS filter.

        Returns:
            List of result rows as dictionaries.
        """
        ...

    async def list_tables(self) -> list[str]:
        """Return a list of available table names."""
        ...

    async def get_table_schema(self, table_name: str) -> list[dict]:
        """Return column metadata for a table.

        Args:
            table_name: Name of the table to describe.

        Returns:
            List of dicts with 'name' and 'type' keys.
        """
        ...
