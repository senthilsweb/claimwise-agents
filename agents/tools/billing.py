"""Tools for the Claims Investigator — the gold/billing bounded context.

Claim is the aggregate root: activities and collections are read only
through it, in time order — the same shape as the article's Claim
aggregate (root owns activities and collections; Patient and Payer are
peer aggregates, referenced by name only, never joined for their own
detail). The join logic is fixed here, in code — the model never writes
SQL for billing, only calls these two functions.

Note on scope: this schema has no claim-to-encounter link (a deliberate
gap noted in the claimwise repo's own design doc — claims are not linked
to encounters, so revenue is never attributed to a specialty). A claim's
story here starts at "filed", not at the clinical visit that caused it.
"""

from strands import tool

from agents import data
from agents.sqlutil import sql_literal

_SUCCESSFUL_COLLECTION_STATUSES = ("Processed", "Completed")


@tool
def list_claims(
    claim_status: str | None = None,
    payer_name: str | None = None,
    patient_name: str | None = None,
    limit: int = 20,
) -> dict:
    """Find claims to investigate, filtered by status, payer, or patient name.

    Returns just enough to pick a claim_code — status, amount, date,
    patient, payer. Call get_claim_story on a specific claim_code next for
    the full lifecycle; this tool never returns activities or collections.

    Args:
        claim_status: Exact match: Submitted, In Review, Approved, Denied, or Appealed.
        payer_name: Exact payer name match.
        patient_name: Exact patient name match.
        limit: Max rows to return (default 20, capped at 100).
    """
    limit = max(1, min(limit, 100))
    clauses = []
    if claim_status:
        clauses.append(f"c.claim_status = {sql_literal(claim_status)}")
    if payer_name:
        clauses.append(f"p.payer_name = {sql_literal(payer_name)}")
    if patient_name:
        clauses.append(f"pt.patient_name = {sql_literal(patient_name)}")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    sql = (
        "SELECT c.claim_code, c.claim_status, c.claim_amount, c.claim_date, "
        "pt.patient_name, p.payer_name "
        f"FROM {data.gold_table('fct_claims')} c "
        f"JOIN {data.gold_table('dim_patient')} pt ON c.patient_key = pt.patient_id "
        f"JOIN {data.gold_table('dim_payer')} p ON c.payer_key = p.payer_id "
        f"{where} "
        f"ORDER BY c.claim_date DESC LIMIT {limit}"
    )
    rows = data.run_select(sql)
    return {"row_count": len(rows), "rows": rows}


@tool
def get_claim_story(claim_code: str) -> dict:
    """Read one claim's full lifecycle: the claim, every activity, every
    collection — in time order, exactly as they happened.

    This is the ONLY way to answer "why is this claim unpaid/denied/still
    open". Narrate the returned events in order (filed, reviewed, denied,
    appealed, collected) — never invent an event that is not in the lists,
    and never guess at a patient's clinical history; this tool only knows
    about the claim itself.

    Args:
        claim_code: The claim's business id, e.g. "CLM21563228".
    """
    claim_rows = data.run_select(
        "SELECT c.claim_id, c.claim_code, c.claim_status, c.claim_amount, c.claim_date, "
        "pt.patient_name, p.payer_name "
        f"FROM {data.gold_table('fct_claims')} c "
        f"JOIN {data.gold_table('dim_patient')} pt ON c.patient_key = pt.patient_id "
        f"JOIN {data.gold_table('dim_payer')} p ON c.payer_key = p.payer_id "
        f"WHERE c.claim_code = {sql_literal(claim_code)}"
    )
    if not claim_rows:
        return {"found": False, "claim_code": claim_code}

    claim = claim_rows[0]
    claim_id = claim.pop("claim_id")

    activities = data.run_select(
        "SELECT activity_code, activity_date, activity_type, is_appeal, is_documentation_request "
        f"FROM {data.gold_table('fct_claim_activities')} "
        f"WHERE claim_key = {claim_id} ORDER BY activity_date"
    )

    collections = data.run_select(
        "SELECT collection_code, collection_date, collection_method, "
        "collected_amount, collection_status "
        f"FROM {data.gold_table('fct_collections')} "
        f"WHERE claim_key = {claim_id} ORDER BY collection_date"
    )

    total_collected = round(
        sum(c["collected_amount"] for c in collections if c["collection_status"] in _SUCCESSFUL_COLLECTION_STATUSES),
        2,
    )

    return {
        "found": True,
        "claim": claim,
        "activities": activities,
        "collections": collections,
        "total_collected": total_collected,
        "amount_outstanding": round(claim["claim_amount"] - total_collected, 2),
    }
