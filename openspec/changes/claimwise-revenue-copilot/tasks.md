# Tasks (AI-DLC Bolts)

AI-DLC mapping: **Intent** = proposal + design (this folder) · **Execution** = bolts B1–B4 · **Operations** = B5 validation against real runs.

## B1. Revenue Analyst, local
- [x] 1.1 Project scaffold: uv, `agents/` package, Makefile (`setup / smoke / run / eval`), data adapter (DuckDB/Databricks from env, read-only enforced in `data.run_select`)
- [x] 1.2 Tools: `query_metric` (mtr_* allowlist, 6 tables), `explain_metric` (description + grain + column meanings)
- [x] 1.3 Revenue Analyst agent with the metrics glossary; CLI chat entrypoint (`make run`)
- [x] 1.4a No-LLM tool smoke check (`make smoke`) — 14/14 passing against the real gold layer (all 6 tables resolve, non-metric table rejected, write statement rejected)
- [ ] 1.4b Golden-question eval through the real agent (`make eval`, `agents/eval/run_eval.py` + `golden_questions.py` written, 5 questions) — **blocked: no AWS credentials configured in this environment.** Needs `BEDROCK_MODEL_ID` set to a model you have Bedrock access to, and `aws sso login` (or equivalent) before this can run.

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
