"""Validation utilities for RLS enforcement and SQL safety."""

import sqlglot
from sqlglot import exp


def validate_rls(sql: str, advertiser_id: str) -> bool:
    """Check that the advertiser_id RLS filter is present in the query.

    Args:
        sql: The SQL query to validate.
        advertiser_id: The expected advertiser ID value.

    Returns:
        True if the query contains the advertiser_id filter.
    """
    parsed = sqlglot.parse_one(sql)
    sql_text = parsed.sql()
    return f"advertiser_id = '{advertiser_id}'" in sql_text


def reject_unsafe_sql(sql: str) -> None:
    """Reject DML and DDL statements to prevent data mutation.

    Only SELECT queries are permitted.  INSERT, UPDATE, DELETE,
    CREATE, DROP, and ALTER TABLE statements will raise ValueError.

    Args:
        sql: The SQL statement to check.

    Raises:
        ValueError: If the statement is not a safe read-only query.
    """
    parsed = sqlglot.parse_one(sql)
    unsafe_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Create,
        exp.Drop,
        exp.Alter,
    )
    if isinstance(parsed, unsafe_types):
        raise ValueError(f"Unsafe SQL statement type: {type(parsed).__name__}")
