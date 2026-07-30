# The Agents

At the end you will know what each agent does, what it's allowed to touch,
and the rules that are enforced in code rather than just in a prompt.

## The idea in one paragraph

Claimwise's gold layer is already organized as bounded contexts —
`clinical`, `billing`, `admin` — with a metrics layer where every KPI is
computed once. This project makes that design executable: **one agent per
bounded context**, each with its own vocabulary and its own tools, plus a
Supervisor that routes each question to whichever specialist owns it and
composes multi-part answers.

## The crew

| Agent | Bounded context | Tools | Answers |
|---|---|---|---|
| Revenue Analyst | `gold/metrics` | `query_metric`, `explain_metric` | "What is our denial rate?" — reads `mtr_claims_funnel` |
| Claims Investigator | `gold/billing` (single claim) | `get_claim_story`, `list_claims` | "Why is this claim unpaid?" — narrates filed → denied → appealed → collected |
| Denials & AR Advisor | `gold/billing` (portfolio) | `payer_scorecard`, `ar_aging`, `appeal_outcomes` | "Which payer is hurting us? Are appeals worth it?" |
| Data Steward | pipeline governance | `run_dq_checks`, `get_lineage`, `glossary_lookup` | "Can I trust these numbers today?" — live dbt test status, real lineage |
| Supervisor | context map | the four agents above, wrapped as tools | routes to the right specialist, composes multi-part answers |

## Rules enforced in code, not just in a prompt

**Read-only, by construction.** Every tool's SQL passes through one
function (`agents/data.py`'s `run_select`) that rejects anything that
isn't a plain `SELECT`/`WITH` statement before it ever reaches a
connection. This is tested directly — `make smoke` includes "run_select
rejects a write statement" — not just assumed from the prompt wording.

**Metric-first.** The Revenue Analyst's `query_metric` only accepts an
explicit allowlist of six published `mtr_*` tables. It cannot see or join
raw fact tables — the allowlist is a Python `dict`, not a suggestion.

**One tool per bounded context, even for the same data.** The Denials &
AR Advisor's `payer_scorecard` and the Revenue Analyst's `query_metric`
can both read `mtr_payer_scorecard`, but each agent gets its own named
tool. No agent's toolset spans another agent's vocabulary.

**A claim's story is read in real time order.** `get_claim_story` returns
a claim's activities and collections ordered by date, with `total_collected`
and `amount_outstanding` computed in Python — the model narrates what the
tool already computed, it never sums rows itself. (This rule exists
*because* an earlier version of the prompt let the model do that
arithmetic, and it got the answer wrong four different ways across four
tries — see [Runbook](runbook.md).)

**The Supervisor has no data tools of its own.** It only holds the four
specialists, each wrapped via Strands'
[`Agent.as_tool()`](https://github.com/strands-agents/sdk-python). Ask it
something that needs two specialists and it calls each one in turn and
composes the answer itself — it never joins their raw data.

## What next

- Every environment variable that shapes these agents → [Configuration](configuration.md)
- Watching exactly what a question does, tool call by tool call → [Observability](observability.md)
