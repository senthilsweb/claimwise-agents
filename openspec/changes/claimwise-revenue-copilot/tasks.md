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
- [x] 3.1 Denials & AR Advisor (`agents/tools/advisor.py`, `agents/contexts/advisor.py`): `payer_scorecard` and `ar_aging` are the Advisor's own scoped tools over the same mtr_* tables the Revenue Analyst reaches via query_metric (bounded-context rule: own tool per agent, not a shared generic one); `appeal_outcomes` is new — computed in code from real claim/activity/collection rows (1,944 ever-appealed claims: 600 collected / 1,344 not, with real dollar totals), never an opinion.
- [x] 3.2 Data Steward (`agents/tools/steward.py`, `agents/contexts/steward.py`): `run_dq_checks` runs the claimwise repo's real `dbt test` live via subprocess (~5s on DuckDB) and reports pass/warn/error/skip + a trustworthy flag; `get_lineage` reads the pipeline's actual `target/manifest.json` DAG (no guessing); `glossary_lookup` reads a new shared `agents/glossary.py` — one definition per term, the ubiquitous-language idea as an actual lookup table instead of prose repeated in every prompt.
- [x] 3.3 Supervisor (`agents/contexts/supervisor.py`): all four specialists wrapped via `Agent.as_tool()`, zero data tools of its own. System prompt's "context map" section names each specialist and the vocabulary it owns.
- [x] 3.4 Routing evals (`agents/eval/routing_questions.py`, 10 questions spanning all four specialists): **10/10 passing**, checked via `result.metrics.tool_metrics` (which specialist tool was actually invoked), never by reading the prose answer.
- [x] Full-crew verification: `make smoke` extended to **29/29** (10 new checks, zero LLM calls). Full live eval (golden + claim + routing, 19 questions total) — **19/19 passing** on `amazon.nova-lite-v1:0`, no flakiness this run (contrast with B1/B2 — see [[claimwise-agents-nova-lite-reliability]] memory, updated).
- One real bug found and fixed (not a model issue): `run_dq_checks` failed every time it ran after any other tool call in the same process — DuckDB's file lock. `agents/data.py`'s cached read-only connection blocked dbt's own DuckDB adapter (which always opens read-write, even for `dbt test`) from acquiring its lock on `rcm.duckdb`. Fixed with `release_duckdb_connection()`, called before the subprocess when `AGENT_TARGET=duckdb`; the connection reopens lazily on the next query. Confirmed fixed: 27/29 → 29/29.

## B4. AgentCore deploy

**Scope decision (2026-07-29):** the IAM user created for this project was
deliberately scoped to Bedrock-model-invoke only (see `claimwise-agents`
memory). A real `agentcore deploy` needs materially more — IAM role
creation/passing (the toolkit creates the Runtime's execution role on your
behalf), full `bedrock-agentcore:*` control plane, and S3/ECR/CodeBuild
depending on deployment mode. Given the choice between a broad grant, a
narrow hand-crafted policy, or pausing live deploy, the call was to **pause
live cloud deployment** and build/verify everything possible without it.
Also noted: `bedrock-agentcore-starter-toolkit` (used below) prints a
deprecation warning pointing at a new Node-based `@aws/agentcore` CLI;
Node was broken locally (unrelated Homebrew issue), so the still-functional
Python toolkit was kept rather than yak-shaving an unrelated fix.

**Resumed and deployed (2026-07-30).** Granted `IAMFullAccess`,
`AmazonS3FullAccess`, `BedrockAgentCoreFullAccess`, and
`AmazonBedrockAgentCoreMemoryBedrockModelInferenceExecutionRolePolicy` to
the `claimwise-agents` IAM user, then ran `agentcore configure` +
`agentcore deploy` for real. Also: the AWS Marketplace payment-instrument
block from Bolt 1 (see `claimwise-agents-nova-lite-reliability` memory)
had cleared by this point, so this deploy runs on the intended production
model, `us.anthropic.claude-sonnet-5` — not the Nova Lite stand-in.

