# Code Tour

At the end you will know where everything lives, which files carry the
load-bearing rules, and where to look first when changing behavior. The
whole package is small on purpose — about 1,800 lines of Python across
`agents/` and `chat-adapter/`.

## The tree

```
openspec/                  the intent — specs and change proposals (AI-DLC: Intent → Execution → Operations)
agents/                    the Python package — everything the agent is
  contexts/                 one file per bounded-context agent
    supervisor.py            the context map: four specialists wrapped as tools, no data tools of its own
    revenue_analyst.py       gold/metrics — KPI questions
    claims_investigator.py   gold/billing — one claim's story
    advisor.py               gold/billing — payer/AR portfolio
    steward.py               governance — dbt tests, lineage, glossary
  tools/                    what each agent is allowed to call
    metrics.py               query_metric + the METRIC_CATALOG allowlist
    billing.py               get_claim_story / list_claims (Claim is the aggregate root)
    advisor.py               payer_scorecard / ar_aging / appeal_outcomes
    steward.py               run_dq_checks / get_lineage / glossary_lookup
  eval/                     deterministic evals — asserted against live tables, no LLM judge
    tool_smoke.py            31 no-LLM checks (data adapter, tools, runtime app)
    run_eval.py              golden + claim + routing suites against the real model
  data.py                   THE read-only gate — every query passes run_select()
  config.py                 all env-driven config; nothing hardcoded elsewhere
  models.py                 Bedrock model factory (BEDROCK_MODEL_ID from env)
  glossary.py               agreed business term definitions
  sqlutil.py                SQL literal escaping for fixed-shape queries
  telemetry.py              OTLP export to LangSmith / Arize / OpenObserve
  runtime.py                the AgentCore Runtime entrypoint (BedrockAgentCoreApp)
  cli.py                    the local chat loop (make run)
chat-adapter/              the browser-widget → AgentCore bridge (its own tiny project + image)
docker-compose.yml         widget + adapter test stack (make chat)
bedrock_agentcore.sample.yaml  shape of the gitignored deploy-state file
docs/                      this wiki
```

## The load-bearing files

Most files are plumbing; these five carry the rules that make the system
trustworthy. Change them knowingly.

| File | The rule it enforces |
|---|---|
| `agents/data.py` | **Read-only by construction.** `run_select()` regex-rejects anything that isn't a single `SELECT`/`WITH` before it reaches a connection — DuckDB and Databricks both. `ReadOnlyViolation` is raised, never caught-and-retried. Tested in `make smoke`. |
| `agents/tools/metrics.py` | **Metric-first.** `METRIC_CATALOG` is a Python dict allowlisting the six published `mtr_*` tables — a table not listed cannot be queried at all. Missing metrics get built in the claimwise dbt repo, not worked around here. |
| `agents/tools/billing.py` | **The aggregate boundary.** A claim's story is computed in code (activities + collections in time order, totals pre-computed) — the model narrates, it never sums rows. The join logic is fixed; the model never writes billing SQL. |
| `agents/contexts/supervisor.py` | **Cross-context only via the Supervisor.** It holds no data tools — just the four specialists via `Agent.as_tool()`. Its system prompt's context map *is* the routing table. |
| `agents/runtime.py` | **Fresh agents per invocation.** A new Supervisor (and specialists) is built for every request so one caller's conversation can never leak into another's — a real bug caught before deploy, now a rule. |

## Patterns worth knowing before editing

- **Every specialist follows the same shape:** a `build_agent(model)`
  factory, a `SYSTEM_PROMPT` carrying exactly one bounded context's
  vocabulary, and tools imported from its matching `agents/tools/`
  module. Adding a fifth specialist means one new file in each folder
  plus a context-map entry in the Supervisor's prompt.
- **Config flows one way.** `agents/config.py` loads `.env` once;
  everything else imports from it. If you find yourself calling
  `os.getenv` elsewhere, you're in the wrong file.
- **Evals are deterministic.** `agents/eval/` asserts model answers
  against values read live from the metric tables — when the data
  regenerates, the expected values move with it. No LLM-as-judge.
- **The adapter is not part of the agent.** `chat-adapter/` has its own
  dependencies, image, and contract ([Chat Channel](chat-channel.md));
  nothing in `agents/` knows it exists.

## Where the intent lives

Code answers *what*; [`openspec/changes/claimwise-revenue-copilot/`](https://github.com/senthilsweb/claimwise-agents/tree/main/openspec/changes/claimwise-revenue-copilot)
answers *why* — the proposal, design decisions, and the bolt-by-bolt task
history. When a rule in the table above feels arbitrary, its reasoning is
recorded there or in [Operations](operations.md#runbook).

## What next

- How these pieces execute a question → [Architecture](architecture.md)
- Running it → [Getting Started](getting-started.md)
