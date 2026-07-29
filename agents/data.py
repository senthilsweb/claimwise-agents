"""Read-only data adapter over the gold layer — DuckDB (dev) or Databricks (prod).

The read-only rule is enforced here, once, by construction: run_select()
rejects anything that is not a single SELECT/WITH statement before it ever
reaches a connection. No tool anywhere in this repo has a path to write.
"""

import re

from agents import config

_SELECT_ONLY_RE = re.compile(r"^\s*(with\b|select\b)", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|"
    r"merge|copy|attach|call|pragma|vacuum|exec|execute)\b",
    re.IGNORECASE,
)


class ReadOnlyViolation(Exception):
    """Raised when a statement is not a plain SELECT — never bypass this."""


def _assert_select_only(sql: str) -> None:
    stripped = sql.strip().rstrip(";")
    if ";" in stripped:
        raise ReadOnlyViolation("Only a single statement is allowed (no ';'-separated statements).")
    if not _SELECT_ONLY_RE.match(stripped):
        raise ReadOnlyViolation("Only SELECT (or WITH ... SELECT) statements are allowed.")
    if _FORBIDDEN_RE.search(stripped):
        raise ReadOnlyViolation("Statement contains a write/DDL keyword — agents are read-only by construction.")


def gold_table(name: str) -> str:
    """Fully-qualified gold table name for the currently active target."""
    if config.AGENT_TARGET == "databricks":
        return f"{config.DATABRICKS_CATALOG}.gold.{name}"
    return f"gold.{name}"


_duckdb_conn = None


def _get_duckdb_conn():
    global _duckdb_conn
    if _duckdb_conn is None:
        import duckdb

        path = config.require(config.DUCKDB_PATH, "DUCKDB_PATH")
        _duckdb_conn = duckdb.connect(path, read_only=True)
    return _duckdb_conn


def release_duckdb_connection() -> None:
    """Close our cached read-only DuckDB connection, if open.

    DuckDB allows only one process to hold a lock on a file at a time, even
    a read-only one, once anything else needs read-write access. dbt's own
    DuckDB adapter always opens read-write (even for `dbt test`), so the
    Data Steward calls this before shelling out to `dbt test` — the
    connection reopens lazily on the next run_select() call.
    """
    global _duckdb_conn
    if _duckdb_conn is not None:
        _duckdb_conn.close()
        _duckdb_conn = None


def _get_databricks_conn():
    from databricks import sql as databricks_sql

    return databricks_sql.connect(
        server_hostname=config.require(config.DATABRICKS_HOST, "DATABRICKS_HOST"),
        http_path=config.require(config.DATABRICKS_HTTP_PATH, "DATABRICKS_HTTP_PATH"),
        access_token=config.require(config.DATABRICKS_TOKEN, "DATABRICKS_TOKEN"),
    )


def run_select(sql: str) -> list[dict]:
    """Execute a read-only SELECT/WITH statement and return rows as dicts."""
    _assert_select_only(sql)

    if config.AGENT_TARGET == "databricks":
        conn = _get_databricks_conn()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute(sql)
                columns = [d[0] for d in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            finally:
                cursor.close()
        finally:
            conn.close()

    conn = _get_duckdb_conn()
    result = conn.execute(sql)
    columns = [d[0] for d in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]
