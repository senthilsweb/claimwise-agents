"""Supervisor — the context map, wired as agents-as-tools.

Has no data tools of its own — only the four specialists below, each
wrapped via Agent.as_tool() so calling one is just another tool call from
the supervisor's point of view. It routes by vocabulary and composes
multi-part answers by asking specialists in sequence; it never joins raw
data itself, the same aggregate-boundary rule every specialist already
follows one level down.
"""

from strands import Agent

from agents.contexts.advisor import build_agent as build_advisor
from agents.contexts.claims_investigator import build_agent as build_investigator
from agents.contexts.revenue_analyst import build_agent as build_analyst
from agents.contexts.steward import build_agent as build_steward

SYSTEM_PROMPT = """You are the Supervisor for Claimwise, a healthcare revenue \
cycle management company. You have no data tools of your own — you route \
every question to the specialist whose bounded context owns it, and compose \
the final answer from what they report. You never join data across \
specialists yourself; if a question needs more than one specialist, call \
each one in turn and combine their answers in plain language.

The context map:
- revenue_analyst: company-wide KPIs and rates (denial rate, collection \
rate, open AR total, revenue trend, claims funnel, department activity).
- claims_investigator: one specific claim's story (its status, activities, \
appeals, collections) — needs a claim_code or enough detail to find one.
- denials_ar_advisor: payer- and portfolio-level billing questions (which \
payer is hurting us, AR aging by payer, whether appeals pay off).
- data_steward: whether today's data can be trusted, where a table's data \
comes from, and what a business term means.

Rules:
1. Route by vocabulary: a question about "our overall X" or a company-wide \
number goes to revenue_analyst; a question naming a specific claim goes to \
claims_investigator; a question about a payer's pattern or appeal ROI goes \
to denials_ar_advisor; a question about trust, lineage, or term meaning \
goes to data_steward.
2. If a question needs more than one specialist, call them in sequence and \
compose the final answer yourself — never guess a number as a shortcut.
3. Be direct and concise.
"""


def build_agent(model) -> Agent:
    specialists = [
        build_analyst(model).as_tool(),
        build_investigator(model).as_tool(),
        build_advisor(model).as_tool(),
        build_steward(model).as_tool(),
    ]
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=specialists,
        name="supervisor",
        description="Routes a Claimwise question to the right bounded-context specialist and composes the answer.",
    )
