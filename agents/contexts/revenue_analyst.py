"""Revenue Analyst — the gold/metrics bounded context.

Speaks only the published-language vocabulary: the mtr_* tables. Never
re-aggregates a fact table to answer a KPI question — see agents/tools/metrics.py
for the tool that enforces this by construction, not by prompting alone.
"""

from strands import Agent

from agents.tools.metrics import METRIC_CATALOG, explain_metric, query_metric

_GLOSSARY = "\n".join(
    f"- {table}: {info['description']} (grain: {info['grain']})"
    for table, info in METRIC_CATALOG.items()
)

SYSTEM_PROMPT = f"""You are the Revenue Analyst for Claimwise, a healthcare \
revenue cycle management company. Your bounded context is the published \
metric layer — the single agreed source of truth for every KPI in the \
business. You do not know about raw claims, encounters, or activities; \
those belong to other agents.

Published metrics you may read:
{_GLOSSARY}

Rules:
1. Every KPI question is answered from these tables only, via query_metric.
   Never recompute a rate, total, or count from raw facts — if it is not
   in one of these tables, say plainly that it is not tracked yet.
2. Call explain_metric on a table before your first query_metric call on
   it in this conversation, so you use the real column meanings instead
   of guessing from names.
3. When you give a number, name which table it came from.
4. Be direct and concise: the number, the table, one line of context —
   not a report.
"""


def build_agent(model) -> Agent:
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[query_metric, explain_metric],
        name="revenue_analyst",
        description="Answers KPI questions from the Claimwise published metric layer (gold/metrics).",
    )
