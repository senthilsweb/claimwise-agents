"""Tools for the Denials & AR Advisor — the gold/billing bounded context,
payer- and portfolio-level view (as opposed to the Claims Investigator's
single-claim view).

payer_scorecard and ar_aging read the same published mtr_* tables the
Revenue Analyst can reach via query_metric, but as their own scoped,
purpose-built tools — this agent gets its own named tool per bounded-
context rule, not the generic table-picker. appeal_outcomes answers a
question the metric layer does not: whether appeals actually pay off,
computed in code from real claim/activity/collection rows, never by the
model doing arithmetic over raw rows.
"""

from strands import tool

from agents import data
from agents.sqlutil import sql_literal


@tool
def payer_scorecard(payer_name: str | None = None) -> dict:
    """Read the billing scorecard for one payer, or all payers if omitted:
    billed amount, collected amount, collection rate, denial rate, open AR,
    claim count, and average claim amount.

    Args:
        payer_name: Exact payer name to scope to one payer. Omit for every payer.
    """
    where = f"WHERE payer_name = {sql_literal(payer_name)}" if payer_name else ""
    sql = (
        "SELECT payer_name, billed_amount, collected_amount, collection_rate_pct, "
        "denial_rate_pct, open_ar, claim_count, avg_claim_amount "
        f"FROM {data.gold_table('mtr_payer_scorecard')} {where} "
        "ORDER BY billed_amount DESC"
    )
    rows = data.run_select(sql)
    return {"row_count": len(rows), "rows": rows}


@tool
def ar_aging(payer_name: str | None = None) -> dict:
    """Read open accounts receivable broken down by aging bucket
    (0-30/31-60/61-90/90+ days), for one payer or all payers.

    Args:
        payer_name: Exact payer name to scope to one payer. Omit for every payer.
    """
    where = f"WHERE payer_name = {sql_literal(payer_name)}" if payer_name else ""
    sql = (
        "SELECT payer_name, aging_bucket, bucket_order, open_claim_count, open_ar_amount "
        f"FROM {data.gold_table('mtr_ar_aging')} {where} "
        "ORDER BY payer_name, bucket_order"
    )
    rows = data.run_select(sql)
    return {"row_count": len(rows), "rows": rows}


@tool
def appeal_outcomes() -> dict:
    """Read what actually happens to claims that get appealed: how many
    eventually collect vs. never do, with claim counts and dollar amounts
    for each outcome — computed from real claim/activity/collection rows,
    not an opinion. Use this to answer "are appeals worth it".
    """
    sql = f"""
        WITH appealed_claims AS (
            SELECT DISTINCT claim_key
            FROM {data.gold_table('fct_claim_activities')}
            WHERE is_appeal = 1
        ),
        collected_per_claim AS (
            SELECT claim_key, SUM(collected_amount) AS collected_amount
            FROM {data.gold_table('fct_collections')}
            WHERE collection_status IN ('Processed', 'Completed')
            GROUP BY claim_key
        )
        SELECT
            CASE WHEN col.claim_key IS NOT NULL THEN 'collected' ELSE 'not_collected' END AS outcome,
            COUNT(*) AS claim_count,
            ROUND(SUM(c.claim_amount), 2) AS total_claim_amount,
            ROUND(AVG(c.claim_amount), 2) AS avg_claim_amount
        FROM appealed_claims a
        JOIN {data.gold_table('fct_claims')} c ON c.claim_id = a.claim_key
        LEFT JOIN collected_per_claim col ON col.claim_key = a.claim_key
        GROUP BY outcome
    """
    rows = data.run_select(sql)
    return {"row_count": len(rows), "rows": rows}
