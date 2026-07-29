# Design: Claimwise Revenue Copilot

## Agents = bounded contexts

| Agent | Context | Glossary (system prompt carries only this) | Tools |
|---|---|---|---|
| Revenue Analyst | gold/metrics | KPI definitions: denial rate, collection rate, open AR, cycle days | `query_metric`, `explain_metric` |
| Claims Investigator | gold/billing | claim, activity, appeal, collection, status lifecycle | `get_claim_story`, `list_claims` |
| Denials & AR Advisor | gold/billing | payer, scorecard, aging bucket, appeal outcome | `payer_scorecard`, `ar_aging`, `appeal_outcomes` |
| Data Steward | governance | test, freshness, lineage, glossary term | `run_dq_checks`, `get_lineage`, `glossary_lookup` |
| Supervisor | context map | routing vocabulary only — no data tools | the four agents (agents-as-tools) |

Rules enforced by construction, not prompts:
- Tools are read-only (SELECT only; no DDL/DML path exists in the code).
- `query_metric` accepts only `mtr_*` table names — an allowlist, not a convention.
- Cross-context data never flows tool-to-tool; it flows through supervisor conversation, referencing IDs (the aggregate rule from the article).

## Data access

One thin adapter, target from env (`AGENT_TARGET`):
- **duckdb** (dev): read the claimwise repo's `rcm.duckdb` directly. Zero infra; same dev story as the pipeline.
- **databricks** (prod): `databricks-sql-connector` against the SQL warehouse, `DATABRICKS_CATALOG.gold.*`, token with read-only grants.

Portable SQL only, unquoted identifiers (serverless rejects quoted ones — known from the pipeline).

## Strands mapping

- Each agent: `Agent(model=bedrock, system_prompt=<context glossary>, tools=[...])`.
- Supervisor: agents-as-tools — specialists wrapped as `@tool` functions; the supervisor's docstrings ARE the context map.
- Local entrypoint: small CLI chat loop (`make run`); no server needed for dev.

## AgentCore mapping (last bolt)

| AgentCore piece | Used for | Maps to (article concept) |
|---|---|---|
| Runtime | supervisor as the single deployed entrypoint | the context map has one door |
| Gateway | SQL tools exposed as MCP tools | published language as an API |
| Identity | read-only warehouse credentials to agents | trust boundary: read freely, write never |
| Memory | user preferences across sessions ("CFO prefers monthly view") | — |
| Observability | OTEL traces per question: which context answered, which tables read | decision lineage next to data lineage |

## Evals (Operations)

- ~30 golden questions in three groups: metric lookups (exact number match against a live query of the same `mtr_*` table), routing (question → expected agent), claim stories (structural assertions: correct event sequence for a known claim).
- Deterministic where possible; no LLM-judge in v1.
- `make eval` runs against DuckDB; the same suite must pass against prod before the AgentCore deploy is called done.

## Decisions

- **Read-only v1.** The propose/dispose write path (appeal recommendations validated by claim rules) is a strong Phase 2 but doubles the surface; deliberately out.
- **Data volume**: current seeds (~300 claims) are too thin for aging demos. Coordination task: raise the data generator volume in the claimwise repo and rebuild. This repo does not generate data.
- **No RAG in v1.** The glossary is small enough to live in system prompts; a vector store would be complexity without payoff at this size.
- **Model id via env** (`BEDROCK_MODEL_ID`), never hardcoded — same rule as all other credentials.
