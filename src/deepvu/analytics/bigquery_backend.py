"""BigQuery analytics backend stub.

This module provides a placeholder implementation for a future
BigQuery-backed analytics service.  All methods raise NotImplementedError.
"""


class BigQueryAnalyticsBackend:
    """Stub BigQuery backend -- not yet implemented."""

    async def execute_query(
        self, query: str, params: dict, rls_advertiser_id: str
    ) -> list[dict]:
        raise NotImplementedError("BigQuery backend not yet implemented")

    async def list_tables(self) -> list[str]:
        raise NotImplementedError("BigQuery backend not yet implemented")

    async def get_table_schema(self, table_name: str) -> list[dict]:
        raise NotImplementedError("BigQuery backend not yet implemented")
