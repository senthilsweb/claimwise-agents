"""No-LLM smoke check: does the data adapter + tool layer actually work?

Run with `make smoke`. This does not call Bedrock — it exercises the same
code path the agent's tools use, directly, so data/config problems surface
before you spend a model call on them. It also proves the read-only guard
actually blocks a write, not just that nobody happened to try one.
"""

import sys

from agents.data import ReadOnlyViolation, run_select
from agents.glossary import GLOSSARY
from agents.tools.advisor import appeal_outcomes, ar_aging, payer_scorecard
from agents.tools.billing import get_claim_story, list_claims
from agents.tools.metrics import METRIC_CATALOG, explain_metric, query_metric
from agents.tools.steward import get_lineage, glossary_lookup, run_dq_checks


def check(label: str, condition: bool, detail: str = "") -> bool:
    """Print a PASS/FAIL line (detail only on failure) and return condition."""
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    return condition


def main() -> int:
    """Exercise every tool and guardrail directly, without any model call.

    Covers all four agents' tools against live data, proves the read-only
    guard and metric allowlist actually reject bad input, and pings the
    AgentCore runtime app. Exit code 0 only when every check passed.
    """
    results = []

    print("Metric catalog and explain_metric:")
    for table in METRIC_CATALOG:
        info = explain_metric(table)
        results.append(check(f"explain_metric('{table}')", info["table"] == table))

    print("\nquery_metric against every published table:")
    for table in METRIC_CATALOG:
        result = query_metric(table, limit=3)
        results.append(
            check(
                f"query_metric('{table}')",
                result["row_count"] > 0,
                f"got {result['row_count']} rows",
            )
        )

    print("\nBilling tools (list_claims / get_claim_story):")
    listed = list_claims(limit=5)
    results.append(check("list_claims(limit=5)", listed["row_count"] > 0, f"got {listed['row_count']} rows"))

    denied = list_claims(claim_status="Denied", limit=5)
    results.append(
        check(
            "list_claims(claim_status='Denied') only returns denied claims",
            all(r["claim_status"] == "Denied" for r in denied["rows"]),
        )
    )

    story = get_claim_story("CLM48516149")  # known appealed claim with an appeal activity
    results.append(check("get_claim_story finds a known claim", story["found"]))
    results.append(
        check(
            "get_claim_story returns its appeal activity",
            any(a["is_appeal"] for a in story.get("activities", [])),
        )
    )

    collected = get_claim_story("CLM46475778")  # known approved claim with a processed collection
    results.append(
        check(
            "get_claim_story computes total_collected from real rows",
            collected["found"] and collected["total_collected"] > 0,
            f"got {collected.get('total_collected')}",
        )
    )

    missing = get_claim_story("CLM00000000")  # does not exist
    results.append(check("get_claim_story reports not-found honestly", missing["found"] is False))

    print("\nAdvisor tools (payer_scorecard / ar_aging / appeal_outcomes):")
    scorecard = payer_scorecard(payer_name="UnitedHealthcare")
    results.append(
        check(
            "payer_scorecard(payer_name=...) scopes to one payer",
            scorecard["row_count"] == 1 and scorecard["rows"][0]["payer_name"] == "UnitedHealthcare",
        )
    )

    aging = ar_aging(payer_name="UnitedHealthcare")
    results.append(check("ar_aging(payer_name=...) returns aging buckets", aging["row_count"] > 0))

    outcomes = appeal_outcomes()
    results.append(
        check(
            "appeal_outcomes returns both outcome groups",
            {r["outcome"] for r in outcomes["rows"]} == {"collected", "not_collected"},
        )
    )

    print("\nSteward tools (run_dq_checks / get_lineage / glossary_lookup):")
    dq = run_dq_checks()
    results.append(check("run_dq_checks actually runs dbt test", dq.get("ran") and dq.get("parsed")))
    results.append(check("run_dq_checks reports trustworthy on green tests", dq.get("trustworthy") is True))

    lineage = get_lineage("mtr_claims_funnel")
    results.append(
        check(
            "get_lineage finds a known model's real upstream",
            lineage["found"] and "fct_claims" in lineage["upstream"],
        )
    )
    missing_lineage = get_lineage("not_a_real_model")
    results.append(check("get_lineage reports not-found honestly", missing_lineage["found"] is False))

    term = glossary_lookup("denial rate")
    results.append(check("glossary_lookup finds a known term", term["found"] and "denial_rate_pct" in term["definition"]))
    unknown_term = glossary_lookup("something made up")
    results.append(
        check(
            "glossary_lookup reports unknown terms honestly with the known list",
            unknown_term["found"] is False and set(unknown_term["known_terms"]) == set(GLOSSARY.keys()),
        )
    )

    print("\nGuardrails:")
    try:
        query_metric("fct_claims")  # not in the allowlist
        results.append(check("query_metric rejects a non-metric table", False))
    except ValueError:
        results.append(check("query_metric rejects a non-metric table", True))

    try:
        run_select("DELETE FROM gold.mtr_claims_funnel")
        results.append(check("run_select rejects a write statement", False))
    except ReadOnlyViolation:
        results.append(check("run_select rejects a write statement", True))

    print("\nAgentCore Runtime app (agents/runtime.py, no model call):")
    from starlette.testclient import TestClient

    from agents.runtime import app as runtime_app

    with TestClient(runtime_app) as client:
        ping = client.get("/ping")
        results.append(check("runtime app /ping responds", ping.status_code == 200 and ping.json().get("status") == "Healthy"))

        empty = client.post("/invocations", json={})
        body = empty.json()
        results.append(
            check(
                "runtime app rejects an empty prompt without calling the model",
                "error" in body and "prompt" in body["error"],
            )
        )

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} checks passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