- [x] 4.1 Runtime: **live, not just local.** Real deploy:
  `arn:aws:bedrock-agentcore:us-east-2:932612418290:runtime/claimwise_supervisor-lmETE5GGLM`,
  status `Ready`. One real packaging bug hit and fixed: the first deploy
  attempt failed at the dependency-build step —
  `numpy==2.5.1` (pulled in transitively via `databricks-sql-connector`
  → `pandas`) had no published wheel for the aarch64-manylinux targets
  AgentCore's `direct_code_deploy` cross-compiles for, and the build
  step refuses to build from source. Pinned `numpy<2.5` (resolved to
  2.4.6), redeployed clean. Second gotcha: the first successful deploy
  had no `--env` vars, so the Runtime crashed on `BEDROCK_MODEL_ID is not
  set` — `agentcore invoke` surfaced this as a generic "initialization
  time exceeded" error; the real cause only appeared in the CloudWatch
  runtime logs (`aws logs tail .../runtime-logs`). Redeployed with
  `--env AGENT_TARGET=databricks --env BEDROCK_MODEL_ID=... --env
  DATABRICKS_HOST=... --env DATABRICKS_HTTP_PATH=... --env
  DATABRICKS_TOKEN=... --env DATABRICKS_CATALOG=...` (DuckDB is a local
  file path — meaningless on the cloud runtime, so the live deployment
  always runs against Databricks). Verified with three real
  `agentcore invoke` calls against the live endpoint: a metrics question
  (denial rate, correct), a claim question (CLM48516149, full correct
  narration), and a portfolio question (appeal outcomes — Sonnet 5 added
  real synthesis on top of the tool's numbers, "$2.23 written off for
  every $1 recovered", still grounded in `appeal_outcomes`'s real output).
- [ ] 4.2 Gateway: still **designed, not built** — exposing tools as MCP
  Gateway targets requires packaging them as Lambda handlers first
  (Gateway targets are `lambda | openApiSchema | mcpServer |
  smithyModel`; there is no "point at a Python function" option).
  Concrete next steps: package `agents/tools/*.py` as a Lambda handler →
  `agentcore create_mcp_gateway --name claimwise-tools-gateway --region
  us-east-2` → `agentcore create_mcp_gateway_target --gateway-arn <arn>
  --gateway-url <url> --role-arn <role> --target-type lambda` → consume
  from the Supervisor via `MCPClient` + `aws_iam_streamablehttp_client`.
- [x] 4.3 Identity: the actual requirement — read-only warehouse access,
  verified a write attempt fails — was already done and verified in
  `make smoke` since Bolt 1. *AgentCore's* Identity service specifically
  (vending the Databricks token via Workload Identity instead of a
  `--env` var) is still deferred — the live deployment above passes the
  token as a plain environment variable, matching this project's stated
  convention; migrating to credential vending is a deliberate future step,
  not a gap.
- [x] 4.4 Memory: **live, not just code-ready.** `agentcore deploy` auto-
  created a real AgentCore Memory resource
  (`claimwise_supervisor_mem-oka122BEo4`, STM-only, 30-day retention) and
  it reached `ACTIVE` (took 153s). `agentcore status` confirms it's
  attached to the Runtime. Not yet verified: that a second invocation in
  the same session actually recalls the first (each test `agentcore
  invoke` call opened its own new session) — worth a follow-up call with
  an explicit shared session id.
- [x] 4.5 Observability: `agents/telemetry.py`'s triple OTLP export
  (LangSmith/Arize/OpenObserve) was **not** enabled for this cloud
  deploy (not passed via `--env`) — separate from that, AgentCore's own
  built-in observability (ADOT → CloudWatch Logs + X-Ray) is live: real
  runtime logs were read directly from CloudWatch to diagnose the
  `BEDROCK_MODEL_ID` crash above. Two minor permission gaps surfaced
  during deploy (non-fatal, deployment succeeds either way):
  `logs:CreateLogGroup` and `logs:PutDeliverySource` — needed for
  AgentCore's automatic trace-delivery setup, not yet granted. Add
  `CloudWatchLogsFullAccess` (or a scoped log-group/delivery-source
  policy) to close this if full X-Ray trace delivery is wanted later.
- Verification: `make smoke` still **31/31** (unaffected — these are all
  live-cloud findings, not local regressions).

## B5. Validation (Operations)
- [ ] 5.1 Full eval suite (~30 golden questions) green on DuckDB
- [ ] 5.2 Same suite green against Databricks prod through the deployed AgentCore runtime
- [ ] 5.3 5-minute demo script recorded in README ("revenue looks down this month" walkthrough)
- [ ] 5.4 Update specs to match reality; update project memory
