"""Routing questions for the Supervisor — does it call the right specialist?

Checked via result.metrics.tool_metrics (which specialist tool the
Supervisor actually invoked), never by reading its prose answer — a
correct-sounding answer routed to the wrong specialist would still be a
bounded-context violation even if the words happen to be right.
"""

from dataclasses import dataclass


@dataclass
class RoutingQuestion:
    """One question plus the specialist tool the Supervisor must invoke for it."""

    id: str
    question: str
    expected_specialist: str


ROUTING_QUESTIONS = [
    RoutingQuestion("denial_rate", "What is our overall denial rate?", "revenue_analyst"),
    RoutingQuestion("collection_rate", "What is our overall collection rate?", "revenue_analyst"),
    RoutingQuestion(
        "open_ar_total", "How much money do we have in open accounts receivable right now?", "revenue_analyst"
    ),
    RoutingQuestion("claim_status", "What is the status of claim CLM48516149?", "claims_investigator"),
    RoutingQuestion("claim_outstanding", "Why is claim CLM46475778 still outstanding?", "claims_investigator"),
    RoutingQuestion("appeals_worth_it", "Are appeals worth the effort for us?", "denials_ar_advisor"),
    RoutingQuestion("payer_ar_aging", "What is UnitedHealthcare's AR aging breakdown?", "denials_ar_advisor"),
    RoutingQuestion("data_trust", "Can I trust today's numbers? Run a check.", "data_steward"),
    RoutingQuestion("lineage", "Where does mtr_claims_funnel's data actually come from?", "data_steward"),
    RoutingQuestion("glossary", "What does the term 'open AR' mean?", "data_steward"),
]
