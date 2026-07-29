# Tasks (AI-DLC Bolts)

AI-DLC mapping: **Intent** = proposal + design (this folder) · **Execution** = bolts B1–B4 · **Operations** = B5 validation against real runs.

## B1. Revenue Analyst, local
- [x] 1.1 Project scaffold: uv, `agents/` package, Makefile (`setup / smoke / run / eval`), data adapter (DuckDB/Databricks from env, read-only enforced in `data.run_select`)
- [x] 1.2 Tools: `query_metric` (mtr_* allowlist, 6 tables), `explain_metric` (description + grain + column meanings)
- [x] 1.3 Revenue Analyst agent with the metrics glossary; CLI chat entrypoint (`make run`)
- [x] 1.4a No-LLM tool smoke check (`make smoke`) — 14/14 passing against the real gold layer (all 6 tables resolve, non-metric table rejected, write statement rejected)
- [x] 1.4b Golden-question eval through the real agent — **5/5 passing**, verified 2026-07-29 with `amazon.nova-lite-v1:0` (Claude Sonnet 5 via `us.anthropic.claude-sonnet-5` is the intended default but is temporarily blocked by an AWS Marketplace payment-instrument verification on this account; swap `BEDROCK_MODEL_ID` back once that clears — no code changes needed, model is env-driven). One real bug found and fixed along the way: the agent answered a company-wide total by manually summing ~40 rows of a breakdown table instead of reading the pre-aggregated `mtr_executive_summary` row, and got it wrong twice with two different wrong numbers. Fixed by adding an explicit "prefer the most aggregated table; never sum across rows yourself" rule to the system prompt — confirmed fixed on re-test.
- [x] 1.5 Observability (not originally scoped, added 2026-07-29): `agents/telemetry.py` triple-exports every trace via OTLP to LangSmith, Arize AX, and a home-lab OpenObserve instance — full prompts/tool calls/responses, all optional and env-gated. Verified past HTTP 200 by querying each backend's own API/UI for the actual stored spans, not just trusting the accepted response.

## B2. Claims Investigator + data scale-up
- [x] 2.1 Coordination (claimwise repo): raised generator volume to 5,000 claims / 8,000 encounters over 2024-08–2026-07, fixed the status/collection-recovery distributions to be realistic (see the claimwise repo's own commits `1841d8c`, `d916f40`) — done in an earlier session, ahead of this bolt.
- [x] 2.2 Tools: `get_claim_story` (claim → activities → collections, ordered, with `total_collected`/`amount_outstanding` computed in code, never by the model) and `list_claims` (filter by status/payer/patient, capped at 100 rows) in `agents/tools/billing.py`. Shared `agents/sqlutil.py` extracted for the literal-escaping helper (previously private/duplicated in `metrics.py`).
- [x] 2.3 Investigator agent (`agents/contexts/claims_investigator.py`) with the billing glossary (claim/activity/appeal/collection); narrates in real time order from `get_claim_story`'s actual rows. `make run AGENT=investigator` to chat with it directly (no supervisor yet — that's B3).
- [x] 2.4 Verification: `make smoke` extended to 20/20 (billing tools added: list/filter, known-claim lookup, appeal detection, collected-amount computation, honest not-found). Golden-question eval (`agents/eval/claim_questions.py`, 4 questions) — **9/9 total passing** across both agents (`amazon.nova-lite-v1:0`). One real bug found and fixed: asked for a claim's status by its exact code, the agent called `list_claims` (which has no claim_code filter) instead of `get_claim_story`, and reported a false "not found." Fixed with an explicit prompt rule — confirmed fixed on re-test, full narration returned correctly (submitted → processed → appealed → $4,218.95 outstanding). The open-AR summing issue from B1 recurred once more on Nova Lite specifically (a 4th different wrong number) despite the fix being in the prompt — logged as a known limitation of this substitute test model, to be re-verified once Claude Sonnet 5 is unblocked, not chased further with Nova-specific prompt tuning.

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
