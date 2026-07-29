"""Golden questions for the Revenue Analyst — deterministic, no LLM-judge.

Each question's expected value is fetched independently, straight off the
gold metric tables (not through query_metric), so the eval is a genuine
check against the source of truth rather than a self-fulfilling one.
"""

from dataclasses import dataclass

from agents.data import gold_table, run_select


@dataclass
class GoldenQuestion:
    id: str
    question: str
    expected: callable  # () -> str, the value the answer must contain


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".") if value == int(value) else f"{value:.2f}"
    return str(value)


def _executive_summary_value(column: str) -> str:
    row = run_select(f"SELECT {column} FROM {gold_table('mtr_executive_summary')}")[0]
    return _fmt(row[column])


def _denied_claim_count() -> str:
    row = run_select(
        f"SELECT claim_count FROM {gold_table('mtr_claims_funnel')} WHERE claim_status = 'Denied'"
    )[0]
    return _fmt(row["claim_count"])


def _worst_payer_by_denial_rate() -> str:
    row = run_select(
        f"SELECT payer_name FROM {gold_table('mtr_payer_scorecard')} "
        "ORDER BY denial_rate_pct DESC LIMIT 1"
    )[0]
    return row["payer_name"]


GOLDEN_QUESTIONS = [
    GoldenQuestion(
        id="denial_rate",
        question="What is our overall denial rate?",
        expected=lambda: _executive_summary_value("denial_rate_pct"),
    ),
    GoldenQuestion(
        id="collection_rate",
        question="What is our overall collection rate?",
        expected=lambda: _executive_summary_value("collection_rate_pct"),
    ),
    GoldenQuestion(
        id="open_ar",
        question="How much money do we have in open accounts receivable right now?",
        expected=lambda: _executive_summary_value("open_ar"),
    ),
    GoldenQuestion(
        id="denied_claim_count",
        question="How many claims have been denied?",
        expected=_denied_claim_count,
    ),
    GoldenQuestion(
        id="worst_payer",
        question="Which payer has the highest denial rate?",
        expected=_worst_payer_by_denial_rate,
    ),
]
