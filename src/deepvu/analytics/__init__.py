"""Analytics query abstraction layer with DuckDB + RLS injection."""

from deepvu.analytics.bigquery_backend import BigQueryAnalyticsBackend
from deepvu.analytics.duckdb_backend import DuckDBAnalyticsBackend
from deepvu.analytics.protocol import AnalyticsQueryService
from deepvu.analytics.rls_injector import inject_rls
from deepvu.analytics.rls_validator import reject_unsafe_sql, validate_rls

__all__ = [
    "AnalyticsQueryService",
    "BigQueryAnalyticsBackend",
    "DuckDBAnalyticsBackend",
    "inject_rls",
    "reject_unsafe_sql",
    "validate_rls",
]
