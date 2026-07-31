"""Tools for the Revenue Analyst — the gold/metrics bounded context.

query_metric is the entire vocabulary this agent may use to answer a KPI
question. METRIC_CATALOG below is the allowlist: a table not listed here
cannot be queried, full stop — the agent never sees or joins raw facts.
"""

from strands import tool

from agents import data
from agents.sqlutil import sql_literal

METRIC_CATALOG: dict[str, dict] = {
    "mtr_executive_summary": {
        "description": "Single-row executive KPI summary: billed, collected, rates, open AR, cycle days.",
        "grain": "one row, whole business",
        "columns": {
            "gross_billed": "Total dollar amount billed across all claims.",
            "total_collected": "Total dollars actually collected against those claims.",
            "collection_rate_pct": "total_collected / gross_billed, as a percentage.",
            "denial_rate_pct": "Percentage of claims with status Denied.",
            "open_ar": "Claim amount minus collections, for claims not denied and not fully paid.",
            "avg_cycle_days": "Average days between a claim being created and last updated.",
            "claim_count": "Total number of claims.",
            "encounter_count": "Total number of patient encounters.",
        },
    },
    "mtr_revenue_monthly": {
        "description": "Billed vs collected by calendar month, with collection rate.",
        "grain": "one row per month",
        "columns": {
            "month": "Calendar month (first day of month).",
            "billed_amount": "Dollars billed in that month.",
            "collected_amount": "Dollars collected in that month.",
            "collection_rate_pct": "collected_amount / billed_amount, as a percentage.",
            "claim_count": "Claims billed in that month.",
            "denied_count": "Of those, how many were denied.",
        },
    },
    "mtr_payer_scorecard": {
        "description": "Per-payer billing scorecard: billed, collected, rates, open AR.",
        "grain": "one row per payer",
        "columns": {
            "payer_name": "The insurance payer.",
            "billed_amount": "Total dollars billed to this payer.",
            "collected_amount": "Total dollars collected from this payer.",
            "collection_rate_pct": "collected_amount / billed_amount, as a percentage.",
            "denial_rate_pct": "Percentage of this payer's claims that were denied.",
            "open_ar": "Open accounts receivable with this payer.",
            "claim_count": "Number of claims billed to this payer.",
            "avg_claim_amount": "Average dollar amount per claim for this payer.",
        },
    },
    "mtr_ar_aging": {
        "description": "Open accounts receivable by payer and aging bucket (0-30/31-60/61-90/90+ days).",
        "grain": "one row per payer per aging bucket",
        "columns": {
            "payer_name": "The insurance payer.",
            "aging_bucket": "0-30, 31-60, 61-90, or 90+ days since the claim was created.",
            "bucket_order": "Sort order for the bucket (1-4).",
            "open_claim_count": "Number of open (unresolved, uncollected) claims in this bucket.",
            "open_ar_amount": "Total open dollars in this bucket.",
        },
    },
    "mtr_claims_funnel": {
        "description": "Claim counts and dollar amounts by lifecycle status.",
        "grain": "one row per claim status",
        "columns": {
            "claim_status": "Submitted, In Review, Approved, Denied, or Appealed.",
            "claim_count": "Number of claims with this status.",
            "total_amount": "Total dollar amount of claims with this status.",
            "pct_of_claims": "This status's share of all claims, as a percentage.",
        },
    },
    "mtr_department_activity": {
        "description": "Encounter volumes by medical specialty. Volumes only — no revenue attribution.",
        "grain": "one row per specialty",
        "columns": {
            "specialty": "The doctor's medical specialty.",
            "encounter_count": "Number of encounters (visits) in this specialty.",
            "unique_patients": "Distinct patients seen.",
            "active_doctors": "Distinct doctors practicing.",
            "avg_duration_minutes": "Average encounter duration, in minutes.",
            "emergency_visits": "Of those encounters, how many were emergency visits.",
        },
    },
}


def _validate_table(table: str) -> dict:
    """Return the table's catalog entry, or raise if it isn't a published metric."""
    if table not in METRIC_CATALOG:
        allowed = ", ".join(sorted(METRIC_CATALOG))
        raise ValueError(f"'{table}' is not a published metric. Allowed tables: {allowed}")
    return METRIC_CATALOG[table]


def _validate_columns(table: str, columns: list[str]) -> None:
    """Raise if any column isn't in the table's catalog entry."""
    known = METRIC_CATALOG[table]["columns"]
    unknown = [c for c in columns if c not in known]
    if unknown:
        allowed = ", ".join(known.keys())
        raise ValueError(f"Unknown column(s) {unknown} for {table}. Allowed columns: {allowed}")


@tool
def explain_metric(table: str) -> dict:
    """Look up what a published metric table means before querying it.

    Returns the table's description, its grain (what one row represents),
    and what every column means. Always call this on a table before your
    first query_metric call on it in this conversation — never guess a
    column's meaning from its name.

    Args:
        table: One of the published metric tables (see query_metric's list).
    """
    catalog = _validate_table(table)
    return {
        "table": table,
        "description": catalog["description"],
        "grain": catalog["grain"],
        "columns": catalog["columns"],
    }


@tool
def query_metric(
    table: str,
    columns: list[str] | None = None,
    filters: dict | None = None,
    order_by: str | None = None,
    descending: bool = False,
    limit: int | None = None,
) -> dict:
    """Read rows from one published metric table in the gold layer.

    This is the ONLY way to answer a KPI question. Never compute a rate,
    total, or count yourself from raw facts — every metric in this system
    is already defined once, in one of these tables: mtr_executive_summary,
    mtr_revenue_monthly, mtr_payer_scorecard, mtr_ar_aging,
    mtr_claims_funnel, mtr_department_activity. If the number you need is
    not in any of these, say so plainly instead of estimating it.

    Args:
        table: One of the published metric tables above.
        columns: Which columns to return. Omit to return all columns.
        filters: Exact-match filters, e.g. {"claim_status": "Denied"}.
        order_by: Column to sort by.
        descending: Sort descending instead of ascending.
        limit: Max rows to return.
    """
    _validate_table(table)
    selected = columns or list(METRIC_CATALOG[table]["columns"].keys())
    _validate_columns(table, selected)

    sql_parts = [f"SELECT {', '.join(selected)}", f"FROM {data.gold_table(table)}"]

    if filters:
        _validate_columns(table, list(filters.keys()))
        clauses = [f"{col} = {sql_literal(val)}" for col, val in filters.items()]
        sql_parts.append("WHERE " + " AND ".join(clauses))

    if order_by:
        _validate_columns(table, [order_by])
        sql_parts.append(f"ORDER BY {order_by} {'DESC' if descending else 'ASC'}")

    if limit:
        sql_parts.append(f"LIMIT {int(limit)}")

    sql = " ".join(sql_parts)
    rows = data.run_select(sql)
    return {"table": table, "sql": sql, "row_count": len(rows), "rows": rows}
