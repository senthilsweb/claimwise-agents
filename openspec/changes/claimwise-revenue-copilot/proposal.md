# Proposal: Claimwise Revenue Copilot — One Agent per Bounded Context

## Intent (AI-DLC phase 1)

Build a working, public showcase that proves one claim: **the boundaries that make a data platform trustworthy are the same boundaries that make AI agents trustworthy.**

Concretely: the Claimwise gold layer is already organized as bounded contexts (clinical / billing / admin) with a metric layer where every KPI is defined once. This change turns that design into a running multi-agent system — one Strands agent per context, a supervisor routing between them, deployed on Amazon Bedrock AgentCore — so that a fuzzy business question ("revenue looks down this month, what is going on?") gets answered with the same numbers the CFO's dashboard shows, with every step traceable.

Boundaries of this intent (as important as the goal):
- **Read-only.** No agent writes to the warehouse. The write path (propose/dispose on appeals) is explicitly out of scope for v1.
- **Metric-first.** KPI questions are answered from `mtr_*` tables only. A missing metric is fixed in the claimwise repo, never worked around here.
- **Local-first.** Everything runs on a laptop against DuckDB before anything touches AWS. AgentCore is the last bolt, not the first.
- **Same discipline as the article.** Each agent gets one context's glossary (ubiquitous language); cross-context questions go through the supervisor (context map). If the code cannot be explained by the DDD-for-AI article, the code is wrong.

Success looks like: the 5-minute demo — one fuzzy question, four contexts cooperating, every number matching the metric tables — plus a deterministic eval suite green on DuckDB and the same agents live on AgentCore.

## Why
- The Claimwise pipeline is verified end-to-end (bronze/silver/gold, 220 green checks, dashboard deployed) but nothing conversational consumes it — the story stops at widgets.
- The DDD-for-AI article argues bounded contexts are what agents need; a public repo that executes the argument is stronger than the argument alone.
- Strands + AgentCore is a current, searchable stack; a grounded example over a real dbt semantic layer (not a toy CSV) fills a visible gap in existing samples.

## What Changes
- **`agents/` package**: four context agents (Revenue Analyst, Claims Investigator, Denials & AR Advisor, Data Steward) + Supervisor, each with its own glossary and read-only tools.
- **Tools**: thin SQL functions over DuckDB/Databricks (target switched by env), metric-first; claim-story tool that narrates a claim's lifecycle from real rows.
- **Evals**: golden question set with expected numbers computed from the metric tables (deterministic, exact assertions).
- **Deploy**: AgentCore Runtime (supervisor), Gateway (SQL tools as MCP), Identity (read-only role), Memory, Observability (OTEL traces).
- **Makefile**: `setup / run / eval` — deliberately simple.

## Impact
- Affected specs: `context-agents` (new), `copilot-operations` (new)
- Affected code: this repo only (new). The claimwise repo is read, not changed — except one coordination task: scale the data generator output (a few thousand claims) so AR/aging demos are convincing.
- Not affected: pipeline models, tests, dashboard.
