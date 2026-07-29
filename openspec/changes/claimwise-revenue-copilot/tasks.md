# Tasks (AI-DLC Bolts)

AI-DLC mapping: **Intent** = proposal + design (this folder) · **Execution** = bolts B1–B4 · **Operations** = B5 validation against real runs.

## B1. Revenue Analyst, local
- [ ] 1.1 Project scaffold: uv, `agents/` package, Makefile (`setup / run / eval`), data adapter (DuckDB/Databricks from env)
- [ ] 1.2 Tools: `query_metric` (mtr_* allowlist), `explain_metric` (definition + underlying SQL)
- [ ] 1.3 Revenue Analyst agent with the metrics glossary; CLI chat entrypoint
- [ ] 1.4 Smoke eval: 5 metric questions match live `mtr_*` values on DuckDB

## B2. Claims Investigator + data scale-up
- [ ] 2.1 Coordination (claimwise repo): raise generator volume to a few thousand claims, rebuild seeds + `rcm.duckdb`
- [ ] 2.2 Tools: `get_claim_story` (claim → activities → collections, ordered), `list_claims` (filterable, small pages)
- [ ] 2.3 Investigator agent with the billing glossary; narration follows the six-sentence story shape from the article

## B3. Full crew
- [ ] 3.1 Denials & AR Advisor: `payer_scorecard`, `ar_aging`, `appeal_outcomes` tools + agent
- [ ] 3.2 Data Steward: `run_dq_checks` (dbt test via subprocess against the claimwise repo), `get_lineage`, `glossary_lookup`
- [ ] 3.3 Supervisor (agents-as-tools); routing docstrings = context map
- [ ] 3.4 Routing evals: 10 questions land on the expected agent

## B4. AgentCore deploy
- [ ] 4.1 Runtime: supervisor packaged and deployed (agentcore starter toolkit)
- [ ] 4.2 Gateway: SQL tools exposed as MCP tools
- [ ] 4.3 Identity: read-only warehouse credential wiring; verify a write attempt fails
- [ ] 4.4 Memory: session + user preference demo
- [ ] 4.5 Observability: OTEL traces visible per question

## B5. Validation (Operations)
- [ ] 5.1 Full eval suite (~30 golden questions) green on DuckDB
- [ ] 5.2 Same suite green against Databricks prod through the deployed AgentCore runtime
- [ ] 5.3 5-minute demo script recorded in README ("revenue looks down this month" walkthrough)
- [ ] 5.4 Update specs to match reality; update project memory
