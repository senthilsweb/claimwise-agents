"""No-LLM smoke check: does the data adapter + tool layer actually work?

Run with `make smoke`. This does not call Bedrock — it exercises the same
code path the agent's tools use, directly, so data/config problems surface
before you spend a model call on them. It also proves the read-only guard
actually blocks a write, not just that nobody happened to try one.
"""

import sys

from agents.data import ReadOnlyViolation, run_select
from agents.tools.billing import get_claim_story, list_claims
from agents.tools.metrics import METRIC_CATALOG, explain_metric, query_metric


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    return condition


def main() -> int:
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

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} checks passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
