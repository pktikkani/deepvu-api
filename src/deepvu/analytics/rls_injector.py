"""Row-level security (RLS) injection for SQL queries using sqlglot.

Parses SQL via sqlglot and injects an `advertiser_id = '<value>'` filter
into the WHERE clause, ensuring tenant isolation at the query level.
"""

import sqlglot
from sqlglot import exp


def inject_rls(sql: str, advertiser_id: str) -> str:
    """Inject advertiser_id filter into a SELECT query.

    Parses the SQL AST and appends (or ANDs) an
    ``advertiser_id = '<advertiser_id>'`` predicate to the WHERE clause.

    Args:
        sql: The original SQL query string.
        advertiser_id: The advertiser ID value to filter on.

    Returns:
        The rewritten SQL string with the RLS filter applied.
    """
    parsed = sqlglot.parse_one(sql)

    rls_condition = exp.EQ(
        this=exp.Column(this=exp.to_identifier("advertiser_id")),
        expression=exp.Literal.string(advertiser_id),
    )

    existing_where = parsed.find(exp.Where)
    if existing_where:
        # Wrap existing conditions in parens to preserve their semantics,
        # then AND with the RLS condition so it cannot be bypassed via OR.
        wrapped_existing = exp.Paren(this=existing_where.this)
        new_condition = exp.And(this=wrapped_existing, expression=rls_condition)
        parsed.set("where", exp.Where(this=new_condition))
    else:
        parsed.set("where", exp.Where(this=rls_condition))

    return parsed.sql()
