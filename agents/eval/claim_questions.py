"""Golden questions for the Claims Investigator — deterministic, no LLM-judge.

Expected values are read straight off get_claim_story (the same tool the
agent uses), which itself computes from live rows in fct_claims/
fct_claim_activities/fct_collections — not hand-picked constants that could
drift from the data.
"""

from dataclasses import dataclass

from agents.tools.billing import get_claim_story


@dataclass
class ClaimQuestion:
    id: str
    question: str
    expected: callable  # () -> str, the value the answer must contain


def _appealed_claim_status() -> str:
    return get_claim_story("CLM48516149")["claim"]["claim_status"]


def _appealed_claim_has_appeal() -> str:
    story = get_claim_story("CLM48516149")
    assert any(a["is_appeal"] for a in story["activities"]), "fixture claim lost its appeal activity"
    return "appeal"


def _collected_claim_total() -> str:
    return str(get_claim_story("CLM46475778")["total_collected"])


def _unknown_claim_not_found() -> str:
    assert get_claim_story("CLM00000000")["found"] is False
    return "not"


CLAIM_QUESTIONS = [
    ClaimQuestion(
        id="claim_status",
        question="What is the status of claim CLM48516149?",
        expected=_appealed_claim_status,
    ),
    ClaimQuestion(
        id="claim_has_appeal",
        question="Was claim CLM48516149 ever appealed?",
        expected=_appealed_claim_has_appeal,
    ),
    ClaimQuestion(
        id="claim_collected_amount",
        question="How much has been collected on claim CLM46475778?",
        expected=_collected_claim_total,
    ),
    ClaimQuestion(
        id="unknown_claim",
        question="What is the status of claim CLM00000000?",
        expected=_unknown_claim_not_found,
    ),
]
