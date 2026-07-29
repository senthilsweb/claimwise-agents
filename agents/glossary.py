"""The shared business glossary — ubiquitous language as an actual lookup
table, not just prose repeated across each agent's system prompt. One
definition per term, agreed once, used by every context. The Data Steward
exposes this via glossary_lookup; nothing stops another agent from
importing GLOSSARY directly if it ever needs to.
"""

GLOSSARY: dict[str, str] = {
    "claim": "A bill sent to a payer for money owed for care given to a patient. "
    "Moves through statuses: Submitted, In Review, Approved, Denied, Appealed.",
    "activity": "An event in a claim's lifecycle — a submission, a review, a "
    "documentation request, or an appeal.",
    "appeal": "An activity filed in response to a denied claim, asking the payer "
    "to reconsider.",
    "collection": "Money actually received against a claim. A claim can have zero, "
    "one, or several collections; the amount collected never exceeds the claim amount.",
    "payer": "The insurance company (or Medicare/Medicaid) billed for a claim.",
    "denial rate": "The percentage of claims with status Denied, out of all claims. "
    "Defined once in mtr_executive_summary.denial_rate_pct / mtr_payer_scorecard.denial_rate_pct.",
    "collection rate": "The percentage of billed dollars actually collected "
    "(collected_amount / billed_amount). Defined once in mtr_executive_summary / "
    "mtr_revenue_monthly / mtr_payer_scorecard.",
    "open ar": "Open accounts receivable — claim amount minus collections, for claims "
    "not denied and not fully paid. Defined once in mtr_executive_summary.open_ar / "
    "mtr_ar_aging (broken down by payer and age).",
    "aging bucket": "How long a claim's open balance has been outstanding: 0-30, "
    "31-60, 61-90, or 90+ days since the claim was created.",
    "gross billed": "The total dollar amount billed across all claims, before any collection.",
    "avg cycle days": "The average number of days between a claim being created and "
    "last updated — a rough proxy for how long claims take to resolve.",
    "gold layer": "The clean, business-ready tables everything downstream reads — "
    "organized as bounded contexts (clinical, billing, admin) plus a metrics layer "
    "where every KPI is computed once.",
}
