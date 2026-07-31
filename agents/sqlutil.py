"""Shared SQL literal-escaping helper for tools that build fixed-shape
queries with dynamic values (never dynamic SQL from the model itself)."""


def sql_literal(value) -> str:
    """Render a Python value as a safe SQL literal (quotes escaped by doubling)."""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"
